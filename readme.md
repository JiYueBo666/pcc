# 渐进式 Agent 工程学习项目

## 项目简介

本项目采用渐进式开发模式，从基础本地工具逐步迭代为全功能多Agent系统，每阶段聚焦核心能力，兼顾工程化规范与可扩展性，最终复刻完整的本地多Agent协作系统（ClawChain复刻版）。

### 当前阶段：阶段3 - 单Agent工具调用助手

本项目已完成阶段1（本地文本记忆小工具）和阶段2（FastAPI接口化记忆工具）的开发，目前已进入阶段3（单Agent工具调用助手）。阶段3在阶段2的基础上，集成了LangChain Agent框架，实现了具备工具调用能力的AI助手，支持与用户进行对话并调用本地工具（如文件读取）。

|阶段|项目名称|核心目标|核心技术点|工程思想 / 进阶点|
|-|-|-|-|-|
|1|本地文本记忆小工具|实现「输入文本→本地存储→查询历史」的基础能力|Python 文件读写（pathlib/os）、基础数据结构（列表/字典）、简单命令行交互|理解「本地优先」的存储设计，掌握数据持久化的最小实现|
|2|FastAPI 接口化记忆工具|把阶段 1 的功能封装为 HTTP 接口，支持「新增记忆 / 查询记忆 / 删除记忆」|FastAPI 路由 / 请求体 / 响应模型、异步接口基础、接口调试（Swagger）|理解「接口化」思维，掌握前后端分离的最小接口设计|
|3|单Agent工具调用助手|实现具备工具调用能力的AI助手，支持对话和工具调用|LangChain Agent框架、LLM集成、工具系统、流式响应|理解「Agent」思维，掌握AI工具调用的最小实现|


### 当前进度

✅ 阶段 1：本地文本记忆小工具（已完成，工程化实现）

✅ 阶段 2：FastAPI 接口化记忆工具（已完成，支持RESTful API）

🔄 阶段 3：单Agent工具调用助手（进行中，已实现基础对话和工具调用功能）

## 项目功能

### 核心功能

1. **记忆管理**
   - 添加记忆：支持添加用户或系统角色的记忆内容
   - 查询记忆：按会话ID查询所有相关记忆
   - 删除记忆：支持删除全部记忆或按内容删除特定记忆

2. **数据持久化**
   - 采用JSONL格式存储记忆数据
   - 按会话ID分文件存储
   - 支持会话记忆数量限制，自动清理最早记忆

3. **双端访问**
   - CLI命令行工具：支持命令行直接操作
   - RESTful API：提供HTTP接口供其他服务调用

4. **AI Agent对话**
   - 支持与AI助手进行对话交互
   - 支持流式和非流式响应模式
   - 集成工具调用能力（目前支持文件读取工具）
   - 支持会话上下文管理

### 技术架构

```
local_memory_tool/
├── src/
│   ├── api/           # API接口层
│   │   ├── deps.py    # 依赖注入
│   │   └── v1/        # v1版本API
│   │       ├── memory.py   # 记忆管理接口
│   │       ├── user.py     # 用户管理接口
│   │       └── agent.py    # Agent对话接口
│   ├── schemas/       # 数据模型定义
│   │   ├── memory.py  # 记忆相关模型
│   │   ├── agent.py   # Agent相关模型
│   │   └── users.py   # 用户相关模型
│   ├── agent/         # Agent系统
│   │   ├── agent_manager.py  # Agent管理器
│   │   ├── llm_factory.py     # LLM工厂
│   │   ├── model_config.py    # 模型配置
│   │   └── model_selection.py # 模型选择
│   ├── tools/         # 工具系统
│   │   └── file_tools.py      # 文件工具
│   ├── config.py      # 全局配置
│   ├── main.py        # FastAPI应用入口
│   ├── cli.py         # 命令行工具
│   ├── memory_manager.py  # 核心业务逻辑
│   └── userInfo.py    # 用户会话管理
├── data/              # 数据存储目录
│   └── memories/      # 记忆数据文件
└── pyproject.toml     # 项目配置
```

## 安装与使用

### 环境要求

- Python 3.8+
- pip

### 安装步骤

1. 克隆项目
```bash
git clone <repository_url>
cd local_memory_tool
```

2. 安装依赖
```bash
pip install -e .
```

3. 配置环境变量（可选）

创建`.env`文件，配置以下参数：
```env
MEMORY_STORAGE_DIR=./data/memories  # 记忆存储目录
LOG_LEVEL=INFO                       # 日志级别
MAX_MESSAGES_PER_SESSION=1000        # 每个会话最大消息数
API_HOST=0.0.0.0                     # API服务主机
API_PORT=8000                        # API服务端口
API_DEBUG=True                       # 调试模式
CORS_ORIGINS=*                       # 跨域允许的源
# Agent配置
OPENAI_KEY=your_api_key              # OpenAI API密钥
BASE_URL=https://api.openai.com/v1   # API基础URL
TEMPERATURE=0.9                      # 温度参数
```

### 使用方法

#### 1. 命令行工具使用

添加记忆：
```bash
memory-tool add --content "这是一条测试记忆" --session-id "test123" --role user
```

