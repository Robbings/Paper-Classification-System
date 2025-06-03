import os
import argparse
import threading
import multiprocessing
import datetime

from process import process_paper_task, get_paper_paths
from acc import split_papers, create_task_configs, parse_classification_result, calculate_accuracy, save_accuracy_results

# 论文分类准确率评估
def evaluate_paper_classification_accuracy(source_folder, excellent_dir, poor_dir, sample_ratio=1/3):
    """
    评估论文分类准确率
    
    Args:
        excellent_dir: 优秀论文目录
        poor_dir: 风险论文目录
        sample_ratio: 示例论文比例
    """
    print("\n===== 开始论文分类准确率评估 =====\n")
    
    # 1. 划分示例论文和待测论文
    excellent_samples, excellent_test, poor_samples, poor_test = split_papers(
        excellent_dir, poor_dir, sample_ratio
    )
    
    # 2. 合并所有待测论文
    all_test_papers = excellent_test + poor_test
    
    # 3. 创建任务配置
    task_configs = create_task_configs(source_folder, excellent_samples, poor_samples, all_test_papers)
    
    # 4. 处理所有任务 - 改为并行处理
    print(f"\n发现 {len(task_configs)} 个评估任务，启动并行处理...")
    
    # 限制最多处理15个任务
    task_configs = task_configs[:15]
    
    # 创建线程列表
    threads = []
    
    # 启动线程处理任务
    for task_config in task_configs:
        thread = threading.Thread(target=process_paper_task, args=(task_config,))
        threads.append(thread)
        thread.start()
        print(f"已启动任务线程: {task_config['task_id']}")
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    print("所有评估任务处理完成!")
    
    # 5. 收集处理结果
    results = {}
    for task_config in task_configs:
        # 获取结果文件路径
        paper_path = task_config["predict_path"]
        paper_name = os.path.basename(paper_path)
        result_dir = f"output/results/{task_config['task_id']}"
        
        # 尝试多种可能的结果文件名
        possible_result_files = [
            os.path.join(result_dir, f"{paper_name}_result.txt"),
            os.path.join(result_dir, "excellent paper_result.txt"),
            os.path.join(result_dir, "poor paper_result.txt")
        ]
        
        result_file = None
        for file_path in possible_result_files:
            if os.path.exists(file_path):
                result_file = file_path
                break
        
        # 读取并解析结果
        if result_file and os.path.exists(result_file):
            with open(result_file, "r", encoding="utf-8") as f:
                result_text = f.read()
            
            # 解析分类结果
            classification = parse_classification_result(result_text)
            if classification:
                results[paper_path] = classification
                print(f"  ✅ 论文 {paper_name} 分类结果: {classification}")
            else:
                print(f"  ❌ 无法解析论文 {paper_name} 的分类结果")
        else:
            print(f"  ❌ 未找到论文 {paper_name} 的结果文件，尝试过以下路径:")
            for path in possible_result_files:
                print(f"     - {path}")
    
    # 6. 计算准确率
    stats = calculate_accuracy(results, excellent_test, poor_test)
    
    # 7. 保存结果
    save_accuracy_results(stats)
    
    # 8. 打印总结
    print("\n===== 论文分类准确率评估完成 =====\n")
    print(f"总准确率: {stats['总准确率']:.2%}")
    print(f"优秀论文准确率: {stats['优秀论文准确率']:.2%}")
    print(f"风险论文准确率: {stats['风险论文准确率']:.2%}")
    print(f"详细结果已保存到 output/accuracy 目录")

# 主函数
def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="论文分类与准确率评估")
    parser.add_argument("--source", type=str, default="D:/paperClassification/data/chapter_chunk/cl - testacc", 
                        help="源文件夹路径")
    parser.add_argument("--sample_ratio", type=float, default=1/3, help="示例论文比例")
    parser.add_argument("--mode", type=str, choices=["classify", "accuracy"], default="classify", 
                        help="运行模式: classify-分类论文, accuracy-评估分类准确率")
    
    args = parser.parse_args()

    # 从源文件夹获取路径
    source_folder = args.source
    print(f"使用源文件夹: {source_folder}")
    paper_paths = get_paper_paths(source_folder)
    
    if args.mode == "accuracy":
        # 评估分类准确率
        # 从源文件夹获取优秀论文和风险论文目录
        excellent_dir = os.path.join(source_folder, "excellent paper")
        poor_dir = os.path.join(source_folder, "poor paper")
        
        # 检查目录是否存在
        if not os.path.exists(excellent_dir):
            print(f"❌ 优秀论文目录不存在: {excellent_dir}")
            return
        if not os.path.exists(poor_dir):
            print(f"❌ 风险论文目录不存在: {poor_dir}")
            return
            
        # 评估分类准确率
        evaluate_paper_classification_accuracy(source_folder, excellent_dir, poor_dir, args.sample_ratio)
    else:
        # 分类论文（多篇）
        # 创建任务列表
        tasks = []
        
        # 为每个待预测论文创建一个任务
        for i, predict_path in enumerate(paper_paths["predict_paths"]):
            folder_name = os.path.basename(predict_path)
            # 确保有优秀论文和警告论文可用
            if paper_paths["excellent_paths"] and paper_paths["warning_paths"]:
                task = {
                    "task_id": folder_name,
                    "source_path": source_folder,
                    "excellent_paths": paper_paths["excellent_paths"],  # 使用所有优秀论文
                    "warning_paths": paper_paths["warning_paths"],  # 使用所有警告论文
                    "predict_path": predict_path  # 当前待预测论文
                }
                tasks.append(task)
        
        # 检查是否有任务配置
        if len(tasks) == 0:
            print("错误: 没有找到待分类的论文")
            return
        
        # 限制最多处理15个任务
        tasks = tasks[:15]
        
        if len(tasks) == 1:
            # 只有一个任务，直接处理
            print("只有一个任务，直接处理...")
            process_paper_task(tasks[0])
        else:
            # 有多个任务，使用线程并行处理
            print(f"发现 {len(tasks)} 个任务，启动并行处理...")
            threads = []
            
            for task in tasks:
                thread = threading.Thread(target=process_paper_task, args=(task,))
                threads.append(thread)
                thread.start()
                print(f"已启动任务线程: {task['task_id']}")
            
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            
            print("所有任务处理完成!")

if __name__ == "__main__":
    # 设置多进程启动方法
    multiprocessing.set_start_method('spawn', force=True)
    main()