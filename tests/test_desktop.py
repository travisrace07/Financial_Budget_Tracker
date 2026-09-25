import io
from pathlib import Path
import tempfile
import unittest

try:
    from desktop import DesktopServer
except ModuleNotFoundError as error:
    if error.name != 'platformdirs':
        raise
    raise unittest.SkipTest('Install requirements-desktop.txt to test desktop packaging')


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.server = DesktopServer(self.directory.name)
        self.client = self.server.app.test_client()
        self.url = self.server.base_url

    def tearDown(self):
        self.server.close()
        self.directory.cleanup()

    def login(self):
        response = self.client.get(self.server.launch_url, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Financial overview', response.data)

    def test_access_and_assets(self):
        self.assertEqual(self.client.get(self.url + '/api/dashboard').status_code, 403)
        self.assertEqual(self.client.get(self.url + '/desktop-launch/wrong').status_code, 403)
        self.login()
        with self.client.get(self.url + '/static/app.js') as response:
            self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(self.url + '/api/dashboard',
                         headers={'Host': 'evil.example'}).status_code, 403)
        self.assertEqual(self.client.put(self.url + '/api/budgets', json={},
                         headers={'Origin': 'https://evil.example'}).status_code, 403)

    def test_data_survives_restart_and_session_does_not(self):
        self.login()
        response = self.client.post(self.url + '/api/import', data={'file':
            (io.BytesIO(b'date,description,amount\n2026-09-01,Payroll,3000\n'), 'bank.csv')})
        self.assertEqual(response.json['imported'], 1)
        response = self.client.put(self.url + '/api/budgets', json={
            'month': '2026-09', 'category': 'Dining', 'amount': 100})
        self.assertEqual(response.status_code, 200)
        old_token = self.server.token
        self.server.close()
        self.server = DesktopServer(self.directory.name)
        self.client = self.server.app.test_client()
        self.url = self.server.base_url
        self.assertEqual(self.client.get(self.url + '/desktop-launch/' + old_token).status_code, 403)
        self.login()
        data = self.client.get(self.url + '/api/dashboard?month=2026-09').json
        self.assertEqual(data['income'], 3000)
        self.assertEqual(data['budgets'][0]['amount'], 100)
        self.assertTrue((Path(self.directory.name) / 'ledger.sqlite3').is_file())


if __name__ == '__main__':
    unittest.main()
