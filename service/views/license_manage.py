import csv
import dataclasses
import datetime
import io
import logging
import os
import re
import tempfile
from pathlib import Path

import chardet
import openpyxl
from flask import Blueprint, abort, render_template, request, redirect, url_for
from flask_login.utils import current_user

from octopus.core import app
from service import models
from service.__utils.ez_dao_utils import object_query_first
from service.models import License
from service.models.ezb import LRF_TYPES, LicRelatedFile

blueprint = Blueprint('license-manage', __name__)

log: logging.Logger = app.logger


@dataclasses.dataclass
class LicenseFile:
    ezb_id: str
    name: str
    table_str: str
    filename: str
    version_datetime: datetime.datetime = None

    def __post_init__(self):
        if self.version_datetime is None:
            self.version_datetime = datetime.datetime.now()

    @property
    def versioned_filename(self):
        idx = self.filename.rfind('.')
        if idx == -1:
            name = self.filename
            fmt = ''
        else:
            name = self.filename[:idx]
            fmt = self.filename[idx + 1:]

        date_str = self.version_datetime.strftime('%Y%m%dT%H%M%S')
        return f'{name}.{date_str}.{fmt}'


def abort_if_not_admin():
    # KTODO change it to Decorators
    if not current_user.is_super:
        abort(401)


@blueprint.route('/')
def details():
    abort_if_not_admin()

    lic_related_files = [l.data for l in LicRelatedFile.object_query()]
    active_list = (l for l in lic_related_files if l.get('status') == 'active')
    history_list = (l for l in lic_related_files if l.get('status') != 'active')

    # KTODO handle query participant

    return render_template('license_manage/details.html',
                           allowed_lic_types=LRF_TYPES,
                           active_list=active_list,
                           history_list=history_list,
                           )


def _load_lic_file_by_csv_bytes(file_bytes: bytes, filename: str) -> LicenseFile:
    csv_str = _decode_csv_bytes(file_bytes)

    first_line = csv_str[:csv_str.find('\n')]
    name, ezb_id = _extract_name_ezb_id_by_line(first_line)

    # find header line index
    header_idx = 0
    for _ in range(4):  # header in line 4
        header_idx = csv_str.find('\n', header_idx + 1)
        if header_idx == -1:
            raise ValueError('header index not found')

    table_str = csv_str[header_idx + 1:]
    return LicenseFile(ezb_id, name, table_str, filename=filename)


def _load_lic_file_by_xls_bytes(file_bytes: bytes, filename: str) -> LicenseFile:
    workbook = openpyxl.load_workbook(io.BytesIO(file_bytes))
    sheet = workbook.active

    rows = [[c.value for c in r] for r in sheet.rows]
    headers = rows[4]
    data = rows[5:]

    name, ezb_id = _extract_name_ezb_id_by_line(rows[0][0])

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

    return LicenseFile(ezb_id, name, table_str, filename=filename)


@blueprint.route('/upload-license', methods=['POST'])
def upload_license():
    if request.values.get('lic_type') not in LRF_TYPES:
        abort(400, f'Invalid parameter "lic_type" [{request.values.get("lic_type")}]')

    # request values
    lic_type = request.values['lic_type']
    admin_notes = request.values.get('admin_notes', '')

    abort_if_not_admin()
    if 'file' not in request.files:
        abort(400, 'parameter "file" not found')

    # load csv_rows
    filename = request.files['file'].filename
    file_bytes = request.files['file'].stream.read()
    lic_file = None
    if filename.lower().endswith('.csv'):
        lic_file = _load_lic_file_by_csv_bytes(file_bytes, filename=filename)
    elif any(filename.lower().endswith(fmt) for fmt in ['xls', 'xlsx']):
        lic_file = _load_lic_file_by_xls_bytes(file_bytes, filename=filename)
    else:
        abort(400, f'Invalid file format [{filename}]')

    # save file to hard disk
    lic_related_path = app.config.get('LIC_RELATED_FILE_DIR', '/data/lic_related_file')
    Path(lic_related_path).joinpath(lic_file.versioned_filename).write_bytes(file_bytes)

    # save license to db
    lic = _load_or_create_lic(lic_file.ezb_id)
    lic.set_license_data(lic_file.ezb_id, lic_file.name,
                         type=lic_type, csvfile=lic_file.table_str,
                         init_status='inactive')

    # save lic_related_file to db
    lic_related_file = _create_lic_related_file(lic_file, lic_type,
                                                admin_notes, lic.id)
    lic_related_file.save()

    return redirect('/license-manage/')


