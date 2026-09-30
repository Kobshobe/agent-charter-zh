"""闸门校验器的行为测试：在临时仓库夹具上钉住覆盖面与失败路径。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from checks import _common, chain_order, doc_budgets, md_links, md_wrap, skill_frontmatter  # noqa: E402


def write(root: Path, relative: str, text: str) -> Path:
    """在夹具里写一个文件，必要时创建父目录。"""
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class GateCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / ".changes" / "archive").mkdir(parents=True)
        (self.root / ".agents" / "scripts").mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()


class DocumentsTest(GateCase):
    def test_root_readme_governed_and_tool_dirs_skipped(self):
        write(self.root, "README.md", "# 标题\n")
        write(self.root, "docs/node_modules/dep.md", "# 依赖\n")
        got = {_common.rel(self.root, path) for path in _common.documents(self.root)}
        self.assertIn("README.md", got)
        self.assertNotIn("docs/node_modules/dep.md", got)


class MdWrapTest(GateCase):
    def test_root_readme_folded_paragraph_flagged(self):
        write(self.root, "README.md", "第一行\n第二行\n")
        self.assertTrue(any("README.md" in error for error in md_wrap.check(self.root)))

    def test_in_progress_chain_folded_paragraph_flagged(self):
        write(self.root, ".changes/probe/intent.md", "# Intent: p\n\n## Problem\n\n一\n二\n")
        self.assertTrue(any(".changes/probe" in error for error in md_wrap.check(self.root)))

    def test_archive_folded_paragraph_skipped(self):
        write(self.root, ".changes/archive/2026-01-01-old/intent.md", "# Intent: o\n\n## Problem\n\n一\n二\n")
        self.assertEqual(md_wrap.check(self.root), [])


class MdLinksTest(GateCase):
    def test_root_readme_broken_link_flagged(self):
        write(self.root, "README.md", "见 [缺失](missing.md)。\n")
        self.assertTrue(any("missing.md" in error for error in md_links.check(self.root)))

    def test_missing_anchor_flagged(self):
        write(self.root, "README.md", "[x](target.md#不存在)\n")
        write(self.root, "target.md", "# 标题\n")
        self.assertTrue(any("不存在" in error for error in md_links.check(self.root)))


class ChainOrderTest(GateCase):
    def test_chain_slug_shape_enforced(self):
        write(self.root, ".changes/BadName/intent.md", "# Intent: x\n\n## Problem\n\nok\n")
        self.assertTrue(any("BadName" in error for error in chain_order.check(self.root)))

    def test_chain_subdirectory_rejected(self):
        write(self.root, ".changes/good/intent.md", "# Intent: x\n\n## Problem\n\nok\n")
        (self.root / ".changes" / "good" / "sub").mkdir()
        self.assertTrue(any("不得有子目录" in error for error in chain_order.check(self.root)))

    def test_archive_name_without_version_rejected(self):
        write(self.root, ".changes/archive/2026-01-01-old/intent.md", "# Intent: x\n\n## Problem\n\nok\n")
        self.assertTrue(any("归档目录名" in error for error in chain_order.check(self.root)))

    def test_archive_name_with_version_accepted(self):
        write(self.root, ".changes/archive/2026-01-01-v1-old/intent.md", "# Intent: x\n\n## Problem\n\nok\n")
        self.assertEqual(chain_order.check(self.root), [])


class DocBudgetsTest(GateCase):
    def _manifest(self, body: str) -> None:
        write(self.root, ".agents/scripts/doc-budgets.json", body)

    def test_tool_dirs_not_required_in_manifest(self):
        self._manifest('{"budgets": {"README.md": 1000}}')
        write(self.root, "README.md", "短\n")
        write(self.root, "docs/node_modules/dep.md", "# " + "x" * 5000 + "\n")
        self.assertEqual(doc_budgets.check(self.root), [])

    def test_unregistered_governed_doc_flagged(self):
        self._manifest('{"budgets": {}}')
        write(self.root, "README.md", "内容\n")
        self.assertTrue(any("未在" in error for error in doc_budgets.check(self.root)))

    def test_headroom_enforced(self):
        self._manifest('{"budgets": {"README.md": 100}}')
        write(self.root, "README.md", "x" * 96 + "\n")
        self.assertTrue(any("余量不足" in error for error in doc_budgets.check(self.root)))

    def test_invalid_json_reported(self):
        self._manifest("{")
        self.assertTrue(any("不是合法 JSON" in error for error in doc_budgets.check(self.root)))

    def test_missing_budgets_reported(self):
        self._manifest("{}")
        self.assertTrue(any("budgets" in error for error in doc_budgets.check(self.root)))

    def test_non_integer_limit_reported(self):
        self._manifest('{"budgets": {"README.md": "lots"}}')
        self.assertTrue(any("整数" in error for error in doc_budgets.check(self.root)))


class SkillFrontmatterTest(GateCase):
    def test_valid_skill_passes(self):
        write(self.root, ".agents/skills/good/SKILL.md", "---\nname: good\ndescription: d\n---\n\n# 好\n")
        self.assertEqual(skill_frontmatter.check(self.root), [])

    def test_name_must_match_directory(self):
        write(self.root, ".agents/skills/bad/SKILL.md", "---\nname: wrong\ndescription: d\n---\n\n# 坏\n")
        self.assertTrue(any("name 应为目录名 bad" in error for error in skill_frontmatter.check(self.root)))

    def test_empty_description_flagged(self):
        write(self.root, ".agents/skills/bad/SKILL.md", "---\nname: bad\ndescription:\n---\n\n# 坏\n")
        self.assertTrue(any("description 为空" in error for error in skill_frontmatter.check(self.root)))

    def test_missing_heading_flagged(self):
        write(self.root, ".agents/skills/bad/SKILL.md", "---\nname: bad\ndescription: d\n---\n\n正文\n")
        self.assertTrue(any("缺少一级标题" in error for error in skill_frontmatter.check(self.root)))


if __name__ == "__main__":
    unittest.main()
