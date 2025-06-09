# 论文分类系统使用指南
本系统用于自动分类论文质量，支持评估分类准确率和对新论文进行分类两种模式。

## 环境配置
具体参考 MinerU-master\MinerU-master\README.md （推荐使用GPU版本，pdf文件转换为md文件的步骤会更快）

## 运行流程
### 一、数据预处理 
1. 将同一学院的论文提取出来
```bash
python file_classifier.py
 ```

注意：请根据需要修改脚本中的路径配置

 2. 手动整理论文结构
将目标学院的论文按以下结构排列：

```plaintext
源文件夹/    # 自由设置，示例：D:/paperClassification/data/02（代表2系论文评估）
├── excellent paper/   # 优秀论文文件夹
│   ├── BY1701171.md
│   └── ...
├── poor paper/        # 风险论文文件夹
│   ├── BY1501105.md
│   └── ...
├── TBD/               # 待测论文文件夹（运行分类模式时使用）
```
 3. 运行数据预处理脚本
```bash
python data_preprocess.py --source "您的源文件夹路径"
```

示例：

```bash
python data_preprocess.py --source "D:/paperClassification/data/02"
```

预处理脚本将依次执行以下操作：

- 创建文件夹结构 ：为源文件夹中的所有文件创建同名（无后缀）的文件夹，并将文件移动到对应文件夹中
- PDF转MD ：将源文件夹中所有论文的pdf转换成md文件
- 章节划分 ：将转换后的md文件按章节划分

### 二、任务实现
预处理完成后，文件组织结构如下：

```plaintext
源文件夹/    #示例：D:/paperClassification/data/02
├── excellent paper/
│   ├── BY1701171/
│   │   ├── BY1701171.md
│   │   ├── BY1701171/
│   │   │   ├── 第一章.md
│   │   │   ├── 第二章.md
│   │   │   └── ...
├── poor paper/
│   ├── BY1501105/
│   │   ├── BY1501105/
│   │   │   ├── 第一章.md
│   │   │   ├── 第二章.md
│   │   │   └── ...
├── TBD/（待测论文）
│   ├── BY1501105/
│   │   ├── BY1501105/
│   │   │   ├── 第一章.md
│   │   │   ├── 第二章.md
│   │   │   └── ...
 ```
```
 评估准确率模式
该模式将 excellent paper/poor paper 中的论文按比例划分，前一部分作为示例论文，剩余部分作为待测论文，最终返回分类准确率。

```bash
python main_acc copy.py --source "您的源文件夹路径" --sample_ratio 比例值 --mode accuracy
 ```
```

示例：

```bash
# 使用1/3的论文作为示例论文（默认比例）
python main_all.py --source "D:/paperClassification/data/02" --mode accuracy

# 使用1/2的论文作为示例论文
python main_acc copy.py --source "D:/paperClassification/data/02" --sample_ratio 0.5 --mode accuracy
 ```
```
 分类论文模式
该模式以 excellent paper/poor paper 中的论文作为示例论文，将 TBD 中的论文作为待测论文，返回预测结果。使用前请将待预测论文放入 TBD 文件夹中。

```bash
python parallel_paper_infro/main_all.py --source "您的源文件夹路径" --mode classify
 ```
```

示例：

```bash
python parallel_paper_infro/main_acc copy.py --source "D:/paperClassification/data/02" --mode classify
 ```
```

## 注意事项
1. 当前上下文仅支持1篇优秀论文加3篇风险论文作为示例论文，超过该数量可能会导致系统报错
2. 为获得最佳分类效果，建议使用同一学院的论文进行分类
3. 预处理步骤可能需要较长时间，特别是PDF转MD的过程，建议使用GPU加速。若长时间无反应，可以单独运行paperClassification\MinerU-master\MinerU-master\process_diviide_copy.py文件（注意要修改路径）进行转换，全部完成后将data_preprocess.py文件中的process_diviide_copy.py文件注释掉后重新运行即可。
4. 分类结果将保存在 output 目录下，可查看详细的分类报告

## 常见问题解决