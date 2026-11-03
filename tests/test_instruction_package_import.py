import io
import unittest

from flask import Flask
from openpyxl import Workbook

from batch_packages import register_batch_packages


class BatchPackageImportTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        register_batch_packages(app)
        self.client = app.test_client()

    def upload(self, rows, filename='packages.xlsx'):
        workbook = Workbook()
        for row in rows:
            workbook.active.append(row)
        stream = io.BytesIO()
        workbook.save(stream)
        stream.seek(0)
        return self.client.post('/data/instruction-packages/batch-parse', data={'file': (stream, filename)})

    def test_preserves_group_ids_versions_and_source_rows(self):
        response = self.upload([
            ['指令包序号', '指令 ID', '指令版本', '指令包名称'],
            ['001', '100021', 'V3', '厨房餐具'],
            [None, None, None, None],
            ['001', '100036', None, '厨房餐具'],
        ])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['rows'], [
            {'line': 2, '指令包序号': '001', '指令ID': '100021', '指令版本': 'V3', '指令包名称': '厨房餐具'},
            {'line': 4, '指令包序号': '001', '指令ID': '100036', '指令版本': '', '指令包名称': '厨房餐具'},
        ])

    def test_rejects_missing_headers_duplicate_headers_and_empty_data(self):
        for rows in ([['指令 ID'], ['100021']], [['指令包序号', '指令ID', '指令ID']], [['指令包序号', '指令ID']]):
            with self.subTest(rows=rows):
                response = self.upload(rows)
                self.assertEqual(response.status_code, 400)
                self.assertIn('error', response.json)

    def test_rejects_wrong_format_and_corrupted_workbook(self):
        self.assertEqual(self.upload([['a']], 'packages.csv').status_code, 400)
        response = self.client.post('/data/instruction-packages/batch-parse', data={'file': (io.BytesIO(b'corrupted'), 'bad.xlsx')})
        self.assertEqual(response.status_code, 400)
        self.assertIn('无法读取', response.json['error'])


if __name__ == '__main__':
    unittest.main()
