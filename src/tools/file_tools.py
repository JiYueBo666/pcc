from langchain.tools import tool
from pydantic import BaseModel,Field
import pathlib
from pathlib import Path
import os

@tool('read_file')
def _read_file(path: str) -> str:
    """
    读取本地文件内容。
    支持相对路径和绝对路径，但会被限制在允许的基础目录内。
    
    Args:
        path: 要读取的文件路径（相对或绝对）
    """
    ALLOWED_BASE_DIR = Path(os.getcwd()).resolve()
    # 1. 基础校验
    if not isinstance(path, str):
        return "错误：路径必须是字符串"
    
    try:
        # 2. 转换为 Path 对象并规范化
        # resolve() 会处理相对路径中的 ".." 和 "."，并将其转换为绝对路径
        # 例如 "./data/../config.txt" 会被解析为 "/path/to/project/config.txt"
        target_path = Path(path).resolve()
        
        # 3. 安全检查：防止路径穿越攻击
        # 确保解析后的绝对路径仍然在允许的基础目录下
        try:
            target_path.relative_to(ALLOWED_BASE_DIR)
        except ValueError:
            return f"错误：拒绝访问路径 '{path}'。访问被限制在项目目录内。"

        # 4. 检查文件是否存在
        if not target_path.exists():
            return f"错误：文件 '{path}' 不存在"
        
        # 5. 检查是否为文件（而不是目录）
        if not target_path.is_file():
            return f"错误：'{path}' 不是一个文件"

        # 6. 读取文件内容
        # 指定 encoding='utf-8' 防止中文乱码，errors='replace' 防止特殊字符报错
        return target_path.read_text(encoding='utf-8', errors='replace')

    except Exception as e:
        # 捕获所有其他未知异常，返回给 Agent
        return f"读取文件时发生未知错误: {str(e)}"
    
