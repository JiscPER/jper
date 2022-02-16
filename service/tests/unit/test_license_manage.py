import time
from typing import Iterable

import flask
import pkg_resources
from bs4 import BeautifulSoup

from octopus.core import app
from octopus.modules.es.testindex import ESTestCase
from service.__utils import ez_dao_utils, ez_query_maker
from service.models import Account, LicRelatedFile, License


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

        lic_bytes = pkg_resources.resource_stream(
            'service', '/tests/resources/new-EZB-NALIW-00493_AL.csv')

        post_data = {
            'file': lic_bytes,
            'lic_type': 'alliance',
            # request.values.get('lic_type')
        }

        # prepare data for assert
        org_size = LicRelatedFile.count(ez_query_maker.match_all())
        org_detail_page = load_lic_detail_page_helper(client)
        org_lrf_id_list = set(org_detail_page.non_active_lrf_id_list())

        # run
        resp: flask.Response = client.post('/license-manage/upload-license', data=post_data,
                                           follow_redirects=True)

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
