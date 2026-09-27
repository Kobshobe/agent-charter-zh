"""校验受治理文档都在字数控额登记表内、未超上限，且不贴住上限。"""

from __future__ import annotations

import json
from pathlib import Path

from ._common import rel, skipped
from .chain_order import EXAMPLE

_HEADROOM_DIVISOR = 20
"""命中文档至少留出上限的 1/20 作余量：上限是护栏，逐字贴住它说明上限本身设错了。"""


def _count(text: str) -> int:
    """按去掉空白后的字符数计，中英文一视同仁。"""
    return len("".join(text.split()))


_TREES = ("docs", ".agents/references")


def _governed(root: Path) -> set[str]:
    """返回必须登记字数控额的文档集合：仓库根的 `*.md`、给人读的文档树、链的标准。

    示例链住在 `.agents/references/` 下，但它由链校验器管，不进文档字数控额。
    """
    paths = {rel(root, path) for path in root.glob("*.md") if path.is_file()}
    for name in _TREES:
        base = root / name
        if not base.is_dir():
            continue
        for path in base.rglob("*.md"):
            if skipped(root, path):
                continue
            relative = path.relative_to(root)
            if relative == EXAMPLE or EXAMPLE in relative.parents:
                continue
            paths.add(rel(root, path))
    chain_standard = root / ".changes" / "README.md"
    if chain_standard.exists():
        paths.add(rel(root, chain_standard))
    return paths


def _load_limits(manifest: Path, root: Path):
    """读取登记表的 budgets 映射，返回 (limits, 错误列表)。"""
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return None, [f"{rel(root, manifest)}：不是合法 JSON（{error.msg}，第 {error.lineno} 行）"]
    if not isinstance(data, dict) or not isinstance(data.get("budgets"), dict):
        return None, [f"{rel(root, manifest)}：缺少 budgets 映射"]
    errors: list[str] = []
    for path, limit in sorted(data["budgets"].items()):
        if not isinstance(limit, int) or isinstance(limit, bool):
            errors.append(f"{rel(root, manifest)}：{path} 的上限应为整数")
    if errors:
        return None, errors
    return data["budgets"], []


def check(root: Path) -> list[str]:
    """返回未登记、缺失、超限或贴住上限的受治理文档。"""
    manifest = root / ".agents" / "scripts" / "doc-budgets.json"
    if not manifest.exists():
        return [f"缺少登记表：{rel(root, manifest)}"]
    limits, malformed = _load_limits(manifest, root)
    if malformed:
        return malformed
    errors: list[str] = []

    for path in sorted(_governed(root)):
        if path not in limits:
            errors.append(f"{path}：未在 {rel(root, manifest)} 登记字数控额")

    for path, limit in sorted(limits.items()):
        target = root / path
        if not target.exists():
            errors.append(f"{path}：已登记但文件不存在")
            continue
        count = _count(target.read_text(encoding="utf-8"))
        if count > limit:
            errors.append(f"{path}：{count} 字，超出上限 {limit}")
            continue
        margin = limit // _HEADROOM_DIVISOR
        if count > limit - margin:
            errors.append(f"{path}：{count} 字，距上限 {limit} 余量不足 {margin} 字——先搬迁或压缩，压不动就抬高上限并说明理由")
    return errors
