import os
import subprocess
import sys
import time
import argparse

def run_script(script_path, description, args=None):
    """
    运行指定的Python脚本并显示进度
    
    参数:
        script_path: 脚本路径
        description: 脚本功能描述
        args: 传递给脚本的命令行参数
    """
    print(f"\n{'='*80}")
    print(f"开始执行: {description}")
    print(f"脚本路径: {script_path}")
    if args:
        print(f"传递参数: {args}")
    print(f"{'='*80}\n")
    
    start_time = time.time()
    
    try:
        # 准备命令行参数
        cmd = [sys.executable, script_path]
        if args:
            cmd.extend(args)
            
        # 使用subprocess运行脚本
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # 实时输出脚本执行结果
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        # 获取错误输出
        stderr = process.stderr.read()
        if stderr:
            print(f"错误信息:\n{stderr}")
        
        # 检查返回码
        return_code = process.poll()
        if return_code == 0:
            elapsed_time = time.time() - start_time
            print(f"\n✅ {description}执行完成！耗时: {elapsed_time:.2f}秒")
            return True
        else:
            print(f"\n❌ {description}执行失败，返回码: {return_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ 执行{description}时出错: {str(e)}")
        return False

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="论文数据预处理流程")
    parser.add_argument("--source", type=str, default="D:/paperClassification/data/chapter_chunk/cl", 
                        help="源文件夹路径")
    args = parser.parse_args()
    
    # 获取当前脚本所在目录作为基础路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 定义要执行的脚本及其描述和参数
    scripts = [
        {
            "path": os.path.join(base_dir, "create_folders_for_files.py"),
            "description": "为源文件夹中的所有文件创建同名（无后缀）的文件夹，并将文件移动到对应文件夹中",
            "args": ["--source", args.source]
        },
        #单独运行该程序后注释掉脚本内的代码
        {
            "path": os.path.join(base_dir, "MinerU-master", "MinerU-master", "process_diviide.py"),
            "description": "将源文件夹中所有论文的pdf转换成md文件",
            "args": ["--source", args.source]
        },
        {
            "path": os.path.join(base_dir, "BUAA_Markdown_Paper_Parser-master", "main.py"),
            "description": "将上一步转换后的md文件按章节划分",
            "args": ["--source", args.source]
        }
    ]
    
    # 记录总体开始时间
    total_start_time = time.time()
    
    # 依次执行每个脚本
    success_count = 0
    for i, script in enumerate(scripts):
        print(f"\n[{i+1}/{len(scripts)}] 正在执行: {script['description']}")
        if run_script(script["path"], script["description"], script.get("args")):
            success_count += 1
        else:
            print(f"警告: {script['description']}执行失败，停止执行后续脚本")
            break  # 如果脚本执行失败，停止执行后续脚本
    
    # 计算总耗时
    total_elapsed_time = time.time() - total_start_time
    
    # 输出总结
    print("\n" + "="*80)
    print(f"数据预处理完成！总耗时: {total_elapsed_time:.2f}秒")
    print(f"成功执行: {success_count}/{len(scripts)} 个脚本")
    if success_count < len(scripts):
        print(f"失败执行: {len(scripts) - success_count}/{len(scripts)} 个脚本")
    print("="*80)

if __name__ == "__main__":
    main()