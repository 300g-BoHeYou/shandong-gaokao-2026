// 验证 app.js 逻辑 (Node 环境, 不加载 DOM)
const fs = require("fs");
const path = require("path");

global.window = {};
const webDir = path.join(__dirname, ".."); // 站点文件在仓库根目录
for (const f of ["data_ruanke.js", "data_toudang.js", "data_fen.js"]) {
  eval(fs.readFileSync(path.join(webDir, f), "utf8"));
}
const app = require(path.join(webDir, "app.js"));

let pass = 0, fail = 0;
function ok(cond, msg) {
  if (cond) { pass++; console.log("  ✔", msg); }
  else { fail++; console.log("  ✘ FAIL:", msg); }
}

console.log("== 基础 ==");
ok(app.TD.length === 23853, "投档行数 23853, 实际 " + app.TD.length);
ok(app.INTENT.length >= 1000, "意向专业列表 ≥1000, 实际 " + app.INTENT.length);

console.log("== 包含专业 ==");
const ck = app.containedKeys("计算机类");
ok(ck.length > 10, "计算机类 目录包含 " + ck.length + " 个专业");
ok(ck.some((k) => app.keyName(k) === "计算机科学与技术"), "含 计算机科学与技术");
ok(app.containedKeys("计算机科学与技术").length === 1, "计算机科学与技术 本身为具体专业");
ok(app.containedKeys("工科试验班").length === 0, "工科试验班 不推断具体专业");
ok(app.containedKeys("大数据与会计").length === 1, "未收录专业按名称自身保留");

console.log("== 排名查找 ==");
const tdQh = app.TD.find((r) => r[1] === "清华大学" && r[2] === "计算机类");
const qhRk = (global.window.TD_SCHOOL_RK)["清华大学"];
ok(qhRk === "清华大学", "清华 -> 软科名 清华大学");
const rk1 = app.rankOf(ck.find((k) => app.keyName(k) === "软件工程"), qhRk);
ok(rk1 === 1, "清华 软件工程 软科第1名, 实际 " + rk1);
const rk2 = app.rankOf(ck.find((k) => app.keyName(k) === "网络工程"), qhRk);
ok(rk2 === null, "清华 网络工程 未上榜(null)");

console.log("== 意向专业匹配 ==");
const r = tdQh;
ok(app.rowMatchesIntent(r, { "计算机科学与技术": true }, false) === true, "大类含意向专业 -> 命中");
ok(app.rowMatchesIntent(r, { "计算机科学与技术": true }, true) === false, "仅直接招生 -> 大类不命中");
ok(app.rowMatchesIntent(r, { "密码科学与技术": true }, false) === true, "大类含其他目录专业也命中(目录口径)");
const direct = app.TD.find((x) => x[2] === "软件工程");
ok(app.rowMatchesIntent(direct, { "软件工程": true }, true) === true, "直接招生命中");

console.log("== 冲稳保 (R=50000, c1=0.8, c2=1.15) ==");
ok(app.bandOf(50000, 48000, 0.8, 1.15) === "冲", "W=48000 冲");
ok(app.bandOf(50000, 50000, 0.8, 1.15) === "冲", "W=50000(压线) 冲");
ok(app.bandOf(50000, 55000, 0.8, 1.15) === "稳", "W=55000 稳");
ok(app.bandOf(50000, 60000, 0.8, 1.15) === "保", "W=60000 保 (>57500)");
ok(app.bandOf(50000, 30000, 0.8, 1.15) === "难", "W=30000 差距大");
ok(app.bandOf(null, 60000, 0.8, 1.15) === null, "未填位次 -> null");

console.log("== 筛选 ==");
app.S.intent = { "数据科学与大数据技术": true };
let idx = app.filteredIndices();
ok(idx.length === 397, "意向专业=数据科学与大数据技术 命中 397(含试验班查证7行), 实际 " + idx.length);
const cntDirect = idx.filter((i) => app.TD[i][2] === "数据科学与大数据技术").length;
ok(cntDirect === 320, "其中直接招生 320, 实际 " + cntDirect);
// 大类命中的行应全部含提醒条件
const leiHit = idx.filter((i) => app.TD[i][2] !== "数据科学与大数据技术" && app.containedKeys(app.TD[i][2]).length > 1);
ok(leiHit.length > 0, "大类命中行数 " + leiHit.length);

