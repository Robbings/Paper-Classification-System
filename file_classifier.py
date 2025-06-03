import os
import shutil

def classify_files(source_folder, destination_folder):
    """
    将源文件夹中的文件按文件名的第5、6位分类到目标文件夹中的子文件夹
    
    参数:
        source_folder: 源文件夹路径
        destination_folder: 目标文件夹路径
    """
    # 确保目标文件夹存在
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    
    # 获取源文件夹中的所有文件
    files = [f for f in os.listdir(source_folder) if os.path.isfile(os.path.join(source_folder, f))]
    
    # 分类计数
    classified_count = 0
    skipped_count = 0
    
    for file in files:
        # 检查文件名长度是否足够
        if len(file) >= 6:
            # 获取第5、6位字符
            category = file[4:6]
            
            # 创建分类文件夹
            category_folder = os.path.join(destination_folder, category)
            if not os.path.exists(category_folder):
                os.makedirs(category_folder)
            
            # 复制文件到分类文件夹
            source_path = os.path.join(source_folder, file)
            destination_path = os.path.join(category_folder, file)
            
            try:
                shutil.copy2(source_path, destination_path)
                classified_count += 1
                print(f"已将文件 {file} 分类到 {category} 文件夹")
            except Exception as e:
                print(f"复制文件 {file} 时出错: {str(e)}")
                skipped_count += 1
        else:
            print(f"跳过文件 {file}，因为文件名长度不足")
            skipped_count += 1
    
    print(f"\n分类完成！共处理 {classified_count} 个文件，跳过 {skipped_count} 个文件")

if __name__ == "__main__":
    # 设置源文件夹和目标文件夹
    source_folder = " "
    destination_folder = "./classify_files"
    
    # 执行分类
    classify_files(source_folder, destination_folder)