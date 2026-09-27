"""校验 markdown 相对链接可达、锚点存在。"""

from __future__ import annotations

import re
from pathlib import Path

from ._common import documents, rel

_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_FENCE = re.compile(r"```.*?```", re.S)
_CODE = re.compile(r"`[^`]*`")
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_SKIP_SCHEME = ("http://", "https://", "mailto:", "tel:")


def _strip_code(text: str) -> str:
    """去掉围栏代码块与行内代码，避免把示例当成真链接。"""
    return _CODE.sub("", _FENCE.sub("", text))


def _slug(heading: str) -> str:
    """把标题文本转成锚点，规则与 GitHub 一致：小写、去标点、空格转连字符。"""
    text = heading.strip().lower()
    text = re.sub(r"[`*]", "", text)
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return re.sub(r"\s+", "-", text.strip())


def _anchors(text: str) -> set[str]:
    """返回文档内所有标题产生的锚点集合。"""
    anchors = set()
    for line in text.splitlines():
        match = _HEADING.match(line)
        if match:
            anchors.add(_slug(match.group(2)))
    return anchors


def check(root: Path) -> list[str]:
    """返回相对链接缺失或锚点不存在的 markdown 文件。"""
    errors: list[str] = []
    for path in documents(root, skip_archived=True):
        r = rel(root, path)
        raw = path.read_text(encoding="utf-8")
        anchors = _anchors(raw)
        for match in _LINK.finditer(_strip_code(raw)):
            target = match.group(1)
            if target.startswith(_SKIP_SCHEME):
                continue
            if target.startswith("#"):
                anchor = target[1:]
                if anchor and anchor not in anchors:
                    errors.append(f"{r}：锚点不存在 {target}")
                continue
            file_part, _, anchor = target.partition("#")
            resolved = (path.parent / file_part).resolve()
            if not resolved.exists():
                errors.append(f"{r}：链接目标不存在 {target}")
                continue
            if anchor and resolved.suffix == ".md" and anchor not in _anchors(resolved.read_text(encoding="utf-8")):
                errors.append(f"{r}：锚点不存在 {target}")
    return errors
