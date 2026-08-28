import re

import toolchain_demo


def test_new_train_drawer_exposes_multi_node_instance_count():
    client = toolchain_demo.app.test_client()
    response = client.get("/model/experiments")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'id="trainInstanceCount"' in html
    assert 'min="1"' in html
    assert 'max="4"' in html
    assert "trainInstanceHint" not in html
    assert "1-4 个实例；大于 1 时按多机方式启动训练" not in html
    assert "validateTrainForm" in html


def test_data_platform_dataset_id_resolves_before_opening_lineage():
    client = toolchain_demo.app.test_client()

    response = client.get("/model/lineage/dataset/ds1")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "未找到匹配的节点" not in html
    assert "clean_whiteboard_v3" in html


def test_dataset_detail_lineage_link_uses_toolchain_dataset_id():
    client = toolchain_demo.app.test_client()

    response = client.get("/model/data/datasets?sel=ds1")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "/model/lineage/dataset/ds_500" in html


def test_dataset_path_detail_resolves_data_platform_id_before_lineage_link():
    client = toolchain_demo.app.test_client()

    response = client.get("/model/data/datasets/ds1")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "clean_whiteboard_v3" in html
    assert "/model/lineage/dataset/ds_500" in html


def test_dataset_lineage_uses_existing_cross_platform_demo_nodes():
    context = toolchain_demo._lineage_context("dataset", "ds1")

    assert context["datasets"][0]["id"] == "ds_500"
    assert {task["id"] for task in context["tasks"]} >= {"11092", "11091", "12088"}
    assert {exp["id"] for exp in context["experiments"]} >= {"exp_7916", "exp_7757"}
    assert {checkpoint["id"] for checkpoint in context["checkpoints"]} >= {"7916", "7757"}
    assert {evaluation["id"] for evaluation in context["evals"]} >= {"t1", "t2"}


def test_lineage_uses_unambiguous_column_names_and_type_filters():
    response = toolchain_demo.app.test_client().get("/model/lineage/dataset/ds1")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert ">数据任务 (" in html
    assert ">评测任务 (" in html
    assert 'lin-type-badge normal' in html
    assert 'lin-type-badge dagger' in html
    assert 'value="test"' in html
    assert 'value="dagger"' in html
    assert 'value="assets"' in html
    assert "TEST任务" not in html


def test_lineage_dimension_picker_is_an_anchor_locator():
    response = toolchain_demo.app.test_client().get("/model/lineage/eval/t6")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '<span class="lin-filter-label">定位节点</span>' in html
    assert '<option value="eval" selected>评测任务</option>' in html
    assert "输入评测任务名称或 ID" in html
    assert toolchain_demo.LINEAGE_CONFIG["eval"]["subtitle"] == "评测任务的 Checkpoint 来源与数据链路"
    assert 'oninput="applyLineageTypeFilters()"' not in html
    assert "不会修改当前血缘图" in html


def test_eval_lineage_card_actions_use_eval_lineage_and_detail_routes():
    response = toolchain_demo.app.test_client().get("/model/lineage/eval/t6")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'data-lineage-kind="assets"' in html
    assert 'href="/model/lineage/eval/t6"' in html
    assert 'href="/model/eval/tasks/t6"' in html


def test_lineage_nodes_expose_filter_metadata_without_changing_card_content():
    response = toolchain_demo.app.test_client().get("/model/lineage/dataset/ds1")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'data-lineage-group="source"' in html
    assert 'data-lineage-kind="normal"' in html
    assert 'data-lineage-kind="dagger"' in html
    assert 'data-lineage-group="eval"' in html
    assert 'data-lineage-kind="test"' in html
    assert 'function applyLineageTypeFilters' in html
    assert "classList.contains('lineage-filtered')" in html
    assert "if (c.classList.contains('lineage-filtered')" in html