查询记忆：
```bash
memory-tool list --session-id "test123"
```

删除记忆：
```bash
# 删除全部记忆
memory-tool delete --session-id "test123" --all

# 删除包含特定内容的记忆
memory-tool delete --session-id "test123" --content "测试"
```

#### 2. API接口使用

启动API服务：
```bash
python src/main.py
```

或使用uvicorn直接启动：
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

访问API文档：
启动服务后，访问 `http://localhost:8000/docs` 查看Swagger文档。

API接口示例：

- 新增记忆
```bash
curl -X POST "http://localhost:8000/api/v1/memory/" \
  -H "Content-Type: application/json" \
  -d '{"content": "这是一条测试记忆", "session_id": "test123", "role": "user"}'
```

- 查询记忆
```bash
curl "http://localhost:8000/api/v1/memory/?session_id=test123"
```

- 删除记忆
```bash
curl -X DELETE "http://localhost:8000/api/v1/memory/" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test123", "delete_all": true}'
```

- Agent对话（非流式）
```bash
curl -X POST "http://localhost:8000/api/v1/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "你好，请介绍一下自己", "session_id": "test123", "stream": false}'
```

- Agent对话（流式）
```bash
curl -X POST "http://localhost:8000/api/v1/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "请读取readme.md文件", "session_id": "test123", "stream": true}'
```

### 开发规范

* 分支管理：每个阶段对应一个功能分支（格式：`feature/阶段名称`），开发完成后合并到 main 分支
* 工程化要求：遵循「分层解耦、可配置化、异常处理、单元测试」原则，为后续扩展预留接口
* 文档要求：每个阶段完成后，补充对应功能的使用说明和核心代码注释

## 开发指南

### 代码结构说明

- **api/**: API接口层，处理HTTP请求和响应
  - **deps.py**: 依赖注入，提供全局单例
  - **v1/**: v1版本API实现
    - **memory.py**: 记忆管理接口
    - **user.py**: 用户管理接口
    - **agent.py**: Agent对话接口
- **schemas/**: 数据模型定义，使用Pydantic进行数据验证
  - **memory.py**: 记忆相关模型
  - **agent.py**: Agent相关模型
  - **users.py**: 用户相关模型
- **agent/**: Agent系统核心实现
  - **agent_manager.py**: Agent管理器，处理对话和工具调用
  - **llm_factory.py**: LLM工厂，管理LLM实例
  - **model_config.py**: 模型配置定义
  - **model_selection.py**: 模型选择逻辑
- **tools/**: 工具系统
  - **file_tools.py**: 文件工具实现
- **config.py**: 全局配置管理，支持环境变量
- **main.py**: FastAPI应用入口，配置中间件和路由
- **cli.py**: 命令行工具实现
- **memory_manager.py**: 核心业务逻辑，处理记忆的增删查
- **userInfo.py**: 用户会话管理

### 添加新功能

1. 在`schemas/`中定义请求和响应模型
2. 在`memory_manager.py`中实现业务逻辑
3. 在`api/v1/`中添加API路由
4. 更新文档和测试用例

#### 添加新工具

1. 在`src/tools/`目录下创建新的工具文件
2. 使用`@tool`装饰器定义工具函数
3. 在`agent_manager.py`的`_build_tools`方法中注册新工具
4. 更新文档说明工具用途

### 代码风格

- 遵循PEP 8规范
- 使用类型注解（Type Hints）
- 添加适当的文档字符串（Docstrings）
- 使用loguru进行日志记录

## 常见问题

### Q: 如何修改记忆存储目录？

A: 在`.env`文件中设置`MEMORY_STORAGE_DIR`环境变量，或修改`config.py`中的默认值。

### Q: API服务无法启动怎么办？

A: 检查以下几点：
1. 确认端口8000未被占用
2. 检查所有依赖是否正确安装
3. 查看日志文件`logs/memory_tool.log`获取详细错误信息

### Q: 如何扩展API接口？

A: 在`api/v1/`目录下创建新的路由文件，然后在`api/v1/__init__.py`中注册该路由。

### Q: 记忆数据可以迁移吗？

A: 记忆数据以JSONL格式存储在`data/memories/`目录下，可以直接复制这些文件到新环境。

### Q: 如何配置Agent使用的LLM模型？

A: 在`.env`文件中配置`OPENAI_KEY`、`BASE_URL`和`TEMPERATURE`参数。支持OpenAI兼容的API接口。

### Q: Agent如何调用工具？

A: Agent会根据对话内容自动判断是否需要调用工具。目前支持文件读取工具，工具调用信息会在流式响应中返回。

## 未来计划

- [🔄] 阶段3：单Agent工具调用助手（进行中）
- [ ] 阶段4：带记忆的单Agent助手
- [ ] 阶段5：多Agent并行协作工具
- [ ] 阶段6：带中断/排队的Agent服务
- [ ] 阶段7：本地索引增强的Agent
- [ ] 阶段8：命令行+接口双端Agent
- [ ] 阶段9：对接前端的Agent服务
- [ ] 阶段10：桌面端封装的Agent应用
- [ ] 阶段11：全功能ClawChain复刻版

## 许可证

本项目采用MIT许可证。

> （注：文档部分内容可能由 AI 生成）

