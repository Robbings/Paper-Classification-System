import os
import multiprocessing
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


from summarize import summarize_chapter
from classify import process_chapter_for_classification

def process_paper_chapters_for_summary(label, chapters):
    """
    处理单个论文的多个章节并生成摘要
    
    Args:
        label: 论文标签
        chapters: 章节列表，每个元素为(章节名, 章节内容)的元组
        
    Returns:
        (label, summary): 论文标签和最终摘要
    """
    print(f"开始处理论文章节: {label}")
    
    # 创建保存中间结果的目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = os.path.join("output", "paper_summaries")
    os.makedirs(save_dir, exist_ok=True)
    
    # 处理每个章节
    summary = None
    for i, (chapter_name, chapter_content) in enumerate(chapters):
        print(f"  ⏳ 处理章节 {i+1}/{len(chapters)}: {chapter_name}")
        summary = summarize_chapter(chapter_name, chapter_content, summary, save_dir, i, label)
    
    # 保存最终摘要
    final_file = os.path.join(save_dir, f"{label}_final_summary.txt")
    with open(final_file, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"📊 已保存 {label} 的最终摘要到 {final_file}")
    
    return label, summary

# 添加并行处理函数
def summarize_papers_chapters_parallel(papers_dict):
    """
    并行处理多篇论文的章节摘要
    
    Args:
        papers_dict: 字典，键为论文标签，值为章节列表
        
    Returns:
        字典，键为论文标签，值为摘要结果
    """
    results = {}
    
    # 使用线程池并行处理（避免进程池序列化问题）
    with ThreadPoolExecutor(max_workers=min(len(papers_dict), multiprocessing.cpu_count())) as executor:
        # 提交所有任务
        future_to_label = {
            executor.submit(process_paper_chapters_for_summary, label, chapters): label 
            for label, chapters in papers_dict.items()
        }
        
        # 获取结果
        for future in as_completed(future_to_label):
            try:
                label, summary = future.result()
                results[label] = summary
                print(f"完成论文处理: {label}")
            except Exception as e:
                print(f"处理论文时出错: {str(e)}")
                # 继续处理其他任务，不让一个失败影响所有
    
    return results

def classify_chapters_parallel(chapters, summary_excellent, summary_warning, save_dir="output/classifications"):
    """
    并行对多个章节进行分类
    
    Args:
        chapters: 章节列表，每个元素为(章节名, 章节内容)的元组
        summary_excellent: 优秀论文摘要
        summary_warning: 警告级别论文摘要
        save_dir: 保存结果的目录
        
    Returns:
        字典，键为章节名，值为分类结果
    """
    results = {}
    
    # 创建保存目录
    os.makedirs(save_dir, exist_ok=True)
    
    # 使用线程池并行处理
    with ThreadPoolExecutor(max_workers=min(len(chapters), multiprocessing.cpu_count())) as executor:
        # 提交所有任务
        future_to_chapter = {
            executor.submit(
                process_chapter_for_classification, 
                i, chapter_name, chapter_content, 
                summary_excellent, summary_warning, save_dir
            ): chapter_name 
            for i, (chapter_name, chapter_content) in enumerate(chapters)
        }
        
        # 获取结果
        for future in as_completed(future_to_chapter):
            try:
                chapter_name, classification = future.result()
                results[chapter_name] = classification
                print(f"完成章节分类: {chapter_name}")
            except Exception as e:
                chapter_name = future_to_chapter[future]
                print(f"处理章节 {chapter_name} 分类时出错: {str(e)}")
                results[chapter_name] = f"处理出错: {str(e)}"
    
    return results

if __name__ == "__main__":
    from parallel_paper_infro.utils import load_chapters_from_directory, load_md

    # 示例：处理多篇论文的章节摘要
    source_folder = './paper'
    excellent_paths = os.path.join(source_folder, "excellent paper")
    excellent_chapters_list = []

    for excellent_path in excellent_paths:
        if os.path.isdir(excellent_path):
            # 如果是目录，加载所有章节
            chapters = load_chapters_from_directory(excellent_path)
            if chapters:
                excellent_chapters_list.append(chapters)
                print(f"成功从目录加载优秀论文章节: {len(chapters)}个")
        else:
            # 如果是单个文件，作为一个章节处理
            try:
                content = load_md(excellent_path)
                excellent_chapters_list.append([("完整论文", content)])
                print(f"成功加载优秀论文作为单个章节")
            except Exception as e:
                print(f"加载优秀论文失败: {excellent_path}, 错误: {str(e)}")

                # 合并所有优秀论文章节
    if excellent_chapters_list:
        # 将所有优秀论文的章节合并为一个列表
        excellent_chapters = []
        for i, chapters in enumerate(excellent_chapters_list):
            for j, (chapter_name, content) in enumerate(chapters):
                excellent_chapters.append((f"优秀论文{i + 1}_{chapter_name}", content))
        print(
            f"成功合并 {len(excellent_chapters_list)} 个优秀级别论文的章节，共 {len(excellent_chapters)} 个章节")
    else:
        print(f"警告: 未能加载任何优秀级别论文章节!")
        exit(-1)
    rst = process_paper_chapters_for_summary("优秀论文", excellent_chapters)
    print(f"最终摘要: {rst}")