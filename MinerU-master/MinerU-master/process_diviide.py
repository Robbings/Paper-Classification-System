import os
import glob
import argparse
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod

def process_pdf_files(source_folder):
    """
    处理指定文件夹中的PDF文件，将其转换为Markdown
    
    参数:
        source_folder: 源文件夹路径
    """
    print(f"处理源文件夹: {source_folder}")
    
    # 获取所有子文件夹
    subfolders = [f.path for f in os.scandir(source_folder) if f.is_dir()]
    
    for subfolder in subfolders:
        # 查找子文件夹中的PDF文件
        pdf_files = glob.glob(os.path.join(subfolder, "*.pdf"))
        
        if not pdf_files:
            print(f"在文件夹 {subfolder} 中未找到PDF文件，跳过处理")
            continue
        
        for pdf_file_name in pdf_files:
            # 获取文件名和文件所在目录
            name_without_suff = os.path.splitext(os.path.basename(pdf_file_name))[0]
            pdf_directory = os.path.dirname(pdf_file_name)
            
            print(f"正在处理: {pdf_file_name}")
            
            # 准备环境 - 将输出目录设置为PDF文件所在目录
            
            local_image_dir = os.path.join(pdf_directory, "images")
            print(f"准备环境完成")
            local_md_dir = pdf_directory
            image_dir = "images"  # 相对路径，用于在Markdown中引用图片
            print(f"准备环境完成")
    
            os.makedirs(local_image_dir, exist_ok=True)
            print(f"准备环境完成")
    
            image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(
                local_md_dir
            )
            print(f"准备环境完成")
    
            try:
                # 读取PDF文件
                print(f"读取PDF文件: {pdf_file_name}")
                reader1 = FileBasedDataReader("")
                pdf_bytes = reader1.read(pdf_file_name)  # 读取PDF内容
                print(f"PDF内容读取成功，大小: {len(pdf_bytes)} 字节")
    
                # 处理
                ## 创建数据集实例
                print("开始创建数据集实例...")
                ds = PymuDocDataset(pdf_bytes)
                print("数据集实例创建成功")
    
                ## 推理
                print("开始推理...")
                if ds.classify() == SupportedPdfParseMethod.OCR:
                    print("使用OCR模式")
                    infer_result = ds.apply(doc_analyze, ocr=True)
                    ## 管道处理
                    pipe_result = infer_result.pipe_ocr_mode(image_writer)
                else:
                    print("使用文本模式")
                    infer_result = ds.apply(doc_analyze, ocr=False)
                    ## 管道处理
                    pipe_result = infer_result.pipe_txt_mode(image_writer)
    
                ### 获取markdown内容
                md_content = pipe_result.get_markdown(image_dir)
    
                ### 保存markdown文件
                pipe_result.dump_md(md_writer, f"{name_without_suff}.md", image_dir)
                
                print(f"已成功将 {pdf_file_name} 转换为Markdown文件: {os.path.join(local_md_dir, name_without_suff)}.md")
            
            except Exception as e:
                import traceback
                print(f"处理 {pdf_file_name} 时出错: {str(e)}")
                print("详细错误信息:")
                traceback.print_exc()

def process_subfolders(root_folder):
    """
    处理源文件夹中的所有下一级文件夹，为每个下一级文件夹中的文件创建同名文件夹
    
    参数:
        root_folder: 根文件夹路径
    """
    print(f"处理源文件夹: {root_folder}")
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
        process_pdf_files(subfolder_path)

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="将PDF文件转换为Markdown")
    parser.add_argument("--source", type=str, required=True, help="源文件夹路径")
    args = parser.parse_args()
    
    print(f"开始处理源文件夹: {args.source}")
    # 处理PDF文件
    process_subfolders(args.source)