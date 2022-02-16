import flask
from bs4 import BeautifulSoup

from octopus.core import app
from octopus.modules.es.testindex import ESTestCase
from service.models import Account


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
        # acc = Account()
        # acc.add_account({
        #     "id": acc_id,
        #     "role": roles,
        #     "email": email,
        #     "api_key": f'{acc_id}.api_key',
        #     "password": password
        # })
        # acc.save()

        client = app.test_client()
        _login_as_admin(client)

        resp: flask.Response = client.get('/license-manage/')

        self.assertEqual(resp.status_code, 200)

    def test_upload_license__normal(self):
        pass
