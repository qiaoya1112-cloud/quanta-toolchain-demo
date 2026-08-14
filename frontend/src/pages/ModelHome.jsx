import React from 'react';
import { Card } from 'antd';

const ModelHome = () => {
  return (
    <div>
      <Card
        style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          border: 'none',
          borderRadius: '12px',
          marginBottom: '24px',
        }}
      >
        <div style={{ color: '#fff' }}>
          <h1 style={{ fontSize: '32px', fontWeight: 700, marginBottom: '16px', color: '#fff' }}>
            欢迎来到模型平台
          </h1>
          <p style={{ fontSize: '16px', lineHeight: '1.6', opacity: 0.95, marginBottom: 0 }}>
            数据 → 训练 → 部署 → 评测，模型平台承载数据 → 训练 → 部署 → 评测的端到端流水线。
            挂载数据集、用 GPU 资源池训练、离线 Benchmark 评测后下发到设备平台。
          </p>
        </div>
      </Card>

      <div style={{ marginTop: '24px', color: '#666', lineHeight: '1.8' }}>
        <h3 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '12px', color: '#262626' }}>
          平台功能
        </h3>
        <ul style={{ paddingLeft: '20px' }}>
          <li>数据管理：数据查询、数据集管理、原始数据访问</li>
          <li>训练管理：训练任务创建、Checkpoint 管理、模型部署</li>
          <li>评测中心：评测任务管理、评测结果查看、排行榜</li>
          <li>具身评测：模型问库、Metric 模板、评测集配置</li>
        </ul>
      </div>
    </div>
  );
};

export default ModelHome;