def test_lineage_type_cards_have_distinct_visual_tokens():
    response = toolchain_demo.app.test_client().get("/model/lineage/eval/t6")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '[data-lineage-group="source"][data-lineage-kind="normal"]' in html
    assert '[data-lineage-group="source"][data-lineage-kind="dagger"]' in html
    assert '[data-lineage-group="eval"][data-lineage-kind="test"]' in html
    assert '[data-lineage-group="eval"][data-lineage-kind="dagger"]' in html
    assert '[data-lineage-group="eval"][data-lineage-kind="assets"]' in html
    assert "TEST" in html
    assert "Assets" in html
    assert '.lin-node[data-lineage-group="source"][data-lineage-kind="normal"] { border-left:3px solid #149DAA; }' in html
    assert '.lin-node[data-lineage-group="eval"][data-lineage-kind="test"] { border-left:3px solid #2563EB; }' in html
    assert '.lineage-hint .hint-bar.test { background:#2563EB; }' in html


def test_lineage_legend_and_filter_counts_cover_empty_states():
    response = toolchain_demo.app.test_client().get("/model/lineage/dataset/ds1")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "数据任务类型：" not in html
    assert "评测任务类型：" not in html
    assert "上游类型：" not in html
    assert "下游类型：" not in html
    assert 'data-lineage-count="source"' in html
    assert 'data-lineage-count="eval"' in html
    assert 'data-lineage-empty="source"' in html
    assert 'data-lineage-empty="eval"' in html
    assert ".lineage-hint .hint-dot.blue { background:#EFFAFC; border:2px solid #149DAA; }" in html
    assert ".lineage-hint .hint-dot.gray { background:#fff; border:1px solid #DDE5E9; }" in html
    assert "updateLineageFilterState" in html


def test_lineage_exploration_uses_canvas_history_cursor_without_page_return():
    response = toolchain_demo.app.test_client().get("/model/lineage/dataset/ds1")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "返回任务详情" not in html
    assert "&#8249; 返回</a>" not in html
    assert 'class="lineage-page-shell"' in html
    assert "document.body.classList.add('lineage-canvas-page')" in html
    assert 'id="linBackView"' in html
    assert "返回上一个视图" in html
    assert 'id="linForwardView"' in html
    assert "window.history.forward()" in html
    assert html.split('id="linBackView"', 1)[1].split('>', 1)[0].endswith(" disabled")
    assert html.split('id="linForwardView"', 1)[1].split('>', 1)[0].endswith(" disabled")
    assert 'id="linHistoryToggle"' in html
    assert 'id="linHistoryPopover"' in html
    assert 'id="linTrail"' in html
    assert 'id="linClearHistory"' in html
    assert "清除血缘浏览记录" in html
    assert "function linClearHistory()" in html
    assert "navigation.items.length <= 1" in html
    assert "当前节点已设为起始视图" in html
    assert "quanta.lineage.pending.v1" in html
    assert "quanta.lineage.navigation.v1" in html
    assert "lineageTrail" in html
    assert "lineageIndex" in html
    assert "lineageView" in html
    assert "window.history.back()" in html
    assert "window.history.go(delta)" in html
    assert "当前视图" in html
    assert "步后退" in html
    assert "步前进" in html


def test_lineage_canvas_supports_zoom_pan_fit_and_view_restoration():
    response = toolchain_demo.app.test_client().get("/model/lineage/checkpoint/7757")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'id="linViewport"' in html
    assert 'id="linStage"' in html
    assert 'id="linZoomValue"' in html
    assert 'id="linLegendFloat"' in html
    assert 'class="lineage-floating-ui lineage-zoom-dock lineage-floating-group"' in html
    assert ".lineage-legend-float { top:14px; left:14px; }" in html
    assert "浏览历史" in html
    assert "当前浏览器会话" in html
    assert "适应画板" in html
    assert "重置" in html
    assert "pointerdown" in html
    assert "pointermove" in html
    assert "Ctrl + 滚轮缩放" in html
    assert "window.__lineageViewport" in html
    assert "getScale:function()" in html
    assert "restore(savedView.canvas)" in html


def test_dataset_detail_lists_related_training_tasks_by_dataset_ids():
    response = toolchain_demo.app.test_client().get("/model/data/datasets/ds1")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "robotwin_pi05_datamil_stack_blocks_two_top10pct_cotrain" in html
    assert "20260615_pi05_oldft_sortpill_newobs_centercrop_manip2" in html


def test_evaluation_task_detail_exposes_lineage_entry():
    client = toolchain_demo.app.test_client()

    response = client.get("/model/eval/tasks/t6")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "/model/lineage/eval/t6" in html


