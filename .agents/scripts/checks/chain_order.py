"""校验变更产物链的目录形状与层与层之间的顺序。"""

from __future__ import annotations

import re
from pathlib import Path

from ._common import rel

FILES = ("intent.md", "spec.md", "plan.md")
# 只有 spec 声称了系统行为，因此它必须由 intent 支撑；plan 可以独立存在（小改动）。
REQUIRES = (("spec.md", "intent.md"),)
ARCHIVE_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}-v\d+-.+$")
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


EXAMPLE = Path(".agents") / "references" / "chain-example"


def chains(root: Path):
    """产出受校验的链目录：`.changes/` 下的在制工作项，以及随包交付的示例链。"""
    changes = root / ".changes"
    if changes.is_dir():
        for entry in sorted(changes.iterdir()):
            if entry.is_dir() and entry.name != "archive" and not entry.name.startswith("."):
                yield entry
    example = root / EXAMPLE
    if example.is_dir():
        yield example


def check(root: Path) -> list[str]:
    """返回缺少目录、归档命名不合规或跳层的链。"""
    changes = root / ".changes"
    if not changes.is_dir():
        return [f"缺少目录：{rel(root, changes)}"]

    errors: list[str] = []
    archive = changes / "archive"
    if not archive.is_dir():
        errors.append(f"缺少目录：{rel(root, archive)}")
    else:
        for entry in sorted(archive.iterdir()):
            if entry.name.startswith("."):
                continue
            if not entry.is_dir() or not ARCHIVE_NAME.match(entry.name):
                errors.append(f"{rel(root, entry)}：归档目录名应为 YYYY-MM-DD-v<序号>-<slug>")

    for entry in sorted(changes.iterdir()):
        if entry.is_dir() and entry.name != "archive" and not entry.name.startswith("."):
            if not SLUG.match(entry.name):
                errors.append(f"{rel(root, entry)}：在制链目录名应为连字符分隔的小写短语，不编号")

    for chain in chains(root):
        for child in sorted(chain.iterdir()):
            if child.is_dir():
                errors.append(f"{rel(root, child)}：链目录下不得有子目录")
        names = {path.name for path in chain.iterdir() if path.is_file()}
        if not names:
            errors.append(f"{rel(root, chain)}：空的工作项目录")
            continue
        for extra in sorted(names - set(FILES)):
            errors.append(f"{rel(root, chain)}：未知文件 {extra}（只允许 {'、'.join(FILES)}）")
        for present, required in REQUIRES:
            if present in names and required not in names:
                errors.append(f"{rel(root, chain)}：有 {present} 却没有 {required}（不得跳层）")
    return errors
