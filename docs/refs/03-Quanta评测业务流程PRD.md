# [PRD]模型双盲评测 - MVP版本 副本

## 一、背景与目标

<cite doc-id="GHVGwIEFhiqh2HkhUOUcT3cPnWd" file-type="wiki" title="[概要] 模型双盲评测" type="doc"></cite>



## 二、业务流程

### 2.1 Quanta 评测业务流程图

<whiteboard token="Bpx4wSKdqhqhz4beuVeci3XVn6b"></whiteboard>



### 2.2 数据流转说明

<whiteboard token="St5swggRLhFDBdbWUFXcU2Q9nHe"></whiteboard>



### 2.3 用户故事

| 角色 | 用户故事 | 故事详情 |
|-|-|-|
|  |  |  |
|  |  |  |



## 三、关键决策点

### 3.1 lowlevel 级别配对打分规则

<callout emoji="🗒️">
**前提：**两个checkpoint，分别执行一组提示词（1 highlevel + N lowlevel），相同 lowlevel 配对 PK 打分，选出表现更好的一方
评测员顺序执行 lowlevel，一条失败，后续 lowlevel 能否继续执行，由评测员自行决定 / 在 Benchmark 级别限制
- 连续任务，不能继续执行 -> 切换下一组
- 单点任务，可以执行下一条（两个任务没关联，一个任务做不了强制要求不能执行后面的也不合适）
**场景：**在一次 highlevel 执行过程中，前序任务失败，可能导致后续任务无法继续，故而一组提示词，lowlevel 最终条数不一致
**问题：**配对 lowlevel 级别打分，什么策略比较合理
</callout>

<callout emoji="🗒️">
**方案**
1. highlevel 执行 m 组即可，按照 highlevel x lowlevel 配对
2. 由于前置阻塞而无法配对的单独 recording：偏好选择按钮禁用，进度分与原因正常打，排行榜不计分
</callout>



## 四、功能详情

### 3.1 原型地址

<bookmark name="quanta-eval-v2.onrender.com" href="https://quanta-eval-v2.onrender.com/"></bookmark>





### 3.2 功能清单

#### 依赖模块

<table><colgroup><col/><col/><col/><col/><col/></colgroup><thead><tr><th><b>模块</b></th><th>功能</th><th>功能说明</th><th>状态</th><th>迭代版本</th></tr></thead><tbody><tr><td><b>标签管理</b></td><td>数据初始化</td><td>数据初始化 </td><td>数据</td><td>MVP</td></tr><tr><td><b>场景管理</b></td><td>场景CRUD</td><td>持自定义场景需要的物料、布置要求、参考图文及视频等<ul><li>MVP 先在评测任务创建时维护</li><li>后续拆分为独立模块</li></ul></td><td>新增</td><td>MVP</td></tr><tr><td rowspan="4"><b>提示词管理</b></td><td>提示词 CRUD</td><td>提示词的增删改查，支持格式化输入<ul><li>一组提示词：1 high_level_prompt + N low_level_prompt</li></ul></td><td>已有</td><td>已有</td></tr><tr><td>提示词标签</td><td>标签打到子 prompt 级别，highlevel 级别是对 lowlevel 的聚合</td><td>调整</td><td>MVP</td></tr><tr><td>提示词标识</td><td>每一条 highlevel x lowlevel 需要有唯一标识<br/>// 现在文字对比的方式，太不严谨了，后续评测任务配对不准确</td><td>调整</td><td>MVP</td></tr><tr><td>数据初始化</td><td>数据初始化 </td><td>数据</td><td>MVP</td></tr><tr><td rowspan="2"><b>评定标准管理</b></td><td>评定标准CRUD</td><td>持自定义评定标准（类型、名称、描述、量表配置等）<ul><li>MVP 版本先不做配置能力，先预置一条数据供选择</li></ul></td><td>新增</td><td>-</td></tr><tr><td>数据初始化</td><td>预置 RoboArena 评定标准（进度分+偏好+解释）</td><td>数据</td><td>MVP</td></tr><tr><td><b>Benchmark</b></td><td>Benchmark CRUD</td><td>Benchmark CRUD，组装场景、提示词、评定标准</td><td>新增</td><td>MVP</td></tr><tr><td><b>checkpoint</b></td><td>-</td><td>云端部署，加在这里？<br/>部署的时机 </td><td>调整</td><td>-</td></tr><tr><td><b>测试任务</b></td><td></td><td>新增字段：评测设备「moz（是否细分型号）、Franka」<br/>部署方式：本地部署、云端部署<ul><li>Moz 默认本地，Franka 默认云端</li></ul><br/>调整字段：预期采集合格量 -&gt; 测试推理次数<br/>新增模式「Eval」</td><td>新增</td><td>MVP</td></tr></tbody></table>



#### 核心模块

