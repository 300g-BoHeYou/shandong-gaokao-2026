# 上线指引：发布到 GitHub + GitHub Pages

本项目是纯静态站点（无构建步骤、无服务器依赖），发布非常简单。以下两种方式任选。

## 方式 A：网页操作（最简）

1. **创建仓库**：登录 [github.com](https://github.com) → New repository → 仓库名如 `shandong-gaokao-2026` → Public（公开）或 Private（私有）→ 不要勾选 README/.gitignore（本地已有）。
2. **推送代码**（在本地项目目录打开终端）：
   ```bash
   git init
   git add .
   git commit -m "山东2026高考志愿参考：投档数据+软科排名整合"
   git branch -M main
   git remote add origin https://github.com/<你的用户名>/shandong-gaokao-2026.git
   git push -u origin main
   ```
3. **启用 Pages**：仓库页面 → Settings → Pages → Source 选 `Deploy from a branch` → Branch 选 `main`、目录选 `/ (root)` → Save。
4. 等待 1~2 分钟，访问 `https://<你的用户名>.github.io/shandong-gaokao-2026/` 即可。

## 方式 B：GitHub CLI（`gh`）

```bash
# 登录（浏览器授权）
gh auth login

# 创建仓库并推送
gh repo create shandong-gaokao-2026 --public --source . --remote origin --push

# 启用 Pages（默认 main 分支根目录）
gh api -X POST repos/{owner}/shandong-gaokao-2026/pages \
  -f "source[branch]=main" -f "source[path]=/"
```

## 方式 C：GitHub Actions 自动发布（含自测）

仓库根目录已含 `.github/workflows/deploy.yml`（见下），推送后 Actions 会自动：
1. 运行 Node 自测脚本（`verify_app.js` / `smoke_dom.js`）；
2. 构建并部署到 `gh-pages` 分支；
3. 之后在 Settings → Pages → Source 选 `Deploy from a branch`，分支 `gh-pages`、目录 `/ (root)`。

> 注：方式 A/B 直接使用 `main` 根目录即可，无需 Actions；Actions 适合希望"提交即自动部署 + 构建校验"的维护流程。

## 发布后收尾

- 将本文件 `docs/DEPLOY.md` 中的链接占位替换为实际地址，或直接在 GitHub 仓库页面编辑 `README.md` 的"在线使用"一行。
- 数据有更新时：本地重跑 `python scripts/build_data.py` 等脚本 → `git add . && git commit && git push`，Pages 自动更新。
