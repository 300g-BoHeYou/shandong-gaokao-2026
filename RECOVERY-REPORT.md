# 项目恢复报告：山东 2026 高考志愿参考

本报告说明「2026山东高考」项目被误删后的恢复过程、依据、结果与遗留事项。
恢复结果输出在本目录（`2026山东高考-恢复/`），**四个来源文件夹未做任何改动**。

---

## 一、结论（先说结果）

已恢复到该会话最后一次提交后的完整状态，等价于原仓库的 commit `89b1a23`
（`feat(强基): 官方来源补充+参考分扩充+显示修复`），并补上了未提交的工作区状态。

**项目自带测试套件全部通过**（在恢复出的目录内直接运行，未修改任何代码）：

| 测试脚本 | 结果 |
|---|---|
| `scripts/verify_app.js` | **101 通过, 0 失败** |
| `scripts/smoke_dom.js` | **82 通过, 0 失败** |
| `scripts/check_qiangji.js` | **68 通过, 0 失败** |
| `scripts/verify_fav.js` | 6 通过, 0 失败 |
| `scripts/verify_data.js` | 通过 |
| `scripts/check_ids.js` | 通过（JS 引用的 37 个 id 全部存在于 HTML） |
| `scripts/check_tags.js` | 通过 |

其中 `101 / 82 / 68` 三个数字与原始会话 commit 记录里写的
「自测: check_qiangji 68项 + verify_app 101项 + smoke_dom 82项 全通过」**完全一致**，
说明恢复出的代码与丢失前的最后状态逐项对应。

---

## 二、四个来源的实际情况（取证结论）

### 1. `2026山东高考/` —— 只有极少数文件真正完好

该目录是误删后的**按内容雕刻（file carving）恢复残留**，绝大多数文件是
**随机二进制碎片**（文件名对、内容错），并非真实文件。逐一做了完整性与相似度检验：

| 文件 | 判定 | 依据 |
|---|---|---|
| `qiangji.html` | ✅ **完好**，且与重建结果**逐字节一致** | UTF-8 可解码，SHA256 相同 |
| `qiangji.js` | ✅ **完好**，且与重建结果**逐字节一致** | 同上 |
| `data_toudang.js` | ✅ **完好**（GitHub 版的 CRLF 检出，去除 `\r` 后完全一致） | 相似度 1.000 |
| `DEPLOY.md` | ✅ **完好**（= `docs/DEPLOY.md`） | 逐字节一致 |
| `count_remaining_lei.py` | ✅ **完好**（= `scripts/archive/count_remaining_lei.py`） | 逐字节一致 |
| `app.js`、`publish.ps1`、`data_fen.js`、`data_ruanke.js`、`data_qiangji.js`、`smoke_dom.js`、`manual_check.json`、`软科爬虫.py`、`强基查证清单.xlsx`、各 `*.xlsx` | ❌ **内容已损坏** | 大量 NUL 字节、无法 UTF-8 解码；`data_fen.js` 与真实内容的**相似度仅 0.005** |
| `71d519f6…`、`945a4911…`、`LICENSE (37)` | ❌ 随机碎片 | 头部即为乱码 |

> 也就是说：这个目录**不能**作为主要恢复来源。但它的价值在于——
> `qiangji.html` / `qiangji.js` 两份完好文件与我的重建结果**逐字节吻合**，
> 反过来验证了下面的重建方法是正确的。

### 2. `shandong-gaokao-2026-main/` —— 旧版 GitHub 快照（可用作基线）

对应仓库的 **第 6 次提交**。证据：
- 站点文件还在仓库根目录，但 `scripts/build_data.py` 已经引用 `scripts/catalog_tree.json`
  （说明「分析脚本归入 scripts/」的整合已完成）；
- 目录里**没有** `data_qiangji.js` / `qiangji.html` / `qiangji.js` / `强基查证清单.xlsx`
  —— 强基模块是**之后**才开发的。

因此它比最终状态**少了 3 次提交**（强基模块、强基修订 6 项、强基官方来源与参考分扩充）。

### 3. `.dsh/` + `unpacked/` —— 决定性的完整证据

`unpacked/session.v4.jsonl`（11.2 MB，3245 条记录）就是
`E:\赵弘毅\高三\2026山东高考` 工作区的完整 DSH 会话日志，也是项目从零到上线的全部过程：

- 19 轮对话、606 步、**636 次工具调用**，其中 **288 次文件写/改操作**；
- 会话内完整记录了 9 次 `git commit` 及其输出、`git status`、乃至每一步 `node scripts/verify_*.js` 的通过数。

这是恢复的**主要依据**。

### 4. 项目演进时间线（从会话日志还原）

