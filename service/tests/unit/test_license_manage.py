import io
import time
from typing import Iterable, Callable, Optional

import flask
import pkg_resources
from bs4 import BeautifulSoup
from flask import Response

from octopus.core import app
from octopus.modules.es.testindex import ESTestCase
from service.__utils import ez_dao_utils, ez_query_maker
from service.models import Account, LicRelatedFile, License
from service.views import license_manage

PATH_LIC_A = '/tests/resources/new-EZB-NALIW-00493_AL.csv'
PATH_PARTI_A = '/tests/resources/EZB-NALIW-00493_OA_participants_current.csv'


def _is_incorrect_login(resp: flask.Response) -> bool:
    soup = BeautifulSoup(resp.data, 'html.parser')
    return any('Incorrect username/password' in ele.text
               for ele in soup.select('article'))


def _login(client, username, password) -> flask.Response:
    resp = client.post('/account/login',
                       data={'username': username,
                             'password': password})
    return resp


def _login_as_admin(client):
    resp = _login(client, 'green@deepgreen.org', 'admin')
    if _is_incorrect_login(resp):
        raise Exception("Unexpected login fail")


def do_upload_lic(client,
                  file_path: str,
                  lic_type: str = 'alliance',
                  follow_redirects=False):
    file_bytes: io.BufferedReader = pkg_resources.resource_stream('service', file_path)
    lic_bytes = io.BytesIO(file_bytes.read())
    lic_bytes.name = file_bytes.name.split('/')[-1]
    post_data = {
        'file': lic_bytes,
        'lic_type': lic_type,
    }

    # run
    resp: flask.Response = client.post('/license-manage/upload-license', data=post_data,
                                       follow_redirects=follow_redirects)
    return resp


class LicDetailPageHelper:
    def __init__(self, html):
        self.soup = BeautifulSoup(html, 'lxml')

    def active_history_table(self) -> tuple:
        table_ele_list = self.soup.select('table')
        active_tbl, history_tbl = table_ele_list
        return active_tbl, history_tbl

    def active_tbl(self):
        return self.active_history_table()[0]

    def history_tbl(self):
        return self.active_history_table()[1]

    def cnt_table_row(self, soup):
        return len(soup.select('tr')) - 1  # -1 for not include header

    def n_active_row(self):
        active_tbl, _ = self.active_history_table()
        return self.cnt_table_row(active_tbl)

    def n_history_row(self):
        _, history_tbl = self.active_history_table()
        return self.cnt_table_row(history_tbl)

    def non_active_lrf_id_list(self) -> Iterable[str]:
        lrf_id_list = (i.get('value') for i in self.history_tbl().select('input[type=hidden][name=lrf_id]'))
        lrf_id_list = filter(None, lrf_id_list)
        return lrf_id_list


def load_lic_detail_page_helper(client) -> LicDetailPageHelper:
    resp: flask.Response = client.get('/license-manage/')
    return LicDetailPageHelper(resp.data)


