# [概要] 模型双盲评测 副本

## 一、背景与目标

### 1.1 需求背景

<callout emoji="📍">
1. 支持基模组**「完成 Spirit v1.6 基础模型迭代，在 RoboArena 榜单上达到全球 Top1」**的目标
2. 建立一个符合行业最佳实践的测试平台与评估机制，服务于模型训练的质量和效率
</callout>

**算法团队 OKR**

> O 完成 Spirit v1.6 基础模型迭代，在 RoboArena 榜单上达到全球 Top1，超越 π0.5 和 DreamZero，并完成模型开源和 report 撰写
> 
> - KR：与平台合作，搭建内部类似 RoboArena 的评测平台，支持双模型对比评测、视频上传、人工/半自动打分与排行榜展示。并据此优化内部评分和 RoboArena 线上评分的相关性，使其正相关。



**平台团队 OKR**

> O 打造一站式具身智能开发平台，实现数采到模型训、推、测闭环
> 
> - KR：跑通双盲评测核心流程，支持100台机器人和100位评审员同时工作



### 1.2 RoboArena 介绍

<callout emoji="📌">
**RoboArena：**一个用于 **真实世界、分布式、众包评估** 通用机器人策略的开放评测基准与平台。
</callout>

**核心背景**

- 解决传统机器人评估依赖**标准化环境、任务单一、难以扩展**的问题
- 灵感源于大语言模型评测平台 **Chatbot Arena**，采用**去中心化众包**与**双盲对比**模式



**业务流程**

<whiteboard token="GvolwiEY2hV2nUbQUa7cYySin7d"></whiteboard>



**核心机制**

- **评价范式 - 去标准化：**从「标准化 benchmark」→「分布式真实世界评测」，用“去标准化 + 分布式 + 统计建模”替代传统benchmark，更好地体现场景泛化性；
- **评价机制 - 双盲测试：**pairwise + ranking 双盲 A/B 测试 + 人类偏好投票 + Bradley-Terry / Elo 排名，屏蔽主观干扰；
- **能力建模 - 多维向量：**从“任务成功率”→“能力向量”：建立 多指标、多维度 能力体系；
- **评测效率 - 众包模式：**“众包”评测，打破硬件、地域、人力的限制，提高评测的规模和效率高。



<callout emoji="📍">
**RoboArena 与 Quanta 评测平台核心差异 —— 面向结果 vs 面向过程**
</callout>

|  | RoboArena | Quanta-评测 |
|-|-|-|
| 核心目标 | 公正排名所有参与者——本质是**「裁判」** | 服务于模型训练，使其达到顶尖水平——本质是**「教练」** |
| 产品重心 | 重「评测结果公平性」 | 重「评测过程可复现、评测结果可解释」 |
| 结果用途 | 发布排行榜 | 指导训练、定位弱点 |

**Quanta 相较于 RoboArena 的“做”与“不做”**

<grid>
<column width-ratio="0.500000">
**✅ 要做的**（核心评测机制与结果解释）
- 评测 - 盲测，评测者看不到评测对象/模型信息
- 评测 - 两组（多组）对比分析
- 结果 - 多指标、多维度能力报告
- 结果 - 得分排行榜
</column>
<column width-ratio="0.500000">
**❌ 短期不做的**（服务于分布式、众包的设定）
- 评测 - Policy 分配（优先取排名最不确定的策略对）
- 评测 - 评测员实时自定义场景与 Benchmark
- 评测 - 众包机制
- 其他 - 社区运营（赞助机构引入、信用点等）
</column>
</grid>



<callout emoji="📍">
**预训练（基模）与后训练（demo）评测核心差异 —— 通用 vs 聚焦**
</callout>

|  | 预训练（通用评测） | 后训练（场景评测） |
|-|-|-|
| 任务分配权重 | 任务覆盖广、权重均衡 | 任务高度聚焦、覆盖该场景的长尾情况 |
| 评价标准定义 | 类 RoboArane 多维评价体系 | 指定场景业务验收标准 |

**平台设计思路：底层能力通用，预训练/基模评测是一种特殊的场景封装**

<grid>
<column width-ratio="0.500000">
**通用能力**
- ckpt 管理：模型准备、部署、版本与血缘管理
- Benchmark 管理：自定义场景与提示词
- 评定标准管理：自定义评定标准
- 分析模板管理：按照指定分析模板，产出结果报告
- 评测机制：多组对比评测
</column>
<column width-ratio="0.500000">
**场景封装（预训练）**
- Benchmark：分析 RoboArane 分布并初始化
- 评定标准：RoboArane 三维数据 + LLM分析
- 分析模板：RoboArane 报告维度
 // 后训练 by 场景自定义 Benchmark、标准与模板
</column>
</grid>



### 1.3 Quanta 评测业务流程

<whiteboard token="S2APwdto6hgRHfbkbIYcGqUcnmg"></whiteboard>



### 1.4 核心设定/决策点

