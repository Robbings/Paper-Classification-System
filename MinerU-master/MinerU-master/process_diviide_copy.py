import os
import glob
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod

# 输入源文件夹路径
source_folder = "D:/paperClassification/data/02/excellent paper"  # 请替换为您的源文件夹路径

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
        local_md_dir = pdf_directory
        image_dir = "images"  # 相对路径，用于在Markdown中引用图片

        os.makedirs(local_image_dir, exist_ok=True)

        image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(
            local_md_dir
        )

        try:
            # 读取PDF文件
            reader1 = FileBasedDataReader("")
            pdf_bytes = reader1.read(pdf_file_name)  # 读取PDF内容

            # 处理
            ## 创建数据集实例
            ds = PymuDocDataset(pdf_bytes)

            ## 推理
            if ds.classify() == SupportedPdfParseMethod.OCR:
                infer_result = ds.apply(doc_analyze, ocr=True)
                ## 管道处理
                pipe_result = infer_result.pipe_ocr_mode(image_writer)
            else:
                infer_result = ds.apply(doc_analyze, ocr=False)
                ## 管道处理
                pipe_result = infer_result.pipe_txt_mode(image_writer)

            ### 获取markdown内容
            md_content = pipe_result.get_markdown(image_dir)

            ### 保存markdown文件
            pipe_result.dump_md(md_writer, f"{name_without_suff}.md", image_dir)
            
            print(f"已成功将 {pdf_file_name} 转换为Markdown文件: {os.path.join(local_md_dir, name_without_suff)}.md")
        
        except Exception as e:
            print(f"处理 {pdf_file_name} 时出错: {str(e)}")