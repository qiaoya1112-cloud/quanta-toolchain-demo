// Model Platform Navigation - Based on toolchain_demo.py PLATFORMS["model"]["nav"]

export const MODEL_NAV = [
  {
    groupTitle: '概览',
    items: [
      { path: '/model', label: '快速入门', badge: '演示' },
    ],
  },
  {
    groupTitle: '数据',
    items: [
      { path: '/model/data/query', label: '数据查询', badge: '优化' },
      { path: '/model/data/datasets', label: '数据集', badge: '优化' },
      { path: '/model/data/raw', label: '原始数据', badge: '演示' },
    ],
  },
  {
    groupTitle: '训练',
    items: [
      { path: '/model/experiments', label: '训练任务', badge: '优化' },
      { path: '/model/checkpoints', label: 'Checkpoint', badge: '优化' },
      { path: '/model/deploy', label: '部署任务', badge: '演示' },
    ],
  },
  {
    groupTitle: '评测',
    items: [
      { path: '/model/eval', label: '评测任务', badge: '特定' },
      { path: '/model/eval/eval-records', label: '评测结果', badge: '特定' },
      { path: '/model/eval/leaderboard', label: '工作台', badge: '特定' },
    ],
  },
  {
    groupTitle: '具身评测',
    items: [
      { path: '/model/embodied-eval/prompts', label: '模型问库', badge: '演示' },
      { path: '/model/embodied-eval/metrics', label: 'Metric 模板', badge: '演示' },
      { path: '/model/embodied-eval/sets', label: '评测集', badge: '演示' },
    ],
  },
];

export const THEME = {
  primaryColor: '#149DAA',
  sidebarBg: '#001529', // Ant Design 默认深色侧边栏背景
  contentBg: '#f5f7fa',
};