<table><colgroup><col/><col/></colgroup><thead><tr><th>决策点</th><th>结论与原因说明</th></tr></thead><tbody><tr><td><b>Quanta 评测模块目标场景</b><br/>一个平台同时支持预训练和后训练，兼顾两种场景评测需求<ul><li>模型层：预训练 ✅，后训练 ✅</li><li>应用层：Agent ❓（暂时不考虑）</li></ul></td><td></td></tr><tr><td><b>提示词管理</b><br/><b>决策点一：场景丰富性问题 </b><b>[已确认]</b><br/>方案选择<ul><li>尽可能丰富物料库和场景库，增加排列组合的可能性 ✅</li><li>仿真（短期不考虑 or 战略层面长期不采用该方案） ❌</li><li>真众包  ❌</li></ul><br/><b>决策点二：提示词维护与选择方式 </b><b>[已确认]</b><br/>方案选择<ul><li>【前置维护，任务创建人指定】提前维护维护固定提示词库，任务创建环节，创建人手动指定<ul><li>提示词库更新方式<ul><li>手动维护提示词库 ✅</li><li>定期爬取 RoboArena Benchmark，LLM生成提示词草稿，审阅后进入提示词库</li></ul></li></ul></li><li>【前置维护，LLM匹配】提前维护维护固定提示词库，评测环节，LLM 根据评测目标实时匹配</li><li>【LLM实时生成】评测环节，LLM 实时生成提示词 -&gt; 评测员调整采纳-&gt; 开始评测 ❌<ul><li>前置维护场景和物料素材包 + 评测目标 + 格式规则</li><li>评测环节，根据以上信息与任务目标，LLM 实时生成提示词</li><li>评测员调整采纳后开始测评</li></ul></li><li>【评测员实时创建】评测环节，评测员随机创建提示词 -&gt; 规则校验 -&gt; 开始评测 ❌</li></ul><br/><b>决策点三：提示词格式、评估维度（偏好选择/结果打分/标注）与评定标准 </b><b>[已确认]</b><br/>提示词格式<ul><li>仅highlevel</li><li>1 highlevel + N lowlevel ✅</li></ul><br/>评估维度<ul><li>Highlevel 级别</li><li>Lowlevel 级别 ✅</li></ul><br/>评定标准<ul><li>RoboArena：进度分[0.0-1.0] + 二元偏好（左，右，平局）+ 文字说明 ✅</li></ul></td><td></td></tr><tr><td><b>评测执行</b><br/><b>决策点一：模型分组方式 </b><b>[已确认]</b><br/>方案选择<ul><li>手动分配：任务管理员创建任务时，手动选择（一个测试任务多个 ckpt）-&gt; 评测员直接执行 ✅</li><li>自动分组（默认两个一组）：评测员开始评测时，实时请求策略对分配 -&gt; RoboArena 策略-优先采样「排名最不确定」的策略对 ❌</li></ul><br/><b>决策点二：</b><b>数据采集与评测分开</b><b> </b><b>[已确认]</b><ol><li seq="1">原因：<ol><li seq="1">系统边界：采集端和平台侧系统边界更清晰</li><li>评测客观性：不感知模型评测更客观</li><li>数据通用性：数据集（数据结构）和具体场景解藕，后续可考虑<ol><li seq="1">存量数据集直接评测</li><li>存量数据集和现采数据集对比评测</li><li>复用采集的质检等功能，保证评测数据质量</li></ol></li><li>操作可行性：操作效率、数据工厂分工等</li></ol></li><li>局限性补偿：缺第三视角<ol><li seq="1">RoboArena 评测 Franka 设备，影响还好</li><li>后续涉及本体移动的任务，补充第三视角</li></ol></li></ol><br/><b>决策点三：数据流转说明 </b><b>[已确认]</b><whiteboard token="QdeqwLXRFhL2KIb1NYncYhPgnAc"></whiteboard><br/><b>决策点：评测数据配对问题</b><b>[已确认]</b><ul><li><b>情况一：两组 checkpoint 采集次数不一致</b></li><li>原因：<ul><li>[目前]，规定采集次数均为 30，实际采集时，操作员可能多采</li><li>[长期]，同 Benchmark 的两个数据集对比，数据量不一致很正常</li><li>[长期]，采集次数一致，质检过滤后数量不一致很正常</li></ul></li><li><b>情况二：一次采集，一个 highlevel 下，lowlevel 数量不一致</b></li><li>原因：一个模型因前序推理失败，阻塞后续任务执行，所以 lowlevel 数量不一致</li></ul><br/><b>处理方式：</b><ul><li>就多原则：将次数较少的组随机重复 n 条，使两者一致❌</li><li>就少原则：从次数较多的组中抽样，使两者一致 ✅</li><li>笛卡尔乘积（量有点太大了）❌</li></ul></td><td></td></tr></tbody></table>



## 二、用户故事

| 角色 | 用户故事 | 故事详情 |
|-|-|-|
|  |  |  |
|  |  |  |



## 三、功能与迭代计划

### 3.1 里程碑

<whiteboard token="Lp7YwI3vihNCBWbzTxJc6667n0g"></whiteboard>



### 3.2 功能清单

