import os
from utils import client, chunk_long_chapter

def split_chunks(text, max_chars=1500):
    paragraphs = text.split("\n\n")
    chunks, buffer = [], ""
    for para in paragraphs:
        if len(buffer) + len(para) < max_chars:
            buffer += para + "\n\n"
        else:
            chunks.append(buffer.strip())
            buffer = para + "\n\n"
    if buffer:
        chunks.append(buffer.strip())
    return chunks

def summarize_chunk(chunk, previous_feedback=None, save_dir=None, chunk_index=None, paper_label=None):
    prefix = f"The following is a part of a research paper:\n\n{chunk}"
    if previous_feedback:
        prefix = f"Previous feedback summary:\n{previous_feedback}\n\nNow review the next part:\n{chunk}"

    messages = [{
        "role": "system",
        "content": (
            "你是一位严谨的学术同行评审员，为顶级会议（如NeurIPS、ACL或CVPR）审稿。"
            "对于每个论文片段，提供结构化且简洁的反馈，包括优点、缺点、清晰度、"
            "方法论、创新性和合理性。保持批判性但公正。你的评审有助于确定论文质量。"
            "请用中文提供你的评审反馈。"
        )
    }, {
        "role": "user",
        "content": prefix + "\n\n请为这个片段提供你的评审反馈。"
    }]
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=0
    )
    
    summary = response.choices[0].message.content.strip()
    
    # 保存中间摘要结果
    if save_dir and chunk_index is not None and paper_label:
        os.makedirs(save_dir, exist_ok=True)
        
        # 创建摘要文件名
        summary_file = os.path.join(save_dir, f"{paper_label}_chunk_{chunk_index+1}_summary.txt")
        
        # 保存摘要内容
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(f"原始内容片段 {chunk_index+1}:\n\n")
            f.write("-" * 80 + "\n\n")
            f.write(chunk)
            f.write("\n\n" + "-" * 80 + "\n\n")
            f.write(f"摘要反馈 {chunk_index+1}:\n\n")
            f.write(summary)
        
        print(f"  ✅ 已保存 {paper_label} 的第 {chunk_index+1} 个摘要到 {summary_file}")
    
    return summary

def summarize_long_text(text, label=None):
    # 创建保存中间结果的目录
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = os.path.join("output", "summaries")
    os.makedirs(save_dir, exist_ok=True)
    
    chunks = split_chunks(text, max_chars=10000)
    print(f"🔹 Summarizing {'['+label+'] ' if label else ''}chunks: {len(chunks)}")
    
    summary = None
    for i, chunk in enumerate(chunks):
        print(f"  ⏳ Chunk {i+1}/{len(chunks)}")
        summary = summarize_chunk(chunk, summary, save_dir, i, label)
        
        # 保存当前的累积摘要
        if label:
            cumulative_file = os.path.join(save_dir, f"{label}_cumulative_summary.txt")
            with open(cumulative_file, "w", encoding="utf-8") as f:
                f.write(summary)
            print(f"  📝 已更新累积摘要到 {cumulative_file}")
    
    # 保存最终摘要
    final_file = os.path.join(save_dir, f"{label}_final_summary.txt" if label else "final_summary.txt")
    with open(final_file, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"📊 已保存最终摘要到 {final_file}")
    
    return summary

