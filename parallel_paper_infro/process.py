import os

from utils import client, load_md, load_chapters_from_directory
from classify import classify_paper_by_chapters
from parallel import summarize_papers_chapters_parallel

def process_paper_task(task_config):
    """
    处理单个论文评估任务
    
    Args:
        task_config: 任务配置字典，包含以下键:
            - task_id: 任务ID
            - source_path: 源文件夹路径
            - excellent_paths: 优秀论文路径
            - warning_paths: 警告论文路径列表
            - predict_paths: 待预测论文路径
    """
    task_id = task_config.get("task_id", "未命名任务")
    print(f"\n===== 开始处理任务: {task_id} =====\n")
    
    # === 加载论文章节 ===
    # 检查路径是文件还是目录
    excellent_paths = task_config["excellent_paths"]
    excellent_chapters_list = []
    
    for excellent_path in excellent_paths:
        if os.path.isdir(excellent_path):
            # 如果是目录，加载所有章节
            chapters = load_chapters_from_directory(excellent_path)
            if chapters:
                excellent_chapters_list.append(chapters)
                print(f"[{task_id}] 成功从目录加载优秀论文章节: {len(chapters)}个")
        else:
            # 如果是单个文件，作为一个章节处理
            try:
                content = load_md(excellent_path)
                excellent_chapters_list.append([("完整论文", content)])
                print(f"[{task_id}] 成功加载优秀论文作为单个章节")
            except Exception as e:
                print(f"[{task_id}] 加载优秀论文失败: {excellent_path}, 错误: {str(e)}")    
    
    # 合并所有优秀论文章节
    if excellent_chapters_list:
        # 将所有优秀论文的章节合并为一个列表
        excellent_chapters = []
        for i, chapters in enumerate(excellent_chapters_list):
            for j, (chapter_name, content) in enumerate(chapters):
                excellent_chapters.append((f"优秀论文{i+1}_{chapter_name}", content))
        print(f"[{task_id}] 成功合并 {len(excellent_chapters_list)} 个优秀级别论文的章节，共 {len(excellent_chapters)} 个章节")
    else:
        print(f"[{task_id}] 警告: 未能加载任何优秀级别论文章节!")
        return
    
    # 加载警告级别的论文章节
    warning_paths = task_config["warning_paths"]
    warning_chapters_list = []
    
    for warning_path in warning_paths:
        if os.path.isdir(warning_path):
            # 如果是目录，加载所有章节
            chapters = load_chapters_from_directory(warning_path)
            if chapters:
                warning_chapters_list.append(chapters)
                print(f"[{task_id}] 成功从目录加载警告论文章节: {len(chapters)}个")
        else:
            # 如果是单个文件，作为一个章节处理
            try:
                content = load_md(warning_path)
                warning_chapters_list.append([("完整论文", content)])
                print(f"[{task_id}] 成功加载警告论文作为单个章节")
            except Exception as e:
                print(f"[{task_id}] 加载警告论文失败: {warning_path}, 错误: {str(e)}")


    # 合并所有警告论文章节
    if warning_chapters_list:
        # 将所有警告论文的章节合并为一个列表
        warning_chapters = []
        for i, chapters in enumerate(warning_chapters_list):
            for j, (chapter_name, content) in enumerate(chapters):
                warning_chapters.append((f"警告论文{i+1}_{chapter_name}", content))
        print(f"[{task_id}] 成功合并 {len(warning_chapters_list)} 个警告级别论文的章节，共 {len(warning_chapters)} 个章节")
    else:
        print(f"[{task_id}] 警告: 未能加载任何警告级别论文章节!")
        return
    
    # 加载待预测论文章节
    predict_path = task_config["predict_path"]
    if os.path.isdir(predict_path):
        # 如果是目录，加载所有章节
        predict_chapters = load_chapters_from_directory(predict_path)
        print(f"[{task_id}] 成功从目录加载待预测论文章节: {len(predict_chapters)}个")
    else:
        # 如果是单个文件，作为一个章节处理
        try:
            content = load_md(predict_path)
            predict_chapters = [("完整论文", content)]
            print(f"[{task_id}] 成功加载待预测论文作为单个章节")
        except Exception as e:
            print(f"[{task_id}] 加载待预测论文失败: {str(e)}")
            return

    # === 检查是否存在已保存的摘要 ===
    summaries_dir = os.path.join("output", "summaries")
    os.makedirs(summaries_dir, exist_ok=True)
    folder_name = os.path.basename(os.path.normpath(task_config["source_path"]))
    excellent_summary_path = os.path.join(summaries_dir, f"{folder_name}_excellent_final_summary.txt")
    warning_summary_path = os.path.join(summaries_dir, f"{folder_name}_warning_final_summary.txt")

    summary_excellent = None
    summary_warning = None
    
    # 尝试加载已有的摘要
    if os.path.exists(excellent_summary_path):
        try:
            with open(excellent_summary_path, 'r', encoding='utf-8') as f:
                summary_excellent = f.read()
            print(f"[{task_id}] 成功加载已有的优秀论文摘要")
        except Exception as e:
            print(f"[{task_id}] 加载优秀论文摘要失败: {str(e)}")
            summary_excellent = None
    
    if os.path.exists(warning_summary_path):
        try:
            with open(warning_summary_path, 'r', encoding='utf-8') as f:
                summary_warning = f.read()
            print(f"[{task_id}] 成功加载已有的警告论文摘要")
        except Exception as e:
            print(f"[{task_id}] 加载警告论文摘要失败: {str(e)}")
            summary_warning = None
    
    # 如果摘要不存在，则生成并保存
    if summary_excellent is None or summary_warning is None:
        print(f"[{task_id}] 开始并行处理论文章节摘要...")
        
        summaries = summarize_papers_chapters_parallel({ # 摘要生成
            f"excellent": excellent_chapters,
            f"warning": warning_chapters
        })
        
        summary_excellent = summaries.get(f"excellent")
        summary_warning = summaries.get(f"warning")
        
        # 保存摘要以便后续使用
        if summary_excellent:
            with open(excellent_summary_path, 'w', encoding='utf-8') as f:
                f.write(summary_excellent)
            print(f"[{task_id}] 已保存优秀论文摘要到 {excellent_summary_path}")
        
        if summary_warning:
            with open(warning_summary_path, 'w', encoding='utf-8') as f:
                f.write(summary_warning)
            print(f"[{task_id}] 已保存警告论文摘要到 {warning_summary_path}")
    

    # === 启动最终分类流程 ===
    overall_judgement = classify_paper_by_chapters(predict_chapters, summary_excellent, summary_warning, task_id)
    print(f"[{task_id}] {overall_judgement}")

    # 保存LLM回复结果到文件
    output_dir = f"output/results/{task_id}"
    os.makedirs(output_dir, exist_ok=True)
    paper_name = os.path.basename(os.path.dirname(predict_path) if os.path.isdir(predict_path) else predict_path).replace(".md", "")
    output_file = os.path.join(output_dir, f"{paper_name}_result.txt")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(overall_judgement)
        
    print(f"[{task_id}] 结果已保存到: {output_file}")
    print(f"\n===== 完成任务: {task_id} =====\n")

