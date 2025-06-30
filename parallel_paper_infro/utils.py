import json

from multipart import file_path
from openai import OpenAI
import os

# === 初始化 ===
client = OpenAI(
    api_key="sk-5245b39f98014ee8a7a44dbbf4db1d46",  # 替换为你的 key
    base_url="https://api.deepseek.com"
)

def load_md(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def load_chapters_from_directory(directory_path):
    """
    从目录中加载所有章节文件
    
    Args:
        directory_path: 章节文件所在的目录路径
        
    Returns:
        章节列表，每个元素为(章节名, 章节内容， description)的元组
    """
    chapters = []
    
    try:
        # 检查目录是否存在
        if not os.path.exists(directory_path):
            print(f"❌ 目录不存在: {directory_path}")
            return []
            
        # 检查是否有同名子文件夹（例如 BY1701171/BY1701171/）
        dir_name = os.path.basename(directory_path)
        sub_dir_path = os.path.join(directory_path, dir_name)
        description_path = os.path.join(sub_dir_path, "chapter_info.json")
        # 如果存在同名子文件夹，则从子文件夹中读取章节文件
        if os.path.exists(sub_dir_path) and os.path.isdir(sub_dir_path):
            print(f"📂 找到章节子文件夹: {sub_dir_path}")
            chapter_dir = sub_dir_path
        else:
            # 否则使用原始目录
            chapter_dir = directory_path
            
        # 获取目录中的所有文件
        files = [f for f in os.listdir(chapter_dir) if f.endswith('.md')]
        
        # 按文件名排序，确保章节顺序正确
        files.sort()

        chapter_info = []
        if os.path.exists(description_path):
            with open(description_path, 'r', encoding='utf-8') as desc_file:
                chapter_info = json.load(desc_file)
                print(f"  📄 成功加载章节描述: {description_path}")
        else:
            print(f"  ⚠️ 未找到章节描述文件: {description_path}, 使用空描述")

        for chapter in chapter_info:
            file_path = chapter.get("file_path")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 使用文件名作为章节名（去掉.md后缀）
                    chapter_name = chapter.get("safe_title")
                    chapters.append((chapter_name, content, chapter.get("description", "chapter")))
                    print(f"  ✅ 成功加载章节: {chapter_name}")
            except Exception as e:
                print(f"  ❌ 加载章节文件失败: {file_path}, 错误: {str(e)}")
        
        return chapters
    except Exception as e:
        print(f"读取目录失败: {directory_path}, 错误: {str(e)}")
        return []


# 添加一个函数来分割过长的章节内容
def chunk_long_chapter(chapter_content, max_tokens=128000):
    """
    将过长的章节内容分割成多个小块
    
    Args:
        chapter_content: 章节内容
        max_tokens: 每个块的最大token数（粗略估计，按平均每个字符1.5个token计算）
        
    Returns:
        分割后的内容块列表
    """
    # 粗略估计token数量（中文每个字约1.5个token）
    estimated_tokens = len(chapter_content) * 1.5
    
    if estimated_tokens <= max_tokens:
        return [chapter_content]
    
    # 计算需要分割的块数
    num_chunks = int(estimated_tokens / max_tokens) + 1
    # 每块的字符数
    chars_per_chunk = len(chapter_content) // num_chunks
    
    chunks = []
    for i in range(0, len(chapter_content), chars_per_chunk):
        chunk = chapter_content[i:i+chars_per_chunk]
        chunks.append(chunk)
    
    print(f"  ⚠️ 章节内容过长，已分割为 {len(chunks)} 个块进行处理")
    return chunks