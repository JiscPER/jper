import csv
import dataclasses
import io
import itertools
import logging
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Iterable, Callable, Type, Optional, NoReturn

import chardet
import openpyxl
from esprit.dao import DomainObject
from flask import Blueprint, abort, render_template, request, redirect, url_for, send_file
from flask_login.utils import current_user

from octopus.core import app
from octopus.lib import dates
from service.__utils import ez_dao_utils, ez_query_maker
from service.__utils.ez_dao_utils import object_query_first
from service.models import License
from service.models.ezb import LRF_TYPES, LicRelatedFile, Alliance

blueprint = Blueprint('license-manage', __name__)

log: logging.Logger = app.logger

ALLOWED_DEL_STATUS = ["validation failed", "archived"]

CompleteChecker = Callable[[], NoReturn]


def _create_versioned_filename(filename: str,
                               version_datetime: datetime = None) -> str:
    if version_datetime is None:
        version_datetime = datetime.now()

    idx = filename.rfind('.')
    if idx == -1:
        name = filename
        fmt = ''
    else:
        name = filename[:idx]
        fmt = filename[idx + 1:]

    date_str = version_datetime.strftime('%Y%m%dT%H%M%S')
    return f'{name}.{date_str}.{fmt}'


@dataclasses.dataclass
class LicenseFile:
    ezb_id: str
    name: str
    table_str: str  # table data as csv string
    filename: str
    version_datetime: datetime = dataclasses.field(default_factory=datetime.now)

    @property
    def versioned_filename(self):
        return _create_versioned_filename(self.filename,
                                          self.version_datetime)


@dataclasses.dataclass
class ParticipantFile:
    lic_ezb_id: str
    table_str: str
    filename: str
    version_datetime: datetime = dataclasses.field(default_factory=datetime.now)

    @property
    def versioned_filename(self):
        return _create_versioned_filename(self.filename,
                                          self.version_datetime)


@dataclasses.dataclass
class ActiveLicRelatedRow:
    lic_lrf_id: str
    lic_filename: str
    lic_upload_date: str
    lic_type: str
    parti_lrf_id: str
    parti_filename: str
    parti_upload_date: str


def abort_if_not_admin():
    # KTODO change it to Decorators
    if not current_user.is_super:
        abort(401)


def _split_list_by_cond_fn(cond_fn: Callable[[any], bool],
                           obj_list: list[any], ) -> tuple[Iterable, Iterable]:
    return filter(cond_fn, obj_list), itertools.filterfalse(cond_fn, obj_list)


def _to_active_lr_rows(lic_lrf: LicRelatedFile,
                       parti_lr_files: list[LicRelatedFile]) -> ActiveLicRelatedRow:
    parti = [lr for lr in parti_lr_files if lr.lic_related_file_id == lic_lrf.id]
    parti = parti and parti[0]
    if parti:
        parti_filename = parti.file_name
        parti_upload_date = parti.upload_date
        parti_lrf_id = parti.id
    else:
        parti_filename = ''
        parti_upload_date = ''
        parti_lrf_id = ''

    return ActiveLicRelatedRow(lic_lrf.id, lic_lrf.file_name, lic_lrf.upload_date, lic_lrf.type,
                               parti_lrf_id, parti_filename, parti_upload_date)


@blueprint.route('/')
def details():
    abort_if_not_admin()

    query = ez_query_maker.match_all()
    query['sort'] = [{"last_updated": {"order": "desc"}}]
    query['size'] = 100
    lic_related_files = [l for l in LicRelatedFile.object_query(query)]
    active_lr_files, inactive_lr_files = _split_list_by_cond_fn(lambda l: l.status == 'active',
                                                                lic_related_files)
    active_lr_files = list(active_lr_files)

    # if lic_related_file_id is None, this record must be license file
    lic_lr_files, parti_lr_files = _split_list_by_cond_fn(lambda l: l.lic_related_file_id is None,
                                                          active_lr_files)
    parti_lr_files = list(parti_lr_files)

    # prepare active_list
    active_list: Iterable[ActiveLicRelatedRow] = (_to_active_lr_rows(lic_lrf, parti_lr_files)
                                                  for lic_lrf in lic_lr_files)

    # KTODO add disable btn message for parti msg

    return render_template('license_manage/details.html',
                           allowed_lic_types=LRF_TYPES,
                           active_list=active_list,
                           history_list=(l.data for l in inactive_lr_files),
                           allowed_del_status=ALLOWED_DEL_STATUS, )


def _load_rows_by_csv_str(csv_str: str) -> list[list]:
    return [row for row in csv.reader(io.StringIO(csv_str), delimiter='\t',
                                      quoting=csv.QUOTE_ALL)]