<table><colgroup><col/><col/><col/><col/><col/></colgroup><thead><tr><th><b>模块</b></th><th>功能</th><th>功能说明</th><th>优先级</th><th>迭代版本</th></tr></thead><tbody><tr><td rowspan="2"><b>【采集端】</b></td><td>本体类型</td><td>支持选择 Franka 设备</td><td>P0</td><td>MVP</td></tr><tr><td>云端推理</td><td>支持云端推理</td><td>P0</td><td>MVP</td></tr><tr><td rowspan="3"><b>评测任务管理</b></td><td>任务状态管理</td><td>任务状态机及其可用操作</td><td>P0</td><td>MVP</td></tr><tr><td rowspan="2">评测任务分配</td><td>评测员管理与手动任务分配</td><td>P2</td><td></td></tr><tr><td>评测员排班与自动分配机制</td><td>P3</td><td></td></tr><tr><td><b>新建评测任务</b></td><td>新建评测任务</td><td>选择 checkpoint +banchmark，组装为一个完整评测任务，同时配置设备要求、评测优先级、次数等核心信息<ul><li>checkpoint：一个任务支持选择多个 ckpt 横测</li></ul></td><td>P0</td><td>MVP</td></tr><tr><td><b>数据采集</b></td><td>拆分采集任务</td><td>将评测任务 by checkpoint 拆分为 测试数据采集任务<br/>短期复用当前采集功能，长期再优化</td><td>P0</td><td>MVP</td></tr><tr><td rowspan="4"><b>评测执行</b></td><td>评测工作台</td><td>展示双盲视频/操作结果，标注员按评分规则逐维度打分</td><td>P0</td><td>MVP</td></tr><tr><td rowspan="2">评测模式</td><td>偏好选择：根据对比型评定标准打分（进度分+ A/B/Tie 偏好选择 + 文字解释）</td><td>P0</td><td>MVP</td></tr><tr><td>量表评分：根据量表型评定标准打分</td><td>P1</td><td>V2</td></tr><tr><td>评分数据存储</td><td>偏好编码兼容 RoboArena（A=2, Tie=1, B=0）</td><td>P0</td><td>MVP</td></tr><tr><td><b>数据处理</b></td><td>数据处理</td><td>进度分处理 1-100 -&gt; 0.0-1.0<br/>文字解释中译英</td><td>P0</td><td>MVP</td></tr><tr><td rowspan="5"><b>结果分析与排行</b></td><td>多维分析报告</td><td>按评分规则的维度聚合得分，输出多维分析报告</td><td>P0</td><td>MVP</td></tr><tr><td>策略对比报告</td><td>选择多个策略，逐维度对比得分差异，定位优劣势</td><td>P1</td><td>V3</td></tr><tr><td>趋势分析</td><td>同一模型跨版本的排名和维度得分变化趋势</td><td>P2</td><td></td></tr><tr><td>排名计算</td><td>实现 Bradley-Terry with Davidson Ties 排名</td><td>P0</td><td>MVP</td></tr><tr><td>Task-Aware Ranking</td><td>实现 EM 算法，分离模型能力与任务难度，更精确的排名</td><td>P3</td><td></td></tr><tr><td><b>质量检测</b></td><td>评测质检</td><td>对评测结果进行质检/抽检</td><td>P4</td><td></td></tr><tr><td colspan="5">以下为依赖模块新增/迭代 ⬇️</td></tr><tr><td rowspan="4"><b>模型管理</b></td><td>模型流转</td><td>模型训练完毕自动转换下发到机器人，从训练完成到可测试时间小于 1 h</td><td>P1</td><td>V2</td></tr><tr><td>模型准备</td><td>通过脚本对ckpt进行merge、trt处理；简化人工操作和加速模推理速度</td><td>P1</td><td>V2</td></tr><tr><td>模型部署</td><td>支持本地部署 &amp; 云端部署<ul><li>本地部署 机器配置 需要支持模型的循环加载，对显存和内存要求较高；需要评估 thor 可以支持部署几个模型</li><li>云端部署 端侧调用模型API进行推理 延迟较高，模型推理表现会比较卡顿</li></ul></td><td>P1</td><td>V2</td></tr><tr><td>版本与血缘管理</td><td>支持模型版本与血缘管理，供后续分析对比</td><td>P2</td><td></td></tr><tr><td rowspan="2"><b>Benchmark 管理</b></td><td rowspan="2">Benchmark 管理</td><td>支持配置 Benchmark，组合提示词与评定标准</td><td>P0</td><td>MVP</td></tr><tr><td>Benchmark 增加场景，并在 [场景 x 提示词] 维度设置难度分</td><td>P1</td><td>V2</td></tr><tr><td><b>场景管理</b></td><td>场景管理</td><td>支持配置场景布置要求，配置相关图片视频参考</td><td>P1</td><td>V2</td></tr><tr><td rowspan="2"><b>提示词管理</b></td><td>提示词 CRUD</td><td>提示词的增删改查，支持格式化输入<ul><li>一组提示词：1 high_level_prompt + N low_level_prompt</li></ul></td><td>P1</td><td>V2</td></tr><tr><td>提示词版本</td><td>支持提示词版本管理</td><td>P2</td><td></td></tr><tr><td rowspan="5"><b>评定标准管理</b></td><td>评定标准CRUD</td><td>持自定义评定标准（类型、名称、描述、量表配置等）</td><td>P1</td><td>V2</td></tr><tr><td rowspan="2">评定标准类型</td><td>支持对比型评定标准：预置 RoboArena 进度分+偏好+解释</td><td>P0</td><td>MVP</td></tr><tr><td>支持量表型评定标准：每个维度可配置量表刻度（0-2 / 0-5 / 0-10）和对应的标注指南文本</td><td>P1</td><td>V2</td></tr><tr><td>维度权重配置</td><td>为同一规则内的不同维度设置权重，用于加权聚合得分</td><td>P2</td><td></td></tr><tr><td>版本管理</td><td>评定标准支持版本迭代，历史版本不可变，新版本可基于旧版本派生</td><td>P3</td><td></td></tr><tr><td><b>分析模板管理</b></td><td>分析模板CRUD</td><td>定义报告结构：指标、聚合方式、图表类型等</td><td>P2</td><td></td></tr><tr><td rowspan="3"><b>标签管理</b></td><td>统一标签管理</td><td>跨模块的标签 CRUD，支持层级标签（eg 类型/能力/场景/难度）</td><td>P2</td><td></td></tr><tr><td>标签标注</td><td>benchmark、数据集、提示词、评定标准、分析模版等，支持标签标注</td><td>P2</td><td></td></tr><tr><td>资源匹配建议</td><td>创建benchmark时，基于标签推荐兼容的提示词、评分规则、分析模板</td><td>P3</td><td></td></tr></tbody></table>

参考文档：<cite doc-id="G03JwCJjhiGGAZkwGnPcsZaynYg" file-type="wiki" title="模型测评--基模方向需求" type="doc"></cite>



## 四、需求详情

### 4.1 原型地址

<bookmark name="评测任务管理 - Quanta 评测平台" href="https://quanta-eval-platform.onrender.com/tasks"></bookmark>



### 4.1 评测模块 

**功能详情**

