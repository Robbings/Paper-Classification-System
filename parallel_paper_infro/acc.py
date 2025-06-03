import os
import pandas as pd
import random

# 获取文件夹中的所有论文目录
def get_paper_directories(base_dir):
    """
    获取指定目录下的所有论文目录
    
    Args:
        base_dir: 基础目录路径
        
    Returns:
        论文目录列表
    """
    if not os.path.exists(base_dir):
        print(f"❌ 目录不存在: {base_dir}")
        return []
        
    # 获取所有子目录（每个子目录代表一篇论文）
    paper_dirs = []
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path):
            paper_dirs.append(item_path)
    
    return paper_dirs

# 划分示例论文和待测论文
def split_papers(excellent_dir, poor_dir, sample_ratio=1/3):
    """
    将论文分为示例论文和待测论文
    
    Args:
        excellent_dir: 优秀论文目录
        poor_dir: 风险论文目录
        sample_ratio: 示例论文比例
        
    Returns:
        (excellent_samples, excellent_test, poor_samples, poor_test): 示例和待测论文目录列表
    """
    # 获取所有论文目录
    excellent_papers = get_paper_directories(excellent_dir)
    poor_papers = get_paper_directories(poor_dir)
    
    # 随机打乱顺序
    random.shuffle(excellent_papers)
    random.shuffle(poor_papers)
    
    # 计算示例论文数量
    excellent_sample_count = max(1, int(len(excellent_papers) * sample_ratio))
    poor_sample_count = max(1, int(len(poor_papers) * sample_ratio))
    
    # 划分示例论文和待测论文
    excellent_samples = excellent_papers[:excellent_sample_count]
    excellent_test = excellent_papers[excellent_sample_count:]
    
    poor_samples = poor_papers[:poor_sample_count]
    poor_test = poor_papers[poor_sample_count:]
    
    print(f"优秀论文: 共{len(excellent_papers)}篇，示例{len(excellent_samples)}篇，待测{len(excellent_test)}篇")
    print(f"风险论文: 共{len(poor_papers)}篇，示例{len(poor_samples)}篇，待测{len(poor_test)}篇")
    
    return excellent_samples, excellent_test, poor_samples, poor_test

# 创建任务配置
def create_task_configs(source_folder, excellent_samples, poor_samples, test_papers):
    """
    创建任务配置列表
    
    Args:
        excellent_samples: 优秀示例论文目录列表
        poor_samples: 风险示例论文目录列表
        test_papers: 待测论文目录列表
        
    Returns:
        任务配置列表
    """
    task_configs = []
    
    for i, test_paper in enumerate(test_papers):
        paper_name = os.path.basename(test_paper)
        task_config = {
            "task_id": f"测试_{paper_name}",
            "source_path": source_folder,
            "excellent_paths": excellent_samples,
            "warning_paths": poor_samples,
            "predict_path": test_paper
        }
        task_configs.append(task_config)
    
    return task_configs

# 解析分类结果
def parse_classification_result(result_text):
    """
    解析分类结果文本，提取评价档次
    
    Args:
        result_text: 分类结果文本
        
    Returns:
        评价档次: "优", "良", "中", "差" 或 None
    """
    try:
        # 查找评价档次行
        for line in result_text.split('\n'):
            if "评价档次：" in line:
                # 提取评价档次
                parts = line.split("：")
                if len(parts) > 1:
                    grade = parts[1].strip()
                    # 提取中括号中的内容
                    if "[" in grade and "]" in grade:
                        grade = grade[grade.find("[")+1:grade.find("]")]
                    return grade
        
        # 如果没有找到明确的评价档次，尝试查找关键词
        if "优" in result_text[:200]:
            return "优"
        elif "良" in result_text[:200]:
            return "良"
        elif "中" in result_text[:200]:
            return "中"
        elif "差" in result_text[:200]:
            return "差"
        
        return None
    except Exception as e:
        print(f"解析分类结果出错: {str(e)}")
        return None

