#渐进式agent 工程学习
# 渐进式 Agent 项目开发计划（11阶段）

本项目采用渐进式开发模式，从基础本地工具逐步迭代为全功能多Agent系统，每阶段聚焦核心能力，兼顾工程化规范与可扩展性，最终复刻完整的本地多Agent协作系统（ClawChain复刻版）。

|阶段|项目名称|核心目标|核心技术点|工程思想 / 进阶点|
|-|-|-|-|-|
|1|本地文本记忆小工具|实现「输入文本→本地存储→查询历史」的基础能力|Python 文件读写（pathlib/os）、基础数据结构（列表/字典）、简单命令行交互|理解「本地优先」的存储设计，掌握数据持久化的最小实现|
|2|FastAPI 接口化记忆工具|把阶段 1 的功能封装为 HTTP 接口，支持「新增记忆 / 查询记忆 / 删除记忆」|FastAPI 路由 / 请求体 / 响应模型、异步接口基础、接口调试（Swagger）|理解「接口化」思维，掌握前后端分离的最小接口设计|
|3|单 Agent 工具调用助手|基于 LangChain 实现「Agent 调用本地文件工具→读取文件→回答用户问题」|LangChain Agent / 工具封装、LLM 基础调用（OpenAI / 本地模型）、结构化输出|理解 Agent 核心逻辑（思考→调用工具→生成回答），掌握工具调用的封装方法|
|4|带记忆的单 Agent 助手|在阶段 3 基础上增加「会话记忆」，Agent 能记住多轮对话上下文|LangChain 记忆模块（ConversationBufferMemory）、会话状态管理|理解「记忆机制」的工程实现，掌握上下文关联的核心逻辑|
|5|多 Agent 并行协作工具|实现「主 Agent 拆分任务→多个子 Agent 并行执行→汇总结果」|Python 异步并发（asyncio）、LangGraph 基础（节点 / 边 / 状态）、任务调度|理解多 Agent 协作的「任务拆分 - 并行执行 - 结果聚合」思想|
|6|带中断 / 排队的 Agent 服务|在阶段 5 基础上增加「任务排队（busy 时）+ 手动中断任务 + 保存中间结果」|FastAPI 接口中断（abort）、任务队列（asyncio.Queue）、会话锁机制|理解「高可用」Agent 服务的工程设计，掌握并发任务的管控逻辑|
|7|本地索引增强的 Agent|为 Agent 增加「本地文件索引→关键词检索→精准召回」能力，替代全量文件读取|Python 文本索引（whoosh / 简易倒排索引）、检索算法基础、记忆召回优化|理解「检索增强」的核心思想，掌握本地数据高效检索的最小实现|
|8|命令行 + 接口双端 Agent|为阶段 7 的服务增加 CLI 命令行工具，支持「终端调用 Agent + HTTP 接口调用」|Python click/cli 框架、配置文件管理（.env）、环境变量解析|理解「多端适配」的工程思想，掌握 CLI+API 双入口的设计方法|
|9|对接前端的 Agent 服务|用 Next.js 实现极简前端页面，调用后端 Agent 接口，支持「对话 / 任务管控」|FastAPI 跨域处理、前后端数据交互（JSON）、接口鉴权（简易 Token）|理解「前后端联调」的核心流程，掌握 Web 端 Agent 服务的适配逻辑|
|10|桌面端封装的 Agent 应用|基于 Tauri 将阶段 9 的 Web 服务封装为桌面应用，支持「本地运行 + 桌面交互」|Tauri 2.0 基础、Rust 极简语法、Tauri 调用后端 API、桌面端打包|理解「跨端封装」思想，掌握「Web 内核 + 桌面壳」的工程实现|
|11|全功能 ClawChain 复刻版|整合所有阶段能力，实现「本地存储 + 多 Agent 协作 + 记忆 + 中断 + 索引 + 跨端」|全技术栈整合、源码拆解方法、工程化重构（分层设计：接口层 / 业务层 / 存储层）|理解大型 Agent 工程的「分层设计」思想，掌握从拆解到复刻的核心方法论|

### 当前进度

✅ 阶段 1：本地文本记忆小工具

✅ 阶段 2：FastAPI 接口化记忆工具

✅ 阶段 3：单个agent调用工具。（读取路径文件）

✅ 阶段 4：添加简单记忆模块。（读取对话文件，构建上下文后交给AI）

### 开发规范

* 分支管理：每个阶段对应一个功能分支（格式：`feature/阶段名称`），开发完成后合并到 main 分支
* 工程化要求：遵循「分层解耦、可配置化、异常处理、单元测试」原则，为后续扩展预留接口
* 文档要求：每个阶段完成后，补充对应功能的使用说明和核心代码注释

> （注：文档部分内容可能由 AI 生成）

## 当前推荐架构

围绕“Agent 交互”作为项目主链，建议后续都按下面这条路径扩展：

`API Router -> Service -> Repository -> File Storage / Agent Runtime`

推荐职责划分：

- `src/api/v1`
  只处理 HTTP 协议细节、请求参数、响应格式、Cookie。
- `src/api/deps.py`
  统一依赖注入，集中创建 service/repository 单例。
- `src/services`
  承担业务编排，是后续替代 `manager` 的主入口。
- `src/repositories`
  只负责数据读写，不放业务判断。
- `src/agents`
  负责 LLM、工具、消息拼装和 agent 执行。
- `src/agent`
  兼容旧导入路径，后续不要继续新增实现。
- `src/memory_manager.py` / `src/userInfo.py`
  旧阶段遗留实现，建议逐步下线，只保留兼容用途。
- `src/config.py` / `src/core/deps.py`
  兼容旧入口，正式实现分别以 `src/core/config.py`、`src/api/deps.py` 为准。

当前建议的核心调用链：

1. `POST /api/v1/agent/chat`
2. `AgentService`
3. `MemoryService`
4. `MemoryRepository`
5. `agents.AgentManager`

这样做的好处：

- `agent` 成为唯一核心入口，避免路由直接操作底层组件。
- memory、session、user 能作为独立能力复用，不和 HTTP 耦合。
- 旧 `manager` 可以平滑迁移，不需要一次性全删。