<table><colgroup><col/><col/><col/></colgroup><thead><tr><th></th><th>图示</th><th>说明</th></tr></thead><tbody><tr><td><b>评测任务管理</b><b>【Quanta】</b></td><td><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Y2RlMmM2YmRmMDllY2I4YWE2OGQwZTMzZGE5YTAzMGVfM2MyMzA0NzEyYjU1YjJkNmE3OTBhNDQyMTAwZTJiMjJfSUQ6NzY2MzAzOTM1NDQxNjM4NTI5OV8xNzg0MTkwNzkxOjE3ODQxOTQzOTFfVjM" mime="image/png" scale="1.000000" src="V108b1g1GocW5txLRzQcegmNnMb"/></td><td><b>任务状态与操作</b><whiteboard token="XNgpwxBWQhzIVcbDJB7c5lPVnGg"></whiteboard><br/><b>页面交互</b><ul><li>列表字段：ID、名称、Benchmark、Checkpoint、启用、状态、采集进度、评测进度、优先级、创建人、创建时间</li><li>筛选条件：ID、名称、Benchmark、Checkpoint、状态、优先级</li><li>列操作：<ul><li>详情-查看评测任务详情；</li><li>查看数据-跳转至结果记录列表并筛选当前任务；</li><li>删除、暂停、分析：见上文状态机</li></ul></li></ul></td></tr><tr><td rowspan="2"><b>评测结果记录</b><b>【Quanta】</b></td><td><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZTdiYjc4ZDQ5MzY0MjM3YzE1MzU0MzZmMzkxNTE4NzRfNjBhNWU2OTFiMGUyNzBkMGFkYTk5MjMzMjFhZDc5MGRfSUQ6NzY2MzAzOTM1Nzg4MzkxMTQzNV8xNzg0MTkwNzkxOjE3ODQxOTQzOTFfVjM" mime="image/png" scale="1.000000" src="L3O8bwp3ZolaA9x2ejkcpTyDnSb"/><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZmY5M2JjYTMyMzdiZTQwYWQ1NmYyNDI5NjM0OWNjNWVfM2JlNWRiMWJiYWM4MTk2YTQyNTA0ZTM4YjYzZjgxMDlfSUQ6NzY2MzAzOTM1MzkwOTAzODI4NV8xNzg0MTkwNzkxOjE3ODQxOTQzOTFfVjM" mime="image/png" scale="1.000000" src="FbLXbR7T8o9MWUxWwwicSe9nnCh"/></td><td><b>评测结果列表页</b><br/><b>视角切换：</b>支持切换任务视角与 ckpt 视角<ul><li>任务视角：任务 ID、任务名称、HL、LL、A模型、B模型、评测结果、A 进度分、B进度分</li><li>ckpt视角：任务 ID、任务名称、HL、LL、Checkpoint、比较结果、比较对手</li></ul></td></tr><tr><td><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NzhiZDY2ZWUzMjczZTE0Zjc0ZjdlNzllOTJmYmUzOWVfNGMzNzEwNWQxNGM2OGE5MDk1OGNlYjhjNjI4ZGYzOTJfSUQ6NzY2MzAzOTM1NTYwMjkxNDU0Nl8xNzg0MTkwNzkxOjE3ODQxOTQzOTFfVjM" mime="image/png" scale="1.000000" src="Abz6brJaEo8bKCxc7ccctwkBn1c"/></td><td><b>评测结果详情页</b><br/>评测页面的只读态</td></tr><tr><td><b>评测任务创建</b><br/><b>【Quanta】</b></td><td><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Mjc3MmViNjdiOTU0N2Y3OTgyYWZlMTU1ODA2YTIxMGZfY2IyYTFmZDEzNjlmZTcwOTJlNGEwZDUxMjU2NDAxYjhfSUQ6NzY2MzAzOTM1NjIyNzY4NTY2N18xNzg0MTkwNzkxOjE3ODQxOTQzOTFfVjM" mime="image/png" scale="1.000000" src="FmBgbL0ZVoy4WkxktAXcqHr7nDb"/></td><td><b>页面交互</b>：相较于已有测试任务新增/变更字段<ul><li>评测本体：枚举，必填，选项「Moz，Franka」</li><li>Checkpoint：枚举，必填，支持多选</li><li>部署方式：枚举，必填，选项「本地部署，云端部署」</li><li>Benchmark：单选，必填</li></ul></td></tr><tr><td><b>生成测试数据采集任务</b><br/><b>【Quanta】</b></td><td><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YjM3ZmQ4NDcyNGMwMjZlOWZkZmE0ZWQzYWJiNjA0MzhfYjcyMzgyM2I5ZmZkMjBiZDkyMTg4NjI3YWE4ZThmNmNfSUQ6NzY2MzAzOTM1NTgwMDAzMDQ0N18xNzg0MTkwNzkxOjE3ODQxOTQzOTFfVjM" mime="image/png" scale="1.000000" src="DticbGtVfovNZdxyzqdc7klZnsg"/><br/>IV<img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YWFmNTRlYzhkYTlhMDg3YTljZjVmZWM0YTcxYmU3NjZfZDUxMGQ3NTIyMTAyNDA0MDIyZDU5ZGIyZWYzMDIyY2FfSUQ6NzY2MzAzOTM1NDc5NzAzNDc3NV8xNzg0MTkwNzkxOjE3ODQxOTQzOTFfVjM" mime="image/png" scale="1.000000" src="UgaYb4jfWoxacyxkTtMcM3kun5d"/></td><td><b>业务流程</b><whiteboard token="Ynlqw15cfhQeuIbYeQYcXpvYnib"></whiteboard><br/><b>实体关系</b><whiteboard token="Vg6YwlsU0h5yVvbq1xScZp0lnvf"></whiteboard><br/>【本期复用】将评测任务 by checkpoint 拆分，生成一条测试任务，落到当前采集需求管理模块。字段映射<ul><li>当前测试任务模块调整：新增字段「本体类型：moz、Franka」</li><li>数据映射处理：评定标准，成功/失败各一即可</li></ul><callout emoji="📍"><p><b>评测任务 </b><b>[不等于]</b><b> 测试采集任务 原因：</b></p><p>后续支持多个 checkpoint「现采数据对比评估、现采数据&amp;存量数据对比评估、存量数据对比评估」等场景</p><p>所以评测任务与测试采集任务分离，有一个拆包动作是合适的</p></callout></td></tr><tr><td rowspan="2"><b>数据采集</b><br/><b>【采集端】</b></td><td><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZTlhNmNhYWVlNWIyN2VjY2IxOWRhZjI0ZmY0ZWU1YzRfOTcwODRjMTcxOWMyYTUzZWNiY2Q0MmE1MTRmMTVkZTFfSUQ6NzY2MzAzOTM1NTgwMDAxNDA2M18xNzg0MTkwNzkxOjE3ODQxOTQzOTFfVjM" mime="image/png" scale="1.000000" src="EzhwbhZpEoM7kVxf5r9crAIdnng"/></td><td><b>设备：</b>根据测试任务中的「本体类型，支持连接 moz、Franka」<br/><b>部署：</b>支持云端部署、云端推理<br/><b>模式组合与支持要求</b><ul><li>一组 checkpoint - moz - 云端推理 [暂不需要]</li><li>一组 checkpoint - Franka - 云端推理 [支持]</li><li>一组 checkpoint - moz - 本地推理 [支持]</li><li>一组 checkpoint - Franka - 本地推理 [暂不需要]</li></ul></td></tr><tr><td><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OTY5MDNmMzZiYTYxZWZmMGQ1YTZhOGEzNDBhNDcxMDNfZWQ5MGFlNDg2Y2Y3MzM1ZDZkNjA1NDlhMzcxMzY1NmZfSUQ6NzY2MzAzOTM1NDEwOTg0MDY3NV8xNzg0MTkwNzkxOjE3ODQxOTQzOTFfVjM" mime="image/png" scale="1.000000" src="B091bSI1WoogB0x0WX9c2psnncg"/></td><td><whiteboard token="Pg1DwBPN3hznD4bQEQUc3cIZnSf"></whiteboard><br/><b>采集流程：</b>[Test 类型] 在现有流程基础上，区分异常原因并做针对性处理<ul><li>长时间推理：推理长时间不结束，支持手动终止</li><li>失败处理<ul><li>推理原因失败：本条失败，后续是否执行，采集员决定（判断是否连续任务）</li><li>非推理原因失败：选择重置本条或者重置全部，重新执行（采集员决定重置范围，同样判断是否连续任务）</li></ul></li></ul><br/><b>状态与操作按钮</b><ul><li><b>行按钮</b></li></ul><ol><li seq="1">未执行 → 显示「执行」按钮 [已有]</li><li>执行中 → 执行按钮 loading [已有]</li><li>执行完 → 「成功并下一条」「成功」「失败」三选一按钮  [已有]</li><li>选择后 → 成功标签+修正按钮 or 失败标签+重置按钮+修正按钮 [新增]</li><li>重置后 → 回到未执行状态，显示「执行」按钮 [新增]</li></ol><ul><li><b>全局按钮</b></li></ul><ol><li seq="1">停止：手动停止执行和推理 [已有]</li><li>重置：重置整组数据 [已有]</li><li>复位：伺服复位 [已有]</li></ol><br/><b>采集界面：</b>摄像头分布、本体上电/控制操作，按照 Franka 设备调整（后续补充详细设计）</td></tr><tr><td><b>执行评测</b><br/><b>【Quanta】</b></td><td><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YmVhNmI1MjUzZDg1OTZhODcxM2U5MGMzMDU2ZmY4NzNfN2U0ZjM4NmY3MWNhYzNlMTdlZTdlYzU2YTZiYjhhMzRfSUQ6NzY2MzAzOTM1NTEyOTEwNTcwOF8xNzg0MTkwNzkxOjE3ODQxOTQzOTFfVjM" mime="image/png" scale="1.000000" src="PpLybp3fsoTk0Lx4NnncG8PenVg"/><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZWRkZmE1M2MxNDlkYmZmNDgxYTQ2YjE1MDBmNDA3ZmJfMWM5MDVhMDRiYjdjOWJmNTAwY2U0OTQzMzYwYWMwOGNfSUQ6NzY2MzAzOTM1NjU2NzMyNTk4M18xNzg0MTkwNzkxOjE3ODQxOTQzOTFfVjM" mime="image/png" scale="1.000000" src="ZOdGbyMcMoAiFXxRqdUcrG9xnQh"/></td><td><b>评测流程</b><whiteboard token="Bu5QwQfaLhXshkbiMoAcp1SKnbc"></whiteboard><ul><li><b>状态判断：</b>创建任务后，关联测试数据采集任务，采集完成后，任务状态从<b>「采集中」</b>切换至<b>「评测中」</b>，可以开始评测</li><li><b>数据准备：</b>对采集到的数据进行预处理</li></ul><ol><li seq="1">两个 checkpoint 最终采集次数不一致 —— 将次数较少的组随机重复 n 条，使条数和次数多的一致</li></ol><br/><b>页面交互</b><ul><li>评测工作台列表<ul><li>列表字段：任务 ID、Bbenchmark、进度、优先级，除进度外均支持筛选</li></ul></li><li>评测工作台详情：所有 lowlevel 拍平评测<ul><li>顶部区域：展示 HL x LL 的提示词，以及当前任务下，所有lowlevel 进度</li><li>视频区域：默认展示主摄，支持展开腕摄，记住选择，切换任务仍保留</li><li>评分区域：进度分（0-100），文字说明，偏好选择，均必填，提交校验</li><li>操作：支持“提交并下一条”，“返回上一条”，可修改结果。最后一条提交，则任务全部完成。</li></ul></li></ul></td></tr><tr><td><b>数据处理</b><br/><b>【Quanta】</b></td><td>/</td><td><b>处理时机</b><ul><li>定时触发：每天 2:00</li><li>手动触发：评测完成的任务，管理员手动点「分析」按钮</li></ul><br/><b>处理内容</b><ul><li>进度分：打分时[1-5]，需转化为[0.0, 1.0]，用于 Task-Aware 排名算法输入</li><li>评价文本：中译英，英译中</li><li>结果报告：LLM 处理，lowlevel 级别。提示词参考</li></ul><pre caption="&#xA;" lang="JSON"><code></code></pre><ul><li>排行榜：分数计算落库，并更新排行</li></ul></td></tr><tr><td><b>排行榜</b><br/><b>【Quanta】</b></td><td><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MTRhZTI5OWQ0MjQxN2IyM2I3NzI1MDBjYzQ1OTI2NzVfZTRlYWI4NzIxZjVlNWRkNTE5Yzg4YmY5ODMyNjI0YmNfSUQ6NzY2MzAzOTM2MTQ1ODI0NDg5OV8xNzg0MTkwNzkxOjE3ODQxOTQzOTFfVjM" mime="image/png" scale="1.000000" src="CKEmbkqfiox9L1xxB1dcAVtMnqh"/></td><td><b>分数计算</b><ul><li><b>【决策点】</b>计算维度：<ul><li>所有 lowlevel 拍平计算 ✅</li><li>Lowlevel 先按照 highlevel 聚合，再计算</li></ul></li><li>得分：Bradley-Terry with Davidson Ties，参考文档<cite doc-id="HozFws0Q3itflkky0gvctboInzb" file-type="wiki" title="RoboArena评分体系逆向工程报告.docx" type="doc"></cite></li><li>SD 标准差：衡量模型表现的波动</li><li>SE 标准误：衡量分数的可靠性</li><li>胜率以及对应场次统计</li></ul><br/><b>页面交互</b><ul><li>模型榜单-查看-跳转至结果记录列表并筛选当前模型</li><li>支持切换图表</li></ul></td></tr><tr><td><b>多维分析</b><br/><b>【Quanta】</b></td><td><img name="image.png" href="https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OGFlZWVkMjhiODFiNDYwYmVlMzIyOTc5OWRkYTcwYjhfNzJiMjk3YjViMDQzYmM2NDU4YmNhYzUyMjUxZTlmMWJfSUQ6NzY2MzAzOTM2NDEwNDQyNDYyOV8xNzg0MTkwNzkxOjE3ODQxOTQzOTFfVjM" mime="image/png" scale="1.000000" src="REWBbOv5yo727ZxhYNTcPhW9n6U"/></td><td>支持选择 checkpoint 查看分析结果（默认展示前5名）<br/>图表按需，根据模型训练所需的数据洞察维度展示，如：标签雷达图、能力短板雷达图、得分趋势图、模型对战矩阵、Low Level 胜率热力图 等</td></tr></tbody></table>



