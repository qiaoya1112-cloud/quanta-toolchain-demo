import { CopyOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons'
import { Button, Collapse, Progress, Tag, message } from 'antd'

function ListBlock({ title, items }) {
  return (
    <section className="list-block">
      <h3>{title}</h3>
      <ol>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ol>
    </section>
  )
}

function StageDetail({ stage, stageIndex, stageCount, onPrevious, onNext }) {
  const [messageApi, contextHolder] = message.useMessage()

  const copyPrompt = async () => {
    try {
      await navigator.clipboard.writeText(stage.promptTemplate)
      messageApi.success('提示词已复制')
    } catch {
      messageApi.error('复制失败，请手动选择提示词')
    }
  }

  const collapseItems = [
    {
      key: 'criteria',
      label: '进入下一阶段前的完成标准',
      children: (
        <ul className="check-list">
          {stage.completionCriteria.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ),
    },
    {
      key: 'mistakes',
      label: '常见误区',
      children: (
        <ul className="risk-list">
          {stage.commonMistakes.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ),
    },
  ]

  return (
    <article className="stage-detail" aria-labelledby="stage-detail-title">
      {contextHolder}
      <header className="stage-detail-header">
        <div>
          <div className="stage-meta">
            <span>阶段 {String(stage.number).padStart(2, '0')}</span>
            <Tag color={stage.required ? 'cyan' : 'default'} bordered={false}>
              {stage.required ? '质量门槛' : '按复杂度裁剪'}
            </Tag>
          </div>
          <h2 id="stage-detail-title">{stage.detailTitle}</h2>
          <p>{stage.purpose}</p>
        </div>
        <div className="stage-progress" aria-label={`阅读进度 ${stageIndex + 1} / ${stageCount}`}>
          <span>{stageIndex + 1} / {stageCount}</span>
          <Progress percent={((stageIndex + 1) / stageCount) * 100} showInfo={false} strokeColor="#149DAA" />
        </div>
      </header>

      <div className="detail-grid">
        <ListBlock title="前置输入" items={stage.inputs} />
        <ListBlock title="标准步骤" items={stage.steps} />
        <ListBlock title="标准产物" items={stage.outputs} />
      </div>

      <section className="responsibility-section">
        <div className="responsibility-title">
          <span>人机分工</span>
          <p>AI 提高信息处理速度，产品经理对业务判断和最终取舍负责。</p>
        </div>
        <div className="responsibility-grid">
          <div>
            <h3>AI 辅助</h3>
            <ul>{stage.aiResponsibilities.map((item) => <li key={item}>{item}</li>)}</ul>
          </div>
          <div>
            <h3>产品经理决策</h3>
            <ul>{stage.pmResponsibilities.map((item) => <li key={item}>{item}</li>)}</ul>
          </div>
        </div>
      </section>

      <Collapse items={collapseItems} className="quality-collapse" />

      {stage.promptTemplate && (
        <section className="prompt-section">
          <div>
            <span className="section-kicker">PROMPT TEMPLATE</span>
            <h3>可直接调整使用的提示词</h3>
          </div>
          <pre>{stage.promptTemplate}</pre>
          <Button icon={<CopyOutlined />} onClick={copyPrompt}>复制提示词</Button>
        </section>
      )}

      <footer className="stage-navigation">
        <Button icon={<LeftOutlined />} onClick={onPrevious} disabled={stageIndex === 0}>
          上一阶段
        </Button>
        <Button type="primary" iconPosition="end" icon={<RightOutlined />} onClick={onNext} disabled={stageIndex === stageCount - 1}>
          下一阶段
        </Button>
      </footer>
    </article>
  )
}

export default StageDetail