def get_paper_paths(source_folder):
    """
    从源文件夹中提取论文路径
    
    Args:
        source_folder: 源文件夹路径
        
    Returns:
        字典，包含excellent_paths, warning_paths和predict_paths
    """
    paper_paths = {
        "excellent_paths": [],
        "warning_paths": [],
        "predict_paths": []
    }
    
    # 获取优秀论文路径
    excellent_dir = os.path.join(source_folder, "excellent paper")
    if os.path.exists(excellent_dir):
        # 获取所有子文件夹
        excellent_subdirs = [os.path.join(excellent_dir, d) for d in os.listdir(excellent_dir) 
                            if os.path.isdir(os.path.join(excellent_dir, d))]
        paper_paths["excellent_paths"] = excellent_subdirs
        print(f"找到 {len(excellent_subdirs)} 个优秀级别论文路径")
    
    # 获取警告级别论文路径
    poor_dir = os.path.join(source_folder, "poor paper")
    if os.path.exists(poor_dir):
        # 获取所有子文件夹
        poor_subdirs = [os.path.join(poor_dir, d) for d in os.listdir(poor_dir) 
                       if os.path.isdir(os.path.join(poor_dir, d))]
        paper_paths["warning_paths"] = poor_subdirs
        print(f"找到 {len(poor_subdirs)} 个警告级别论文路径")
    
    # 获取待预测论文路径
    tbd_dir = os.path.join(source_folder, "TBD")
    if os.path.exists(tbd_dir):
        # 获取所有子文件夹
        tbd_subdirs = [os.path.join(tbd_dir, d) for d in os.listdir(tbd_dir) 
                      if os.path.isdir(os.path.join(tbd_dir, d))]
        paper_paths["predict_paths"] = tbd_subdirs
        print(f"找到 {len(tbd_subdirs)} 个待测论文路径")
        for path in tbd_subdirs:
            print(f"找到待预测论文路径: {path}")
    
    return paper_paths