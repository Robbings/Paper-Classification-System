import re

from Markdown_Spliter.config import keywords_config


class MarkdownParser:

    def __init__(self):
        self.metadata = {}
        self.content = None
        self.path = None
        self.lines = []
        self.paser_tree = []
        self.keywords_config = keywords_config

    @classmethod
    def init_by_path(cls, path):
        """
        Initialize the parser with a file path.
        :param path: Path to the markdown file.
        :return: An instance of MarkdownParser.
        """
        instance = cls()
        instance.path = path
        instance._load_md(path)
        instance._parse()
        return instance

    @classmethod
    def init_by_str(cls, content):
        """
        Initialize the parser with a string.
        :param content: Content of the markdown file.
        :return: An instance of MarkdownParser.
        """
        instance = cls()
        instance.content = content
        return instance

    def _load_md(self, path):
        """
        Load markdown content from a file.
        :param path: Path to the markdown file.
        :return: Content of the markdown file.
        """
        with open(path, "r", encoding="utf-8") as f:
            self.content =  f.read()
        lines = self.content.split("\n")
        # 移除空行
        self.lines = [line for line in lines if line.strip() != ""]

    def get_metadata(self) -> dict:
        """
        Parse metadata from the markdown content.
        :return: A dictionary containing metadata.
        """
        return self.metadata

    def get_parse_tree(self) -> list:
        """
        Get the parse tree of the markdown content.
        :return: A list representing the parse tree.
        """
        return self.parse_tree


    def _match_keyword_level(self, text):
        """
        Match keywords in the text to determine their level and description.
        :param text: Text to be matched.
        :return:    A tuple containing the level and description of the matched keyword.
        """
        for config in self.keywords_config:
            if re.search(config["keyword"], text):
                return config["level"], config["description"]
        return None, None

    def _parse(self):
        """
        Parse the markdown content to extract metadata and structure.
        :return:
        """
        stage = 0
        current_metadata_lines = []
        tree = []
        node_stack = []
        last_part = False
        last_description = None

        def add_node(level, description, title, line):
            node = {
                "level": level,
                "description": description,
                "title": title.strip("# ").strip(),
                "line": line,
                "content": "",
                "children": []
            }

            while node_stack and node_stack[-1]["level"] >= level:
                node_stack.pop()

            if node_stack and level > 0:
                node_stack[-1]["children"].append(node)
            else:
                tree.append(node)
            node_stack.append(node)

        def add_content(line):
            if node_stack:
                node_stack[-1]["content"] += line.strip() + "\n"

        i = 0
        while i < len(self.lines):
            line = self.lines[i].strip()

            # Step 1: 等待出现 北京航空航天大學博士学位论文（中间可能有空格）
            if stage == 0:
                if line.startswith("#") and re.search(r"博\s*士\s*学\s*位\s*论\s*文", line, re.IGNORECASE):
                    stage = 1

            # Step 2: 捕捉论文题目
            elif stage == 1:
                self.metadata["title"] = line.strip("# ").strip()
                self.metadata["raw"] = "# title: " + self.metadata["title"] + "\n\n"
                stage = 2

            elif stage == 2:
                if line.startswith("#"):
                    stage = 3  # metadata 结束
                    self.metadata["raw"] += "\n"
                    continue
                self.metadata["raw"] += line + "\n"
                i += 1
                continue

            # Step 3: 正文结构解析（只解析 # 开头的段落）
            elif stage == 3:
                if line.startswith("#"):
                    if last_part:
                        stage = 4
                        continue
                    level, description = self._match_keyword_level(line)
                    if description == "references":
                        last_part = True
                    if level is not None:
                        add_node(level, description, line, i)
                    else:
                        add_content(line)
                else:
                    if not re.search(r"^\s*参\s*考\s*文\s*献\s*$", line):
                        add_content(line)
                    else:
                        last_part = True
                        add_node(1, "references", line, i)
            # 处理最后的部分，作为metadata
            elif stage == 4:
                if line.startswith("#"):
                    level, last_description = self._match_keyword_level(line)
                    if level is None:
                        last_description = "raw"
                        if last_description not in self.metadata:
                            self.metadata[last_description] = ""
                        self.metadata[last_description] += "\n" + line.strip() + "\n"
                else:
                    if last_description not in self.metadata:
                        self.metadata[last_description] = ""
                    self.metadata[last_description] += line.strip() + "\n"
            i += 1

        self.parse_tree = tree

    def get_section_content(self, **kwargs):
        """
        获取指定章节及其子内容，并转换为Markdown格式字符串返回

        可用的查询参数:
        :param level: 标题级别，例如 1 表示章，2 表示节，等
        :param description: 描述，例如 'chapter', 'section', 'abstract_ch' 等
        :param title: 标题内容，将进行部分匹配
        :param exact_title: 标题内容，将进行精确匹配

        :return: 包含指定章节及其子内容的Markdown格式字符串
        """
        if not hasattr(self, 'parse_tree'):
            self._parse()

        # 如果parse_tree为空，返回空字符串
        if not self.parse_tree:
            return ""

        # 查找符合条件的节点
        found_nodes = self._find_nodes(self.parse_tree, **kwargs)

        if not found_nodes:
            return ""

        # 将节点转换为Markdown格式
        result = ""
        for node in found_nodes:
            result += self._node_to_markdown(node)

        return result

    def _find_nodes(self, nodes, **kwargs):
        """
        递归查找符合条件的节点

        :param nodes: 要搜索的节点列表
        :param kwargs: 查询参数
        :return: 符合条件的节点列表
        """
        found = []

        for node in nodes:
            # 检查节点是否符合所有指定的条件
            match = True

            for key, value in kwargs.items():
                if key == 'level' and 'level' in node and node['level'] != value:
                    match = False
                    break
                elif key == 'description' and 'description' in node and node['description'] != value:
                    match = False
                    break
                elif key == 'title' and 'title' in node and value not in node['title']:
                    match = False
                    break
                elif key == 'exact_title' and 'title' in node and value != node['title']:
                    match = False
                    break

            if match:
                found.append(node)

            # 递归搜索子节点
            if 'children' in node and node['children']:
                child_found = self._find_nodes(node['children'], **kwargs)
                found.extend(child_found)

        return found

    def _node_to_markdown(self, node, depth=0):
        """
        将节点转换为Markdown格式

        :param node: 要转换的节点
        :param depth: 当前的深度，用于确定标题级别
        :return: Markdown格式的字符串
        """
        # 根据节点的级别决定标题等级
        heading_level = min(6, node['level'] + depth) if node['level'] > 0 else 1 + depth

        # 创建 Markdown 标题
        md = '#' * heading_level + ' ' + node['title'] + '\n\n'

        # 添加节点内容（如果有）
        if node['content'].strip():
            md += node['content'].strip() + '\n\n'

        # 递归添加子节点内容
        for child in node['children']:
            md += self._node_to_markdown(child, depth + 1)

        return md