app.S.intent = {};
app.S.schoolKw = "山东大学";
idx = app.filteredIndices();
ok(idx.length > 0, "院校筛选 山东大学 -> " + idx.length + " 条");
app.S.schoolKw = "";

app.S.scoreMin = 600; app.S.scoreMax = 650;
idx = app.filteredIndices();
ok(idx.every((i) => { const s = app.TD[i][5]; return s != null && s >= 600 && s <= 650; }), "分数区间筛选正确");
app.S.scoreMin = null; app.S.scoreMax = null;

console.log("== 一分一段 ==");
const s1 = app.scoreToRank(650);
ok(s1 && s1.rank > 0 && s1.rank < 20000, "650分 -> 位次 " + (s1 && s1.rank) + " (合理区间)");
const s2 = app.scoreToRank(697);
ok(s2 && s2.rank === 56, "697分 -> 位次56");
const r1 = app.rankToScore(10000);
ok(r1 && typeof r1.score === "number" && r1.score < 697, "位次10000 -> 分数 " + (r1 && r1.score));

console.log("== 意向专业列表抽查 ==");
ok(app.INTENT.some((x) => x.n === "具身智能"), "含新专业 具身智能");
ok(app.INTENT.some((x) => x.n === "大数据与会计"), "含职业本科专业 大数据与会计");
const cs = app.INTENT.filter((x) => x.n.indexOf("计算机") >= 0);
console.log("  含'计算机'的意向专业:", cs.map((x) => x.n).slice(0, 12).join("、"), "…共", cs.length);

console.log("== 排名状态(四态) ==");
// 特色专业: 蒙医学(开设<4校)
const mengKey = Object.keys(app.RK_META).find((k) => app.RK_META[k].name === "蒙医学");
ok(!!mengKey, "找到特色专业 蒙医学: " + mengKey);
const stMeng = app.majorStatus(mengKey, "内蒙古医科大学");
ok(stMeng.st === "special", "蒙医学 -> special, 实际 " + stMeng.st);
const stMeng2 = app.majorStatus(mengKey, "");
ok(stMeng2.st === "special" && stMeng2.inList === false, "无软科院校时 special.inList=false");
// 未上榜: 清华 网络工程 (专业在838内, 清华未进前50%)
const ck2 = app.containedKeys("计算机类");
const wangKey = ck2.find((k) => app.keyName(k) === "网络工程");
const stWg = app.majorStatus(wangKey, "清华大学");
ok(stWg.st === "unranked", "清华 网络工程 -> unranked(前50%外)");
// ranked: 清华 软件工程
const ruanKey = ck2.find((k) => app.keyName(k) === "软件工程");
const stRj = app.majorStatus(ruanKey, "清华大学");
ok(stRj.st === "ranked" && stRj.rank === 1, "清华 软件工程 -> ranked #1");
// notpub: 具身智能 (2026版目录内, 但软科838未发布)
const stJz = app.majorStatus("具身智能", "上海交通大学");
ok(stJz.st === "notpub" && stJz.inCat === true, "具身智能 -> notpub 且为2026目录内专业(软科未发布)");

console.log("== 备注拆分与去重 ==");
ok(JSON.stringify(app.splitNote("为先书院，高校专项计划")) === JSON.stringify(["为先书院", "高校专项计划"]), "拆分为两部分");
ok(JSON.stringify(app.splitNote("含双学士学位项目、外语+财会等实验班选拔，高校专项")) === JSON.stringify(["含双学士学位项目、外语+财会等实验班选拔", "高校专项"]), "含顿号段不拆, 按逗号拆");
ok(JSON.stringify(app.splitNote("5+3一体化，儿科学")) === JSON.stringify(["5+3一体化", "儿科学"]), "5+3一体化拆分");
ok(JSON.stringify(app.splitNote("中外合作办学)(中南大学和蒙纳士大学中外合作办学项目")) === JSON.stringify(["中外合作办学", "中南大学和蒙纳士大学中外合作办学项目"]), "嵌套括号转逗号拆分");
ok(JSON.stringify(app.noteBadges("高校专项计划", "高校专项计划")) === "[]", "备注与类型完全重复 -> 去重");
ok(JSON.stringify(app.noteBadges("为先书院，高校专项计划", "高校专项计划")) === JSON.stringify(["为先书院"]), "部分重复 -> 仅保留非重复段");
ok(JSON.stringify(app.noteBadges("中外合作办学)(中南大学和蒙纳士大学中外合作办学项目", "中外合作办学")) === JSON.stringify(["中南大学和蒙纳士大学中外合作办学项目"]), "中外合作去重");
ok(JSON.stringify(app.noteBadges("高校专项", "高校专项计划")) === "[]", "前缀'高校专项'被'高校专项计划'覆盖");
ok(JSON.stringify(app.noteBadges("师范类，地方专项计划", "地方专项计划")) === JSON.stringify(["师范类"]), "师范类保留");
ok(JSON.stringify(app.noteBadges("无穹书院，高校专项计划", "高校专项计划")) === JSON.stringify(["无穹书院"]), "清华书院样例");

