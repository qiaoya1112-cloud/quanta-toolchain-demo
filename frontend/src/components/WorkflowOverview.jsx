import { Tag } from 'antd'

function WorkflowOverview({ stages, selectedStageId, onSelect }) {
  return (
    <nav className="workflow-strip" aria-label="工作流阶段">
      {stages.map((stage) => {
        const selected = stage.id === selectedStageId
        return (
          <button
            key={stage.id}
            type="button"
            className={`stage-button${selected ? ' is-selected' : ''}`}
            aria-label={`阶段 ${stage.number}：${stage.title}`}
            aria-current={selected ? 'step' : undefined}
            onClick={() => onSelect(stage.id)}
          >
            <span className="stage-number">{String(stage.number).padStart(2, '0')}</span>
            <strong>{stage.title}</strong>
            <span className="stage-summary">{stage.summary}</span>
            <Tag color={stage.required ? 'cyan' : 'default'} bordered={false}>
              {stage.required ? '必做' : '可裁剪'}
            </Tag>
          </button>
        )
      })}
    </nav>
  )
}

export default WorkflowOverview