<table><colgroup><col/><col/><col/><col/><col/></colgroup><thead><tr><th><b>模块</b></th><th>功能</th><th>功能说明</th><th>状态</th><th>迭代版本</th></tr></thead><tbody><tr><td rowspan="3"><b>【采集端】</b></td><td>本体类型</td><td>支持选择、链接 Franka 设备</td><td>新增</td><td>-</td></tr><tr><td>云端推理</td><td>支持云端推理（不需要模型下载步骤）</td><td>新增</td><td>-</td></tr><tr><td>推理交互</td><td>失败处理：区分系统失败和推理失败（人打标）<ul><li>非推理失败：支持重置本条/整组，数据步保留（不参与评测）</li><li>推理失败：不支持重置数据，后续任务是否执行由数采人员决定</li></ul></td><td>调整</td><td>MVP</td></tr><tr><td><b>评测任务管理</b></td><td>任务状态管理</td><td>任务状态机及其可用操作</td><td>新增</td><td>MVP</td></tr><tr><td><b>评测结果记录</b></td><td>评测结果记录</td><td>从任务视角、模型视角，查看数据<ul><li>MVP 先只做任务视角</li></ul></td><td>新增</td><td>MVP</td></tr><tr><td><b>1 新建评测任务</b></td><td>新建评测任务</td><td>选择 checkpoint +banchmark，组装为一个完整评测任务，同时配置设备要求、评测优先级、次数等核心信息<ul><li>checkpoint：一个任务支持选择多个 ckpt 横测</li><li>banchmark：场景（现配）、提示词（引用）、评定标准（引用）</li></ul></td><td>新增</td><td>MVP</td></tr><tr><td><b>2 测试数据推理（采集）</b></td><td>拆分推理任务</td><td>将评测任务 by checkpoint 拆分为 测试数据采集任务「Eval」<ul><li>拆分时字段映射、采集过程中进度同步</li></ul></td><td>新增</td><td>MVP</td></tr><tr><td><b>3 评测任务配对</b></td><td>评测任务配对</td><td>lowlevel 标识一致配对<ul><li>以评测任务要求的测试组数为基准，进行 checkpoint 的筛选</li><li>Random lowlevel 顺序、A/B 组顺序</li></ul><br/>这步是放在评测执行前，还是单独步骤？评测执行前？</td><td>新增</td><td></td></tr><tr><td rowspan="3"><b>3 评测执行</b></td><td>评测工作台</td><td>展示双盲视频/操作结果，标注员按评分规则逐维度打分</td><td>新增</td><td>MVP</td></tr><tr><td>评测模式</td><td>偏好选择：根据对比型评定标准打分（进度分+ 偏好选择 + 文字解释）</td><td>新增</td><td>MVP</td></tr><tr><td>评分数据存储</td><td>评分数据存储，支持任务与模型视角</td><td>新增</td><td>MVP</td></tr><tr><td><b>4 数据处理</b></td><td>数据处理</td><td>进度分处理 0-5 -&gt; 0.0-1.0<br/>偏好选择兼容 RoboArena -&gt; A/B/Tie<br/>文字解释中译英</td><td>新增</td><td>MVP</td></tr><tr><td rowspan="2"><b>5 结果报告</b></td><td>排名计算</td><td>Bradley-Terry with Davidson Ties 排名</td><td>新增</td><td>MVP</td></tr><tr><td>多维分析</td><td>多维分析报表（待和算法确认分析内容，单独评审）</td><td>新增</td><td></td></tr></tbody></table>



## 四、需求详情

### 4.1 原型地址

<bookmark name="评测任务管理 - Quanta 评测平台" href="https://quanta-eval-v2.onrender.com/tasks"></bookmark>

页面跳转关系：https://mastergo.com/goto/SUr4p7lq?page_id=13:7506&file=189630750479422 

### 4.1 功能详情