console.log("== 软科链接 ==");
ok(app.ruankeUrl("080901 计算机科学与技术") === "https://www.shanghairanking.cn/rankings/bcmr/2026/080901", "普通专业链接");
ok(app.ruankeUrl("100504K 蒙医学") === "https://www.shanghairanking.cn/rankings/bcmr/2026/100504K", "特色专业链接(带K)");
ok(app.ruankeUrl("大数据与会计") === null, "pseudo key 无链接");

console.log("== 我的选科判定 (subjectState) ==");
ok(app.subjectState("不限", { "物理": true }).state === "full", "不限 -> full");
ok(app.subjectState("物理、化学", { "物理": true, "化学": true, "生物": true }).state === "full", "物化生选3科 -> 物理化学要求 full");
ok(app.subjectState("物理", { "物理": true }).state === "full", "只选物理 -> 仅要求物理 full");
ok(app.subjectState("物理、化学", { "物理": true }).state === "partial"
  && JSON.stringify(app.subjectState("物理、化学", { "物理": true }).missing) === '["化学"]', "只选物理 -> 物理化学要求 partial 缺化学");
ok(app.subjectState("化学", { "物理": true }).state === "none", "只选物理 -> 仅要求化学 none 不显示");
ok(app.subjectState("物理、化学、生物", { "物理": true, "化学": true }).state === "partial"
  && JSON.stringify(app.subjectState("物理、化学、生物", { "物理": true, "化学": true }).missing) === '["生物"]', "物化 -> 物化生要求 partial 缺生物");
ok(app.subjectState("思想政治、历史、地理", { "物理": true, "化学": true, "生物": true }).state === "none", "物化生 -> 政史地要求 none");
ok(app.subjectState("物理、化学", {}).state === "full", "未填选科 -> 不限制 full");

// 集成: 物化生组合的筛选 (选满3科 -> 精确匹配)
app.S.subject = { "物理": true, "化学": true, "生物": true };
app.S.intent = {};
let idxS = app.filteredIndices();
const allS = app.TD.length;
ok(idxS.length < allS, "物化生筛选后数量减少: " + idxS.length + " / " + allS);
ok(idxS.every((i) => app.subjectState(app.TD[i][4], app.S.subject).state !== "none"), "物化生筛选后无 none 行");
ok(idxS.every((i) => app.subjectState(app.TD[i][4], app.S.subject).state !== "partial"), "选满3科精确匹配: 无 partial 行");
const stCnt3 = { full: 0, partial: 0, none: 0 };
app.TD.forEach((r) => stCnt3[app.subjectState(r[4], app.S.subject).state]++);
console.log("  物化生3科: 完全满足", stCnt3.full, "需补选(被排除)", stCnt3.partial, "不可报", stCnt3.none);
ok(idxS.length === stCnt3.full, "3科时结果=完全满足数");

// 只选1科 -> 宽松: partial 保留
app.S.subject = { "物理": true };
let idx1 = app.filteredIndices();
ok(idx1.some((i) => app.subjectState(app.TD[i][4], app.S.subject).state === "partial"), "只选物理1科: partial 行保留(模糊匹配)");
ok(idx1.every((i) => app.subjectState(app.TD[i][4], app.S.subject).state !== "none"), "只选物理1科: 无 none 行");
app.S.subject = {};

