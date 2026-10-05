# 恢复续做指南（GIT-RECOVERY）

本文件说明当前仓库**从哪来的、处于什么状态、怎么接着做**。
它由一次误删后的恢复过程生成，可以随时删除，不影响应用运行。

---

## 一、当前状态

- 分支 `main`，远端 `origin` = `https://github.com/300g-BoHeYou/shandong-gaokao-2026.git`
- 工作区**干净**（`git status` 无改动）
- 全部自测通过：`verify_app 101` · `smoke_dom 82` · `check_qiangji 68` · `verify_fav 6` · `verify_data` / `check_ids` / `check_tags` 通过

### 提交历史

```
d40bf40  feat(强基): 官方来源补充+参考分扩充+显示修复     ← 恢复出的最新进度
0dd29cc  fix(强基): 按反馈修订6项
e8d8a42  feat: 强基计划模块(页面+切换入口+查证表)
35945a4  feat: 分数/位次醒目化展示                        ← 误删前已推送到 GitHub 的最后一次提交
```

**恢复方式**：项目误删后，以 GitHub 上的 `35945a4` 为基线，把 DSH 会话日志
（`session.v4.jsonl`，完整记录了 288 次文件写/改操作）中该提交之后的全部操作
逐条重放，重现了丢失的 3 次提交内容。

> 注意：这 3 个提交是**重新生成**的，SHA 与原会话日志中的 `f35c2bd` / `42269c7` / `89b1a23`
> 不同（原提交对象随 `.git` 一起丢失）；**提交信息与文件内容按原样还原**。
> 三个提交的 `changed` 统计也与原日志吻合（9 / 7 / 9 个文件）。

---

## 二、接着做之前，需要做的 3 件事

### 1) 把恢复的 3 个提交推送到 GitHub

凭据已存在于本机 Windows 凭据管理器（`git:https://github.com`，账号 `300g-BoHeYou`），
在你自己的终端里直接执行即可，无需重新登录：

```powershell
cd "2026山东高考-恢复"
git push origin main
```

推送会触发 `.github/workflows/deploy.yml`：先在 CI 上跑
`verify_app.js` / `smoke_dom.js` / `check_tags.js` / `check_ids.js`，
**全部通过后**才部署到 GitHub Pages。这四个脚本本地已验证通过，CI 应当顺利。

### 2) 决定本项目放在哪个目录继续做

本次恢复产物在工作区 `高考恢复\2026山东高考-恢复\`。原项目路径是
`E:\赵弘毅\高三\2026山东高考`（已被误删）。建议：
把 `2026山东高考-恢复` 整个目录（含 `.git`）移动/改名为你想要的最终路径，
**再**回到 DSH 里继续对话——这样新会话的工作目录与仓库根目录一致，
页面、数据与脚本的相对路径都不会错位。

### 3) 确认线上地址是否仍有效

`README.md` 里写的在线地址是 Cloudflare Pages 的 `https://sdgk.pages.dev`。
若该 Cloudflare 站点当初是直接上传部署（而非从 GitHub 构建），
它**不会**随本次推送自动更新，需要你在 Cloudflare 侧重新上传，或改为从 GitHub 构建。

---

## 三、已知的小瑕疵（建议下次顺手修掉）

1. **README 的两处口径已过时**（当时只改了数据与页面，漏改文档）：
   - 强基页说明仍写「清北模式/复交南模式」，而已按 commit `0dd29cc` 统一改为
     **「出分前/出分后」**（`data_qiangji.js` 中 `mode` 取值就是 `出分前` / `出分后`）；
   - `强基查证清单.xlsx` 的 Sheet2 专业信息实际是 **250 行**，README 写的是 247 行。
2. `README.md` 的「构造与自测」第 4 步提到「需先改造 `make_qiangji_sheet.py` 读取填好的表」，
   而当前脚本已是**直接生成**查证表与 `data_qiangji.js`，该提示可以更新。

---

## 四、下一步的实质工作（来自会话最后一次回复的遗留清单）

会话在 commit `d40bf40` 后列出仍待你填写的查证项：

- **入围比例**：35 校仍空缺；
- **入围方式 / 入围成绩计算**细节；
- **31 个大类名下的具体专业**（强基专业类名与本科目录不完全对应）；
- **东南大学专业类**：官方专业表为图片，无法读取，留空待补；
- 可选项：把「包含专业」的软科排名也写进 `强基查证清单.xlsx` 的 Sheet2（目前只在网页显示）。

---

## 五、重新构建数据的方法（改动原始数据后）

见 `README.md` 的「构建与自测」一节。要点：

```bash
python scripts/parse_catalog.py        # 目录 PDF -> catalog_tree.json
python scripts/merge_manual_check.py   # 合并人工查证清单 -> manual_check.json
python scripts/build_data.py           # -> data_ruanke.js / data_toudang.js / data_fen.js
python scripts/make_qiangji_sheet.py   # -> 强基查证清单.xlsx + data_qiangji.js
```

> ⚠️ 当前 `data_*.js` 仍是**首次提交时构建**的版本：之后的提交只改了
> `scripts/build_data.py` 与查证数据，没有重新生成。若你更新过
> `2026山东高考第一批次投档.xlsx` 或查证清单，需要按上面顺序重跑一次。