def test_evaluation_task_list_exposes_lineage_entry():
    response = toolchain_demo.app.test_client().get("/model/eval/tasks")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "/model/lineage/eval/t6" in html


def test_new_evaluation_task_is_available_to_lineage_without_static_mirror():
    evaluation_module = toolchain_demo.ep
    task = {
        "id": "t_dynamic_lineage",
        "task_no": 1099,
        "name": "动态评测任务血缘验证",
        "benchmark_id": "b1",
        "model_ids": ["9001"],
        "status": "未开始",
        "created_at": "2026-08-25",
        "total_sessions": 1,
        "collect_done": 0,
        "eval_done": 0,
    }
    evaluation_module.EVAL_TASKS.append(task)
    try:
        response = toolchain_demo.app.test_client().get("/model/lineage/eval/t_dynamic_lineage")
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "动态评测任务血缘验证" in html
        assert "未找到匹配的节点" not in html
    finally:
        evaluation_module.EVAL_TASKS.remove(task)


def test_new_train_drawer_exposes_priority_and_feishu_notification():
    client = toolchain_demo.app.test_client()
    response = client.get("/model/experiments")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'id="trainPriority"' in html
    assert '<option value="2">2</option>' in html
    assert '<option value="4" selected>4</option>' in html
    assert '<option value="6">6</option>' in html
    assert '<option value="low">低</option>' not in html
    assert 'class="qi" data-tooltip="数值越大，优先级越大"' in html
    assert 'id="trainFeishuNotify"' in html
    assert 'class="qi" data-tooltip="开启通知即可通过飞书通知训练启动、进度和报错信息"' in html
    assert 'class="toggle-sw train-notify-toggle"' in html


def test_recommended_image_mode_uses_selectable_curated_images():
    client = toolchain_demo.app.test_client()
    response = client.get("/model/experiments")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'id="trainRecommendedName"' in html
    assert 'id="trainRecommendedVersion"' in html
    assert 'updateRecommendedImageVersions' in html
    assert "推荐镜像" in html
    assert 'id="trainImageName"' in html
    assert 'id="trainImageVersion"' in html


def test_internal_train_drawer_removes_dualarm_robot_option():
    client = toolchain_demo.app.test_client()
    response = client.get("/model/experiments")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'id="trainBaseSel"' in html
    assert '<option value="dualarm">dualarm</option>' not in html


def test_new_train_drawer_groups_fields_into_interactive_sections():
    client = toolchain_demo.app.test_client()
    response = client.get("/model/experiments")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'id="trainSectionNav"' not in html
    assert 'id="trainSectionMeta"' in html
    assert 'id="trainSectionRuntime"' in html
    assert 'id="trainSectionConfig"' in html
    assert 'id="trainTagPicker"' in html
    assert 'data-path="场景 / 桌面整理 / 收纳"' in html
    assert 'onclick="toggleTrainSection(this)' in html
    assert 'id="drawerNewTrain"' in html


def test_new_train_drawer_exposes_tag_hierarchy_without_footer_status():
    client = toolchain_demo.app.test_client()
    response = client.get("/model/experiments")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'id="trainTagMenu"' in html
    assert 'data-level="一级标签"' in html
    assert 'data-level="二级标签"' in html
    assert 'data-level="三级标签"' in html
    assert 'id="trainSubmitState"' not in html
    assert 'function selectTrainTag' in html
    assert 'function scrollTrainSection' in html


def test_new_train_drawer_matches_benchmark_tag_picker_and_compact_controls():
    client = toolchain_demo.app.test_client()
    response = client.get("/model/experiments")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'class="ts-wrap train-tag-select"' in html
    assert 'class="ts-trigger"' in html
    assert 'class="ts-panel"' in html
    assert 'class="ts-row"' in html
    assert 'class="train-name-control"' in html
    assert 'class="train-name-count" id="nameCount"' in html
    assert 'class="train-copy-path"' not in html
    assert 'id="trainSubmitState"' not in html
    assert 'class="train-section-status"' not in html
    assert '>高级配置<' in html
    assert 'YAML 默认配置 / 参数覆盖' not in html