<table><colgroup><col/><col/><col/></colgroup><thead><tr><th></th><th>图示</th><th>说明</th></tr></thead><tbody><tr><td><b>评测任务管理</b><b>【Quanta】</b></td><td><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NmE4ZjUzMTJmZmVjNjU2NWUzMjRkODdjN2ZjMWIzMDRfMGMwOTcyMTIwYjZlMTIxOTQ4ZDI1Y2RhZTk5NjMzNGVfSUQ6NzY2MzAzOTQwNzI0NjcyNDMzMl8xNzg0MTkwNzgxOjE3ODQxOTQzODFfVjM" mime="image/png" scale="1.000000" src="R7oxb91jCo0hajxO0cKcJsWkn5f"/></td><td><b>任务状态与操作</b><whiteboard token="Puc8wBtORho38BbIqAlcO5qOneh"></whiteboard><br/><b>页面交互</b><ul><li>列表字段：ID、名称、Benchmark、Checkpoint、启用、状态、采集进度、评测进度、优先级、创建人、创建时间，部署方式， 标签<ul><li>采集进度：已采集组数/需采集组数（m组 x checkpoint 数量）</li><li>评测进度：已评测对数/需评测对数（需评测对数为配对记录数）</li></ul></li><li>筛选条件：ID、名称、Benchmark、Checkpoint、状态、优先级</li><li>列操作：<ul><li>详情-查看评测任务详情；</li><li>查看数据-跳转至结果记录列表并筛选当前任务；</li><li>删除、关闭：见上文状态机</li></ul></li><li>状态流转确认：<ul><li>可关闭/不关闭：<ul><li>可关闭: evaluating, collecting</li><li>不可关闭：其它</li></ul></li><li>已关闭/未关闭： status: closed, 加一个<u>关闭接口</u>。关闭不可逆</li><li>可编辑：status: draft, 前端加个开始按钮，调用“启动”接口</li><li>可删除：status: draft | closed.</li></ul></li></ul></td></tr><tr><td rowspan="2"><b>评测结果记录</b><b>【Quanta】</b></td><td><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NDBhYzBkZTY1YTI0OWRlZDc1NjU5ZTc1MTZlYjljYWJfOTcyZTFmZTJhZGQ3ZDU2NGY1ZmZmNGYyYTJiYjk2ZmVfSUQ6NzY2MzAzOTQwMzgxMjQ3NDA4Nl8xNzg0MTkwNzgxOjE3ODQxOTQzODFfVjM" mime="image/png" scale="1.000000" src="EVqwbD2B1oj358x1DPscv034neg"/></td><td><b>评测结果列表页</b><br/>支持任务视角展示评测结果 （不展示checkpoint视角）<ul><li>列表字段：任务 ID、任务名称、HL、LL、A模型、B模型、评测结果、A 进度分、B进度分</li><li>筛选条件：任务（下拉选择）、HL、LL、checkpoint（同时筛选作为A/B模型的记录）</li></ul></td></tr><tr><td><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Y2IxNThlN2ZiNTEyOTYzMDgyMzVmMTM4MDFkYWFiOWRfOTljYmM3ZmRkZTA3NzUxMDFmNzc5YjYzMDAxZGE1OGNfSUQ6NzY2MzAzOTQwNTQwMTcwNTcwN18xNzg0MTkwNzgxOjE3ODQxOTQzODFfVjM" mime="image/png" scale="1.000000" src="GOqsb50FgoblVnxjIDRcf2zvnzd"/></td><td><b>评测结果详情页</b><br/>评测页面的只读态，展示模型名称，支持切换 上/下一条</td></tr><tr><td><b>评测任务创建</b><br/><b>【Quanta】</b></td><td><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YmVhNmYxMTI3YzY1MjU3NzhjNmNkNmJiY2QyOGI2MjNfMzZjMDMyZmY4NTYwNDBlY2M1YWI0Nzg3ODIxZGRmZGVfSUQ6NzY2MzAzOTQwNzE4NzkyMjE3MV8xNzg0MTkwNzgxOjE3ODQxOTQzODFfVjM" mime="image/png" scale="1.000000" src="VHMUb6wBToskwMxtR0pcLqMsnOb"/><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OTQ1ZWQ5YWYwMzNiODg0ZDJmZGUxZmUzNzJjYWQ4MTRfNzA4MTM2Y2VmNTAyNGU1YWU4MGNmZDE1NjRiNGY0ZjRfSUQ6NzY2MzAzOTQwNDAwNTM2Mjk3M18xNzg0MTkwNzgxOjE3ODQxOTQzODFfVjM" mime="image/png" scale="1.000000" src="L281bSY9mow0HixMvAbce2R7n8b"/></td><td><b>页面交互</b>：相较于已有测试任务新增/变更字段<ul><li>向评测员展示名称：采集端选择任务时展示名称，placeholder“不要包含评测模型的信息”</li><li>评测本体：枚举，必填，选项「Moz，Franka」</li><li>部署方式：枚举，必填，选项「本地部署，云端部署」（一期禁用，与本体联动，Moz -&gt; 本地部署，Franka -&gt; 云端部署」</li><li>Checkpoint：枚举，必填，支持多选</li><li>Benchmark：单选，必填<ul><li>选择 Benchmark，展示场景、提示词、评价标准信息，支持查看详情</li></ul></li></ul></td></tr><tr><td><b>数据采集任务</b><br/>【自动生成】<br/><b>【Quanta】</b></td><td><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NTVlMTFkMjFlYjZmY2RmMmFmYTZjNDVjODIxYjIyYTJfZWRkYWI4NGQxYzg0NjIyNTE0YjEyZGY1YjI0NjBlZGNfSUQ6NzY2MzAzOTQwNTMxNzk2NzA0OF8xNzg0MTkwNzgxOjE3ODQxOTQzODFfVjM" mime="image/png" scale="1.000000" src="X37qbqk3oo6ZuIxktoccyCY6nUm"/></td><td><b>业务流程</b><whiteboard token="A0Ixw5jeChxHz2bnc2pcUMyWnYd"></whiteboard><br/><b>实体关系</b><whiteboard token="Jlc1whqE5ho3fMb0l4Mc50k1nkb"></whiteboard><br/>将评测任务 by checkpoint 拆分，生成多条采集任务。采集任务新增「Eval」类型，相较于「test」<ul><li>新增字段「本体类型：moz、Franka」「部署方式：本地部署，云端部署」</li><li>评定标准：成功/失败各一</li><li><b>查看Recordings：看是否能复用现有Recording页面</b></li></ul></td></tr><tr><td rowspan="3"><b>数据采集</b><br/><b>【采集端】</b></td><td><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=N2MxNjIxODk3ZWRkZGY5MTEwZDhiYWI1ZWZiMTlhNDlfYjI4MjYyYjBjNjEwMWVjMTNkNGI1ODM0ZjE3MzUzMWJfSUQ6NzY2MzAzOTQwNTQ0NzY3OTE2Ml8xNzg0MTkwNzgxOjE3ODQxOTQzODFfVjM" mime="image/png" scale="1.000000" src="SWI5bjuaZoxuOyxPiUncqaimnYc"/></td><td><b>模式：</b>新增枚举「Eval」<br/><b>设备：</b>禁用状态，根据测试任务配置自动带出「 moz、Franka」<br/><b>部署：</b>禁用状态，根据测试任务配置自动带出「云端部署、本地部署」<ul><li>云端部署：可直接点击「下一步」进入推理</li><li>本地部署：需等待模型下载完成后再点击「下一步」进入推理（同当前逻辑）</li></ul><br/><b>模式组合与支持要求</b><ul><li>一组 checkpoint - moz - 云端推理 [暂不支持]</li><li>一组 checkpoint - Franka - 云端推理 [支持]</li><li>一组 checkpoint - moz - 本地推理 [支持]</li><li>一组 checkpoint - Franka - 本地推理 [暂不支持]</li></ul></td></tr><tr><td><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MmZlZjY5ZTlkYjgwNzBjMWM1ZDc2Y2EyNjk3MGRlN2RfZjc3M2M2Y2FiOWQyZDcxNGQ0N2VkNDAzN2FiYzE1YThfSUQ6NzY2MzAzOTQwNTEwODIzNTQ0NV8xNzg0MTkwNzgxOjE3ODQxOTQzODFfVjM" mime="image/png" scale="1.000000" src="Jhx2b5XEsoKDdixbUapcu4n9nCS"/></td><td>新增步骤，展示 Benchmark 信息</td></tr><tr><td><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZDIwMTEyYzc4M2I0MTQ4ZTY4NGJlM2M2NzljNjA5MzJfMTg0ZjBlYTc2N2ZkYTM1NzI2MTM5NmIwYjdiODhhNzNfSUQ6NzY2MzAzOTQwNjE2MDcyNzMxMF8xNzg0MTkwNzgxOjE3ODQxOTQzODFfVjM" mime="image/png" scale="1.000000" src="UD6qbBXKOozwS0xTNUncGtAWnot"/></td><td><whiteboard token="WfqTwLaFHhYBwQbaednc5izfnyd"></whiteboard><br/><b>采集流程：</b>[Eval 类型] 流程执行规则<ol><li seq="1">执行顺序：仅允许顺序执行，不能随意选择</li><li>失败处理：本条任务失败，允许进行以下操作（采集员自行判断是否连续任务）<ol><li seq="1">继续执行下一条</li><li>直接切换下一组</li></ol></li><li>异常处理<ol><li seq="1">长时间推理：推理长时间不结束，支持手动终止</li></ol></li></ol><br/><b>状态与操作按钮</b><ul><li><b>行按钮</b></li></ul><ol><li seq="1">未执行 → 显示「<b>执行」</b>按钮 [已有]</li><li>执行中 → 执行按钮 loading [已有]</li><li>执行完 → <b>「成功并下一条</b><b>/成功</b><b>」「失败」</b>二选一按钮  [已有]</li><li><del>选择后 → 有两种情况</del><ol><li seq="1"><del>成功标签+</del><b><del>「</del></b><b><del>改</del></b><b><del>为”失败“」</del></b><del>按钮（修改结果数据，仅最新一条有修改按钮）</del></li><li><del>失败标签+</del><b><del>「</del></b><b><del>改</del></b><b><del>为”成功“」</del></b><del>按钮（修改结果数据，仅最新一条有修改按钮）</del></li></ol></li></ol><ul><li><b>全局按钮</b></li></ul><ol><li seq="1">停止：标记<b>「失败」abandoned</b></li><li>复位：<b>「</b>机器人复位<b>」VRMOV</b></li><li>重置：重置整组数据 + 复位 —— <del>数据作废（仅重置数据，不复位本体）</del></li></ol><ul><li>其他操作<ul><li>切换提示词组<ul><li>最新的一条是成功，且其不是本组最后一条</li></ul></li></ul></li></ul><br/><b>采集界面：</b>摄像头分布、本体上电/控制操作，按照 Franka 设备调整（后续补充详细设计）</td></tr><tr><td><b>执行评测</b><br/><b>【Quanta】</b></td><td><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NGVhMDVkZGM4NjY1YjMxOWIwZDdiNmU1YzdiZWQwODlfZjcyZGIzZDNiZDQ4NTUzOGI1ODg4MGFiMDA1ZDFjYWVfSUQ6NzY2MzAzOTQxMTUzODM0OTM0M18xNzg0MTkwNzgxOjE3ODQxOTQzODFfVjM" mime="image/png" scale="1.000000" src="At57b0r92oua7XxrIunc24bVnSg"/><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZjljNjI3ZmRjMzczMjIyMDllMDU4Y2ZhOWIxYzcwMjhfZjFlOTdlMDU3MzFmZjdiMGM0ODAyNWI0NDNhNTA4ZDNfSUQ6NzY2MzAzOTQxMDYyMzk5MDk5M18xNzg0MTkwNzgxOjE3ODQxOTQzODFfVjM" mime="image/png" scale="1.000000" src="UOBfbUrdIofIoxxmTRJcxmY8nqg"/><img name="image.png" caption="&#xA;" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MTI4MmRiZTAxNWRmNjZkNzhlYzM3YTNlOTE2ZTMzYjlfOGI5YWI2NTI1M2FjZThiZTY3ZjNmNTljYjg3ZmExMjZfSUQ6NzY2MzAzOTQxMTEyNzM1NjY2M18xNzg0MTkwNzgxOjE3ODQxOTQzODFfVjM" mime="image/png" scale="1.000000" src="J4FebGH4Lomuo2xsUbnc2eQbnIg"/></td><td><b>评测流程</b><whiteboard token="BILAwIai2hjec9b2lDBc136Dn7d"></whiteboard><ul><li><b>状态判断：</b>创建任务后，关联测试数据采集任务，采集完成后，任务状态从<b>「采集中」</b>切换至<b>「准备中」</b>进行记录配对，准备完成后进入<b>「评测中」</b>，可以开始评测<ul><li>配对逻辑：见上文决策点</li></ul></li></ul><br/><b>页面交互</b><ul><li>评测工作台列表<ul><li>列表字段：任务 ID、Benchmark、进度、优先级，除进度外均支持筛选</li></ul></li><li>评测工作台详情：所有 lowlevel 拍平评测<ul><li>顶部区域：展示 HL x LL 的提示词，以及当前任务下，所有lowlevel 进度</li><li>视频区域：默认展示主摄，支持展开腕摄，记住选择，切换任务仍保留</li><li>评分区域：进度分（0-5），文字说明，偏好选择，均必填，提交校验</li><li>操作：支持“提交并下一条”，“返回上一条”，可修改结果。最后一条提交，则任务全部完成。</li></ul></li><li>特殊情况：单 recording 无配对，交互见左图，仅需选择单记录的进度分和文字说明，偏好选择禁用</li></ul></td></tr><tr><td><b>数据处理与排行榜</b><br/><b>【Quanta】</b></td><td><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Yzk2NTNmZDFlZWU4YmE5YWQxNDhhNDRhMGZmMTg1NjdfODQ1MjM2OWUwMjMzYTEwZDA5ODViYzhkZTU3YTAxY2FfSUQ6NzY2MzAzOTQxMjE2NzE1MDg1MV8xNzg0MTkwNzgyOjE3ODQxOTQzODJfVjM" mime="image/png" scale="1.000000" src="Ps12bLsbLoUBpUx2UxzcU4Trnnh"/></td><td><b>处理时机</b><ul><li>定时触发：每天 2:00</li><li>手动触发：评测完成的任务，管理员手动点「分析」按钮</li></ul><br/><b>处理内容</b><ul><li>进度分：打分时[1-5]，需转化为[0.0, 1.0]，用于 Task-Aware 排名算法输入</li><li>偏好选择：需将「平局、都好、都差」均按照「平局」处理</li></ul><br/><b>分数计算</b><ul><li><b>【决策点】</b>计算维度：<ul><li>所有 lowlevel 拍平计算 ✅</li><li>Lowlevel 先按照 highlevel 聚合，再计算</li></ul></li><li>得分：Bradley-Terry with Davidson Ties，参考 <cite doc-id="PTORwzosAiR3bfk2o2Bcj4Fmneg" file-type="wiki" title="基础模型Model Card" type="doc"></cite>，<source href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YmZlYzc0ZDIyOTlhMmRkMzhkMTA1NGEyNGQ5MzY1MTVfM2QxZTg5Y2U3OGExMDQ0M2U3NDhiOTc3ZWVhNWIxYTZfSUQ6NzY2MzAzOTQxMzc2NDcyMTg2NF8xNzg0MTkwNzgxOjE3ODQxOTQzODFfVjM" mime="application/zip" token="BcKPbvyUjoBQwsxGHv3cbskTnHb"/>，<cite doc-id="HozFws0Q3itflkky0gvctboInzb" file-type="wiki" title="RoboArena评分体系逆向工程报告.docx" type="doc"></cite></li><li>SD 标准差：衡量模型表现的波动</li><li>SE 标准误：衡量分数的可靠性</li><li>胜率以及对应场次统计</li></ul><br/><b>页面交互</b><ul><li>模型榜单-查看-跳转至结果记录列表并筛选当前模型</li><li>支持切换图表：趋势图单点指标确认 </li></ul></td></tr><tr><td><b>多维分析 </b><b>待定</b><br/><b>【Quanta】</b></td><td><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OTMzNmM3ZjE1ODE3Y2MwZjZkZmJlZjJkYWZiYzI4MDVfNjY5NzY0Yzk4MDQ3MTEzOTdiZDViMzNiYWE1YThkMjFfSUQ6NzY2MzAzOTQxMTQ4Mzc0MTQ3MF8xNzg0MTkwNzgxOjE3ODQxOTQzODFfVjM" mime="image/png" scale="1.000000" src="B4q1bKZbEowVIbx05P1cKuMfn2F"/></td><td>支持选择 checkpoint 查看分析结果（默认展示前5名）<br/>图表按需，根据模型训练所需的数据洞察维度展示，如：标签雷达图、能力短板雷达图、得分趋势图、模型对战矩阵、Low Level 胜率热力图 等</td></tr></tbody></table>



