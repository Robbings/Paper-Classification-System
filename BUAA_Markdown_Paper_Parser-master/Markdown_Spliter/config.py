keywords_config = [
    {
        # 章
        "keyword": r"第.*章",
        "description": "chapter",
        "level": 1,
    },
    {
        # 节
        "keyword": r"\b\d+\.\d+\b",
        "description": "section",
        "level": 2,
    },
    {
        # 条
        "keyword": r"\b\d+\.\d+\.\d+\b",
        "description": "clause",
        "level": 3,
    },
    {
        # 款
        "keyword": r"（\d+）",
        "description": "item",
        "level": 4,
    },
    {
        # 摘要
        "keyword": r"摘\s*要",
        "description": "abstract_ch",
        "level": 1,
    },
    {
        # Abstract
        "keyword": r"Abstract",
        "description": "abstract_en",
        "level": 1,
    },
    {
        # 作者介绍
        "keyword": r"作者介绍",
        "description": "author_introduction",
        "level": -1,
    },
    {
        # 目录
        "keyword": r"目\s*录",
        "description": "table_of_contents",
        "level": 1,
    },
    {
        # 参考文献
        "keyword": r"参\s*考\s*文\s*献",
        "description": "references",
        "level": 1,
    },
    {
        # 图清单
        "keyword": r"图\s*清\s*单",
        "description": "list_of_figures",
        "level": 1,
    },
    {
        # 表清单
        "keyword": r"表\s*清\s*单",
        "description": "list_of_tables",
        "level": 1,
    },
    {
        # 取得的研究成果
        "keyword": r"取得的研究成果",
        "description": "research_results",
        "level": -1,
    }
]