import os
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import pandas as pd
from typing import Dict, Any
from utils import client, chunk_long_chapter

def classify_chapter_with_context(chapter_name, chapter_content, summary_excellent, summary_warning, chapter_index=None, save_dir=None):
    """
    对单个章节进行分类
    
    Args:
        chapter_name: 章节名称
        chapter_content: 章节内容
        summary_excellent: 优秀论文摘要
        summary_warning: 警告级别论文摘要
        chapter_index: 章节索引
        save_dir: 保存结果的目录
        
    Returns:
        分类反馈
    """
    # 检查内容长度，如果过长则分块处理
    max_chars = 60000  # 每块最大字符数
    original_length = len(chapter_content)
    
    if len(chapter_content) > max_chars:
        print(f"  ⚠️ 章节内容过长 ({original_length} 字符)，将分块处理")
        # 分块处理
        content_chunks = chunk_long_chapter(chapter_content, max_tokens=60000)
        
        # 处理每个块并收集反馈
        chunk_feedbacks = []
        for i, chunk in enumerate(content_chunks):
            print(f"  ⏳ 处理章节 '{chapter_name}' 的第 {i+1}/{len(content_chunks)} 个块")
            
            # 为每个块创建消息
            messages = [
                {"role": "system", "content": (
                    "你是一位评估研究论文质量的专家评审员。基于论文的章节内容，将其分类为以下类别之一：\n\n"
                    "- '优': 高质量的写作，清晰的问题定义，扎实且创新的方法论，合理的实验设计，以及显著的贡献。(相当于90-100分)\n"
                    "- '良': 写作清晰，问题定义合理，方法论可靠，有一定创新性，但可能在某些方面有小缺陷。(相当于80-89分)\n"
                    "- '中': 具有足够清晰度和合理方法的平均水平论文，但缺乏新颖性或深度，或存在一些明显问题。(相当于60-79分)\n"
                    "- '差': 写作不清晰，结构混乱，方法论有缺陷或浅薄，结果薄弱，或缺少评估。(相当于60分以下)\n\n"
                    "请与提供的示例进行比较。评价时应着重关注本段的不足之处，以严厉的风格进行判断，并且最终以更加严格的标准分类。\n"
                    "将评价为'优''良'的分类为优秀级别章节；将评价为'中''差'的分类为警告级别章节。回复应包含最终的章节类别以及对该章节的详细评价。\n"
                    "注意，需要用中文生成回答。"
                )},
                {"role": "user", "content": f"优秀论文摘要：\n{summary_excellent}"},
                {"role": "assistant", "content": "优"},
                {"role": "user", "content": f"警告级别论文摘要：\n{summary_warning}"},
                {"role": "assistant", "content": "差"},
                {"role": "user", "content": f"请对这篇论文的章节 '{chapter_name}' 的第 {i+1}/{len(content_chunks)} 部分进行分类和评价：\n{chunk}"}
            ]
            
            # 添加重试机制
            max_retries = 3
            retry_delay = 5  # 秒
            
            for attempt in range(max_retries):
                try:
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=messages,
                        temperature=0
                    )
                    
                    chunk_feedback = response.choices[0].message.content.strip()
                    chunk_feedbacks.append(chunk_feedback)
                    
                    # 保存分块分类结果
                    if save_dir and chapter_index is not None:
                        os.makedirs(save_dir, exist_ok=True)
                        
                        # 创建分类文件名
                        classification_file = os.path.join(save_dir, f"{chapter_name}_chunk{i+1}_classification.txt")
                        
                        # 保存分类内容
                        with open(classification_file, "w", encoding="utf-8") as f:
                            f.write(f"论文章节 '{chapter_name}' 的第 {i+1}/{len(content_chunks)} 部分:\n\n")
                            f.write("-" * 80 + "\n\n")
                            f.write(chunk[:500] + "..." if len(chunk) > 500 else chunk)  # 只保存前500个字符
                            f.write("\n\n" + "-" * 80 + "\n\n")
                            f.write(f"分类结果:\n\n")
                            f.write(chunk_feedback)
                        
                        print(f"  ✅ 已保存章节 '{chapter_name}' 的第 {i+1} 部分分类结果到 {classification_file}")
                    
                    break  # 成功获取反馈，跳出重试循环
                    
                except Exception as e:
                    error_str = str(e)
                    if "maximum context length" in error_str or "requested" in error_str and "tokens" in error_str:
                        # 如果是上下文长度错误，进一步分割内容
                        print(f"  ⚠️ 块 {i+1} 上下文长度超限，将进一步分割")
                        sub_chunks = chunk_long_chapter(chunk, max_tokens=5000)
                        sub_feedbacks = []
                        
                        for j, sub_chunk in enumerate(sub_chunks):
                            sub_messages = [
                                {"role": "system", "content": (
                                    "你是一位评估研究论文质量的专家评审员。基于论文的章节内容，将其分类为以下类别之一：\n\n"
                                    "- '优': 高质量的写作，清晰的问题定义，扎实且创新的方法论，合理的实验设计，以及显著的贡献。(相当于90-100分)\n"
                                    "- '良': 写作清晰，问题定义合理，方法论可靠，有一定创新性，但可能在某些方面有小缺陷。(相当于80-89分)\n"
                                    "- '中': 具有足够清晰度和合理方法的平均水平论文，但缺乏新颖性或深度，或存在一些明显问题。(相当于60-79分)\n"
                                    "- '差': 写作不清晰，结构混乱，方法论有缺陷或浅薄，结果薄弱，或缺少评估。(相当于60分以下)\n\n"
                                    "请与提供的示例进行比较。评价时应着重关注本段的不足之处，以严厉的风格进行判断，并且最终以更加严格的标准分类。\n"
                                    "将评价为'优''良'的分类为优秀级别章节；将评价为'中''差'的分类为警告级别章节。回复应包含最终的章节类别以及对该章节的详细评价。\n"
                                    "注意，需要用中文生成回答。"
                                )},
                                {"role": "user", "content": f"优秀论文摘要：\n{summary_excellent}"},
                                {"role": "assistant", "content": "优"},
                                {"role": "user", "content": f"警告级别论文摘要：\n{summary_warning}"},
                                {"role": "assistant", "content": "差"},
                                {"role": "user", "content": f"请对这篇论文的章节 '{chapter_name}' 的第 {i+1}.{j+1} 部分进行分类和评价：\n{sub_chunk}"}
                            ]
                            
                            try:
                                sub_response = client.chat.completions.create(
                                    model="deepseek-chat",
                                    messages=sub_messages,
                                    temperature=0
                                )
                                
                                sub_feedback = sub_response.choices[0].message.content.strip()
                                sub_feedbacks.append(sub_feedback)
                                
                            except Exception as sub_e:
                                print(f"  ❌ 处理子块 {j+1} 时出错: {str(sub_e)}")
                                sub_feedbacks.append(f"处理出错: {str(sub_e)}")
                        
                        # 整合子块反馈
                        if sub_feedbacks:
                            combined_feedback = "\n\n".join([f"部分 {j+1}:\n{fb}" for j, fb in enumerate(sub_feedbacks)])
                            chunk_feedbacks.append(combined_feedback)
                            
                            # 保存整合的分块结果
                            if save_dir and chapter_index is not None:
                                combined_file = os.path.join(save_dir, f"{chapter_name}_chunk{i+1}_combined.txt")
                                with open(combined_file, "w", encoding="utf-8") as f:
                                    f.write(f"论文章节 '{chapter_name}' 的第 {i+1} 部分 (分割处理):\n\n")
                                    f.write(combined_feedback)
                                print(f"  ✅ 已保存章节 '{chapter_name}' 的第 {i+1} 部分整合结果到 {combined_file}")
                        
                        break  # 跳出重试循环
                        
                    elif attempt < max_retries - 1:
                        print(f"  ⚠️ API调用失败，{retry_delay}秒后重试 ({attempt+1}/{max_retries}): {str(e)}")
                        import time
                        time.sleep(retry_delay)
                    else:
                        print(f"  ❌ API调用失败，已达最大重试次数: {str(e)}")
                        chunk_feedbacks.append(f"处理出错: {str(e)}")
        
        # 整合所有块的反馈
        if chunk_feedbacks:
            try:
                # 创建整合消息
                integration_messages = [
                    {"role": "system", "content": (
                        "你是一位评估研究论文质量的专家评审员。你需要基于多个部分的评价，对整个章节进行最终分类。"
                        "最终分类应为以下类别之一：\n\n"
                        "- '优': 高质量的写作，清晰的问题定义，扎实且创新的方法论，合理的实验设计，以及显著的贡献。(相当于90-100分)\n"
                        "- '良': 写作清晰，问题定义合理，方法论可靠，有一定创新性，但可能在某些方面有小缺陷。(相当于80-89分)\n"
                        "- '中': 具有足够清晰度和合理方法的平均水平论文，但缺乏新颖性或深度，或存在一些明显问题。(相当于60-79分)\n"
                        "- '差': 写作不清晰，结构混乱，方法论有缺陷或浅薄，结果薄弱，或缺少评估。(相当于60分以下)\n\n"
                        "请与提供的示例进行比较。评价时应着重关注本段的不足之处，以严厉的风格进行判断，并且最终以更加严格的标准分类。\n"
                        "将评价为'优''良'的分类为优秀级别章节；将评价为'中''差'的分类为警告级别章节。回复应包含最终的章节类别以及对该章节的详细评价。\n"
                        "注意，需要用中文生成回答，并且评价应该简洁明了。"
                    )},
                    {"role": "user", "content": f"以下是对论文章节 '{chapter_name}' 的各个部分的评价：\n\n" + 
                     "\n\n".join([f"第 {i+1} 部分评价:\n{fb}" for i, fb in enumerate(chunk_feedbacks)]) + 
                     "\n\n请综合以上评价，给出最终的分类结果和整体评价。"}
                ]
                
                integration_response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=integration_messages,
                    temperature=0
                )
                
                feedback = integration_response.choices[0].message.content.strip()
                
                # 保存最终整合结果
                if save_dir and chapter_index is not None:
                    os.makedirs(save_dir, exist_ok=True)
                    
                    # 创建分类文件名
                    classification_file = os.path.join(save_dir, f"{chapter_name}_classification.txt")
                    
                    # 保存分类内容
                    with open(classification_file, "w", encoding="utf-8") as f:
                        f.write(f"论文章节 '{chapter_name}' 整体评价:\n\n")
                        f.write("-" * 80 + "\n\n")
                        f.write(f"原始内容长度: {original_length} 字符，分为 {len(content_chunks)} 个部分处理\n\n")
                        f.write("-" * 80 + "\n\n")
                        f.write(f"最终分类结果:\n\n")
                        f.write(feedback)
                    
                    print(f"  ✅ 已保存章节 '{chapter_name}' 的最终分类结果到 {classification_file}")
                
                return feedback
                
            except Exception as e:
                print(f"  ❌ 整合评价时出错: {str(e)}")
                # 如果整合失败，返回第一个块的评价作为备选
                return chunk_feedbacks[0] if chunk_feedbacks else "无法获取分类结果"
        else:
            return "无法获取分类结果"
    else:
        # 内容不长，直接处理
        messages = [
            {"role": "system", "content": (
                "你是一位评估研究论文质量的专家评审员。基于论文的章节内容，将其分类为以下类别之一：\n\n"
                "- '优': 高质量的写作，清晰的问题定义，扎实且创新的方法论，合理的实验设计，以及显著的贡献。(相当于90-100分)\n"
                "- '良': 写作清晰，问题定义合理，方法论可靠，有一定创新性，但可能在某些方面有小缺陷。(相当于80-89分)\n"
                "- '中': 具有足够清晰度和合理方法的平均水平论文，但缺乏新颖性或深度，或存在一些明显问题。(相当于60-79分)\n"
                "- '差': 写作不清晰，结构混乱，方法论有缺陷或浅薄，结果薄弱，或缺少评估。(相当于60分以下)\n\n"
                "请与提供的示例进行比较。评价时应着重关注本段的不足之处，以严厉的风格进行判断，并且最终以更加严格的标准分类。\n"
                "将评价为'优''良'的分类为优秀级别章节；将评价为'中''差'的分类为警告级别章节。回复应包含最终的章节类别以及对该章节的详细评价。\n"
                "注意，需要用中文生成回答。"
            )},
            {"role": "user", "content": f"优秀论文摘要：\n{summary_excellent}"},
            {"role": "assistant", "content": "优"},
            {"role": "user", "content": f"警告级别论文摘要：\n{summary_warning}"},
            {"role": "assistant", "content": "差"},
            {"role": "user", "content": f"请对这篇论文的章节 '{chapter_name}' 进行分类和评价：\n{chapter_content}"}
        ]
        
        # 添加重试机制
        max_retries = 3
        retry_delay = 5  # 秒
        
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    temperature=0
                )
                
                feedback = response.choices[0].message.content.strip()
                
                # 保存分类结果
                if save_dir and chapter_index is not None:
                    os.makedirs(save_dir, exist_ok=True)
                    
                    # 创建分类文件名
                    classification_file = os.path.join(save_dir, f"{chapter_name}_classification.txt")
                    
                    # 保存分类内容
                    with open(classification_file, "w", encoding="utf-8") as f:
                        f.write(f"论文章节 '{chapter_name}':\n\n")
                        f.write("-" * 80 + "\n\n")
                        f.write(chapter_content[:500] + "..." if len(chapter_content) > 500 else chapter_content)  # 只保存前500个字符
                        f.write("\n\n" + "-" * 80 + "\n\n")
                        f.write(f"分类结果:\n\n")
                        f.write(feedback)
                    
                    print(f"  ✅ 已保存章节 '{chapter_name}' 的分类结果到 {classification_file}")
                
                return feedback
                
            except Exception as e:
                error_str = str(e)
                if "maximum context length" in error_str or "requested" in error_str and "tokens" in error_str:
                    # 如果是上下文长度错误，切换到分块处理模式
                    print(f"  ⚠️ 上下文长度超限，切换到分块处理模式")
                    # 递归调用自身，但使用分块处理模式
                    return classify_chapter_with_context(chapter_name, chapter_content, summary_excellent, summary_warning, chapter_index, save_dir)
                elif attempt < max_retries - 1:
                    print(f"  ⚠️ API调用失败，{retry_delay}秒后重试 ({attempt+1}/{max_retries}): {str(e)}")
                    import time
                    time.sleep(retry_delay)
                else:
                    print(f"  ❌ API调用失败，已达最大重试次数: {str(e)}")
                    raise
        
        return "API调用失败，无法获取分类结果"

