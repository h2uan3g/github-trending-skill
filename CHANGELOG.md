# Changelog

## 2.0.0

- 新增模式 C：`repo_analyze.py` 抓取仓库元数据 + 完整 README + 类似项目，由 Agent 产出中文使用方法、适用场景、类似项目推荐。
- `trending.py` 改为直接解析 github.com/trending 页面（社区 trending API 已下线），支持 daily / weekly / monthly 与 30+ 语言。
- **可移植性**：SKILL.md 不再硬编码 `.agents/skills/...` 安装路径，改用 `$SKILL_DIR`（本文件所在目录），因此可作为 Pi package、`npx skills add` 包或任意目录下的本地技能运行。
- 补充 frontmatter：`license`、`compatibility`、`metadata.repository`。
- 文档校正：写出两个脚本的真实输出 schema（含 `_rate_limited`），并说明进度信息走 stderr、JSON 走 stdout。
- 打包为 Pi package：仓库采用 `skills/` 约定目录 + `pi.skills` 清单。

## 1.x

- 仅模式 A（GitHub Search API `curl` 示例）与模式 B 的第三方 trending API 封装。
