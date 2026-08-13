import { useMemo, useState } from 'react'
import { Button, Tag } from 'antd'
import { ArrowDownOutlined, CheckOutlined } from '@ant-design/icons'
import CasePlaceholder from './components/CasePlaceholder'
import StageDetail from './components/StageDetail'
import WorkflowOverview from './components/WorkflowOverview'
import { workflowStages } from './content/workflow'
import './styles/app.css'

function App() {
  const [selectedStageId, setSelectedStageId] = useState(workflowStages[0].id)
  const selectedIndex = useMemo(
    () => Math.max(0, workflowStages.findIndex((stage) => stage.id === selectedStageId)),
    [selectedStageId],
  )
  const selectedStage = workflowStages[selectedIndex]

  const selectStage = (stageId) => {
    setSelectedStageId(stageId)
    window.requestAnimationFrame(() => {
      const guide = document.getElementById('stage-guide')
      if (typeof guide?.scrollIntoView === 'function') {
        guide.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    })
  }

  return (
    <main className="workflow-page">
      <header className="site-header">
        <a className="brand" href="/" aria-label="返回 Quanta 控制台">
          <span className="brand-mark">Q</span>
          <span>Quanta Product Practice</span>
        </a>
        <nav aria-label="页面导航">
          <a href="#workflow-overview">工作流</a>
          <a href="#stage-guide">执行指南</a>
          <a href="#case-study">案例占位</a>
        </nav>
      </header>

      <section className="hero-section">
        <div className="hero-copy">
          <span className="section-kicker">AI-AUGMENTED PRODUCT WORKFLOW</span>
          <h1>从需求输入，到可验证、可交付的产品方案</h1>
          <p>一套团队产品经理可以按阶段执行、按质量门槛检查，并根据需求复杂度裁剪的 AI 辅助工作手册。</p>
          <div className="hero-actions">
            <Button type="primary" size="large" href="#workflow-overview">查看完整工作流</Button>
            <Button size="large" href="#stage-guide" icon={<ArrowDownOutlined />}>从第一阶段开始</Button>
          </div>
        </div>
        <aside className="reading-guide" aria-label="阅读方式">
          <span className="section-kicker">阅读方式</span>
          <dl>
            <div><dt>30 秒</dt><dd>理解完整链路</dd></div>
            <div><dt>5 分钟</dt><dd>浏览阶段方法</dd></div>
            <div><dt>15 分钟</dt><dd>复制模板执行</dd></div>
          </dl>
        </aside>
      </section>

      <section className="principle-bar" aria-label="核心原则">
        <div>
          <span className="section-kicker">核心原则</span>
          <strong>流程允许裁剪，质量门槛不能跳过</strong>
        </div>
        <ul>
          <li><CheckOutlined />理解需求</li>
          <li><CheckOutlined />业务确认</li>
          <li><CheckOutlined />方案验收</li>
        </ul>
      </section>

      <section id="workflow-overview" className="workflow-section">
        <header className="section-heading">
          <Tag color="cyan" bordered={false}>团队工作手册</Tag>
          <h2>八个阶段，从信息输入到交付闭环</h2>
          <p>点击任意阶段查看前置输入、标准方法、人机分工和完成标准。</p>
        </header>
        <WorkflowOverview
          stages={workflowStages}
          selectedStageId={selectedStageId}
          onSelect={selectStage}
        />
      </section>

      <section id="stage-guide" className="guide-layout">
        <StageDetail
          stage={selectedStage}
          stageIndex={selectedIndex}
          stageCount={workflowStages.length}
          onPrevious={() => setSelectedStageId(workflowStages[Math.max(0, selectedIndex - 1)].id)}
          onNext={() => setSelectedStageId(workflowStages[Math.min(workflowStages.length - 1, selectedIndex + 1)].id)}
        />
        <div id="case-study">
          <CasePlaceholder />
        </div>
      </section>

      <footer className="site-footer">
        <strong>Quanta Product Practice</strong>
        <span>内部方法页，内容可根据团队实践持续更新。</span>
      </footer>
    </main>
  )
}

export default App
