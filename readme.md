# Local Memory Tool

一个工程化的本地文本记忆管理工具，用于持久化存储和管理对话会话记忆。

## 功能特性

- ✅ **会话记忆管理**：支持按会话ID管理对话记忆
- ✅ **角色区分**：支持user、system、assistant三种角色
- ✅ **持久化存储**：基于JSONL格式的本地文件存储
- ✅ **自动清理**：支持单个会话最大消息数限制，自动清理旧消息
- ✅ **命令行接口**：简洁易用的CLI命令行工具
- ✅ **日志记录**：完善的日志系统，支持文件和控制台输出

## 安装
### 安装步骤

1. 克隆仓库：
```bash
git clone <repository-url>
cd local_memory_tool
```

2. 安装依赖：
```bash
pip install -e .
```

3. （可选）配置环境变量

创建`.env`文件（可选）：
```env
MEMORY_STORAGE_DIR=./data/memories
LOG_LEVEL=INFO
MAX_MESSAGES_PER_SESSION=1000
```

## 使用方法

### 命令行工具

安装完成后，可以使用`memory-tool`命令：

#### 1. 添加记忆

```bash
# 添加一条新记忆
memory-tool add --content "这是一条测试记忆" --session-id "abc123" --role user

# 使用简写参数
memory-tool add -c "系统提示词" -s "abc123" -r system
```

参数说明：
- `--content, -c`：记忆内容（必需）
- `--session-id, -s`：会话ID（默认自动生成8位）
- `--role, -r`：角色，可选值：user/system（默认user）

#### 2. 查询记忆

```bash
# 查询指定会话的所有记忆
memory-tool list --session-id "abc123"
```

#### 3. 删除记忆

```bash
# 删除指定会话的所有记忆
memory-tool delete --session-id "abc123" --all

# 删除包含特定内容的记忆
memory-tool delete --session-id "abc123" --content "要删除的内容"
```

### Python API使用

```python
from src.memory_manager import MemoryManager

# 初始化管理器
mm = MemoryManager()

# 添加记忆
memory = mm.add_memory(
    content="这是一条记忆",
    session_id="abc123",
    role="user"
)

# 获取记忆
for mem in mm.get_memories("abc123"):
    print(f"{mem.role}: {mem.content}")

# 删除记忆
mm.delete_memories(
    session_id="abc123",
    delete_all=True  # 或指定 content 参数删除特定内容
)
```

## 项目结构

```
local_memory_tool/
├── data/
│   └── memories/          # 记忆存储目录
├── logs/                  # 日志文件目录
├── src/
│   ├── cli.py            # 命令行接口
│   ├── config.py         # 配置管理
│   └── memory_manager.py # 核心记忆管理
├── pyproject.toml        # 项目配置
└── readme.md             # 项目文档
```

## 配置说明

支持通过环境变量或`.env`文件配置：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| MEMORY_STORAGE_DIR | ./data/memories | 记忆存储目录 |
| LOG_LEVEL | INFO | 日志级别 |
| MAX_MESSAGES_PER_SESSION | 1000 | 单个会话最大消息数 |

## 数据存储格式

记忆以JSONL格式存储，每行一个记忆项：

```json
{
  "content": "记忆内容",
  "session_id": "会话ID",
  "role": "user",
  "created_at": "2024-01-01T00:00:00+00:00"
}
```

## 开发

### 依赖包

- python-dotenv：环境变量配置
- typing-extensions：类型注解兼容
- loguru：日志管理

## 许可证

MIT License