### 4.2 依赖模块

<table><colgroup><col/><col/><col/></colgroup><thead><tr><th></th><th>图示</th><th>说明</th></tr></thead><tbody><tr><td><b>Benchmark管理</b></td><td><img name="image.png" caption="&#xA;" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NDQ5MzUzNWUxMmQwMGYwY2EwYTA4YjkxZjE1YWI4NGNfM2IyNmM0NjU1ZmViZDMxMGZjNWQzYTI4OTYwZjhiYzhfSUQ6NzY2MzAzOTQxMDkzMDk5NDQ1OF8xNzg0MTkwNzgxOjE3ODQxOTQzODFfVjM" mime="image/png" scale="1.000000" src="HZLTbITaDo7E4LxfxX1c0w45nac"/><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZGI2NTAyOGRkYzRmODI4ZWJhYjUwZGE2ZTQ1ZGNhNzFfZjcwZDlmMTk0ZTEyNmE1YmU0N2RmY2UwZDlmMzE5ZDFfSUQ6NzY2MzAzOTQxMDQ2MDU0NDI4M18xNzg0MTkwNzgyOjE3ODQxOTQzODJfVjM" mime="image/png" scale="1.000000" src="UMqGbesAloOnH5xAusgcb3fMnwg"/></td><td><b>新增 Benchmark</b><ul><li>基础信息：<ul><li>名称（必填）</li><li>描述（可选）：长文本</li></ul></li><li>场景配置：<ul><li>场景描述（必填）：长文本</li><li>任务道具（必填）：文本，多个逗号分隔</li><li>场景图片、场景视频（校验二者至少填写一个）：数组，支持上传多个</li><li>关联配置：<ul><li>提示词（必填）：引用提示词管理模块，多选</li><li>评价标准（必填）：本期预置「RoboArena 标准」，不支持其他选项</li></ul></li></ul></li></ul></td></tr><tr><td><b>评价标准管理 </b><b>参考，本期不包含</b></td><td></td><td><b>标准内容</b><ul><li>基本信息：<ul><li>标识、名称、描述</li><li>类型：成功失败、量表评分、偏好选择、基线对照（类型对应不同的交互界面和底层数据存储结构）</li></ul></li><li>表单信息<ul><li>类型（必填）：不同类型数据结构不同（参考下文结构）</li><li>量表（可选）：每种类型都可以附一个量表</li><li>备注（可选）：每种类型都可以增加备注信息</li></ul></li></ul><br/>// 备注与量表长文本的区别：备注跨模型填写一份；量表表单项，每个模型分别填写；<br/><b>数据结构（供参考）</b><pre caption="&#xA;" lang="JSON"><code>整体数据结构<br/>{<br/>  "criterion_id": "string",<br/>  "criterion_name": "string",<br/>  "criterion_type": "pass_fail | preference | baseline | scale",<br/>  "criterion_description": "string",<br/><br/>  "form": {<br/>    // 类型模块：items 的结构由 criterion_type 决定，见下方四种 item 定义<br/>    "type_module": {<br/>      "items": []<br/>    },<br/><br/>    // 量表模块：独立于类型模块，可选，任何类型都可附带<br/>    "scale_module": {<br/>      "items": []<br/>    },<br/><br/>    // 备注模块：富文本，可选<br/>    "note": "string | null"<br/>  }<br/>}<br/><br/>四种 item 结构<br/>// pass_fail item<br/>{ "prompt": "string", "model": "string", "result": "success | fail" }<br/><br/>// preference item<br/>{ "prompt": "string", "winner": "string | null", "is_tie": false }<br/><br/>// baseline item<br/>{ "prompt": "string", "result": "win | lose | tie" }<br/><br/>// scale item<br/>{ "prompt": "string", "model": "string", "metric_name": "string", "metric_description": "string", "score_range": { "min": 0, "max": 0 }, "value": null }</code></pre><br/><b>MVP 预置数据 —— RoboArena 评价标准</b><pre caption="&#xA;" lang="Markdown"><code>基本信息<br/>- 标准名称：RoboArena 标准<br/>- 标准类型：偏好选择<br/>- 标准描述：<br/><br/>标准表单<br/>- 类型：哪方更优/平局的选择结果<br/>- 量表：进度分[1-5]<br/>- 备注：文字说明</code></pre></td></tr></tbody></table>



