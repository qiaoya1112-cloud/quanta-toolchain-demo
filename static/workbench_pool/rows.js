(function () {
  'use strict';
  function history(item, task) {
    const pretraining = task.id.startsWith('WB-PRETRAINING-');
    const acceptance = task.id === 'WB-PRETRAINING-ACCEPTANCE';
    const entries = [
      {label:'采集', name:item.collector, supplier:item.supplier_id, time:item.collected_at},
      {label:'采集自检', name:item.self_checker || item.self_checker_id, supplier:item.self_checker_supplier_id || item.supplier_id, time:item.self_checked_at},
    ];
    if (acceptance) entries.push({label:'采集质检', name:item.collection_qc_operator || item.collection_qc_operator_id, supplier:item.collection_qc_supplier_id, time:item.collection_qc_at});
    else if (!pretraining) entries.push({label:'采集质检', name:item.result ? item.operators?.['质检人'] || item.operator_ids?.['质检人'] : '', supplier:item.reviewer_supplier_id || item.supplier_id, time:item.reviewed_at});
    return entries;
  }
  const escape = value => String(value).replace(/[&<>"']/g, value => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[value]));
  const details = entries => '<div class="wp-details">' + entries.map(([label, value]) =>
    '<div><span>' + escape(label) + '：</span>' + escape(Array.isArray(value) ? value.join('、') || '--' : value || '--') + '</div>'
  ).join('') + '</div>';
  function render(visible, task, options = {}) {
    const busy = Boolean(options.busy), selected = options.selected || new Set();
    const pretraining = task.id.startsWith('WB-PRETRAINING-');
    const acceptance = task.id === 'WB-PRETRAINING-ACCEPTANCE';
    return visible.length ? visible.map(item => {
      const processing = item.status === 'processing';
      const images = ['头部', '左臂', '右臂'].map(view => '<div class="wp-view"><img src="/static/annotation_workbench/assets/frame.png" alt="' + view + '视角示例帧"><span>' + view + ' · 示例</span></div>').join('');
      const conclusion = value => !value || ['未自检', '未质检'].includes(value) ? '-' : value;
      const conclusionEntries = [['采集自检', conclusion(item.self_check_result)], ['自动化质检', conclusion(item.auto_result)]];
      if (acceptance) conclusionEntries.push(['采集质检', conclusion(item.collection_qc_result)]);
      else if (!pretraining) conclusionEntries.push(['采集质检', conclusion(item.result)]);
      const conclusions = details(conclusionEntries);
      const qualityResult = ['合格','不合格','操作失误'].includes(item.result) ? item.result : '-';
      const qualityClass = {'合格':'pass','操作失误':'mistake','不合格':'fail'}[qualityResult] || '';
      const showQualityNotes = !(task.id === 'WB-PRETRAINING-QC' && !task.return_to_workbench);
      const qualityDetails = '<div class="wp-quality-'+qualityClass+'">'+escape(qualityResult)+'</div>' +
        (showQualityNotes && (item.qc_error_count || item.reason || item.remark) ? '<div class="wp-quality-errors">'+escape(item.qc_error_count || item.reasons?.length || 1)+'条错误</div>' : '');
      const entries = history(item, task);
      const operators = details(entries.map(entry => [entry.label, entry.name ? entry.name + '（' + (entry.supplier ? String(Number(String(entry.supplier).replace(/\D/g, ''))).padStart(2, '0') : '--') + '）' : '--']));
      const operationTimes = details(entries.map(entry => [entry.label, entry.time]));
      const buttons = '<button class="wp-process" data-action="process">处理</button>' + (!acceptance && (pretraining || processing) ? '<button data-action="不合格" class="wp-reject" '+(item.occupied?'disabled':'')+'>不合格</button>' : '');
      return '<tr data-record-id="' + escape(item.id) + '" class="' + (processing ? 'wp-processing' : '') + '">' +
        (task.job_center || task.compact_list ? '' : '<td><input type="checkbox" aria-label="选择 ' + escape(item.id) + '" ' + ((processing || busy) ? 'disabled ' : '') + (selected.has(item.id) ? 'checked ' : '') + '></td>') +
        '<td class="wp-task-id">' + escape(item.task_id) + '</td><td class="wp-data-id"><b>' + escape(item.id) + '</b></td>' +
        '<td class="wp-video-cell"><div class="wp-preview"><div class="wp-instruction"><b>' + escape(item.instruction) + '</b>：<span>' + escape(item.description) + '</span></div><div class="wp-views">' + images + '</div></div></td>' +
        '<td>' + escape(item.device) + '</td>' +
        '<td class="wp-operators">' + operators + '</td><td class="wp-operation-times">' + operationTimes + '</td><td class="wp-conclusions">' + conclusions + '</td>' +
        (task.hide_status ? '' : '<td><span class="wp-status ' + (processing ? 'processing' : '') + '">' + (processing ? '已领取' : '待领取') + '</span></td>') +
        (task.compact_list ? '<td class="wp-quality-result">'+qualityDetails+'</td>' : '') +
        '<td class="wp-action-cell"><div class="wp-row-actions">' + buttons + '</div></td></tr>';
    }).join('') : '<tr><td colspan="' + (10 - Number(Boolean(task.hide_status)) - Number(Boolean(task.job_center || task.compact_list))) + '" class="wp-empty">当前没有匹配的数据</td></tr>';
  }
  window.WorkbenchPoolRows = {render, history};
})();
