import argparse
import uuid
from loguru import logger
from config import config
from memory_manager import MemoryManager, MemoryItem

def main():
    """命令行交互主函数"""
    # 初始化管理器
    mm = MemoryManager()

    # 创建命令行解析器（工程化：清晰的子命令设计）
    parser = argparse.ArgumentParser(description="本地文本记忆小工具（工程化版）")
    subparsers = parser.add_subparsers(dest="command", required=True, help="可用命令")

    # 1. 添加记忆子命令
    add_parser = subparsers.add_parser("add", help="添加记忆")
    add_parser.add_argument("--content", "-c", required=True, help="记忆内容")
    add_parser.add_argument("--session-id", "-s", default=str(uuid.uuid4())[:8], help="会话ID（默认自动生成8位）")
    add_parser.add_argument("--role", "-r", default="user", choices=["user", "system"], help="角色（默认user）")

    # 2. 查询记忆子命令
    list_parser = subparsers.add_parser("list", help="查询会话记忆")
    list_parser.add_argument("--session-id", "-s", required=True, help="会话ID")

    # 3. 删除记忆子命令
    delete_parser = subparsers.add_parser("delete", help="删除记忆")
    delete_parser.add_argument("--session-id", "-s", required=True, help="会话ID")
    delete_parser.add_argument("--all", "-a", action="store_true", help="删除全部记忆")
    delete_parser.add_argument("--content", "-c", help="删除包含该内容的记忆（与--all互斥）")

    # 解析参数
    args = parser.parse_args()

    # 执行对应命令
    try:
        if args.command == "add":
            memory = mm.add_memory(args.content, args.session_id, args.role)
            print(f"\n✅ 记忆添加成功！")
            print(f"会话ID：{memory.session_id}")
            print(f"创建时间：{memory.created_at.astimezone()}")  # 转换为本地时区显示
            print(f"内容：{memory.content}")
        
        elif args.command == "list":
            memories = list(mm.get_memories(args.session_id))
            if not memories:
                print(f"\n📄 会话{args.session_id}暂无记忆")
                return
            print(f"\n📄 会话{args.session_id}共有{len(memories)}条记忆：")
            for i, mem in enumerate(memories, 1):
                print(f"\n{i}. 角色：{mem.role}")
                print(f"   时间：{mem.created_at.astimezone()}")
                print(f"   内容：{mem.content}")
        
        elif args.command == "delete":
            if args.all and args.content:
                print("❌ --all和--content不能同时使用")
                return
            success = mm.delete_memories(
                session_id=args.session_id,
                delete_all=args.all,
                content=args.content
            )
            if success:
                print(f"\n🗑️ 会话{args.session_id}记忆删除成功！")
    
    except Exception as e:
        logger.error(f"命令执行失败：{str(e)}")
        print(f"\n❌ 错误：{str(e)}")

if __name__ == "__main__":
    main()