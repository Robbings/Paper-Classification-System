import os
import shutil
import argparse

def create_folders_for_files(source_folder):
    """
    为源文件夹中的所有文件创建同名（无后缀）的文件夹，并将文件移动到对应文件夹中
    
    参数:
        source_folder: 源文件夹路径
    """
    # 确保源文件夹存在
    if not os.path.exists(source_folder):
        print(f"源文件夹 {source_folder} 不存在！")
        return
    
    # 获取源文件夹中的所有文件
    files = [f for f in os.listdir(source_folder) if os.path.isfile(os.path.join(source_folder, f))]
    
    # 处理计数
    processed_count = 0
    skipped_count = 0
    
    for file in files:
        # 获取文件名（无后缀）
        file_name_without_ext = os.path.splitext(file)[0]
        
        # 创建同名文件夹
        folder_path = os.path.join(source_folder, file_name_without_ext)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            
        # 移动文件到新创建的文件夹
        source_path = os.path.join(source_folder, file)
        destination_path = os.path.join(folder_path, file)
        
        try:
            shutil.move(source_path, destination_path)
            processed_count += 1
            print(f"已将文件 {file} 移动到文件夹 {file_name_without_ext}")
        except Exception as e:
            print(f"移动文件 {file} 时出错: {str(e)}")
            skipped_count += 1
    
    print(f"\n处理完成！共处理 {processed_count} 个文件，跳过 {skipped_count} 个文件")

def process_subfolders(root_folder):
    """
    处理源文件夹中的所有下一级文件夹，为每个下一级文件夹中的文件创建同名文件夹
    
    参数:
        root_folder: 根文件夹路径
    """
    # 确保根文件夹存在
    if not os.path.exists(root_folder):
        print(f"根文件夹 {root_folder} 不存在！")
        return
    
    # 获取根文件夹中的所有下一级文件夹
    subfolders = [f for f in os.listdir(root_folder) if os.path.isdir(os.path.join(root_folder, f))]
    
    if not subfolders:
        print(f"根文件夹 {root_folder} 中没有下一级文件夹！")
        return
    
    print(f"在 {root_folder} 中找到 {len(subfolders)} 个下一级文件夹")
    
    # 处理每个下一级文件夹
    for subfolder in subfolders:
        subfolder_path = os.path.join(root_folder, subfolder)
        print(f"\n开始处理下一级文件夹: {subfolder_path}")
        create_folders_for_files(subfolder_path)

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="为源文件夹中的所有文件创建同名文件夹并移动文件")
    
    parser.add_argument("--source", type=str, required=True, help="源文件夹路径")
    args = parser.parse_args()
    
    # 对每个文件夹执行处理
    process_subfolders(args.source)