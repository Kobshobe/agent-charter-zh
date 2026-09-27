#!/usr/bin/env python3
"""文档闸门单一入口：依次运行各校验器，任一失败则返回 1。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from checks import (  # noqa: E402  （需先把 .agents/scripts/ 加入模块搜索路径）
    _common,
    chain_format,
    chain_order,
    doc_budgets,
    md_links,
    md_wrap,
    skill_frontmatter,
)

CHECKS = (
    ("链顺序与目录", chain_order.check),
    ("链产物格式", chain_format.check),
    ("markdown 链接", md_links.check),
    ("一段一行", md_wrap.check),
    ("文档字数控额", doc_budgets.check),
    ("技能前置元数据", skill_frontmatter.check),
)


def main() -> int:
    """运行全部校验器，返回进程退出码。"""
    root = _common.repo_root()
    passed = True
    for name, check in CHECKS:
        if not _common.report(name, check(root)):
            passed = False
    print()
    if passed:
        print("文档闸门全部通过。")
        return 0
    print("文档闸门未通过。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
