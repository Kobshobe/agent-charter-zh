# agent-charter-zh

行为规范工具包（变更链版）——一套可直接复制进项目的 **AI 编码工程规范**：给编码代理一套常驻规则、一套变更产物链、一包可复用工作流，以及一个能机械执行的检查闸门。

它不含任何具体产品的架构约定，只描述与项目无关的行为规范；项目特有部分由根 `AGENTS.md` 的空槽位承接。

包自己的一切都在 `.agents/` 与 `.changes/` 里，不占用目标项目的 `scripts/`、`templates/`、`docs/` 等常用目录。

## 包含什么

| 路径 | 作用 |
|---|---|
| `AGENTS.md` | 根常驻军令：agent 每次会话都要知道的规则；文末留项目特有槽位 |
| `.changes/` | 一次改动的 `intent.md`、`spec.md`、`plan.md`，层数按边界浮动 |
| `.agents/skills/` | 9 个可复用工作流 |
| `.agents/references/doc-standard.md` | 文档标准：分层、教程与参考、写作规则、反 slop 清单、字数控额 |
| `.agents/references/chain-example/` | 一条完整的示例链，受与真实链相同的校验 |
| `.agents/scripts/check_docs.py` | 文档闸门单一入口（Python 3 标准库，零依赖） |
| `.agents/scripts/doc-budgets.json` | 受治理文档的字数控额登记表 |
| `.agents/tests/` | 闸门校验器的 unittest 行为测试 |

9 个工作流：`pre-push-checks`、`code-review`、`doc-standards`、`find-simplifications`、`merging-stacked-prs`、`prose-standard`、`trim-cot-leakage`、`grilling`、`tdd`。

## 接入一个项目

**不要把本包的 `README.md`、`LICENSE`、`.gitignore` 复制过去**——它们是本包自己的仓库元数据，会覆盖目标项目的同名文件。

1. 复制 `.agents/` 与 `.changes/` 到目标项目的仓库根。
2. 把本包的根 `AGENTS.md` 并进项目自己的 `AGENTS.md`。`.changes/` 随包交付时是空的，那是给目标项目的目录，本包不在里面记自己的账。
3. 填根 `AGENTS.md` 里"项目特有约定"的空槽位：架构文档位置、构建与测试命令、目录结构、语言特有约定、密钥来源。
4. 按项目调整 `.agents/scripts/doc-budgets.json` 里的字数上限：第一次按现状上浮至少 1/19（约 +5.3%）登记，再逐步收紧——闸门要求命中上限的文档保留 5% 余量，按当前字数登记会直接失败。
5. 跑一次闸门，确认通过：

```sh
python3 .agents/scripts/check_docs.py
```

## 日常怎么用

- **每个非平凡改动**：在 `.changes/<slug>/` 写 `intent.md`；改动改变系统行为或越过策略边界时补 `spec.md`；落地时写 `plan.md`。链的规则见 [`.changes/README.md`](.changes/README.md)，完整范例见 [`.agents/references/chain-example/`](.agents/references/chain-example/)。
- **完成后归档**：`git mv .changes/<slug> .changes/archive/$(date +%F)-<slug>`。
- **推送前**：按 `pre-push-checks` 选最小检查集；涉及文档或链的改动跑 `python3 .agents/scripts/check_docs.py`。
- **评审**：按 `code-review` 走阻塞性要求与人工检查。
- **精简与清理**：找简化候选用 `find-simplifications`，判文风用 `prose-standard`，清推理过程泄漏用 `trim-cot-leakage`。

## 闸门

`python3 .agents/scripts/check_docs.py` 依次运行六个校验器：

1. **链顺序与目录**：在制链目录名与归档目录名形状正确，链目录只允许三个产物文件、不得有子目录，且 `spec.md` 存在时必须有 `intent.md`。
2. **链产物格式**：每份产物的首行标识与必备章节，以及"`spec.md` 存在时 `intent.md` 不得遗留 `[NEEDS CLARIFICATION: ...]`"。
3. **markdown 链接**：相对链接可达、锚点存在。
4. **一段一行**：段落不折行。
5. **文档字数控额**：受治理文档都在登记表内，未超上限，且没有贴住上限。
6. **技能前置元数据**：每个技能的 `name` 与目录名一致，`description` 非空，且有一级标题。

任一失败即返回非零，未通过不算完成。归档的链只校验路径形状，不校验内容格式；`.agents/references/chain-example/` 下的示例走与真实链相同的规则。CI 在 [`.github/workflows/check-docs.yml`](.github/workflows/check-docs.yml) 上跑这道闸门与 `python3 -m unittest discover -s .agents/tests`；两者都只用 Python 3.8+ 标准库。

## 这个包不承载什么

链是历史快照，不承载"当前生效的决策"——当前行为只在架构文档、模块参考与源码里。想知道系统现在为什么是这样，读文档与代码；想知道某次改动当时为什么这么做，读链。

## 许可

本包自身是 MIT，见 [`LICENSE`](LICENSE)。它是中文改编：制度与技能来自 [`deepseek-ai/deepseek-harness`](https://github.com/deepseek-ai/deepseek-harness) 与 [`mattpocock/skills`](https://github.com/mattpocock/skills)。