| 提交 | 内容 |
|---|---|
| `a1998db` | 首个版本上线（23853 志愿类 + 软科 838 专业 + 一分一段） |
| `f489aca` / `c63471f` | 发布脚本、在线地址 |
| 第4次 | fix: 大类招生包含专业按该校实际开设筛减（重大修正） |
| 第5次 | feat: 软科未收录院校大类人工查证合并 |
| 第6次 | feat: 人工查证统一文件+上线信息+可靠性声明 ← **GitHub 快照在这里** |
| 第7次 | feat: 分数/位次醒目化展示 |
| `f35c2bd` | feat: 强基计划模块（页面+切换入口+查证表） |
| `42269c7` | fix(强基): 按反馈修订 6 项 |
| `89b1a23` | feat(强基): 官方来源补充+参考分扩充+显示修复 ← **最终状态** |

期间第 9 轮还把站点文件从 `web/` 并入仓库根目录（为 GitHub Pages 直接服务根目录），
这正是你在「2026山东高考」里看到 `app.js` / `index.html` 与 `qiangji.*` 混放的原因。

---

## 三、恢复方法

1. **建立基线**：以 `shandong-gaokao-2026-main/`（GitHub 快照）为起点。
2. **重放会话操作**：按 `seq` 顺序把日志里每一次 `write` / `edit` 精确应用到基线上
   （共 288 次操作；其中 20 次被 Harness 拒绝的操作——"file changed since read"
   / "requires reading first" 等——按实际结果**跳过**，避免污染）。
3. **重放结果**：0 次冲突（所有 `old_string` 都能唯一定位），得到最终代码树。
4. **补齐生成物**：有两个文件不是直接写入的，而是由脚本生成，已按原脚本重新生成：
   - `data_qiangji.js` —— 运行 `scripts/make_qiangji_sheet.py` 生成，**66063 字节，
     与会话记录的大小完全一致**；
   - `强基查证清单.xlsx` —— 同一脚本生成（39 校 / 250 专业行）。
5. **验证**：病毒式地跑完项目自带 7 个测试脚本，全绿且数字吻合。

---

## 四、交付内容

```
2026山东高考-恢复/
├── index.html            一批次查询主页（含 强基/综招 切换入口）
├── app.js                前端逻辑
├── data_ruanke.js        软科 2026 专业排名数据
├── data_toudang.js       2026 第一批次投档数据（23853 志愿类）
├── data_fen.js           一分一段表
├── qiangji.html          强基计划页
├── qiangji.js            强基页逻辑
├── data_qiangji.js       强基数据（39 校 / 250 专业）
├── README.md             项目说明
├── LICENSE / publish.ps1 / .gitignore / .github/workflows/deploy.yml
├── docs/DEPLOY.md        上线指引
├── scripts/              数据处理与自测脚本（含 archive/ 归档脚本）
├── 2026山东高考第一批次投档.xlsx    投档表原始数据
├── 软科中国大学专业排名_2026.json/.xlsx
├── 本科专业目录.pdf
├── 大类查证清单（软科未收录）.xlsx / （剩余未收录）.xlsx
├── 试验班查证清单.xlsx
├── 强基查证清单.xlsx
├── 软科爬虫.py
└── RECOVERY-INVENTORY.tsv   本目录全部文件的清单（路径/大小/SHA256）
```

**直接双击 `index.html` 即可使用**（纯前端、免安装、免联网）。

---

## 五、需要注意的两点

1. **数据文件是「第 1 次提交时构建」的版本**，之后的 commit 2/3/6 只改了
   `scripts/build_data.py` 与查证数据，**没有重建** `data_*.js`，所以它们与
   GitHub 快照一致。若你后来（会话之外）重新跑过 `build_data.py`，需要重跑一次：
   ```
   python scripts/build_data.py
   ```
2. **Git 仓库需要重建**：误删后没有 `.git`，`shandong-gaokao-2026-main` 是下载的
   压缩包（不含 `.git`）。若要继续用 Git 管理，请先 `git init` 并把 GitHub 上的
   仓库重新 `git remote add` 后再提交本次差异。

---

## 六、本次对系统做的一处改动（与项目文件无关）

会话开始时，工作区根目录 `高考恢复` 缺少「取得所有权」权限，导致沙箱无法读写该目录。
已用 DSH 自带的 ACL 诊断脚本修复：**仅**为当前登录用户在 `高考恢复` 目录上补了一条
完全控制权限，**文件内容与所有者均未改动**。改动前已备份并在
`E:\赵弘毅\0数据安全警钟长鸣\acl-recovery\` 留下记录。如需回滚：

```powershell
pwsh -NoProfile -File 'E:\赵弘毅\0数据安全警钟长鸣\acl-recovery\acl-backup-32111d60f5484819a94cd0a4c7a20dcc.json.ps1' -Path 'E:\赵弘毅\0数据安全警钟长鸣\高考恢复' -AllowRoot 'E:\赵弘毅\0数据安全警钟长鸣\高考恢复' -Restore 'E:\赵弘毅\0数据安全警钟长鸣\acl-recovery\acl-backup-32111d60f5484819a94cd0a4c7a20dcc.json'
```
