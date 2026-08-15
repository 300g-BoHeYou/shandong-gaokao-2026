# ============================================================
# 一键发布：推送到 GitHub 并启用 GitHub Pages
# 用法：在本机普通 PowerShell 终端运行  .\publish.ps1
# 前提：已登录 GitHub（网页授权过 git，或安装了 gh 并 gh auth login）
# ============================================================

$ErrorActionPreference = "Stop"

$USER = Read-Host "请输入 GitHub 用户名"
if (-not $USER) { Write-Host "用户名不能为空"; exit 1 }
$REPO = Read-Host "仓库名（默认 shandong-gaokao-2026）"
if (-not $REPO) { $REPO = "shandong-gaokao-2026" }
$VIS = Read-Host "公开/私有（public/private，默认 public）"
if (-not $VIS) { $VIS = "public" }

# 0) 已存在远程则先移除
git remote remove origin 2>$null | Out-Null

# 1) 创建远程仓库（若 gh 可用则自动创建；否则提示网页创建）
if (Get-Command gh -ErrorAction SilentlyContinue) {
    gh repo create "$USER/$REPO" --$VIS --source . --remote origin --push
    if ($LASTEXITCODE -ne 0) {
        Write-Host "gh 创建仓库失败，请检查登录状态（gh auth login）。"
        exit 1
    }
    Write-Host "已通过 gh 创建并推送仓库。"
} else {
    Write-Host "未检测到 gh CLI。请在浏览器创建仓库："
    Write-Host "  https://github.com/new  -> 仓库名 $REPO -> $VIS"
    Read-Host "创建完成后按回车继续"
    git remote add origin "https://github.com/$USER/$REPO.git"
    git push -u origin main
    if ($LASTEXITCODE -ne 0) {
        Write-Host "推送失败：请检查远程地址、网络与凭据。"
        exit 1
    }
}

# 2) 启用 GitHub Pages（main 分支根目录）
if (Get-Command gh -ErrorAction SilentlyContinue) {
    gh api -X POST "repos/$USER/$REPO/pages" -f "source[branch]=main" -f "source[path]=/" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Pages 启用失败，请在仓库 Settings -> Pages 手动启用（branch: main, /root）。"
    } else {
        Write-Host "GitHub Pages 已启用。"
    }
} else {
    Write-Host "请手动启用 Pages：Settings -> Pages -> Source: Deploy from a branch -> main / (root) -> Save"
}

Write-Host ""
Write-Host "======================================================"
Write-Host "在线地址: https://$USER.github.io/$REPO/"
Write-Host "（首次启用后需等待 1-2 分钟）"
Write-Host "======================================================"
Read-Host "按回车关闭"
