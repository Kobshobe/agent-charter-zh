"""校验在制的链里各产物的头部块与必备章节。"""

from __future__ import annotations

import re
from pathlib import Path

from ._common import rel
from .chain_order import chains

TITLE = {"intent.md": "# Intent: ", "spec.md": "# Spec: ", "plan.md": "# Plan: "}
REQUIRED = {
    "intent.md": ("## Problem",),
    "spec.md": ("## Behavior", "## Alternatives considered", "## Areas of concern"),
    "plan.md": ("## Files", "## Proof"),
}
UNRESOLVED = re.compile(r"\[NEEDS CLARIFICATION:[^\]]*\]")


def _headings(text: str) -> list[str]:
    """返回正文里所有二级标题行（原样）。"""
    return [line for line in text.splitlines() if line.startswith("## ")]


def check(root: Path) -> list[str]:
    """返回头部块、必备章节或未决标记不合规的产物。"""
    errors: list[str] = []
    for chain in chains(root):
        relative = rel(root, chain)
        found: set[str] = set()
        for name, prefix in TITLE.items():
            path = chain / name
            if not path.exists():
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
            if not lines or not lines[0].startswith(prefix) or not lines[0][len(prefix) :].strip():
                errors.append(f"{relative}/{name}：首行应为 `{prefix}<标题>`")
                continue
            found.add(name)
            headings = _headings("\n".join(lines))
            for required in REQUIRED[name]:
                if required not in headings:
                    errors.append(f"{relative}/{name}：缺少必备章节 {required}")
        if "spec.md" in found and "intent.md" in found:
            intent = (chain / "intent.md").read_text(encoding="utf-8")
            if UNRESOLVED.search(intent):
                errors.append(f"{relative}/intent.md：spec.md 已存在，却仍有 [NEEDS CLARIFICATION: ...] 标记")
    return errors