# 修改摘要章节函数，处理过长的章节
def summarize_chapter(chapter_name, chapter_content, previous_feedback=None, save_dir=None, chapter_index=None, paper_label=None):
    """
    对单个章节进行摘要
    
    Args:
        chapter_name: 章节名称
        chapter_content: 章节内容
        previous_feedback: 之前章节的反馈摘要
        save_dir: 保存结果的目录
        chapter_index: 章节索引
        paper_label: 论文标签
        
    Returns:
        章节摘要
    """
    # 检查内容长度，如果过长则分块处理
    content_chunks = chunk_long_chapter(chapter_content)
    
    summary = previous_feedback
    for i, chunk in enumerate(content_chunks):
        chunk_name = f"{chapter_name}_块{i+1}" if len(content_chunks) > 1 else chapter_name
        
        if len(content_chunks) > 1:
            print(f"  ⏳ 处理章节 {chapter_name} 的第 {i+1}/{len(content_chunks)} 个块")
        
        prefix = f"以下是一篇研究论文的章节 '{chunk_name}':\n\n{chunk}"
        if summary:
            prefix = f"之前的反馈摘要:\n{summary}\n\n现在请评审下一部分 '{chunk_name}':\n{chunk}"

        messages = [{
            "role": "system",
            "content": (
                "你是一位严谨的学术同行评审员，为顶级会议（如NeurIPS、ACL或CVPR）审稿。"
                "对于每个论文章节，提供结构化且简洁的反馈，包括优点、缺点、清晰度、"
                "方法论、创新性和合理性。保持批判性但公正。你的评审有助于确定论文质量。"
                "请用中文提供你的评审反馈。"
            )
        }, {
            "role": "user",
            "content": prefix + "\n\n请为这个部分提供你的评审反馈。"
        }]
        
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0
            )
            
            chunk_summary = response.choices[0].message.content.strip()
            
            # 保存中间摘要结果
            if save_dir and chapter_index is not None and paper_label:
                os.makedirs(save_dir, exist_ok=True)
                
                # 创建摘要文件名
                summary_file = os.path.join(save_dir, f"{paper_label}_{chunk_name}_summary.txt")
                
                # 保存摘要内容
                with open(summary_file, "w", encoding="utf-8") as f:
                    f.write(f"原始内容 '{chunk_name}':\n\n")
                    f.write("-" * 80 + "\n\n")
                    f.write(chunk[:1000] + "..." if len(chunk) > 1000 else chunk)
                    f.write("\n\n" + "-" * 80 + "\n\n")
                    f.write(f"摘要反馈:\n\n")
                    f.write(chunk_summary)
                
                print(f"  ✅ 已保存 {paper_label} 的 '{chunk_name}' 摘要到 {summary_file}")
            
            # 更新总摘要
            if summary:
                summary = f"{summary}\n\n继续评审 '{chunk_name}':\n{chunk_summary}"
            else:
                summary = chunk_summary
                
        except Exception as e:
            print(f"  ❌ 处理章节 '{chunk_name}' 时出错: {str(e)}")
            # 如果处理失败，尝试进一步分割内容
            if len(chunk) > 128000:
                print(f"  🔄 尝试进一步分割内容...")
                sub_chunks = chunk_long_chapter(chunk, max_tokens=15000)
                for j, sub_chunk in enumerate(sub_chunks):
                    sub_chunk_name = f"{chunk_name}_子块{j+1}"
                    print(f"  ⏳ 处理子块 {j+1}/{len(sub_chunks)}")
                    
                    sub_prefix = f"以下是一篇研究论文的章节 '{sub_chunk_name}':\n\n{sub_chunk}"
                    if summary:
                        sub_prefix = f"之前的反馈摘要:\n{summary}\n\n现在请评审下一部分 '{sub_chunk_name}':\n{sub_chunk}"
                    
                    sub_messages = [{
                        "role": "system",
                        "content": (
                            "你是一位严谨的学术同行评审员，为顶级会议（如NeurIPS、ACL或CVPR）审稿。"
                            "对于每个论文章节，提供结构化且简洁的反馈，包括优点、缺点、清晰度、"
                            "方法论、创新性和合理性。保持批判性但公正。你的评审有助于确定论文质量。"
                            "请用中文提供你的评审反馈，并保持简洁。"
                        )
                    }, {
                        "role": "user",
                        "content": sub_prefix + "\n\n请为这个部分提供你的评审反馈。"
                    }]
                    
                    try:
                        sub_response = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=sub_messages,
                            temperature=0
                        )
                        
                        sub_summary = sub_response.choices[0].message.content.strip()
                        
                        # 更新总摘要
                        if summary:
                            summary = f"{summary}\n\n继续评审 '{sub_chunk_name}':\n{sub_summary}"
                        else:
                            summary = sub_summary
                            
                    except Exception as sub_e:
                        print(f"  ❌ 处理子块 '{sub_chunk_name}' 时出错: {str(sub_e)}")
    
    # 如果所有块都处理完毕，生成最终摘要
    if summary and len(content_chunks) > 1:
        try:
            final_messages = [{
                "role": "system",
                "content": (
                    "你是一位严谨的学术同行评审员，负责整合多个章节评审的结果。"
                    "请基于之前的评审反馈，提供一个简洁的总结性评价。"
                    "评价应包括论文的主要优点、缺点、方法论评估和整体质量。"
                    "请用中文提供你的评审反馈。"
                )
            }, {
                "role": "user",
                "content": f"以下是对论文章节 '{chapter_name}' 的多个部分的评审反馈:\n\n{summary}\n\n请提供一个整合的总结性评价。"
            }]
            
            final_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=final_messages,
                temperature=0
            )
            
            summary = final_response.choices[0].message.content.strip()
            
            # 保存最终整合的摘要
            if save_dir and chapter_index is not None and paper_label:
                final_summary_file = os.path.join(save_dir, f"{paper_label}_{chapter_name}_final_summary.txt")
                with open(final_summary_file, "w", encoding="utf-8") as f:
                    f.write(f"章节 '{chapter_name}' 的最终整合评价:\n\n")
                    f.write(summary)
                print(f"  ✅ 已保存 {paper_label} 的章节 '{chapter_name}' 最终整合摘要到 {final_summary_file}")
                
        except Exception as e:
            print(f"  ⚠️ 生成最终整合摘要时出错: {str(e)}")
    
    return summary

