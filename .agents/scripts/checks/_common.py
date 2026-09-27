"""文档闸门共用的定位与遍历工具。"""

from __future__ import annotations

import sys
from pathlib import Path

# 工具生成、不被手工编辑的目录，因此不可能承载受治理的文档。
# 按路径分段匹配，所以只有名为 build 的目录会被跳过，`docs/build.md` 不受影响。
# 不给配置入口：这些目录名由工具决定，不由项目决定。
_SKIP_DIRS = {
    # 版本控制与依赖
    ".git",
    "node_modules",
    "vendor",
    ".venv",
    "venv",
    ".eggs",
    # Python 工具缓存
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    # 构建产物
    "build",
    "dist",
    # 其他语言生态的产物
    "target",
    ".next",
    ".nuxt",
    ".gradle",
}


def repo_root() -> Path:
    """返回仓库根：`.agents/scripts/checks/` 上溯三级。"""
    return Path(__file__).resolve().parents[3]


def rel(root: Path, path: Path) -> str:
    """返回相对仓库根的 POSIX 路径，用于稳定地打印。"""
    return str(path.relative_to(root)).replace("\\", "/")


# 文档住在仓库根的 `*.md` 与 docs/、.agents/、.changes/ 三棵树里。不扫仓库其余部分：
# 源码树里散落的笔记、被 gitignore 的缓存目录都不是文档，对它们套排版规则会把接入
# 一个真实仓库的成本抬到没人愿意付。
_DOC_TREES = ("docs", ".agents", ".changes")


def skipped(root: Path, path: Path) -> bool:
    """判断路径是否落在工具生成、不被手工编辑的目录里。"""
    return any(part in _SKIP_DIRS for part in path.relative_to(root).parts)


def documents(root: Path, skip_archived: bool = False):
    """遍历受治理的 markdown：仓库根的 `*.md`、`docs/`、`.agents/`、`.changes/`。

    @param root 仓库根目录。
    @param skip_archived 为真时跳过 `.changes/archive/`，即冻结的历史快照。
    """
    for path in sorted(root.glob("*.md")):
        if path.is_file():
            yield path
    for name in _DOC_TREES:
        base = root / name
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.md")):
            if skipped(root, path):
                continue
            parts = path.relative_to(root).parts
            if skip_archived and "/".join(parts).startswith(".changes/archive/"):
                continue
            yield path


def report(name: str, errors: list[str]) -> bool:
    """打印单个校验器的结果，返回是否通过。"""
    if errors:
        print(f"[失败] {name}")
        for error in errors:
            print(f"    - {error}")
        return False
    print(f"[通过] {name}")
    return True