# 并行处理论文章节分类
def process_chapter_for_classification(chapter_index, chapter_name, chapter_content, summary_excellent, summary_warning, save_dir):
    """
    处理单个论文章节的分类任务
    
    Args:
        chapter_index: 章节索引
        chapter_name: 章节名称
        chapter_content: 章节内容
        summary_excellent: 优秀论文摘要
        summary_warning: 警告级别论文摘要
        save_dir: 保存结果的目录
        
    Returns:
        (chapter_index, chapter_name, feedback): 章节索引、名称和分类反馈
    """
    print(f"🧩 处理章节 {chapter_index+1}: {chapter_name}")
    feedback = classify_chapter_with_context(chapter_name, chapter_content, summary_excellent, summary_warning, chapter_index, save_dir)
    print(f"   ➜ 反馈: {feedback[:100]}...")  # 只打印前100个字符
    return chapter_index, chapter_name, feedback

def classify_chapters_parallel(chapters, summary_excellent, summary_warning):
    """
    并行对多个论文章节进行分类
    
    Args:
        chapters: 章节列表，每个元素为(章节名, 章节内容)的元组
        summary_excellent: 优秀论文摘要
        summary_warning: 警告级别论文摘要
        
    Returns:
        分类结果列表
    """
    results = [None] * len(chapters)
    
    # 创建保存中间结果的目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = os.path.join("output", "chapter_classifications", timestamp)
    os.makedirs(save_dir, exist_ok=True)
    
    # 使用线程池而不是进程池来避免序列化问题
    with ThreadPoolExecutor(max_workers=min(len(chapters), multiprocessing.cpu_count())) as executor:
        # 提交所有任务
        future_to_index = {
            executor.submit(process_chapter_for_classification, i, chapter_name, chapter_content, 
                           summary_excellent, summary_warning, save_dir): i 
            for i, (chapter_name, chapter_content) in enumerate(chapters)
        }
        
        # 获取结果
        for future in as_completed(future_to_index):
            i, chapter_name, feedback = future.result()
            results[i] = f"章节 '{chapter_name}' 反馈: {feedback}"
    
    # 保存所有分类结果
    all_results_file = os.path.join(save_dir, "all_chapter_classifications.txt")
    with open(all_results_file, "w", encoding="utf-8") as f:
        f.write("\n\n" + "="*50 + "\n\n".join(results))
    print(f"📊 已保存所有章节分类结果到 {all_results_file}")
    
    return results