def test_new_train_drawer_enables_feishu_notification_by_default():
    client = toolchain_demo.app.test_client()
    response = client.get("/model/experiments")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'id="trainFeishuNotify"' in html
    assert 'id="trainFeishuNotify" type="checkbox" checked' in html


def test_train_config_exposes_recommended_and_custom_modes():
    client = toolchain_demo.app.test_client()
    response = client.get("/model/experiments")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'id="trainConfigModeTabs"' in html
    assert 'data-train-config-mode="recommended"' in html
    assert 'data-train-config-mode="custom"' in html
    assert 'id="trainRecommendedConfig"' in html
    assert 'id="trainCustomConfig"' in html
    assert 'id="customYamlEditor"' in html


def test_custom_yaml_mode_exposes_restore_action_only():
    client = toolchain_demo.app.test_client()
    response = client.get("/model/experiments")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'onclick="switchTrainConfigMode(this,\'custom\')"' in html
    assert 'restoreRecommendedYaml()' in html
    custom = html.split('id="trainCustomConfig"', 1)[1].split('id="entryCmdBox"', 1)[0]
    assert '复制全部' not in custom
    assert '格式化' not in custom
    assert '校验' not in custom
    assert 'class="at-reset"' in custom
    assert 'function switchTrainConfigMode' in html
    assert 'function validateCustomYaml' in html


def test_train_drawer_uses_requested_field_rows_and_optional_fields():
    client = toolchain_demo.app.test_client()
    response = client.get("/model/experiments")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    drawer = html.split('<div class="drawer drawer-wide" id="drawerNewTrain">', 1)[1].split('</div>\n    """', 1)[0]
    assert 'class="train-name-control"' in drawer
    assert drawer.count('id="trainNameInput"') == 1
    assert 'class="fg-req">标签' not in drawer
    assert 'id="trainFeishuNotify"' in drawer
    assert 'class="fg-req">训练代码' not in drawer
    assert 'train-runtime-code-row' in drawer
    assert 'train-runtime-queue-row' in drawer
    assert 'train-runtime-priority-row' in drawer


def test_train_drawer_orders_priority_queue_and_count_specification_as_requested():
    html = toolchain_demo.app.test_client().get('/model/experiments').get_data(as_text=True)
    drawer = html.split('<div class="drawer drawer-wide" id="drawerNewTrain">', 1)[1].split('</div>\n    """', 1)[0]
    queue_row_start = drawer.index('class="fg-row train-runtime-queue-row"')
    spec_row_start = drawer.index('class="fg-row train-runtime-priority-row"')
    queue_row = drawer[queue_row_start:spec_row_start]
    assert queue_row.index('优先级') < queue_row.index('训练队列')
    spec_row = drawer[spec_row_start:]
    assert spec_row.index('实例数') < spec_row.index('实例规格')


def test_custom_yaml_keeps_only_restore_recommended_action():
    client = toolchain_demo.app.test_client()
    response = client.get("/model/experiments")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    custom = html.split('id="trainCustomConfig"', 1)[1].split('id="entryCmdBox"', 1)[0]
    assert '恢复推荐配置' in custom
    assert '复制全部' not in custom
    assert '格式化' not in custom
    assert '校验' not in custom
    assert 'class="at-reset"' in custom


def test_dataset_query_creation_modal_uses_validation_state_and_model_progress_route():
    response = toolchain_demo.app.test_client().get('/model/data/query')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '数据集校验中' in html
    assert '数据集核验中' not in html
    assert 'href="/model/data/ds_progress"' in html
    assert '只保存' not in html


def test_dataset_progress_supports_validation_status_and_legacy_redirect():
    client = toolchain_demo.app.test_client()
    response = client.get('/model/data/ds_progress')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '校验中' in html
    assert '进行中' in html
    assert 'data-value="todo"' not in html
    assert '未开始</button>' not in html
    assert 'data-value="verify"' in html
    assert '<h3 id="dpErrorTitle">异常原因</h3>' in html
    assert '数据格式不一致' in html
    assert '格式组 1' in html
    assert '视频文件缺失' in html
    assert 'TaskID' in html
    assert 'RecordingID' in html
    assert '还有 2 个' in html
    assert 'toggleDsErrorIds' in html
    assert 'title="查看异常原因"' in html
    assert '查看失败日志' not in html
    assert '>返回数据查询</a>' in html
    format_failure = html.split('id="dpErrorTemplate80"', 1)[1].split('</template>', 1)[0]
    assert '数据格式不一致' in format_failure
    assert '格式组 2' in format_failure
    assert 'task_11092' in format_failure
    assert 'rec_0012' in format_failure
    assert '视频文件缺失' not in format_failure
    video_failure = html.split('id="dpErrorTemplate79"', 1)[1].split('</template>', 1)[0]
    assert '视频文件缺失' in video_failure
    assert '数据格式不一致' not in video_failure
    legacy = client.get('/ds_progress')
    assert legacy.status_code in (301, 302)
    assert legacy.headers['Location'].endswith('/model/data/ds_progress')


