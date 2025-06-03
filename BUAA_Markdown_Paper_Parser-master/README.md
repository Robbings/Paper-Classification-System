# MarkdownParser 使用指南

## 简介

`MarkdownParser` 是一个专门用于解析和提取学术论文（尤其是博士学位论文）结构和内容的Python工具类。该工具可以识别论文中的章、节、条等不同层级的内容，提取元数据，并支持按照特定条件检索和导出论文的各个部分。

## 主要功能

- 识别并解析论文的结构层次（章、节、条等）
- 提取论文元数据（标题、摘要等）
- 构建文档的解析树
- 按照级别、描述、标题等条件检索特定内容
- 将检索到的内容以Markdown格式导出

## 安装

安装为软件包或直接复制代码包到项目目录下，安装方式：
```bash
# 假设代码包在 Markdown_Spliter 目录下
pip install -e /path/to/Markdown_Spliter
```

## 快速入门

### 初始化解析器

有两种方式初始化解析器：

```python
# 方式1：从文件初始化
from Markdown_Spliter.parser import MarkdownParser

parser = MarkdownParser.init_by_path("path/to/your/thesis.md")

# 方式2：从字符串初始化
content = "# 博士学位论文\n\n# 基于人工智能的文本分析\n\n## 第一章 绪论\n\n研究背景与意义..."
parser = MarkdownParser.init_by_str(content)
parser._parse()  # 从字符串初始化后需要手动调用解析
```

### 获取元数据

```python
# 获取论文的元数据
metadata = parser.get_metadata()
print(f"论文标题: {metadata.get('title')}")
```

### 获取解析树

```python
# 获取整个文档的解析树
parse_tree = parser.get_parse_tree()
```

### 提取特定内容

使用 `get_section_content` 方法，可以灵活地检索论文中的特定部分：

```python
# 获取第一章的全部内容（包括其中的所有节、条等）
chapter_one = parser.get_section_content(description="chapter", title="第一章")

# 获取中文摘要
abstract_cn = parser.get_section_content(description="abstract_ch")

# 获取英文摘要
abstract_en = parser.get_section_content(description="abstract_en")

# 获取参考文献
references = parser.get_section_content(description="references")

# 获取所有二级标题内容（所有"节"）
all_sections = parser.get_section_content(level=2)

# 通过精确标题匹配获取特定部分
methodology = parser.get_section_content(exact_title="研究方法")

# 将提取的内容导出到文件
with open("chapter_one.md", "w", encoding="utf-8") as f:
    f.write(chapter_one)
```

## 参数说明

`get_section_content` 方法支持的查询参数：

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| level | int | 标题级别，1表示章，2表示节，3表示条，以此类推 | `level=1` |
| description | str | 内容类型描述，如"chapter", "section", "abstract_ch"等 | `description="chapter"` |
| title | str | 标题内容，进行部分匹配（包含关系） | `title="研究背景"` |
| exact_title | str | 标题内容，进行精确匹配（完全相等） | `exact_title="1.2 研究意义"` |

## 关键词配置

系统内置的关键词配置支持识别以下内容类型：
级别：-1代表Metadata，其他级别表示章节、节、条等。

| 内容类型 | 描述标识 | 级别 |
|---------|----------|------|
| 章 | chapter | 1 |
| 节 | section | 2 |
| 条 | clause | 3 |
| 款 | item | 4 |
| 中文摘要 | abstract_ch | 1 |
| 英文摘要 | abstract_en | 1 |
| 作者介绍 | author_introduction | -1 |
| 目录 | table_of_contents | 1 |
| 参考文献 | references | 1 |
| 图清单 | list_of_figures | 1 |
| 表清单 | list_of_tables | 1 |
| 研究成果 | research_results | -1 |

## 完整示例

下面是一个完整的示例，展示如何解析一篇论文并提取各个部分：

```python
from Markdown_Spliter.parser import MarkdownParser

# 初始化解析器
parser = MarkdownParser.init_by_path("thesis.md")

# 提取论文基本信息
metadata = parser.get_metadata()
print(f"论文标题: {metadata.get('title', '未找到标题')}")

# 提取摘要
abstract = parser.get_section_content(description="abstract_ch")
with open("abstract.md", "w", encoding="utf-8") as f:
    f.write(abstract)

# 提取所有章节
chapters = []
parse_tree = parser.get_parse_tree()
for node in parse_tree:
    if node.get("description") == "chapter":
        chapter_content = parser.get_section_content(exact_title=node["title"])
        chapters.append((node["title"], chapter_content))

# 将各章节保存为单独的文件
for title, content in chapters:
    safe_title = title.replace(" ", "_").replace("/", "_")
    with open(f"{safe_title}.md", "w", encoding="utf-8") as f:
        f.write(content)

print(f"共提取了 {len(chapters)} 个章节")
```

## 注意事项

1. 该解析器主要针对特定格式的博士学位论文设计，可能需要根据实际论文格式进行调整
2. 解析效果依赖于原始Markdown文件的格式规范性
3. 对于非标准格式的内容，可能需要调整 `keywords_config` 配置
4. 处理大型文档时，请注意内存使用情况

## 自定义关键词配置

如果默认的关键词配置不满足需求，可以在config.py中直接添加，也可以使用代码进行自定义配置：

```python
from Markdown_Spliter.parser import MarkdownParser
from Markdown_Spliter.config import keywords_config

# 添加新的关键词配置
keywords_config.append({
    "keyword": r"附录\s*[A-Z]",  # 正则表达式匹配"附录A"等格式
    "description": "appendix",
    "level": 1
})

# 使用自定义配置初始化解析器
parser = MarkdownParser()
parser.keywords_config = keywords_config
parser.path = "thesis.md"
parser._load_md("thesis.md")
parser._parse()

# 现在可以提取附录内容
appendix = parser.get_section_content(description="appendix")
```

## 贡献

欢迎提交问题和改进建议！