def get_metrics_info(sid: str) -> Dict[str, Any]:
    """获取论文的各项指标信息"""
    try:
        info_df = pd.read_excel('博士论文全信息汇总.xlsx')  # 全信息汇总的文件路径
        info_df = info_df[info_df['学号'] == sid]
        
        # 检查是否找到匹配的学号
        if len(info_df) == 0:
            print(f"⚠️ 未找到学号为 {sid} 的学生信息")
            # 返回空字典而非默认值
            return {}
            
        paper_count = info_df['论文数'].values[0]
        max_impact = info_df['最高影响因子'].values[0]
        zones = info_df['分区'].values[0]
        gender = info_df['性别'].values[0]
        department = info_df['院系'].values[0]
        study_type = info_df['学制'].values[0]
        training_type = info_df['培养方式'].values[0]
        proposal_grade = info_df['开题成绩'].values[0]
        fail_count = info_df['开题不及格次数'].values[0]
        proposal_time = info_df['开题时间'].values[0]
        return {
            '论文数': paper_count,
            '最高影响因子': max_impact,
            '分区分布': zones,
            '性别': gender,
            '院系': department,
            '学制': study_type,
            '培养方式': training_type,
            '开题成绩': proposal_grade,  # 对开题成绩进行了数值化处理
            '开题不及格次数': fail_count,
            '开题时间': proposal_time
        }
    except Exception as e:
        print(f"⚠️ 获取学生信息时出错: {str(e)}")
        # 出错时也返回空字典而非默认值
        return {}