def _to_csv_str(headers: list, data: Iterable[list]) -> str:
    dict_rows = [{headers[col_idx]: row[col_idx] for col_idx in range(len(headers))}
                 for row in data]

    tmp_file_path = tempfile.mkstemp(prefix='__lc__')[1]
    with open(tmp_file_path, 'w') as tmp_file:
        writer = csv.DictWriter(tmp_file, fieldnames=headers, delimiter='\t', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in dict_rows:
            writer.writerow(row)

    with open(tmp_file_path, 'r') as tmp_file:
        table_str = tmp_file.read()

    os.remove(tmp_file_path)
    return table_str


def _load_rows_by_xls_bytes(xls_bytes: bytes) -> list[list]:
    workbook = openpyxl.load_workbook(io.BytesIO(xls_bytes))
    sheet = workbook.active
    rows = [[c.value for c in r] for r in sheet.rows]
    return rows


def _load_lic_file_by_rows(rows: list[list], filename: str) -> LicenseFile:
    headers = rows[4]
    data = rows[5:]
    table_str = _to_csv_str(headers, data)
    name, ezb_id = _extract_name_ezb_id_by_line(rows[0][0])
    return LicenseFile(ezb_id, name, table_str, filename=filename)


@blueprint.route('/upload-license', methods=['POST'])
def upload_license():
    abort_if_not_admin()
    lrf = _upload_new_lic_lrf(request.values.get('lic_type'),
                              request.files.get('file'),
                              admin_notes=request.values.get('admin_notes', ''))
    ez_dao_utils.wait_unit_id_found(LicRelatedFile, lrf.id)
    return redirect(url_for('license-manage.details'))


def _upload_new_lic_lrf(lic_type: str, file,
                        admin_notes: str = '',
                        ezb_id: str = None):
    if lic_type not in LRF_TYPES:
        abort(400, f'Invalid parameter "lic_type" [{lic_type}]')

    if file is None:
        abort(400, 'parameter "file" not found')

    # load lic_file
    filename = file.filename
    file_bytes = file.stream.read()

    filename_lower: str = filename.lower().strip()
    if all(not filename_lower.endswith(f) for f in ['.csv', '.xls', '.xlsx']):
        abort(400, f'Invalid file format [{filename}]')

    if any(filename.lower().endswith(fmt) for fmt in ['.xls', '.xlsx']):
        rows = _load_rows_by_xls_bytes(file_bytes)
    else:
        csv_str = _decode_csv_bytes(file_bytes)
        rows = _load_rows_by_csv_str(csv_str)

    # validate and abort if failed
    try:
        _validate_lic_lrf(rows)
    except ValueError as e:
        lrf_raw = dict(file_name=filename,
                       type=lic_type,
                       status='validation failed',
                       admin_notes=admin_notes,
                       validation_notes=str(e),
                       )
        LicRelatedFile.save_by_raw(lrf_raw, blocking=False)
        abort(400, f'file validation fail --- {str(e)}')
        return
    lic_file = _load_lic_file_by_rows(rows, filename=filename)
    ezb_id = ezb_id or lic_file.ezb_id

    # create license by csv file
    lic = License()
    lic.set_license_data(ezb_id, lic_file.name,
                         type=lic_type, csvfile=lic_file.table_str,
                         init_status='inactive')

    # save lic_related_file to db
    lrf_raw = dict(file_name=lic_file.versioned_filename,
                   type=lic_type,
                   ezb_id=ezb_id,
                   status='validation passed',
                   admin_notes=admin_notes,
                   record_id=lic.id,
                   upload_date=dates.format(lic_file.version_datetime), )
    lrf = LicRelatedFile.save_by_raw(lrf_raw, blocking=False)

    # save file to hard disk
    _save_lic_related_file(lic_file.versioned_filename, file_bytes)

    return lrf


def _find_idx(header_row, col_name):
    for i, v in enumerate(header_row):
        if v == col_name:
            return i
    raise ValueError(f'colum not found [{col_name}]')


def _is_empty_or_int(header_row, row, col_name):
    _val = row[_find_idx(header_row, col_name)].strip()
    return not _val or _val.isdigit()


def _is_empty_or_http(header_row, row, col_name):
    _val = row[_find_idx(header_row, col_name)].strip()
    return not _val or _val.startswith('http')


class ValidEmptyOrInt:
    def __init__(self, col_name: str, header_row: list):
        self.col_name = col_name
        self.col_idx = _find_idx(header_row, col_name)

    def validate(self, row: list) -> Optional[str]:
        _val = row[self.col_idx].strip()
        if not _val or _val.isdigit():
            return None
        else:
            return f'column [{self.col_name}][{_val}] must be int'


class ValidEmptyOrHttpLink:
    def __init__(self, col_name: str, header_row: list):
        self.col_name = col_name
        self.col_idx = _find_idx(header_row, col_name)

    def validate(self, row: list) -> Optional[str]:
        _val = row[self.col_idx].strip()
        if not _val or _val.startswith('http'):
            return None
        else:
            return f'column [{self.col_name}][{_val}] must be start with http'


def _validate_parti_lrf(rows: list[list]):
    header_row_idx = 0
    n_cols = 3
    if len(rows) < header_row_idx + 1:
        raise ValueError('header not found')

    if len(rows[0]) < n_cols:
        raise ValueError(f'csv should have {n_cols} columns')


def _validate_lic_lrf(rows: list[list]):
    n_cols = 9
    header_row_idx = 4

    if len(rows) == 0 or len(rows[0]) == 0:
        raise ValueError('first line not found')
    _extract_name_ezb_id_by_line(rows[0][0])

    if len(rows) < header_row_idx + 1:
        raise ValueError('header not found')

    if len(rows) < n_cols:
        raise ValueError(f'csv should have {n_cols} columns')

    header_row = rows[header_row_idx]

    # check mandatory header
    missing_headers = {'Titel', 'Verlag', 'E-ISSN', 'P-ISSN', 'Embargo'} - set(header_row)
    if missing_headers:
        raise ValueError(f'missing header {missing_headers}')

    validate_fn_list = [
        ValidEmptyOrInt('erstes Jahr', header_row),
        ValidEmptyOrInt('Embargo', header_row),
    ]

    row_validator_list = itertools.product(rows[header_row_idx + 1:], validate_fn_list)
    err_msgs = (validator.validate(row) for row, validator in row_validator_list)
    err_msgs = filter(None, err_msgs)
    for err_msg in err_msgs:
        raise ValueError(err_msg)


@blueprint.route('/active-lic-related-file', methods=['POST'])
def active_lic_related_file():
    abort_if_not_admin()
    checker_list = []

    lrf_id = request.values.get('lrf_id')
    checker_list.append(_active_lic_related_file(lrf_id))

    # deactivate if lrf with same ezb_id
    lr_file = _check_and_find_lic_related_file(lrf_id)
    if lr_file.is_license():
        old_lic_lrf_list = LicRelatedFile.pull_all_by_query_str('ezb_id', lr_file.ezb_id)
        old_lic_lrf_list = (lrf for lrf in old_lic_lrf_list
                            if lrf.id != lrf_id and lrf.is_active())
        for old_lrf in old_lic_lrf_list:
            checker_list.append(_deactivate_lrf_by_lrf_id(old_lrf.id, License))
            old_pari_lrf_list = LicRelatedFile.pull_all_by_query_str("lic_related_file_id", old_lrf.id)
            old_pari_lrf_list = (lrf for lrf in old_pari_lrf_list
                                 if lrf.is_active())
            checker_list.extend(_deactivate_lrf_by_lrf_id(old_pari_lrf.id, Alliance)
                                for old_pari_lrf in old_pari_lrf_list)

    # wait all db update completed
    for checker in checker_list:
        checker()

    return redirect(url_for('license-manage.details'))


def _active_lic_related_file(lrf_id) -> CompleteChecker:
    # active lic_related_file
    lr_file = _check_and_find_lic_related_file(lrf_id)
    lr_file.status = 'active'
    lr_file.save()

    record_cls = Alliance if lr_file.lic_related_file_id else License

    # active record
    record = object_query_first(record_cls, lr_file.record_id)
    if record:
        record.status = 'active'
        record.save()
    else:
        log.warning(f'license / alliance not found record_id[{lr_file.record_id}] lrf_id[{lrf_id}]')

    def _checker():
        _wait_unit_status(lr_file.id, 'active')

    return _checker


def _wait_unit_status(lrf_id: str, target_status):
    def _is_updated():
        _obj = object_query_first(LicRelatedFile, lrf_id)
        if _obj:
            return _obj.status == target_status
        return False

    ez_dao_utils.wait_unit(_is_updated)


def _check_and_find_lic_related_file(lrf_id: str) -> LicRelatedFile:
    def _abort():
        log.warning(f'lic_related_file not found lrf_id[{lrf_id}]')
        abort(404)

    if not lrf_id:
        _abort()

    lr_file: LicRelatedFile = object_query_first(LicRelatedFile, lrf_id)
    if not lr_file:
        _abort()

    return lr_file


def _load_parti_csv_str_by_xls_bytes(xls_bytes: bytes) -> str:
    rows = _load_rows_by_xls_bytes(xls_bytes)
    if len(rows) == 0:
        return ''

    table_str = _to_csv_str(rows[0], rows[1:])
    return table_str


def _save_lic_related_file(filename: str, file_bytes: bytes):
    path = _path_lic_related_file(filename)
    if not path.parent.exists():
        path.parent.mkdir(exist_ok=True, parents=True)
    path.write_bytes(file_bytes)


def _path_lic_related_file(filename: str) -> Path:
    path = app.config.get('LIC_RELATED_FILE_DIR', '/data/lic_related_file')
    path = Path(path)
    return path.joinpath(filename)


@blueprint.route('/upload-participant', methods=['POST'])
def upload_participant():
    abort_if_not_admin()

    lrf = _upload_new_parti_lrf(request.values.get('lic_lrf_id'),
                                request.files.get('file'))

    ez_dao_utils.wait_unit_id_found(LicRelatedFile, lrf.id)

    return redirect(url_for('license-manage.details'))


@blueprint.route('/update-license', methods=['POST'])
def update_license():
    abort_if_not_admin()

    old_lic_lrf_id = request.values.get('lic_lrf_id')
    old_lic_lrf: LicRelatedFile = _check_and_find_lic_related_file(old_lic_lrf_id)

    new_lrf = _upload_new_lic_lrf(old_lic_lrf.type,
                                  request.files.get('file'),
                                  ezb_id=old_lic_lrf.ezb_id)
    ez_dao_utils.wait_unit_id_found(LicRelatedFile, new_lrf.id)

    active_checker = _active_lic_related_file(new_lrf.id)

    deact_checker = _deactivate_lrf_by_lrf_id(old_lic_lrf_id, License)

    # replace to new lic_lrf_id
    parti_lrf_id = request.values.get('parti_lrf_id')
    if parti_lrf_id:
        parti_lr_file = _check_and_find_lic_related_file(parti_lrf_id)
        parti_lr_file.lic_related_file_id = new_lrf.id
        parti_lr_file.save()
        ez_dao_utils.wait_unit(
            lambda: LicRelatedFile.count(ez_query_maker.by_term("lic_related_file_id", new_lrf.id))
        )

    # wait for completed
    active_checker()
    deact_checker()

    return redirect(url_for('license-manage.details'))


def _upload_new_parti_lrf(lic_lrf_id: str, file) -> LicRelatedFile:
    lic_lr_file: LicRelatedFile = _check_and_find_lic_related_file(lic_lrf_id)

    # validate
    lic: License = object_query_first(License, lic_lr_file.record_id)
    lic_ezb_id = lic and lic.get_first_ezb_id()
    if lic_ezb_id is None:
        log.warning(f'ezb_id not found -- {lic_lr_file.record_id}')
        abort(404)

    # load parti_file
    filename = file.filename
    file_bytes = file.stream.read()
    csv_str: str = None
    if filename.lower().endswith('.csv'):
        csv_str = _decode_csv_bytes(file_bytes)
    elif any(filename.lower().endswith(fmt) for fmt in ['xls', 'xlsx']):
        csv_str = _load_parti_csv_str_by_xls_bytes(file_bytes)
    else:
        abort(400, f'Invalid file format [{filename}]')

    rows = _load_rows_by_csv_str(csv_str)
    _validate_parti_lrf(rows)

    parti_file = ParticipantFile(lic_lrf_id, csv_str, filename)

    # disable all old record
    for old_lic in Alliance.pull_all_by_status_ezb_id('active', lic_ezb_id):
        old_lic.status = 'inactive'
        old_lic.save()

    # save participant to db
    alliance = Alliance()
    alliance.set_alliance_data(lic_lr_file.record_id, lic_ezb_id, csvfile=csv_str,
                               init_status='inactive')

    # save lic_related_file to db
    lr_file_raw = dict(file_name=parti_file.versioned_filename,
                       type=None,
                       ezb_id=lic_ezb_id,
                       status='validation passed',
                       admin_notes=None,
                       record_id=alliance.id,
                       upload_date=dates.format(parti_file.version_datetime),
                       lic_related_file_id=lic_lr_file.id)
    new_lrf = LicRelatedFile.save_by_raw(lr_file_raw, blocking=False)

    # save file to hard disk
    _save_lic_related_file(parti_file.versioned_filename, file_bytes)

    return new_lrf


@blueprint.route('/update-participant', methods=['POST'])
def update_participant():
    abort_if_not_admin()
    lic_lrf_id = request.values.get('lic_lrf_id')
    _check_and_find_lic_related_file(lic_lrf_id)

    # save new parti
    new_lrf = _upload_new_parti_lrf(lic_lrf_id, request.files.get('file'), )
    ez_dao_utils.wait_unit_id_found(LicRelatedFile, new_lrf.id)

    # active new record immediately
    active_checker = _active_lic_related_file(new_lrf.id)

    # deactivate old parti
    parti_lrf_id = request.values.get('parti_lrf_id')
    deact_checker = _deactivate_lrf_by_lrf_id(parti_lrf_id, Alliance)

    # wait for completed
    active_checker()
    deact_checker()

    return redirect(url_for('license-manage.details'))


@blueprint.route('/deactivate-license', methods=['POST'])
def deactivate_license():
    abort_if_not_admin()
    lic_checker = _deactivate_lrf_by_lrf_id(request.values.get('lic_lrf_id'), License)
    parti_checker = None
    if request.values.get('parti_lrf_id'):
        parti_checker = _deactivate_lrf_by_lrf_id(request.values.get('parti_lrf_id'), Alliance)

    lic_checker()
    parti_checker and parti_checker()
    return redirect(url_for('license-manage.details'))


@blueprint.route('/delete-lic-related-file', methods=['POST'])
def delete_lic_related_file():
    abort_if_not_admin()

    # KTODO delete lic alli record ??

    # delete record LicRelatedFile
    lrf_id = request.values.get('lrf_id')
    lr_file = _check_and_find_lic_related_file(lrf_id)
    lr_file.delete()

    # delete file from hard disk
    path = _path_lic_related_file(filename=lr_file.file_name)
    if path.is_file():
        log.info(f'remove file[{path.as_posix()}]')
        os.remove(path)
    else:
        log.debug(f'skip remove -- file not found [{path.as_posix()}] ')

    # make sure removed from db
    ez_dao_utils.wait_unit_id_not_found(LicRelatedFile, lrf_id)

    return redirect(url_for('license-manage.details'))


@blueprint.route('/download-lic-related-file')
def download_lic_related_file():
    abort_if_not_admin()

    lrf_id = request.values.get('lrf_id')
    lr_file = _check_and_find_lic_related_file(lrf_id)

    file_path = _path_lic_related_file(lr_file.file_name)

    # check file exist
    if not file_path.is_file():
        log.warning(f'file not found [{file_path.as_posix()}]')
        abort(404)

    # define mimetype
    _path_str = file_path.as_posix().lower()
    if _path_str.endswith('.xls'):
        mimetype = 'application/vnd.ms-excel'
    elif _path_str.endswith('.xlsx'):
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    else:
        mimetype = 'text/csv'

    return send_file(io.BytesIO(file_path.read_bytes()),
                     as_attachment=True, attachment_filename=lr_file.file_name,
                     mimetype=mimetype)


def _deactivate_lrf_by_lrf_id(lrf_id: str,
                              record_cls: Type[DomainObject], ) -> CompleteChecker:
    lr_file = _check_and_find_lic_related_file(lrf_id)
    lr_file.status = "archived"
    lr_file.save()

    record = object_query_first(record_cls, lr_file.record_id)
    if record is None:
        log.warning(f'record[{lr_file.record_id}]] not found')
    else:
        record.status = 'inactive'
        record.save()

    def _complete_checker():
        _wait_unit_status(lr_file.id, 'archived')

    return _complete_checker


@blueprint.route('/deactivate-participant', methods=['POST'])
def deactivate_participant():
    abort_if_not_admin()

    _deactivate_lrf_by_lrf_id(request.values.get('lrf_id'), Alliance)()

    return redirect(url_for('license-manage.details'))


def _decode_csv_bytes(csv_bytes: bytes) -> str:
    encoding = chardet.detect(csv_bytes)['encoding']
    if encoding == 'ISO-8859-1':
        return csv_bytes.decode(encoding='iso-8859-1', errors='ignore')
    else:
        if encoding != 'utf-8':
            log.warning(f'unknown encoding[{encoding}], decode as utf8')
        return csv_bytes.decode(encoding='utf-8', errors='ignore')


def _extract_name_ezb_id_by_line(line: str) -> tuple[str, str]:
    results = re.findall(r'.+:\s*(.+?)\s*\[(.+?)\]', line)
    if len(results) and len(results[0]) == 2:
        name, ezb_id = results[0]
        return name.strip(), ezb_id.strip()
    else:
        raise ValueError(f'name and ezb_id not found[{line}]')
