import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import ModelLayout from './layouts/ModelLayout';
import ModelHome from './pages/ModelHome';
import PlaceholderPage from './components/PlaceholderPage';
import { THEME } from './config/modelNav';

const App = () => {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: THEME.primaryColor,
          borderRadius: 6,
        },
      }}
    >
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<ModelLayout />}>
            {/* Default redirect to model home */}
            <Route index element={<Navigate to="/model" replace />} />

            {/* 概览 */}
            <Route path="/model" element={<ModelHome />} />

            {/* 数据 */}
            <Route path="/model/data/query" element={<PlaceholderPage title="数据查询" />} />
            <Route path="/model/data/datasets" element={<PlaceholderPage title="数据集" />} />
            <Route path="/model/data/raw" element={<PlaceholderPage title="原始数据" />} />

            {/* 训练 */}
            <Route path="/model/experiments" element={<PlaceholderPage title="训练任务" />} />
            <Route path="/model/checkpoints" element={<PlaceholderPage title="Checkpoint" />} />
            <Route path="/model/deploy" element={<PlaceholderPage title="部署任务" />} />

            {/* 评测 */}
            <Route path="/model/eval" element={<PlaceholderPage title="评测任务" description="评测任务管理功能开发中" />} />
            <Route path="/model/eval/eval-records" element={<PlaceholderPage title="评测结果" />} />
            <Route path="/model/eval/leaderboard" element={<PlaceholderPage title="工作台" />} />

            {/* 具身评测 */}
            <Route path="/model/embodied-eval/prompts" element={<PlaceholderPage title="模型问库" />} />
            <Route path="/model/embodied-eval/metrics" element={<PlaceholderPage title="Metric 模板" />} />
            <Route path="/model/embodied-eval/sets" element={<PlaceholderPage title="评测集" />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;