def test_dataset_detail_shows_empty_identifier_when_not_defined():
    response = toolchain_demo.app.test_client().get('/model/data/datasets/ds1')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '<span class="dataset-ident-inline">test1</span>' in html
    assert '标识：' not in html
    assert 'LeRobot' in html
    assert '数据集标识</span>' not in html


def test_image_management_page_and_recommended_image_options_share_catalog():
    client = toolchain_demo.app.test_client()
    config = client.get('/model/config/images')
    assert config.status_code == 200
    config_html = config.get_data(as_text=True)
    assert '镜像名称' in config_html
    assert '版本' in config_html
    assert '描述信息' in config_html
    assert '创建人' in config_html
    assert '创建时间' in config_html
    assert '更新时间' not in config_html
    assert '删除' in config_html
    experiments = client.get('/model/experiments')
    html = experiments.get_data(as_text=True)
    assert 'id="trainRecommendedImage"' in html
    assert 'data-image-path=' in html
    assert 'id="trainImagePath"' in html


def test_train_detail_basic_info_contains_drawer_fields_and_id_column():
    client = toolchain_demo.app.test_client()
    list_html = client.get('/model/experiments').get_data(as_text=True)
    assert '<th>ID</th>' in list_html
    assert 'class="mono muted">9001</td>' in list_html
    assert 'class="mono muted">DEMO_EXP_9001</td>' not in list_html
    detail_html = client.get('/model/experiments/DEMO_EXP_9001').get_data(as_text=True)
    assert '飞书通知' in detail_html
    assert '优先级' in detail_html
    assert '实例数' in detail_html
    assert '配置模式' in detail_html
    assert 'bi-sec-title">任务信息<' in detail_html
    assert 'bi-sec-title">运行配置<' in detail_html
    assert 'bi-sec-title">训练配置<' in detail_html
    assert 'bi-submodule-title' not in detail_html.split('id="det-pane-basic"', 1)[1]


def test_train_list_shows_edit_in_more_menu_only_for_queued_tasks():
    html = toolchain_demo.app.test_client().get('/model/experiments').get_data(as_text=True)
    queued_row = re.search(r'<tr>\s*<td class="mono muted">9005</td>.*?</tr>', html, re.S)
    done_row = re.search(r'<tr>\s*<td class="mono muted">9001</td>.*?</tr>', html, re.S)

    assert queued_row and done_row
    queued_actions = queued_row.group(0).split('class="actions-cell"', 1)[1]
    done_actions = done_row.group(0).split('class="actions-cell"', 1)[1]
    queued_menu = re.search(r'<span class="action-menu">(.*?)</span>\s*</span>', queued_actions, re.S)
    assert queued_menu
    assert 'class="action-edit"' in queued_menu.group(1)
    assert 'class="action-edit"' not in queued_actions.split('<span class="action-more">', 1)[0]
    assert 'class="action-edit"' not in done_actions
    assert queued_actions.index('复制') < queued_actions.index('更多')


def test_train_detail_basic_info_uses_the_same_three_primary_sections_as_drawer():
    html = toolchain_demo.app.test_client().get('/model/experiments/DEMO_EXP_9001').get_data(as_text=True)
    basic = html.split('id="det-pane-basic"', 1)[1]
    task_section = basic.split('bi-sec-title">任务信息<', 1)[1].split('bi-sec-title">运行配置<', 1)[0]
    runtime_section = basic.split('bi-sec-title">运行配置<', 1)[1].split('bi-sec-title">训练配置<', 1)[0]
    assert basic.count('class="bi-sec"') == 3
    assert basic.count('class="bi-sec-title"') == 3
    assert 'bi-sec-title">任务信息<' in basic
    assert 'bi-sec-title">运行配置<' in basic
    assert 'bi-sec-title">训练配置<' in basic
    assert 'bi-submodule-title' not in basic
    assert '任务 ID' not in task_section
    assert '镜像模式' in runtime_section
    assert '推荐镜像' in runtime_section
    assert '<span class="lbl">任务 ID:</span>' in html