### 4.3 权限配置

<table><colgroup><col/><col/><col/></colgroup><thead><tr><th>角色</th><th>资源</th><th>用户名单</th></tr></thead><tbody><tr><td>评测操作员</td><td><b>评测模块</b><ul><li>评测工作台 piritArena/execution/workbench</li></ul></td><td></td></tr><tr><td>评测管理员</td><td><b>评测模块所有菜单 spiritArena</b><ul><li>评测任务管理 spiritArena/management/campaign</li><li>评测采集管理 spiritArena/management/collection</li><li>评测结果记录 spiritArena/management/judge-records</li><li>评测工作台 spiritArena/execution/workbench</li><li>排行榜 spiritArena/dashboard/leaderboard</li><li>Benchmark 管理 spiritArena/config/benchmark</li></ul><br/><b>机器学习平台</b><ul><li>任务提示词 evaluation/taskPrompt</li><li>标签管理 tag/list</li></ul></td><td></td></tr><tr><td>平台超管（已有的管理员角色）</td><td><b>评测模块所有菜单 spiritArena</b><ul><li>评测任务管理 spiritArena/management/campaign</li><li>评测采集管理 spiritArena/management/collection</li><li>评测结果记录 spiritArena/management/judge-records</li><li>评测工作台 spiritArena/execution/workbench</li><li>排行榜 spiritArena/dashboard/leaderboard</li><li>Benchmark 管理 spiritArena/config/benchmark</li></ul></td><td></td></tr></tbody></table>



