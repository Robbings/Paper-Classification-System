from Markdown_Spliter.markdown_parser import MarkdownParser
import os
import json
from datetime import datetime
import re
import shutil
import sys
import argparse

def is_toc_content(content):
    """
    判断内容是否为目录页
    目录页的特征：
    1. 内容较短
    2. 包含多个章节标题和页码
    3. 没有实质性的段落内容
    """
    # 检查是否包含页码模式（如"第一节...9"，"第二节...13"等）
    page_number_pattern = re.compile(r'第[一二三四五六七八九十]+[节章].+\d+$', re.MULTILINE)
    page_numbers = page_number_pattern.findall(content)
    
    # 检查内容是否较短且主要由标题和页码组成
    lines = content.strip().split('\n')
    if len(lines) < 5:  # 内容太少，可能不是完整章节
        return False
        
    # 计算包含页码的行数比例
    page_number_lines = 0
    for line in lines:
        if re.search(r'\d+$', line.strip()):
            page_number_lines += 1
    
    # 如果大部分行都包含页码，且没有长段落，可能是目录
    if page_number_lines > len(lines) * 0.5 and len(content) < 1000:
        return True
        
    # 检查是否包含典型的目录结构（如"第一节...第二节...第三节..."）
    section_count = 0
    for line in lines:
        if re.match(r'^第[一二三四五六七八九十]+[节章]', line.strip()):
            section_count += 1
    
    # 如果包含多个节标题且没有长段落，可能是目录
    if section_count >= 3 and not any(len(line.strip()) > 50 for line in lines):
        return True
        
    return False

def should_process_file(file_path):
    """
    判断文件是否需要处理
    跳过已经分割好的章节文件
    """
    # 跳过output/chapters目录下的文件
    if "output/chapters" in file_path or "output\\chapters" in file_path:
        return False
    return True

def process_md_file(file_path, output_dir):
    """
    处理单个MD文件并将结果保存到指定目录
    """
    print(f"处理文件: {file_path}...")
    
    # 创建以原文件名命名的子目录
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    file_output_dir = os.path.join(output_dir, file_name)
    
    parser = MarkdownParser.init_by_path(file_path)
    metadata = parser.get_metadata()
    parse_tree = parser.get_parse_tree()
    
    # 获取摘要部分
    abstract = parser.get_section_content(description="abstract_ch")
    
    # 提取所有章节
    chapters = []
    for node in parse_tree:
        if node.get("description") == "chapter":
            chapter_content = parser.get_section_content(exact_title=node["title"])
            
            # 检查内容是否为目录页
            if is_toc_content(chapter_content):
                print(f"跳过目录页: {node['title']}")
                continue
                
            chapters.append((node["title"], chapter_content))

    # 如果没有提取到章节，跳过创建空目录
    if not chapters and not abstract:
        print(f"未从 {file_path} 提取到任何内容，跳过")
        return None
    
    # 创建输出目录
    os.makedirs(file_output_dir, exist_ok=True)
    
    # 将各章节保存为单独的文件
    chapter_info = []
    for title, content in chapters:
        # 更强的文件名清理，移除所有可能导致问题的特殊字符
        safe_title = re.sub(r'[\\/*?:"<>|${}]', '', title)
        safe_title = safe_title.replace(" ", "_").replace("/", "_")
        # 限制文件名长度
        if len(safe_title) > 100:
            safe_title = safe_title[:100]
        
        chapter_file_path = os.path.join(file_output_dir, f"{safe_title}.md")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(chapter_file_path), exist_ok=True)
        
        try:
            with open(chapter_file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # 记录章节信息
            chapter_info.append({
                "title": title,
                "file_path": chapter_file_path,
                "content_length": len(content)
            })
        except Exception as e:
            print(f"保存章节 '{title}' 时出错: {e}")
            print(f"尝试使用的文件路径: {chapter_file_path}")

    # 保存摘要信息
    if abstract:
        abstract_path = os.path.join(file_output_dir, "abstract.md")
        with open(abstract_path, "w", encoding="utf-8") as f:
            f.write(abstract)
    
    # 保存元数据
    if metadata:
        metadata_path = os.path.join(file_output_dir, "metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)
    
    # 返回处理结果
    file_result = {
        "original_file": file_path,
        "output_directory": file_output_dir,
        "extraction_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "chapters_count": len(chapters),
        "chapters": chapter_info,
        "has_abstract": bool(abstract),
        "metadata": metadata
    }
    
    print(f"共提取了 {len(chapters)} 个章节，已保存到 {file_output_dir}")
    return file_result

def process_markdown_files(source_folder):
    """
    处理指定文件夹中的Markdown文件，按章节划分
    
    参数:
        source_folder: 源文件夹路径
    """
    print(f"使用源文件夹: {source_folder}")
    
    # 创建结果汇总信息
    extraction_results = []
    
    # 遍历源文件夹下的所有子文件夹
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                
                # 判断文件是否需要处理
                if not should_process_file(file_path):
                    print(f"跳过已分割的章节文件: {file_path}")
                    continue
                
                # 将处理结果保存到MD文件所在的同一子文件夹中
                output_dir = os.path.dirname(file_path)
                
                # 处理MD文件
                result = process_md_file(file_path, output_dir)
                if result:
                    extraction_results.append(result)
    
    # 只有在有提取结果时才保存结果汇总
    if extraction_results:
        # 保存整体提取结果到源文件夹
        results_path = os.path.join(source_folder, "extraction_results.json")
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(extraction_results, f, ensure_ascii=False, indent=4)
        
        print(f"所有提取结果已保存")
        print(f"提取结果汇总已保存到 {results_path}")
    else:
        print("未提取到任何内容，没有生成结果汇总")

if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="将Markdown文件按章节划分")
    parser.add_argument("--source", type=str, required=True, help="源文件夹路径")
    args = parser.parse_args()
    
    # 处理Markdown文件
    process_markdown_files(args.source)