class TestLicenseManage(ESTestCase):
    def setUp(self):
        self.run_schedule = app.config.get("RUN_SCHEDULE")
        app.config["RUN_SCHEDULE"] = False

        from service import web  # setup blueprint
        web  # avoid pycharm auto cleanup the import

        super(TestLicenseManage, self).setUp()

    def tearDown(self):
        super(TestLicenseManage, self).tearDown()
        app.config["RUN_SCHEDULE"] = self.run_schedule

    def test_details__normal(self):
        client = app.test_client()
        _login_as_admin(client)

        resp: flask.Response = client.get('/license-manage/')

        self.assertEqual(resp.status_code, 200)
        soup = BeautifulSoup(resp.data, 'lxml')

        h2_text_list = [e.text for e in soup.select('h2')]
        for t in ['Upload License', 'Current License Files', 'History']:
            self.assertIn(t, h2_text_list)

        table_ele_list = soup.select('table')
        self.assertEqual(len(table_ele_list), 2)

        active_tbl, history_tbl = table_ele_list

        self.assertGreater(len(active_tbl.select('tr')), 0)
        self.assertGreater(len(history_tbl.select('tr')), 0)

    def test_details__not_admin(self):
        client = app.test_client()

        acc = Account()
        acc_id = str(time.time())
        acc.add_account({
            "id": acc_id,
            "role": ['publisher'],
            "email": f'{acc_id}@abc.com',
            "api_key": f'{acc_id}.api_key',
            "password": 'password',
        })
        acc.save()
        ez_dao_utils.wait_unit_id_found(Account, acc_id)

        resp = _login(client, acc.email, 'password')
        if _is_incorrect_login(resp):
            raise Exception("Unexpected login fail")

        resp: flask.Response = client.get('/license-manage/')

        self.assertEqual(resp.status_code, 401)

    def test_upload_license__normal(self):
        client = app.test_client()
        _login_as_admin(client)

        # prepare data for assert
        org_size = LicRelatedFile.count(ez_query_maker.match_all())
        org_detail_page = load_lic_detail_page_helper(client)
        org_lrf_id_list = set(org_detail_page.non_active_lrf_id_list())

        # run
        resp: flask.Response = do_upload_lic(client, PATH_LIC_A,
                                             lic_type='alliance', follow_redirects=True)

        # assert
        new_size = LicRelatedFile.count(ez_query_maker.match_all())
        self.assertGreater(new_size, org_size)

        detail_page = LicDetailPageHelper(resp.data)
        self.assertEqual(detail_page.n_active_row(), org_detail_page.n_active_row())
        self.assertGreater(detail_page.n_history_row(), org_detail_page.n_history_row())

        new_lrf_id_list = set(detail_page.non_active_lrf_id_list())
        diff_lrf_id_list = new_lrf_id_list - org_lrf_id_list
        self.assertEqual(len(diff_lrf_id_list), 1)

        # assert LicRelatedFile
        new_lrf_id = next(iter(diff_lrf_id_list))
        lrf: LicRelatedFile = ez_dao_utils.pull_by_id(LicRelatedFile, new_lrf_id)
        self.assertIsNotNone(lrf)
        self.assertTrue(lrf.is_license())
        self.assertEqual(lrf.status, "validation passed")
        self.assertFalse(lrf.is_active())

        # assert License
        ez_dao_utils.wait_unit_id_found(License, lrf.record_id)
        lic: License = ez_dao_utils.pull_by_id(License, lrf.record_id)
        self.assertFalse(lic.is_active())
        self.assertGreater(len(lic.identifiers), 0)
        self.assertEqual(lrf.ezb_id, lic.get_first_ezb_id())

        # check file saved to hard disk
        # print(lrf.file_name)
        self.assertTrue(license_manage.
                        _path_lic_related_file(lrf.file_name)
                        .is_file())

        # clean table
        lic.delete()
        lrf.delete()

    def test_upload_license__invalid_lic_file(self):
        client = app.test_client()
        _login_as_admin(client)

        # prepare data for assert
        org_detail_page = load_lic_detail_page_helper(client)

        lrf_finder = create_new_lrf_finder()

        # run
        resp: flask.Response = do_upload_lic(client, PATH_PARTI_A,
                                             lic_type='alliance', follow_redirects=True)
        self.assertEqual(resp.status_code, 400)

        time.sleep(3)  # wait for lrf saved
        new_detail_page = load_lic_detail_page_helper(client)

        # assert new history rows
        self.assertGreater(new_detail_page.n_history_row(),
                           org_detail_page.n_history_row())

        # assert lrf
        lrf = lrf_finder()
        self.assertIsNotNone(lrf)
        self.assertEqual(lrf.status, 'validation failed')
        self.assertIsNotNone(lrf.data.get('validation_notes'))

    def test_upload_license__duplicate_upload(self):  # KTODO
        client = app.test_client()
        _login_as_admin(client)

        lrf_finder = create_new_lrf_finder()
        resp: flask.Response = do_upload_lic(client, PATH_PARTI_A,
                                             lic_type='alliance', follow_redirects=False)
        lrf = lrf_finder()

    def test_active_lic_related_file__normal(self):
        client = app.test_client()
        _login_as_admin(client)

        # prepare upload / validation passed record
        new_lrf_finder = create_new_lrf_finder()
        resp: flask.Response = do_upload_lic(client, PATH_LIC_A,
                                             lic_type='alliance', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        new_lrf = new_lrf_finder()
        self.assertIsNotNone(new_lrf)

        # prepare data before run

        # deactivate all lrf
        for checker in [license_manage._deactivate_lrf_by_lrf_id(lrf.id, License) for lrf in
                        LicRelatedFile.pull_all_by_status('active')]:
            checker()

        org_detail_page = LicDetailPageHelper(resp.data)
        incorrect_id_list = {l.id for l in License.pull_all_by_status_ezb_id('active', new_lrf.ezb_id)}

        # run
        resp: Response = client.post('/license-manage/active-lic-related-file',
                                     data={'lrf_id': new_lrf.id, },
                                     follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # assert new active lrf record in table
        new_detail_page = LicDetailPageHelper(resp.data)
        self.assertGreater(new_detail_page.n_active_row(),
                           org_detail_page.n_active_row(), )

        self.assertTrue(new_lrf.is_license())

        # only one active record for each ezb_id
        time.sleep(2)  # wait for License.save()
        active_lic_id_list = {l.id for l in License.pull_all_by_status_ezb_id('active', new_lrf.ezb_id)}
        active_lic_id_list = active_lic_id_list - incorrect_id_list
        self.assertEqual(len(list(active_lic_id_list)), 1)

        # cleanup
        new_lrf.delete()
        ez_dao_utils.pull_by_id(License, new_lrf.record_id).delete()

    def test_active_lic_related_file__auto_deactivate(self):  # KTODO
        pass

    def test_update_license__difference_ezb_id(self):  # KTODO
        pass


def create_new_lrf_finder() -> Callable[[], Optional[LicRelatedFile]]:
    size = 1000
    org_lrf_id_list = {lrf.id for lrf in ez_dao_utils.query_objs(LicRelatedFile, ez_query_maker.match_all(size=size))}

    def _fn():
        new_lrf_list = ez_dao_utils.query_objs(LicRelatedFile, ez_query_maker.match_all(size=size))
        diff_lrf_list = [lrf for lrf in new_lrf_list if lrf.id not in org_lrf_id_list]
        return diff_lrf_list[0] if diff_lrf_list else None

    return _fn


def pull_all_by_status(status):
    query = {
        "query": {
            "match": {
                "status": status
            }
        }
    }
    results = ez_dao_utils.query_objs(LicRelatedFile, query)
    return results