## 附录

### 相关资料及链接

**科研 & 政策文档**

> 核心机制参考：
> 
> - 论文：[《RoboArena: Distributed Real-World Evaluation of Generalist Robot Policies》](https://arxiv.org/pdf/2506.18123)
> - 网站：https://robo-arena.github.io/#resources-section
> - 数据集：https://huggingface.co/datasets/RoboArena/DataDump_02-03-2026/tree/main
> - 代码：https://github.com/robo-arena/roboarena
> 
>   - 评测协议、排名算法和数据结构：[RoboArena 评分体系逆向工程报告](https://nwd4iy9rd2s.feishu.cn/wiki/HozFws0Q3itflkky0gvctboInzb)（根据代码和论文倒推，非官方文件）
> 
> 诊断归因参考：
> 
> - [《Embodied Arena: A Comprehensive, Unified, and Evolving Evaluation Platform for Embodied AI》](https://arxiv.org/pdf/2509.15273)
> - [《YD/T 6770—2026 人工智能 关键基础技术 具身智能基准测试方法》](https://std.miit.gov.cn/#/fullTextList)(点击链接，搜索“YD/T 6770-2026”并预览），工信部，2026.6 开始实施





### Lowlevel 配对打分规则 - 方案讨论

<table><colgroup><col/><col/></colgroup><thead><tr><th>方案</th><th>分析结论</th></tr></thead><tbody><tr><td><b>方案一 保证所有 lowlevel 至少执行 m 组</b><ol><li seq="1">所有 lowlevel 至少执行 m 组 -&gt; 有的 lowlevel 会执行 m+ 次（成功和失败记录都保留）</li><li>每条 lowlevel 都随机抽样 m 组，配对打分</li></ol></td><td>❌ 【可操作性问题：<b>成本高，且可能完不成】</b><br/>连续任务中，为了让靠后的 lowlevel 凑够 m 组，需要反复回跑前序链条，执行成本随链长呈倍数放大；极端情况下前序持续失败则永远无法达到 m 组，规则本身不可收敛。<br/><b>详细优缺点 ⬇️</b><pre caption="&#xA;" lang="Markdown"><code><b>优点</b><br/>- 样本量最大、统计功效最强<br/>- 成功/失败记录都保留并抽样，<b>不掩盖失败信号</b>，对能力差的 checkpoint 不会"因执行少而免责"<br/>- 随机抽样 m 组可以对冲执行次数不均的偏差<br/><br/><b>缺点</b><br/>- <b>执行成本最高</b>。为了把 lowlevel 凑够 m 组，可能需要反复回跑<br/>- 随机抽样引入方差，小样本时结果不稳定</code></pre></td></tr><tr><td><b>方案二 highlevel 执行 m 组即可，lowlevel 没执行算 0 分</b><ol><li seq="1">highlevel 执行 m 组，部分 lowlevel 执行不足 m 组</li><li>配对比较，lowlevel 没执行计 0 分，执行了的正常打分 1-5 </li></ol></td><td>❌ <b>【</b>方法论问题：<b>0 分不是真实数据、重复惩罚】</b><ol><li seq="1">checkpoint 没跑到 lowlevel-2，你不知道它跑到了会得几分，强行记 0 分等于凭空造了一个观测值</li><li>lowlevel-1 的失败已经扣过一次，后续未执行的 lowlevel 再记 0 分 = <b>同一个失败被扣了 N 次（N = 该 highlevel 下的 lowlevel 数量）</b>。</li><li>连续任务链越长、前序成功率越低，这个放大效应越严重，会系统性奖励"前序稳但后续能力平庸"的 checkpoint，严重时让 PK 排名与真实能力相反。</li></ol><br/><b>详细优缺点 ⬇️</b><pre caption="&#xA;" lang="Markdown"><code><b>优点</b><br/>- 执行成本最低，一次 highlevel 跑 m 轮就收工<br/>- 简单直接，规则清晰<br/><br/><b>缺点</b><br/>- <b>0 分惩罚过重且不对称</b>。假设 checkpoint A 在 lowlevel-1 反复失败导致 lowlevel-2 全部 0 分，checkpoint B 在 lowlevel-1 偶尔成功让 lowlevel-2 跑到了拿了 3 分——B 在 lowlevel-2 上的"能力"其实没被独立验证过，只是因为前序通过了就享受了 3 分的配对优势<br/><b>- 双重惩罚</b>：lowlevel-1 的失败已经在 lowlevel-1 的打分里体现过一次，lowlevel-2 又计 0 分，相当于一次失败被计算了多次<br/>- 当 m 较小时，0 分会严重拉低均分，PK 结果被"前序任务稳定性"单一维度主导</code></pre></td></tr><tr><td><b>方案三 highlevel 执行 m 组即可，按照最小执行次数配对</b><ol><li seq="1"> highlevel 执行 m 组，部分 lowlevel 执行不足 m 组</li><li>每条 lowlevel，判断 所有 checkpoint 执行的最小次数，并按照最小次数配对（部分执行多的 lowlevel 不会参与评测）</li><li><b>增加「执行率 = 实际执行次数/应执行次数」指标，辅助判断</b><ul><li>打分差异显著时，以 lowlevel 得分为准</li><li>打分差异不显著（比如均分差 &lt; 0.3）时，<b>以执行率更高的一方胜出</b></li><li>执行率可在报告中独立展示，不污染打分本身</li></ul></li></ol></td><td><b>失败保留，公平性高。不造假、不惩罚、不重跑</b><br/>缺点是"掩盖了执行次数差异"，通过**「执行率 = 实际执行次数 / 应执行次数」作为辅助指标**补救：<br/><b>详细优缺点 ⬇️</b><pre caption="&#xA;" lang="Markdown"><code><b>优点</b><br/>- 严格配对，比较的是<b>两个 checkpoint 都执行过的同等条件</b>下的表现，公平性最高<br/>- 不引入人为 0 分，不虚增执行量<br/><br/><b>缺点</b><br/>- <b>系统性掩盖失败信号</b>。如果 A 在 lowlevel-2 执行了 5 次（因为前序稳定），B 只执行了 1 次（前序老是挂），按 min=1 只比这 1 次，等于<b>奖励了失败更多的 B</b>——B 因为"样本少"反而少暴露了问题<br/>- 丢弃数据，统计功效下降<br/>- 极端情况下 min=0，该 lowlevel 直接无法评测</code></pre></td></tr><tr><td><b>方案四 highlevel 执行 m 组即可，不足 m 组的 lowlevel 重复补足</b><ol><li seq="1"> highlevel 执行 m 组，部分 lowlevel 执行不足 m 组</li><li>要求配对 m 组，不够的通过重复补齐</li></ol></td><td>❌<b> 【</b>方法论问题：<b>重复补足是伪造置信度】</b><br/>只观测到 1 次的结果复制 m 次，均值看起来没变，但样本量从 1 被人为放大到 m，统计显著性失真<br/><b>详细优缺点 ⬇️</b><pre caption="&#xA;" lang="Markdown"><code><b>优点</b><br/>- 保持 m 组配对的数量一致，样本量稳定<br/>- 比方案二温和：不用 0 分硬惩罚<br/><br/><b>缺点</b><br/>- <b>重复采样会放大偶然结果</b>。如果某条 lowlevel 只执行了 1 次且恰好成功，重复补到 m 组相当于把这一次的打分复制 m 次，人为抬高了置信度——但实际上你只观测到 1 次<br/><b>- 同样掩盖了"为什么执行次数不足"这个关键信息</b>。执行少本身是能力弱的信号，重复补足把这个信号擦掉了<br/>- 如果补的是成功的记录，等于奖励幸存者偏差；如果按比例补，方差难以解释</code></pre></td></tr></tbody></table>