def test_lineage_filter_uses_renamed_dimensions_and_secondary_search():
    html = toolchain_demo.app.test_client().get('/model/lineage/dataset/ds1').get_data(as_text=True)
    assert '>数据任务<' in html
    assert '>评测任务<' in html
    assert 'Normal' in html
    assert 'TEST' in html
    assert 'lineageSourceSearch' not in html
    assert 'lineageEvalSearch' not in html
    assert 'optgroup' in html
    assert 'value="task:normal"' in html
    assert 'value="task:dagger"' in html
    assert 'value="eval:test"' in html
    assert 'value="eval:dagger"' in html
    assert 'value="eval:assets"' in html
    assert 'class="lineage-type-filters"' not in html
    assert 'lineageSecondaryPanel' not in html


def test_lineage_dimension_picker_uses_cascader_style_single_select_menu():
    html = toolchain_demo.app.test_client().get('/model/lineage/dataset/ds1').get_data(as_text=True)
    picker = html.split('id="linDimensionPicker"', 1)[1].split('</div>', 1)[0]
    assert 'class="lin-dimension-picker"' in html
    assert 'id="linDimensionMenu"' in html
    assert 'id="linDimensionSecondary"' in html
    assert 'data-dimension="task"' in html
    assert 'data-dimension="eval"' in html
    assert 'data-value="task:normal"' in html
    assert 'data-value="task:dagger"' in html
    assert 'data-value="eval:test"' in html
    assert 'data-value="eval:dagger"' in html
    assert 'data-value="eval:assets"' in html
    assert 'type="checkbox"' not in picker
    assert 'lin-native-dimension' in html


def test_lineage_dimension_picker_omits_all_type_secondary_options():
    html = toolchain_demo.app.test_client().get('/model/lineage/dataset/ds1').get_data(as_text=True)
    assert '全部数据任务' not in html
    assert '全部评测任务' not in html
    assert 'data-value="task:normal"' in html
    assert 'data-value="task:dagger"' in html
    assert 'data-value="eval:test"' in html
    assert 'data-value="eval:dagger"' in html
    assert 'data-value="eval:assets"' in html


def test_lineage_cards_use_requested_metadata_and_hide_checkpoint_history():
    html = toolchain_demo.app.test_client().get('/model/lineage/dataset/ds1').get_data(as_text=True)
    assert '标识' in html
    assert 'Step ' in html
    assert '查看历史版本' not in html
    assert 'target="_blank"' in html
    assert 'lin-type-badge normal' in html
    assert 'lin-type-badge assets' in html
    assert '>上游数据任务<' not in html
    assert '>下游评测任务<' not in html


def test_lineage_task_type_is_a_horizontal_badge_above_the_card_name():
    html = toolchain_demo.app.test_client().get('/model/lineage/dataset/ds1').get_data(as_text=True)
    assert '<span class="lin-type-badge normal">NORMAL</span><div class="ln-ttl"' in html
    assert '<span class="lin-type-badge dagger">DAGGER</span><div class="ln-ttl"' in html
    assert '<span class="lin-type-badge test">TEST</span><div class="ln-ttl"' in html
    assert '<span class="lin-type-badge assets">ASSETS</span><div class="ln-ttl"' in html
    assert 'lin-type-label' not in html
    assert 'writing-mode:vertical-rl' not in html
    assert 'class="ln-ttl" title=' in html


def test_lineage_legend_hides_task_type_backup_sections():
    html = toolchain_demo.app.test_client().get('/model/lineage/dataset/ds1').get_data(as_text=True)
    legend = html.split('<div class="lineage-hint">', 1)[1].split('</div>', 1)[0]
    assert '节点状态：' in legend
    assert '数据任务类型：' not in legend
    assert '评测任务类型：' not in legend
