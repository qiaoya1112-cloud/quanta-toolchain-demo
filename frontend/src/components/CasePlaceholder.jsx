import { Empty, Tag } from 'antd'

function CasePlaceholder() {
  return (
    <aside className="case-placeholder" aria-labelledby="case-title">
      <div className="section-kicker">QUANTA CASE STUDY</div>
      <Tag bordered={false}>预留展位</Tag>
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description={
          <div>
            <strong id="case-title">真实案例待补充</strong>
            <p>后续可加入需求理解稿、访谈提纲、原型截图和迭代结论。</p>
          </div>
        }
      />
    </aside>
  )
}

export default CasePlaceholder