### 4.2 依赖模块（非 MVP 内容，先忽略）

<table><colgroup><col/><col/><col/></colgroup><thead><tr><th></th><th>图示</th><th>说明</th></tr></thead><tbody><tr><td><b>Checkpoint管理</b></td><td></td><td></td></tr><tr><td><b>场景管理</b></td><td></td><td></td></tr><tr><td><b>提示词管理</b></td><td></td><td></td></tr><tr><td><b>评价标准管理</b></td><td></td><td><b>标准内容</b><ul><li>基本信息：<ul><li>标识、名称、描述</li><li>类型：成功失败、量表评分、偏好选择、基线对照（类型对应不同的交互界面和底层数据存储结构）</li></ul></li><li>表单信息<ul><li>类型（必填）：不同类型数据结构不同（参考下文结构）</li><li>量表（可选）：每种类型都可以附一个量表</li><li>备注（可选）：每种类型都可以增加备注信息</li></ul></li></ul><br/>// 备注与量表长文本的区别：备注跨模型填写一份；量表表单项，每个模型分别填写；<br/><b>数据结构（供参考）</b><pre caption="&#xA;" lang="JSON"><code>整体数据结构<br/>{<br/>  "criterion_id": "string",<br/>  "criterion_name": "string",<br/>  "criterion_type": "pass_fail | preference | baseline | scale",<br/>  "criterion_description": "string",<br/><br/>  "form": {<br/>    // 类型模块：items 的结构由 criterion_type 决定，见下方四种 item 定义<br/>    "type_module": {<br/>      "items": []<br/>    },<br/><br/>    // 量表模块：独立于类型模块，可选，任何类型都可附带<br/>    "scale_module": {<br/>      "items": []<br/>    },<br/><br/>    // 备注模块：富文本，可选<br/>    "note": "string | null"<br/>  }<br/>}<br/><br/>四种 item 结构<br/>// pass_fail item<br/>{ "prompt": "string", "model": "string", "result": "success | fail" }<br/><br/>// preference item<br/>{ "prompt": "string", "winner": "string | null", "is_tie": false }<br/><br/>// baseline item<br/>{ "prompt": "string", "result": "win | lose | tie" }<br/><br/>// scale item<br/>{ "prompt": "string", "model": "string", "metric_name": "string", "metric_description": "string", "score_range": { "min": 0, "max": 0 }, "value": null }</code></pre><br/><b>MVP 预置数据 —— RoboArena 评价标准</b><pre caption="&#xA;" lang="Markdown"><code>基本信息<br/>- 标准名称：RoboArena 标准<br/>- 标准类型：偏好选择<br/>- 标准描述：<br/><br/>标准表单<br/>- 类型：哪方更优/平局的选择结果<br/>- 量表：进度分[1-5]<br/>- 备注：文字说明</code></pre></td></tr><tr><td><b>Benchmark管理</b></td><td></td><td></td></tr><tr><td><b>标签管理</b></td><td></td><td></td></tr></tbody></table>