console.log("== 非法输入校验 (cleanNum) ==");
ok(app.cleanNum("0", 750) === null, "0 拒绝");
ok(app.cleanNum("-5", 750) === null, "负数拒绝");
ok(app.cleanNum("650.5", 750) === null, "小数拒绝");
ok(app.cleanNum("abc", 750) === null, "非数字拒绝");
ok(app.cleanNum("800", 750) === null, "超上限(分数>750)拒绝");
ok(app.cleanNum("2000000", 1000000) === null, "超上限(位次)拒绝");
ok(app.cleanNum("650", 750) === 650, "正整数正常");
ok(app.cleanNum(" 12 ", 100) === 12, "去空格后正常");
ok(app.cleanNum("", 750) === null, "空拒绝");

console.log("== 试验班查证合并 (syb) ==");
// 上交 工科试验班类(信息类): 查证为具体专业列表
const sybRow = app.TD.find((r) => r[1] === "上海交通大学" && r[2] === "工科试验班类" && r[3] === "信息类");
ok(sybRow && sybRow[8] && sybRow[8].mode === "list", "上交工科试验班类(信息类)有查证列表");
ok(sybRow[8].majors.length > 3, "查证专业数 >3, 实际 " + sybRow[8].majors.length);
ok(sybRow[8].majors.includes("计算机科学与技术"), "含计算机科学与技术");
// sybKeys 转换
const sk = app.sybKeys(sybRow);
ok(sk.length === sybRow[8].majors.length, "sybKeys 长度一致");
ok(sk.some((k) => app.keyName(k) === "计算机科学与技术"), "sybKeys 含计算机科学与技术");
// 意向专业匹配生效
ok(app.rowMatchesIntent(sybRow, { "计算机科学与技术": true }, false) === true, "试验班查证专业可被意向专业命中");
ok(app.rowMatchesIntent(sybRow, { "计算机科学与技术": true }, true) === false, "仅直接招生时试验班不命中");
ok(app.rowMatchesIntent(sybRow, { "临床医学": true }, false) === false, "不相关专业不命中");
// 任选行
const renRow = app.TD.find((r) => r[1] === "清华大学" && r[3] === "理科各专业");
ok(renRow && renRow[8] && renRow[8].mode === "renxuan", "清华理科试验班(理科各专业)为任选");
ok(renRow[8].dir === "理科任选", "任选方向=理科任选");
ok(app.rowMatchesIntent(renRow, { "计算机科学与技术": true }, false) === false, "任选行不参与意向专业匹配");
// 未查证行
const unfRow = app.TD.find((r) => r[1] === "西安交通大学" && r[2] === "工科试验班" && r[3] === "越杰电类领军班");
ok(unfRow && (unfRow[8] == null || unfRow[8].mode === "notfound"), "西交未填行保持未公开");
// 修正生效: 通讯工程->通信工程
const sybRow2 = app.TD.find((r) => r[1] === "上海理工大学" && r[2] === "工科试验班" && r[3] === "电子与信息类");
ok(sybRow2 && sybRow2[8].majors.includes("通信工程"), "通讯工程已修正为通信工程");
ok(!sybRow2[8].majors.includes("通讯工程"), "无未修正的通讯工程");
// 统计: 查证覆盖情况
const sybCnt = { list: 0, renxuan: 0, notfound: 0, null: 0 };
app.TD.forEach((r) => {
  const s = r[8];
  if (!s) sybCnt["null"]++;
  else sybCnt[s.mode]++;
});
console.log("  试验班查证分布:", JSON.stringify(sybCnt), " (list=", sybCnt.list, ", renxuan=", sybCnt.renxuan, ")");

console.log("== 试验班统计(问题4) ==");
const shiyan = app.TD.filter((r) => /试验班|实验班|试点班/.test(r[2]));
ok(shiyan.length === 312, "缺少具体专业的志愿类=312行, 实际 " + shiyan.length);
const shiyanNames = new Set(shiyan.map((r) => r[2]));
ok(shiyanNames.size === 12, "去重核心名=12个, 实际 " + shiyanNames.size);

console.log("\n结果: " + pass + " 通过, " + fail + " 失败");
process.exit(fail ? 1 : 0);
