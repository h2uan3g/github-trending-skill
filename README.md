# github-trending-skill

Agent Skill：在编码 Agent 里查 GitHub 热门项目、拉 GitHub Trending 榜单、分析任意仓库。
An Agent Skill that lets your coding agent search popular GitHub repositories, read the GitHub Trending page, and turn any repo into Chinese usage documentation.

三种模式 / Three modes:

| 模式 | 能力 | 实现 |
| --- | --- | --- |
| **A. Popular Search** | 按语言 / topic / star 数搜热门仓库 | GitHub REST Search API（`curl`） |
| **B. Trending** | 日/周/月榜单，含「今日新增 star」 | `trending.py` 解析 github.com/trending |
| **C. Repo Analysis** | 抓取 README → 中文使用方法、适用场景、类似项目推荐 | `repo_analyze.py` + Agent 二次加工 |

依赖：仅 Python 3 标准库，**无需 `pip install`**。

---

## 安装 / Install

### Pi

```bash
# 从 GitHub 源码安装（推荐）
pi install git:github.com/h2uan3g/github-trending-skill

# 试用一次、不写进配置
pi -e git:github.com/h2uan3g/github-trending-skill

# 本地目录安装
git clone https://github.com/h2uan3g/github-trending-skill
cd github-trending-skill && pi install .
```

### 通用 Agent Skills 安装器（Claude Code / Codex / Cursor 等）

```bash
npx skills add h2uan3g/github-trending-skill        # 装进当前项目
npx skills add h2uan3g/github-trending-skill -g     # 装到用户级
npx skills add h2uan3g/github-trending-skill -l     # 只看有哪些技能
```

### 手动

```bash
git clone https://github.com/h2uan3g/github-trending-skill
cp -r github-trending-skill/skills/github-trending ~/.agents/skills/
```

任何遵循 [Agent Skills 规范](https://agentskills.io/specification) 的客户端都可以直接把 `skills/github-trending/` 放进 `.agents/skills/` 或 `~/.agents/skills/`。

---

## 使用 / Usage

装好后用自然语言触发，或强制调用：

```
/skill:github-trending 最近火的 Python AI 项目
```

| 你说 | 触发模式 |
| --- | --- |
| 「热门 Python 项目」「stars 最多的 AI 仓库」 | A |
| 「这周 trending 的 Go 项目」「最近火了什么」 | B |
| 「分析下 https://github.com/xxx/yyy」「这个仓库怎么用？」「推荐类似项目」 | C |

### 直接跑脚本

```bash
SKILL_DIR=~/.agents/skills/github-trending   # 技能目录（含 SKILL.md 的那个目录）

# Trending 榜单：[language] [daily|weekly|monthly]
python3 "$SKILL_DIR/trending.py" Python daily
python3 "$SKILL_DIR/trending.py" Go weekly

# 仓库分析：输出 repo / readme / similar_projects 三段 JSON
python3 "$SKILL_DIR/repo_analyze.py" https://github.com/owner/repo
python3 "$SKILL_DIR/repo_analyze.py" owner/repo
```

输出示例（`trending.py`）：

```json
[
  {
    "full_name": "calesthio/OpenMontage",
    "url": "https://github.com/calesthio/OpenMontage",
    "description": "World's first open-source, agentic video production system...",
    "language": "Python",
    "total_stars": "52,359",
    "total_forks": "6,559",
    "period_stars": "1,292 stars today"
  }
]
```

模式 C 的最终交付物由 Agent 生成：核心特性 → 环境要求 → 使用方法（安装 + 快速开始）→ ✅适合 / ❌不适合 → 类似项目对比表。

---

## 限流 / Rate limits

未认证：core API 10 次/小时、search API 30 次/分钟。设置 token 后 5,000 次/小时：

```bash
export GITHUB_TOKEN=ghp_xxx
```

`trending.py` 走 github.com/trending 网页，不占 API 配额。

---

## 已知限制 / Notes

- Trending 榜单依赖 github.com/trending 的 HTML 结构；GitHub 改版时需要更新 `trending.py` 里的正则。
- 「今日新增 star」只有 trending 页面提供，官方 search API 没有对应字段。
- 部分仓库无 README 或使用 `.rst`；`repo_analyze.py` 会依次尝试 `main`/`master` 与 API，实在没有则 `readme` 为空字符串。
- 模式 C 每次消耗 2–4 个 API 调用，无 token 时约 2–3 次分析后会撞限流。

## 许可

[MIT](LICENSE)