---







## 评审记录

<table><colgroup><col/><col/><col/><col/></colgroup><thead><tr><th>时间</th><th>类型</th><th>目标</th><th>会议记录</th></tr></thead><tbody><tr><td>4.14</td><td>概要评审</td><td>对齐核心决策点</td><td>评测场景与优先级<ul><li>Quanta 平台，Moz 设备，评测自己的模型 [高优]</li><li>Quanta 平台，Franka 设备，评测自己的模型 [高优]</li><li>Quanta 平台，Franka 设备，评测 RoboArena 的模型</li></ul><br/>Benchmark 管理：benchmark 通常包含数据集、场景、提示词、评价标准，[提示词 x 场景] 维度设置难度分</td></tr><tr><td>4.17</td><td>产品评审</td><td>产品方案评审</td><td>评测打分：1-5 分，平局可细分为 [都好、都差]</td></tr><tr><td></td><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td></tr></tbody></table>







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



### 平台架构迭代方向

<whiteboard token="YsJPwUXfEhksqcbwrrLc2HW5n5g"></whiteboard>





### RoboArena 用户故事

<table><colgroup><col/><col/><col/></colgroup><thead><tr><th>角色</th><th>用户故事</th><th>故事详情</th></tr></thead><tbody><tr><td>模型开发者</td><td>首次提交模型</td><td><b>场景</b>：团队刚训练好一个新版本的 VLA 模型，想让它进入平台评测池。<br/><b>流程</b>：<ol><li seq="1"><b>部署推理服务器</b>：开发者在自己的服务器上部署模型推理服务（论文原文："users host their own policies when submitting them"）。平台不要求开发者上传模型权重，只需要暴露一个远程推理接口——这对闭源模型尤其重要，权重始终留在开发者自己的服务器上。</li><li><b>提交接入信息</b>：通过平台的 Web Portal 提交推理服务器的接入信息（API Endpoint 或 IP 地址），并填写模型的基本元数据（名称、版本、开源/闭源、所属机构）。</li><li><b>格式合规检查</b>：平台自动验证推理服务器是否符合标准接口协议（Observation → Action），检查输入输出格式是否一致。这一步是自动化的，通常在几分钟内完成。</li><li><b>安全测试（Safety Gate）</b>：合规检查通过后，模型进入「测试环境」。一名经过专项训练的评测者会操作真实机器人，在可快速人工干预的条件下对模型进行试运行（论文原文："run said policy in a 'test environment' with a specifically trained evaluator that is able to quickly intervene if a policy runs the danger of acting unsafely"）。这一步类似自动驾驶测试中的「安全员」机制，目的是确认模型不会产生危险动作，而非评判性能好坏。</li><li><b>进入评测池</b>：安全测试通过后，模型被正式加入常规评测池（论文原文："we add it to the regular pool and assign it to evaluators"），开始被随机分配给评测者进行配对比较。</li><li><b>初始信用配额</b>：新模型入池后，开发者获得一定的初始免费评测配额（由赞助机构提供的基础预算支撑），可立即触发若干次评测。</li></ol></td></tr><tr><td></td><td>持续追踪模型表现</td><td><b>场景</b>：模型已入池，开发者想了解它的评测进展和能力短板。<br/><b>流程</b>：<ol><li seq="1"><b>查看实时排名</b>：登录 Web Portal，在「我的模型」页面查看当前 ELO 分数、全局排名和分项排名（7 大能力维度各自的得分）。排名每日更新，ELO 分数随每次配对结果动态调整。</li><li><b>查阅能力剖面报告</b>：平台自动生成能力雷达图，展示模型在感知/空间理解/具身推理/导航/任务执行等维度的相对强弱。开发者可以据此判断下一步训练应重点补强哪个方向。</li><li><b>查看失败案例</b>：报告中会引用具体的失败视频片段，并附上 LLM 自动提取的失败原因标签（如「抓取位姿偏差」、「多步骤任务中途中断」等）。开发者可以直接回溯到真实评测录像。</li><li><b>跨版本回归分析</b>：提交新版本模型后，平台支持将新旧版本的能力剖面叠加对比，直观看出改进点和退步点。</li></ol></td></tr><tr><td></td><td>主动请求更多评测（信用消费）</td><td><b>场景</b>：模型入池后自然积累的评测数量不够，开发者想加速获得更多数据。<br/><b>流程</b>：<ol><li seq="1"><b>查看信用余额</b>：在账户页面确认当前持有的信用点数量。信用点来源有两个：平台赠送的初始配额，以及通过自己的评测者贡献所赚取的信用（见评测者故事）。</li><li><b>兑换评测配额</b>：每消耗一个信用点，可请求一次「自己的模型 vs 池中随机策略」的配对评测（论文原文："evaluators earn one credit...which they can use to request the same number of paired comparisons of their own policy against other policies in the pool"）。</li><li><b>指定评测范围（可选）</b>：高级选项中，开发者可以指定希望与哪类策略配对（如仅对比同量级的开源模型），或指定希望覆盖的能力维度（如重点测试导航能力）。</li><li><b>等待评测完成</b>：任务进入调度队列，按优先级（信用等级、当前排名不确定度）分配给在线评测者。开发者可在后台实时看到评测进度。</li></ol></td></tr><tr><td></td><td>申请私密评测（闭源模型）</td><td><b>场景</b>：某商业公司不希望自己的模型出现在公开排行榜，但需要内部基准数据。<br/><b>流程</b>：<ol><li seq="1">提交时选择「私密模式」，模型不出现在公开排行榜，评测结果仅对提交方账户可见。</li><li>私密模式下同样走安全测试流程，保证平台整体安全性。</li><li>评测费用以付费订阅或信用点支付（无法通过赞助机构的免费配额使用）。</li></ol></td></tr><tr><td>评测者</td><td>首次加入评测者网络</td><td><b>场景</b>：某高校实验室有一台 DROID 机器人，想加入平台成为评测贡献者。<br/><b>流程</b>：<ol><li seq="1"><b>设备注册</b>：在 Web Portal 注册账户，提交机器人硬件信息（型号、传感器配置、所在机构）。平台记录设备能力，判断可承接的任务类型。</li><li><b>安装客户端</b>：下载并安装评测客户端脚本，配置与本地机器人控制系统（ROS2）的连接。客户端负责处理与云端服务器的所有通信，本地无需任何推理算力（论文原文："no client-side inference compute required"）。</li><li><b>新手引导评测</b>：首次参与时，平台分配一组引导任务，帮助评测者熟悉操作流程、了解评分标准，并由平台工作人员异步审核其首次提交的评测质量。</li></ol></td></tr><tr><td></td><td>执行一次完整评测</td><td><b>场景</b>：评测者想在今天下午完成几次评测，赚取信用点。<br/><b>流程</b>：<br/><b>第一步：申请任务</b><ul><li>打开客户端，点击「申请评测对」。</li><li>客户端向中央调度服务发送请求，服务器从评测池中随机采样两个策略，返回各自推理服务器的 IP 地址（论文原文："we simply provide them with the IP addresses of remotely hosted evaluation servers"）。评测者看不到任何关于策略身份的信息——没有名称、没有机构、没有版本号。</li></ul><br/><b>第二步：布置场景</b><ul><li>评测者自主决定在哪里测、测什么任务：推着机器人到厨房台面，摆上几个物体，心里构思一个任务（如「把蓝色杯子移到砧板上」）。</li><li>关键约束：同一轮评测中，策略 A 和策略 B 必须在尽可能相同的初始场景下被测试——相同的物体摆放、相同的机器人起始位姿。这是保证配对公平性的核心要求。</li></ul><br/><b>第三步：输入任务指令</b><ul><li>在客户端界面输入自然语言任务描述（如 "move the blue cup onto the cutting board"）。</li><li>这条指令会被原封不动地传给两个策略的推理服务器。</li></ul><br/><b>第四步：执行策略 A</b><ul><li>客户端自动连接策略 A 的推理服务器，开始发送机器人当前观测（摄像头画面、关节状态等），服务器返回动作指令，机器人执行。</li><li>评测者全程在旁监护，若机器人出现危险动作立即按急停（安全责任在评测者）。</li><li>客户端自动录制多视角视频，记录完整的观测-动作轨迹。</li><li>任务完成或超时后停止，评测者在客户端输入<b>进度分（0–100）</b>：0 表示完全没有任何进展，100 表示完美完成任务。</li></ul><br/><b>第五步：重置场景，执行策略 B</b><ul><li>将场景恢复到与策略 A 测试前尽可能相同的初始状态（物体复位、机器人归位）。</li><li>重复第四步流程，对策略 B 完成同样的任务，记录进度分。</li></ul><br/><b>第六步：提交配对结果</b><ul><li>在客户端填写最终反馈： <ul><li><b>配对偏好</b>：A 明显更好 / B 明显更好 / 基本相当</li><li><b>自然语言说明</b>：简要描述两者的差异点（如「A 在抓取阶段位姿估计更准，B 在靠近物体时有碰撞」）</li></ul></li><li>点击提交，客户端将视频、轨迹数据、评分一并上传至中央服务器。</li></ul><br/><b>第七步：信用结算</b><ul><li>提交成功后，账户自动到账 1 个信用点（论文原文："for each paired policy evaluation, the evaluator earns one credit"）。</li><li>若平台质量检测系统判定此次评测质量较高（评分一致性好、视频清晰、说明详细），可获得信用乘数加成。</li></ul></td></tr><tr><td></td><td>离线环境下的评测</td><td><b>场景</b>：评测者在网络不稳定的环境（如机器人实验场地）进行评测。<br/><b>流程</b>：<ol><li seq="1">评测执行过程中网络中断，客户端自动切换为离线缓存模式，将视频和数据保存到本地。</li><li>网络恢复后，客户端后台自动同步所有缓存数据，无需评测者手动操作。</li><li>信用在数据同步完成并通过质量检测后到账。</li></ol></td></tr><tr><td></td><td>用信用兑换自己模型的评测</td><td><b>场景</b>：评测者同时也是模型开发者，想用赚来的信用为自己的模型加速评测。<br/><b>流程</b>：<ol><li seq="1">切换到「模型管理」页面，选择目标模型和希望对比的策略范围。</li><li>每消耗 1 个信用点，发起 1 次配对评测请求，加入调度队列。</li><li>信用闭环完成：贡献评测资源 → 赚取信用 → 换取自身评测 → 获得排名和报告 → 改进模型 → 再次提交。</li></ol></td></tr><tr><td>排行榜访问者</td><td>查阅排行榜做决策参考</td><td><b>场景</b>：某机器人公司产品团队想了解当前 VLA 模型的能力水平，作为技术路线选型依据。<br/><b>流程</b>：<ol><li seq="1">无需注册，直接访问公开排行榜页面。</li><li>按需筛选：开源模型榜 / 全部模型榜；按能力维度排序（如只看「任务执行」维度最强的模型）；按任务类型筛选（操作任务 / 导航 / EQA）。</li><li>点击具体模型，查看其能力雷达图、评测视频样本、历史 ELO 趋势曲线。</li><li>横向对比感兴趣的几个模型，导出对比报告。</li></ol></td></tr><tr><td>平台管理员</td><td>审核新模型入池</td><td><b>场景</b>：有开发者提交了一个新模型，需要通过安全测试才能入池。<br/><b>流程</b>：<ol><li seq="1">系统自动完成接口格式合规检查，通过后推送给管理员审核队列。</li><li>管理员指派一名「安全测试评测者」（经过专项训练，懂得识别危险动作并快速急停）。</li><li>安全测试评测者在隔离测试环境中运行模型：先用低风险任务试探，逐步测试是否存在不可控的动作输出。</li><li>管理员根据测试报告决定：通过（加入正式池）/ 条件通过（限制任务类型）/ 拒绝（通知开发者整改）。</li></ol></td></tr><tr><td></td><td>处理异常评测数据</td><td><b>场景</b>：质量检测系统标记了一批可疑评测结果，疑似存在刷分行为。<br/><b>流程</b>：<ol><li seq="1">系统自动检测异常模式（如同一评测者对某模型持续给出异常高分、评测时间异常短、视频画面异常静止等），生成可疑报告推送给管理员。</li><li>管理员人工复核视频录像，判断是否存在违规。</li><li>若确认异常：撤销相关评测结果，对该评测者账号发出警告或封禁，触发排名重新计算。</li><li>争议处理：开发者可对评测结果提出仲裁申请，管理员调取审计日志进行裁决。</li></ol></td></tr><tr><td></td><td>VLM 场景标注的人工校验</td><td><b>场景</b>：VLM 自动分类的场景/任务标签出现错误率上升。<br/><b>流程</b>：<ol><li seq="1">管理员定期抽样检查 VLM 标注结果与人工标注的一致性。</li><li>若准确率低于阈值（目标 ≥ 95%），触发模型迭代：收集错误样本、微调 VLM 分类器、重新验证。</li><li>历史数据可根据新分类器结果批量重新标注，保持排行榜数据的一致性。</li></ol></td></tr></tbody></table>



### RoboArena 与 Embodied Arena 比较分析
