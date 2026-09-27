---
name: merging-stacked-prs
description: 落地一串相互依赖的 GitHub PR（A ← B ← C，每个基于下面那个）到主干、合并一个基线是另一个未合 PR 的 PR，或任何提到叠层 PR、PR 栈、依赖 PR、按顺序合并几个相关 PR 的请求。要求每条同仓库依赖链在落地前都使用 GitHub 官方叠层 PR 功能，让 GitHub 拥有栈级的规则、CI、顺序、重定向与合并状态。
---

# 落地一个官方 GitHub PR 栈

通过 GitHub 的原生 stack 对象与 `gh stack merge` 落地依赖 PR。不要用 `gh pr merge` 与 `gh pr edit` 逐个合并再重定向来复刻栈语义。分支历史政策（允许 merge-forward 与 rebase）由根 [`AGENTS.md`](../../../AGENTS.md) 拥有。

## 要求原生栈支持

改 GitHub 状态前先跑 `gh stack --version`。官方扩展或服务端栈功能不可用时**硬停止**，不要退回到逐个手动合并与重定向。GitHub 栈要求每个头分支都在同一个仓库里，跨 fork 的链硬停止。

用一个干净的专用 worktree。拉取当前 PR 元数据与确切头 OID，不要相信分支名或早先的报告：

```sh
gh pr view <pr> --json number,author,baseRefName,baseRefOid,headRefName,headRefOid,isCrossRepository,state,isDraft,reviewDecision,mergeStateStatus,statusCheckRollup
```

对每条疑似链至少查一个 PR 的 `PullRequest.stack` 与 `stackEntry.position`：官方 GitHub 对象、而非仅凭基线分支推断，才是栈成员资格的权威。从活的 PR 基线确定自下而上的预期顺序：最底部指向主干，每个更高的 PR 指向紧邻下方那个的头分支。

## 链接缺失的栈成员

先把已有栈项与预期链对比。一个已有栈可能包含请求链的一个保序子集；出现多个栈号、意外项或冲突顺序时，需要用户指示再改。

当某个依赖 PR 还不在官方栈里：

1. 精确比较每个 `author.login`。
2. 作者全一致时，按自下而上的顺序自动链接：

```sh
gh stack link --base <主干> <底部PR> <下一个PR> ... <顶部PR>
```

3. 作者不同或有作者取不到时，改 GitHub 状态前先问用户。
4. 重新查询 GraphQL，要求：一个栈号、预期主干、完整 PR 集、预期位置与基线链。

永远不要自动解散、重排或重建一个已有栈；`gh stack link` 是加法，已合并或已入队的项无法解栈。

## 只在需要时刷新

不要因为有刷新机制就重写分支。当活的合并状态或仓库规则要求更新主干时，二选一：

- **原生级联 rebase**：用 `gh stack checkout <pr或栈>` 检出远端栈（本地未跟踪时），再跑 `gh stack sync`。它可能在本地校验前就 rebase 并 lease 保护地强推每一层；立刻检查被重写的范围，对每一层跑相关检查，在它们通过前不要合并或宣称就绪。`gh stack rebase` 解决冲突后用 `gh stack push` 发布。checkout 或 sync 报告本地与远端栈组成分歧时，取消并询问，不要自动删除或重建远端栈。
- **增量 merge-forward**：把主干并进最底部受影响的层，再自下而上把每个更新过的父分支并入其子分支，正常推送。过程中基线前进时，先保存那个检查点再并入更新的 tip。

评审后允许任何历史重写，但它使提交 OID 假设失效。推送后重新拉取确切头并重新核对未解决的评审线程、批准、可合并性与检查。**绝不使用裸 `--force`**，也不要覆盖并发前进的远端头。

## 合并前预检范围

合并前立刻重查官方栈。要求每个被选中的 PR 都是开启、非草稿、在预期顺序、且满足仓库的评审与检查要求。把每个 PR 的状态独立对待：顶层就绪不能证明它的依赖就绪。

"落地这个栈"选中整个栈。部分落地需要一个显式的边界 PR，并包含从底部到该边界的每一层。

## 通过栈 API 合并

按官方栈号合并整个栈：

```sh
gh stack merge <栈号> --yes --merge
```

显式请求的部分落地，通过边界 PR 合并：

```sh
gh stack merge <边界PR> --yes --merge
```

不要传 `--delete-branch`、不要手动重定向依赖、不要逐 PR 下合并命令。GitHub 自下而上合并选中范围，并重定向或 rebase 剩下的上层。直接栈合并是全有或全无；主干使用合并队列时，GitHub 把选中范围一起入队，但可能分组合落地。

不要绕过合并要求。原生合并报告阻塞时，检查并通过拥有它的 PR 解决，或停下报告；**绝不**退回 `gh pr merge`。

## 核对落地状态

等每个被选中的 PR 都报告 `MERGED`；入队不算完成落地：

```sh
gh pr view <pr> --json number,state,mergedAt,mergeCommit,baseRefName,headRefName
```

部分落地时，重查官方栈，核对每个剩余 PR 仍按预期顺序链接、且指向栈主干或它下方那一层。因为 GitHub 可能已 rebase 剩余层，重新检查当前头、评审状态与 CI。

删分支只在对应的 PR 报告 `MERGED` 后、单独最后一遍做。删之前要求 GitHub 报告没有开启的 PR 还以它为基线：

```sh
gh pr list --state open --base <分支> --json number --jq length
```

结果不是 `0` 就阻止删除。

## 清单

- [ ] 原生 `gh stack` 可用；每个 PR 分支都在同一个仓库。
- [ ] 活的 PR 基线与确切头确定了一条自下而上的依赖链。
- [ ] GraphQL 报告一个官方栈，主干、项与顺序符合预期；符合同作者条件的未栈链已自动链接。
- [ ] 被重写的层都通过了相关校验，之后重新核对了评审线程、批准、可合并性与检查。
- [ ] 整个栈或显式限定的前缀，都通过 `gh stack merge --yes --merge` 提交。
- [ ] 每个被选中的 PR 都报告 `MERGED`；剩余上层仍构成预期官方栈。
- [ ] 分支删除只发生在核对过合并状态与零依赖之后。
