import unittest
import data_platform
import toolchain_demo

class PreannotationQualityFlowTests(unittest.TestCase):
    def setUp(self):
        self.client = toolchain_demo.app.test_client()
        self.flow = next(item for item in data_platform.PIPELINES if item['id'] == 'pl-preannotation-qc')

    def test_automated_graph_has_no_sampling_or_rejection(self):
        nodes, edges, frames = data_platform._processing_canvas_payload(self.flow)
        self.assertEqual([], frames)
        self.assertEqual(['开始', '自动化质检', '采集质检', '采集验收', '完成'], [node['name'] for node in nodes])
        self.assertEqual(4, len(edges))
        by_name = {node['name']: node for node in nodes}
        qc, acceptance = by_name['采集质检'], by_name['采集验收']
        self.assertEqual(100, qc['processingPercent'])
        self.assertEqual(100, acceptance['processingPercent'])
        self.assertEqual(qc['id'], acceptance['inheritProcessingRuleNodeId'])
        self.assertIn({'from': qc['id'], 'to': acceptance['id']}, edges)
        self.assertFalse(acceptance['rejectEnabled'])
        self.assertFalse(any(edge.get('label') or edge.get('branch') for edge in edges))
        self.assertEqual('none', by_name['自动化质检']['processingRuleMode'])
        self.assertEqual('op_post_processing', by_name['自动化质检']['operatorId'])

    def test_manual_flow_is_acceptance_only_full_inspection(self):
        flow = next(item for item in data_platform.PIPELINES if item['id'] == 'pl-preannotation-qc-manual')
        nodes, edges, _ = data_platform._processing_canvas_payload(flow)
        self.assertEqual(['开始', '采集验收', '完成'], [node['name'] for node in nodes])
        self.assertEqual(2, len(edges))
        self.assertEqual(100, nodes[1]['processingPercent'])
        self.assertFalse(nodes[1]['allowTaskPercent'])
        self.assertEqual('审核', nodes[1]['workbenchStatus'])
        self.assertEqual(200, self.client.get('/data/pipelines/pl-preannotation-qc-manual?version=draft').status_code)

    def test_list_and_operator_catalog(self):
        listing = self.client.get('/data/pipelines?stage=质检').get_data(as_text=True)
        for title in ['预训练自动化质检流程', '预训练人工质检流程']:
            self.assertIn('<td><b>' + title + '</b>', listing)
        editor = self.client.get('/data/pipelines/pl-preannotation-qc?version=draft').get_data(as_text=True)
        self.assertIn('data-processing-flow="pl-preannotation-qc"', editor)
        self.assertIn('id="flowEditName" value="预训练自动化质检流程">', editor)
        for name in ['后处理执行算子', '自动化质检算子']:
            self.assertIn(name, editor)
        operators = self.client.get('/data/operators').get_data(as_text=True)
        self.assertIn("openOpDetail('op_automatic_quality_check')", operators)

if __name__ == '__main__': unittest.main()