# 计算分类准确率
def calculate_accuracy(results, excellent_test, poor_test):
    """
    计算分类准确率
    
    Args:
        results: 分类结果字典，键为论文路径，值为分类结果
        excellent_test: 优秀待测论文目录列表
        poor_test: 风险待测论文目录列表
        
    Returns:
        准确率统计信息
    """
    # 初始化计数器
    total = 0
    correct = 0
    excellent_correct = 0
    excellent_total = 0
    poor_correct = 0
    poor_total = 0
    
    # 创建结果表格数据
    table_data = []
    
    # 检查优秀论文分类结果
    for paper_dir in excellent_test:
        paper_name = os.path.basename(paper_dir)
        result = results.get(paper_dir)
        
        if result:
            total += 1
            excellent_total += 1
            
            # 优秀论文应该被分类为"优"或"良"
            is_correct = result in ["优秀论文"]
            if is_correct:
                correct += 1
                excellent_correct += 1
            
            table_data.append({
                "论文名称": paper_name,
                "真实类别": "优秀",
                "预测类别": result,
                "是否正确": "✓" if is_correct else "✗"
            })
    
    # 检查风险论文分类结果
    for paper_dir in poor_test:
        paper_name = os.path.basename(paper_dir)
        result = results.get(paper_dir)
        
        if result:
            total += 1
            poor_total += 1
            
            # 风险论文应该被分类为"中"或"差"
            is_correct = result in ["风险论文"]
            if is_correct:
                correct += 1
                poor_correct += 1
            
            table_data.append({
                "论文名称": paper_name,
                "真实类别": "风险",
                "预测类别": result,
                "是否正确": "✓" if is_correct else "✗"
            })
    
    # 计算准确率
    accuracy = correct / total if total > 0 else 0
    excellent_accuracy = excellent_correct / excellent_total if excellent_total > 0 else 0
    poor_accuracy = poor_correct / poor_total if poor_total > 0 else 0
    
    # 创建统计信息
    stats = {
        "总准确率": accuracy,
        "优秀论文准确率": excellent_accuracy,
        "风险论文准确率": poor_accuracy,
        "总样本数": total,
        "正确样本数": correct,
        "优秀论文样本数": excellent_total,
        "优秀论文正确数": excellent_correct,
        "风险论文样本数": poor_total,
        "风险论文正确数": poor_correct,
        "详细结果": table_data
    }
    
    return stats

# 保存准确率结果
def save_accuracy_results(stats, output_dir="output/accuracy"):
    """
    保存准确率结果到文件
    
    Args:
        stats: 准确率统计信息
        output_dir: 输出目录
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存详细结果为CSV
    df = pd.DataFrame(stats["详细结果"])
    csv_path = os.path.join(output_dir, "classification_results.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    
    # 保存统计摘要为文本文件
    summary_path = os.path.join(output_dir, "accuracy_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("# 论文分类准确率统计\n\n")
        f.write(f"总准确率: {stats['总准确率']:.2%}\n")
        f.write(f"优秀论文准确率: {stats['优秀论文准确率']:.2%}\n")
        f.write(f"风险论文准确率: {stats['风险论文准确率']:.2%}\n\n")
        
        f.write("## 详细统计\n\n")
        f.write(f"总样本数: {stats['总样本数']}\n")
        f.write(f"正确样本数: {stats['正确样本数']}\n")
        f.write(f"优秀论文样本数: {stats['优秀论文样本数']}\n")
        f.write(f"优秀论文正确数: {stats['优秀论文正确数']}\n")
        f.write(f"风险论文样本数: {stats['风险论文样本数']}\n")
        f.write(f"风险论文正确数: {stats['风险论文正确数']}\n")
    
    print(f"✅ 准确率结果已保存到 {output_dir}")
    print(f"  - 详细结果: {csv_path}")
    print(f"  - 统计摘要: {summary_path}")