def classify_paper_by_chapters(chapters, summary_excellent, summary_warning, task_id=""):
    """
    按章节对论文进行分类评估
    
    Args:
        chapters: 章节列表，每个元素为(章节名, 章节内容)的元组
        summary_excellent: 优秀论文摘要
        summary_warning: 警告级别论文摘要
        task_id: 任务ID
        
    Returns:
        最终评估结果
    """
    print(f"\n🔍 [{task_id}] 待预测论文共有 {len(chapters)} 个章节...")

    # 创建保存结果的目录
    save_dir = os.path.join("output", "paper_classifications", task_id)
    os.makedirs(save_dir, exist_ok=True)
    
    # 并行处理所有章节
    # 并行处理所有章节
    feedback_list = classify_chapters_parallel(chapters, summary_excellent, summary_warning)
    full_feedback = "\n\n".join(feedback_list)

    # 获取论文指标信息
    if not task_id:
        print("未获取到学号信息")
        metrics_info = {}
    else:
        metrics_info = get_metrics_info(task_id)
        print(f"获取到学号 {task_id} 的指标信息: {metrics_info}")
    
    # === 综合判断整体分级 ===
    final_messages = [
        {"role": "system", "content": (
            "你是一位负责对论文提交做出最终判断的高级评审员。\n\n"
            + (
                "以下给出一些关于该论文作者的指标信息来辅助你进行打分：\n\n"
                "1. 科研成果：\n"
                f"   - 发表论文数量：{metrics_info.get('论文数', '未知')}篇\n"
                f"   - 最高影响因子：{metrics_info.get('最高影响因子', '未知')}\n"
                f"   - 论文分区分布：{metrics_info.get('分区分布', '未知')}\n\n"
                "2. 学生信息：\n"
                f"   - 性别：{metrics_info.get('性别', '未知')}\n"
                f"   - 所属院系：{metrics_info.get('院系', '未知')}\n"
                f"   - 学制：{metrics_info.get('学制', '未知')}\n"
                f"   - 培养方式：{metrics_info.get('培养方式', '未知')}\n\n"
                "3. 开题情况：\n"
                f"   - 开题成绩：{metrics_info.get('开题成绩', '未知')}\n"
                f"   - 开题不及格次数：{metrics_info.get('开题不及格次数', '未知')}次\n"
                f"   - 开题时间：{metrics_info.get('开题时间', '未知')}\n\n"
                if metrics_info else "未找到该论文作者的指标信息，请仅基于论文内容进行评价。\n\n"
                )
            # +"请基于论文作者的指标信息和每个章节的详细反馈，尤其是每个章节的不足之处，用严格的标准对论文进行全面评估，并按以下格式输出评价结果：\n\n"
            +"请基于论文作者的指标信息和每个章节的详细反馈，对论文进行全面评估，并按以下格式输出评价结果：\n\n"
            "# 论文总体评价\n"
            "- 总分：[0-100分]\n"
            "- 评价档次：[优秀论文/风险论文] (80-100分为优秀论文，80分以下为风险论文)\n"
            # "- 评价档次：[优/良/中/差] (90-100分为优，80-89分为良，60-79分为中，60分以下为差)\n"
            "- 推荐优秀论文指数：[0-1之间的数值，数值越大，评分为90分以上的概率越高]\n"
            "- 风险系数：[0-1之间的数值，数值越大，风险越高]\n\n"
            "# 论文分项评价情况\n"
            "- 论文选题（15分）：[得分] - [简短评语]\n"
            "- 文献综述（10分）：[得分] - [简短评语]\n"
            "- 创新成果（30分）：[得分] - [简短评语]\n"
            "- 科研能力（15分）：[得分] - [简短评语]\n"
            "- 基础理论与专门知识（20分）：[得分] - [简短评语]\n"
            "- 学术规范与写作规范（10分）：[得分] - [简短评语]\n\n"
            "# 论文综合评价\n"
            "[一段200-300字的综合评语，包括论文的主要优点、不足以及改进建议]\n\n"
            "请确保各项分数加起来等于总分，并且评价档次与总分相符。评价要客观公正，基于论文内容给出合理的评分和评语。请用中文回答。"
        )},
        {"role": "user", "content": f"以下是每个章节的反馈：\n\n{full_feedback}\n\n请给出论文的详细评价。"}
    ]
    
    # print(f"当前prompt：{final_messages}")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=final_messages,
        temperature=0
    )
    
    final_result = response.choices[0].message.content.strip()
    
    # 保存最终结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_dir = os.path.join("output", "final_chapter_results")
    os.makedirs(final_dir, exist_ok=True)
    final_file = os.path.join(final_dir, f"final_result_{task_id}_{timestamp}.txt")
    
    with open(final_file, "w", encoding="utf-8") as f:
        f.write("所有章节反馈:\n\n")
        f.write(full_feedback)
        f.write("\n\n" + "=" * 80 + "\n\n")
        f.write("最终判断:\n\n")
        f.write(final_result)
    
    print(f"🏆 [{task_id}] 已保存最终判断结果到 {final_file}")
    
    return final_result