"""Behavior checks for the in-memory data lake selection prototype."""

import json
import unittest

import data_platform
import toolchain_demo


class QueryCircleTests(unittest.TestCase):
    def setUp(self):
        self.client = toolchain_demo.app.test_client()

    def test_initial_state_matches_selection_flow(self):
        page = self.client.get("/model/data/query").get_data(as_text=True)
        self.assertIn("提示词", page)
        self.assertIn("执行圈选", page)
        self.assertIn("圈选结果", page)
        self.assertIn("暂无数据", page)
        self.assertNotIn("执行圈选成功后在此预览", page)
        self.assertIn('<a href="/model/data/ds_progress" class="btn">查看数据集创建进度</a>', page)
        self.assertIn('<button class="btn" onclick="openBuildDsDrawer()">用圈选结果创建数据集</button>', page)
        self.assertIn('<input type="text" name="hl" value="" placeholder="输入 prompt">', page)
        self.assertIn('<input type="text" name="ll" value="" placeholder="输入 prompt">', page)
        self.assertNotIn('name="hl" value="p', page)
        self.assertNotIn('name="ll" value="p', page)
        self.assertIn('placeholder="开始时间"', page)
        self.assertIn('placeholder="结束时间"', page)
        self.assertIn('placeholder="请选择操作员"', page)
        self.assertIn('<option value="en" selected>英文</option><option value="zh">中文</option><option value="">全部</option>', page)
        self.assertIn('<div class="q-mode-tabs" hidden style="display:none" aria-hidden="true">', page)
        self.assertIn('id="qModeFilter"', page)
        self.assertIn('id="qModeSql" style="display:none;"', page)
        self.assertIn("group.op=group.op==='or'?'and':'or';qRenderConditions();", page)
        self.assertIn("q-condition-toggle", page)

    def test_selection_dataset_form_keeps_only_requested_fields(self):
        page = self.client.get("/model/data/query").get_data(as_text=True)
        drawer = page.split('id="buildDsDrawer"', 1)[1].split('<script>', 1)[0]
        for label in ("标识", "数据集名称", "选择目录", "标签"):
            self.assertIn(label, drawer)
        self.assertNotIn("生成格式", drawer)
        self.assertNotIn("可见范围", drawer)
        self.assertNotIn("用户组", drawer)
        self.assertIn("请选择目录（可选）", drawer)
        self.assertNotIn('id="buildDsIncludeInvalid"', drawer)
        self.assertNotIn("纳入质检不合格视频", drawer)

    def test_nested_or_conditions_filter_actual_recordings(self):
        tree = {"op": "and", "children": [
            {"op": "or", "children": [
                {"field": "recording_id", "operator": "=", "value": "120489"},
                {"field": "recording_id", "operator": "=", "value": "121005"},
            ]},
            {"field": "recording_length", "operator": ">", "value": "1200"},
        ]}
        page = self.client.get("/model/data/query", query_string={"run": "1", "advanced": json.dumps(tree)}).get_data(as_text=True)
        self.assertIn("共 1 条", page)
        self.assertIn("<td>120489</td>", page)
        self.assertNotIn("<td>121005</td>", page)
        self.assertIn("用圈选结果创建数据集", page)

    def test_between_and_empty_operators(self):
        recording = data_platform.RECORDINGS[0]
        self.assertTrue(data_platform.query_matches_condition(recording, {
            "field": "recording_length", "operator": "介于", "value": "1400,1500"}))
        self.assertTrue(data_platform.query_matches_condition(recording, {
            "field": "recording_dagger_type", "operator": "为空"}))
        self.assertFalse(data_platform.query_matches_condition(recording, {
            "field": "recording_dagger_type", "operator": "不为空"}))

    def test_prompt_keywords_match_each_level_and_language(self):
        cases = [
            ({"hl": "WHITEBOARD"}, "120489", "121005"),
            ({"hl": "整理桌面"}, "121005", "120489"),
            ({"ll": "RED CANDY"}, "121005", "120489"),
            ({"ll": "浇水壶"}, "121131", "121005"),
            ({"hl": "TIDY", "ll": "red candy"}, "121005", "120489"),
        ]
        for filters, expected, excluded in cases:
            with self.subTest(filters=filters):
                page = self.client.get("/model/data/query", query_string={"run": "1", **filters}).get_data(as_text=True)
                self.assertIn(f"<td>{expected}</td>", page)
                self.assertNotIn(f"<td>{excluded}</td>", page)

    def test_prompt_fields_preserve_independent_values_and_show_empty_result(self):
        pending = self.client.get("/model/data/query", query_string={
            "hl": "Tidy", "ll": "red candy"
        }).get_data(as_text=True)
        self.assertIn("暂无数据", pending)
        self.assertNotIn("<td>121005</td>", pending)

        page = self.client.get("/model/data/query", query_string={
            "run": "1", "hl": "Tidy", "ll": "watering can"
        }).get_data(as_text=True)
        self.assertIn('<input type="text" name="hl" value="Tidy" placeholder="输入 prompt">', page)
        self.assertIn('<input type="text" name="ll" value="watering can" placeholder="输入 prompt">', page)
        self.assertIn("共 0 条", page)
        self.assertIn("未找到符合条件的 episode", page)
        self.assertNotIn("<td>121005</td>", page)

        page = self.client.get("/model/data/query", query_string={
            "run": "1", "hl": "Tidy", "ll": ""
        }).get_data(as_text=True)
        self.assertIn('<input type="text" name="hl" value="Tidy" placeholder="输入 prompt">', page)
        self.assertIn('<input type="text" name="ll" value="" placeholder="输入 prompt">', page)
        self.assertIn("<td>121005</td>", page)

    def test_prompt_filters_combine_with_existing_conditions(self):
        page = self.client.get("/model/data/query", query_string={
            "run": "1", "hl": "Tidy", "task": "t1"
        }).get_data(as_text=True)
        self.assertIn("共 0 条", page)
        self.assertNotIn("<td>121005</td>", page)

    def test_creation_progress_exposes_filters_and_validation_reasons(self):
        page = self.client.get("/model/data/ds_progress").get_data(as_text=True)
        self.assertIn("<th>标识</th>", page)
        self.assertIn('id="dpNameFilter"', page)
        self.assertIn("function dpApplyFilters", page)
        self.assertIn("function dpResetFilters", page)
        self.assertIn("Feature 不一致（数据格式不一致）", page)
        self.assertIn("视频文件缺失", page)
        self.assertIn("还有 2 个", page)
        self.assertIn("查看异常原因", page)
        self.assertIn("查看数据集", page)


if __name__ == "__main__":
    unittest.main()
