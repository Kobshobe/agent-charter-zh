"""校验技能的 SKILL.md：前置元数据完整，name 与目录名一致，且有标题。"""

from __future__ import annotations

from pathlib import Path

from ._common import rel


def _frontmatter(text: str) -> list[str] | None:
    """返回 YAML 前置元数据的行；缺失或未闭合时返回 None。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:index]
    return None


def _field(block: list[str], key: str) -> str | None:
    """返回前置元数据里某个标量字段的值。"""
    prefix = f"{key}:"
    for line in block:
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return None


def _heading(text: str) -> bool:
    """判断正文（跳过前置元数据后）是否存在一级标题。"""
    lines = text.splitlines()
    start = 0
    if lines and lines[0].strip() == "---":
        for index, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                start = index + 1
                break
    return any(line.startswith("# ") for line in lines[start:])


def check(root: Path) -> list[str]:
    """返回缺失、name 不符、description 为空或缺一级标题的 SKILL.md。"""
    errors: list[str] = []
    base = root / ".agents" / "skills"
    if not base.is_dir():
        return errors
    for skill in sorted(base.iterdir()):
        if not skill.is_dir():
            continue
        path = skill / "SKILL.md"
        relative = rel(root, path)
        if not path.exists():
            errors.append(f"{relative}：技能缺少 SKILL.md")
            continue
        text = path.read_text(encoding="utf-8")
        block = _frontmatter(text)
        if block is None:
            errors.append(f"{relative}：缺少 YAML 前置元数据")
            continue
        name = _field(block, "name")
        if name != skill.name:
            errors.append(f"{relative}：name 应为目录名 {skill.name}")
        if not _field(block, "description"):
            errors.append(f"{relative}：description 为空")
        if not _heading(text):
            errors.append(f"{relative}：缺少一级标题")
    return errors