@blueprint.route('/active-license', methods=['POST'])
def active_license():
    abort_if_not_admin()

    # active lic_related_file
    lrf_id = request.values.get('lrf_id')
    lic_file = _check_and_find_lic_related_file(lrf_id)
    lic_file.status = 'active'
    lic_file.save()

    # active license
    lic: License = object_query_first(License, lic_file.record_id)
    if lic:
        lic.status = 'active'
        lic.save()
    else:
        log.warning(f'license not found lic_id[{lic_file.record_id}] lrf_id[{lrf_id}]')

    return redirect(url_for('license-manage.details'))


def _check_and_find_lic_related_file(lrf_id: str) -> LicRelatedFile:
    if not lrf_id:
        abort(404)

    lic_file: LicRelatedFile = object_query_first(LicRelatedFile, lrf_id)
    if not lic_file:
        log.warning(f'lic_related_file not found lrf_id[{lrf_id}]')
        abort(404)

    return lic_file


@blueprint.route('/deactivate-license')
def deactivate_license():
    abort_if_not_admin()

    lrf_id = request.values.get('lrf_id')
    lic_file = _check_and_find_lic_related_file(lrf_id)
    # KTODO


@blueprint.route('/deactivate-participant')
def deactivate_participant():
    abort_if_not_admin()
    # KTODO


def _load_or_create_lic(ezb_id: str) -> License:
    lic = None
    if ezb_id:
        lic_list = License.pull_by_key('identifier.id.exact', ezb_id)
        if lic_list and len(lic_list) > 0:
            log.info('Existing license found for #{x}'.format(x=ezb_id))
            lic = lic_list[0]
    if not lic:
        log.info('Adding new license for {x}'.format(x=ezb_id))
        lic = License()
    return lic


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
        raise ValueError(f'first line not found [{line}]')


def _create_lic_related_file(lic_file: LicenseFile, lic_type: str, admin_notes: str,
                             record_id: str) -> models.LicRelatedFile:
    lic_related_file_raw = dict(
        file_name=lic_file.versioned_filename,
        type=lic_type,
        ezb_id=lic_file.ezb_id,
        status='validation passed',
        admin_notes=admin_notes,
        record_id=record_id,
        upload_date=lic_file.version_datetime,
    )
    lic_related_file = models.LicRelatedFile(raw=lic_related_file_raw)
    return lic_related_file


def main3():
    with open('/home/kk/tmp/testing.csv', mode='rb') as f:
        b = f.read()

    lic_file = _load_lic_file_by_csv_bytes(b, 'abc.csv')
    print(lic_file.versioned_filename)


def main4():
    with open('/home/kk/tmp/EZB-NALIW-00493_AL_2019-02-07.xlsx', mode='rb') as f:
        xls_bytes = f.read()
        # w = openpyxl.load_workbook(io.BytesIO(f.read()))

    result = _load_lic_file_by_xls_bytes(xls_bytes)
    print(result)

    # sheet = w.active
    # rows = [[c.value for c in r] for r in sheet.rows]
    # rows = rows[5:]
    # print(rows)


def main5():
    a = License.pull_actives()
    print(a)
    # results = LicRelatedFile.query()
    # print(results)

    # results = LicRelatedFile.object_query()
    # results[0]
    # print(results)


if __name__ == '__main__':
    main5()
