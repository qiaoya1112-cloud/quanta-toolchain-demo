import unittest
from unittest.mock import patch

import toolchain_demo


class WorkflowRouteTest(unittest.TestCase):
    def setUp(self):
        self.client = toolchain_demo.app.test_client()

    def test_workflow_serves_built_frontend(self):
        response = self.client.get('/workflow')
        try:
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'id="root"', response.data)
        finally:
            response.close()

    @patch('toolchain_demo.os.path.isfile', return_value=False)
    def test_workflow_explains_missing_build(self, _isfile):
        response = self.client.get('/workflow')
        try:
            self.assertEqual(response.status_code, 503)
            self.assertIn(b'npm run build', response.data)
        finally:
            response.close()


if __name__ == '__main__':
    unittest.main()
