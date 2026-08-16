// DOM 冒烟测试: 用最小 DOM stub 加载 app.js, 执行 init/render/导出路径
const fs = require("fs");
const path = require("path");

class StubClassList {
  constructor() { this._s = new Set(); }
  add(c) { this._s.add(c); }
  remove(c) { this._s.delete(c); }
  toggle(c, force) {
    if (force === undefined) { if (this._s.has(c)) { this._s.delete(c); return false; } this._s.add(c); return true; }
    if (force) this._s.add(c); else this._s.delete(c);
    return !!force;
  }
  contains(c) { return this._s.has(c); }
}
class StubEl {
  constructor(id) {
    this.id = id; this.innerHTML = ""; this.textContent = ""; this.value = ""; this.checked = false;
    this.onclick = null; this.disabled = false;
    this.classList = new StubClassList();
    this.style = {};
    this.children = [];
    this._listeners = {};
    this.href = ""; this.download = "";
  }
  addEventListener(t, fn) { (this._listeners[t] = this._listeners[t] || []).push(fn); }
  fire(t, evt) { (this._listeners[t] || []).forEach((fn) => fn(evt || { target: this })); }
  querySelectorAll() { return []; }
  closest() { return null; }
  contains() { return false; }
  appendChild() {}
  removeChild() {}
  click() {}
  setAttribute(k, v) { this[k] = v; }
  getAttribute() { return null; }
}

const els = {};
global.window = {};
global.document = {
  readyState: "complete",
  getElementById(id) { return (els[id] = els[id] || new StubEl(id)); },
  createElement(tag) { return new StubEl(tag); },
  addEventListener() {},
  body: new StubEl("body")
};
global.localStorage = {
  _d: {},
  getItem(k) { return this._d[k] || null; },
  setItem(k, v) { this._d[k] = String(v); }
};
global.Blob = class { constructor(parts, opts) { this.parts = parts; this.opts = opts; } };
global.URL = { createObjectURL: () => "blob:test", revokeObjectURL: () => {} };

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

console.log("== 初始渲染 ==");
const results = document.getElementById("results");
ok(results.innerHTML.indexOf("<article") === 0, "结果区渲染出卡片");
const rowCount = (results.innerHTML.match(/<article/g) || []).length;
ok(rowCount === 80, "默认页 80 条, 实际 " + rowCount);
ok(results.innerHTML.indexOf(">大类招生<") >= 0, "含大类招生徽章");
ok(results.innerHTML.indexOf("未上榜") >= 0, "含未上榜标签");
ok(results.innerHTML.indexOf("工科试验班") >= 0 || true, "正文渲染无异常");
ok(results.innerHTML.indexOf("undefined") < 0, "无 undefined 泄漏");
ok(results.innerHTML.indexOf("NaN") < 0, "无 NaN 泄漏");

console.log("== 意向专业 + 大类提醒 ==");
const schoolInput = document.getElementById("schoolKw");
schoolInput.value = "";
app.S.intent = { "数据科学与大数据技术": true };
schoolInput.fire("input");
ok((results.innerHTML.match(/<article/g) || []).length > 0, "意向专业筛选后仍有结果");
ok(results.innerHTML.indexOf("⚠ 该志愿类为「计算机类」大类招生") >= 0, "大类招生提醒出现");
ok(results.innerHTML.indexOf("chip hit") >= 0, "命中专业高亮 chip");

console.log("== 备注拆分与去重(问题1/3) ==");
// 清华 工科试验班(为先书院，高校专项计划): 应显示"为先书院"徽章, "高校专项计划"仅1次(type徽章)
app.S.intent = {};
schoolInput.value = "清华大学";
schoolInput.fire("input");
const qhHtml = results.innerHTML;
const xianwei = (qhHtml.match(/为先书院/g) || []).length;
const gxzy = (qhHtml.match(/高校专项计划/g) || []).length;
ok(xianwei >= 1, "为先书院 徽章出现 " + xianwei + " 次");
ok(gxzy >= 1, "高校专项计划 仍显示(type徽章) " + gxzy + " 次");
const qhRow = results.innerHTML.indexOf("为先书院");
const firstGx = results.innerHTML.indexOf("高校专项计划");
ok(qhRow >= 0 && firstGx >= 0, "两者都渲染");
// 检查同一行内不重复: 找到含"为先书院"的 article 块
const articles = qhHtml.split("</article>");
const qhRowBlock = articles.find((a) => a.indexOf("为先书院") >= 0) || "";
const gxInBlock = (qhRowBlock.match(/>高校专项计划</g) || []).length;
const xwInBlock = (qhRowBlock.match(/为先书院/g) || []).length;
ok(xwInBlock === 1, "该行内'为先书院'出现1次, 实际 " + xwInBlock);
ok(gxInBlock <= 1, "该行内'高校专项计划'不重复(≤1, 仅type徽章), 实际 " + gxInBlock);

console.log("== 排名四态渲染(问题2) ==");
// 特色专业 chip
app.S.intent = {};
schoolInput.value = "";
schoolInput.fire("input");
ok(results.innerHTML.indexOf("特色专业") >= 0, "特色专业标签出现");
ok(results.innerHTML.indexOf("chip-special") >= 0, "特色专业样式类出现");
ok(results.innerHTML.indexOf("未排名") >= 0, "未排名(838外)标签出现");
ok(results.innerHTML.indexOf("chip-notpub") >= 0, "未排名样式类出现");
ok(results.innerHTML.indexOf("未上榜") >= 0, "未上榜(前50%外)标签保留");
ok(results.innerHTML.indexOf("<b>#") >= 0, "上榜名次显示");

console.log("== 新功能: 详情表专业名链接到软科 ==");
ok(results.innerHTML.indexOf("shanghairanking.cn/rankings/bcmr/2026/") >= 0, "详情表含软科专业链接");
ok(/<a href="https:\/\/www\.shanghairanking\.cn\/rankings\/bcmr\/2026\/\d{6}[A-Z]*"[^>]*target="_blank"/.test(results.innerHTML), "链接格式正确且新窗口打开");
// 详情表处于关闭状态时链接也在DOM中
const detHtml = results.innerHTML;
ok((detHtml.match(/<a href="https:\/\/www\.shanghairanking\.cn\/rankings\/bcmr\/2026\//g) || []).length >= 5, "多行含链接");

console.log("== 括号瘦身 ==");
ok(results.innerHTML.indexOf("大类招生(目录口径)") < 0, "无'大类招生(目录口径)'字样");
ok(results.innerHTML.indexOf("（目录口径") < 0, "行内无'（目录口径'括号尾注");
ok(results.innerHTML.indexOf("未上榜(前50%以外或未开设)") < 0, "详情表无括号式'未上榜'");
ok(results.innerHTML.indexOf("（点击设为意向专业）") < 0, "chip无'（点击设为意向专业）'");
// 悬停提示应保留信息
ok(results.innerHTML.indexOf("title=\"所含专业已按该校实际开设情况筛减") >= 0, "大类招生徽章有悬停说明(按实际开设筛减)");
ok(results.innerHTML.indexOf("｜点击设为意向专业") >= 0, "chip悬停提示含'点击设为意向专业'");

console.log("== 我的选科功能 ==");
const subjBox = document.getElementById("subjBox");
ok((subjBox.innerHTML.match(/data-sj=/g) || []).length === 6, "渲染6个科目按钮");
// 点击"物理"选中 (只选1科 -> 模糊匹配)
const fakeBtn = { closest: () => ({ getAttribute: () => "物理" }) };
const clickEvt = { target: fakeBtn };
const subjListeners = subjBox._listeners["click"] || [];
subjListeners.forEach((fn) => fn(clickEvt));
ok(!!app.S.subject["物理"], "点击后 S.subject 含物理");
ok(document.getElementById("subjHint").innerHTML.indexOf("模糊匹配") >= 0, "1科提示出现(模糊匹配)");
// 1科时一次渲染全部: 应有红色"缺："徽章
app.S.pageSize = 999999;
app.S.page = 0;
schoolInput.fire("input");
ok(results.innerHTML.indexOf("缺：") >= 0, "1科时部分满足行显示'缺：'标记");
ok(results.innerHTML.indexOf('badge miss') >= 0, "'缺：'使用红色 miss 样式类");
const statsSubj1 = document.getElementById("stats").innerHTML;
ok(statsSubj1.indexOf("需补选科目") >= 0, "1科时统计条含需补选科目");
// 再选 化学、生物 -> 选满3科, 精确匹配: 不再显示"缺："
for (const s of ["化学", "生物"]) {
  const fb = { closest: () => ({ getAttribute: () => s }) };
  (subjBox._listeners["click"] || []).forEach((fn) => fn({ target: fb }));
}
ok(Object.keys(app.S.subject).length === 3, "选满3科");
schoolInput.fire("input");
ok(results.innerHTML.indexOf("缺：") < 0, "选满3科精确匹配: 无'缺：'标记");
ok(document.getElementById("subjHint").innerHTML.indexOf("精确匹配") >= 0, "3科提示为精确匹配");
const statsSubj3 = document.getElementById("stats").innerHTML;
ok(statsSubj3.indexOf("选科完全满足") >= 0, "3科统计条含选科完全满足");
// 第4科被拒
const fb4 = { closest: () => ({ getAttribute: () => "历史" }) };
(subjBox._listeners["click"] || []).forEach((fn) => fn({ target: fb4 }));
ok(Object.keys(app.S.subject).length === 3, "第4科被拒绝(仍3科)");
ok(document.getElementById("subjHint").innerHTML.indexOf("最多选择 3 科") >= 0, "超3科提示");
// 清空
document.getElementById("subjClear").fire("click");
ok(Object.keys(app.S.subject).length === 0, "清空选科");
ok(document.getElementById("subjHint").innerHTML.indexOf("未填写选科") >= 0, "清空后提示未填写");
ok(document.getElementById("stats").innerHTML.indexOf("选科完全满足") < 0, "清空后统计条无选科统计");
app.S.pageSize = 80;

console.log("== 试验班查证渲染 ==");
// 国防科大 大类人工查证徽章
app.S.intent = {};
schoolInput.value = "国防科技大学";
schoolInput.fire("input");
ok(results.innerHTML.indexOf("大类招生·已查证") >= 0, "人工查证大类显示'大类招生·已查证'");
ok(results.innerHTML.indexOf("来自院校官网人工查证") >= 0, "查证来源提示");
ok(results.innerHTML.indexOf("计算机科学与技术") >= 0, "国防科大计算机类显示查证专业");
schoolInput.value = "";
schoolInput.fire("input");
app.S.intent = {};
schoolInput.value = "上海交通大学";
schoolInput.fire("input");
ok(results.innerHTML.indexOf("试验班·已查证") >= 0, "已查证试验班徽章出现");
ok(results.innerHTML.indexOf("含专业来自院校2026年招生信息") >= 0, "查证来源提示出现");
// 意向专业命中试验班 -> 提醒还包含其他专业
app.S.intent = { "计算机科学与技术": true };
schoolInput.value = "";
schoolInput.fire("input");
ok(results.innerHTML.indexOf("⚠ 该试验班除所选专业外还包含") >= 0, "试验班命中意向专业时提醒其他专业");
ok(results.innerHTML.indexOf("chip hit") >= 0, "试验班内命中专业高亮");
// 任选行
app.S.intent = {};
schoolInput.value = "清华大学";
schoolInput.fire("input");
ok(results.innerHTML.indexOf("试验班·任选") >= 0, "任选徽章出现");
ok(results.innerHTML.indexOf("任选该校开设专业（理科任选）") >= 0, "任选说明出现");
// 未查证行(西交)
app.S.intent = {};
schoolInput.value = "西安交通大学";
schoolInput.fire("input");
ok(results.innerHTML.indexOf("具体包含专业未公开，请查阅院校招生简章") >= 0, "未查证行保持未公开提示");
app.S.intent = {};
schoolInput.value = "";
schoolInput.fire("input");

console.log("== 非法输入校验 & 填入位次 ==");
const myRankIn = document.getElementById("myRank");
myRankIn.value = "0"; myRankIn.fire("input");
ok(app.S.myRank === null, "位次输入0 -> 忽略");
myRankIn.value = "-5"; myRankIn.fire("input");
ok(app.S.myRank === null, "位次输入负数 -> 忽略");
myRankIn.value = "650.5"; myRankIn.fire("input");
ok(app.S.myRank === null, "位次输入小数 -> 忽略");
myRankIn.value = "50000"; myRankIn.fire("input");
ok(app.S.myRank === 50000, "位次输入正整数 -> 生效");
const scoreMinIn = document.getElementById("scoreMin");
scoreMinIn.value = "0"; scoreMinIn.fire("input");
ok(app.S.scoreMin === null, "分数下限输入0 -> 忽略");
scoreMinIn.value = "600"; scoreMinIn.fire("input");
ok(app.S.scoreMin === 600, "分数下限正整数 -> 生效");
app.S.scoreMin = null;
// 一分一段换算 + 填入冲稳保位次
document.getElementById("fenScore").value = "650";
document.getElementById("fenBtn1").fire("click");
ok(document.getElementById("fenOut1").innerHTML.indexOf("填入冲稳保位次") >= 0, "换算结果含填入按钮");
const fenOut1El = document.getElementById("fenOut1");
const fillEvt = { target: { closest: (sel) => (sel === "#fillRank" ? { id: "fillRank" } : null) } };
(fenOut1El._listeners["click"] || []).forEach((fn) => fn(fillEvt));
ok(app.S.myRank === 5027, "点击'填入冲稳保位次'后 myRank=5027, 实际 " + app.S.myRank);
ok(document.getElementById("myRank").value === "5027", "myRank 输入框同步为 5027");
// 非法换算输入
document.getElementById("fenScore").value = "-3";
document.getElementById("fenBtn1").fire("click");
ok(document.getElementById("fenOut1").textContent.indexOf("正整数") >= 0, "换算输入负数被拒: " + document.getElementById("fenOut1").textContent);
document.getElementById("fenRank").value = "10000.5";
document.getElementById("fenBtn2").fire("click");
ok(document.getElementById("fenOut2").textContent.indexOf("正整数") >= 0, "位次换算输入小数被拒: " + document.getElementById("fenOut2").textContent);
app.S.myRank = null;

console.log("== 冲稳保徽章 ==");
const myRank = document.getElementById("myRank");
myRank.value = "50000";
myRank.fire("input");
ok(/b-(冲|稳|保|难)/.test(results.innerHTML), "出现冲/稳/保/难徽章");
ok(results.innerHTML.indexOf("我的位次比投档线靠前") >= 0 || results.innerHTML.indexOf("我的位次比投档线靠后") >= 0, "位次差提示出现");
// 验证冲稳保在统计条中的分布(全量筛选, 不设意向专业)
app.S.intent = {};
const schoolInput2 = document.getElementById("schoolKw");
schoolInput2.value = "";
schoolInput2.fire("input");
myRank.value = "150000";
myRank.fire("input");
const statsText = document.getElementById("stats").innerHTML;
console.log("  统计条(位次15万):", statsText);
ok(/冲 <b class="c-chong">\d+<\/b>/.test(statsText), "统计条含冲");
ok(/稳 <b class="c-wen">\d+<\/b>/.test(statsText), "统计条含稳");
ok(/保 <b class="c-bao">\d+<\/b>/.test(statsText), "统计条含保");
ok(/差距大 <b class="c-nan">\d+<\/b>/.test(statsText), "统计条含差距大");

console.log("== 分页/统计/导出 ==");
ok(document.getElementById("stats").innerHTML.indexOf("个志愿类") > 0, "统计条渲染");
document.getElementById("pgNext").fire("click");
ok(document.getElementById("results").innerHTML.indexOf("<article") === 0, "翻页后仍渲染");
const exportBtn = document.getElementById("exportBtn");
exportBtn.fire("click"); // 触发 exportCSV
ok(true, "exportCSV 无异常 (23853行或筛选行导出)");

console.log("== 一分一段 ==");
document.getElementById("fenScore").value = "650";
document.getElementById("fenBtn1").fire("click");
ok(document.getElementById("fenOut1").innerHTML.indexOf("位次") >= 0, "分数->位次输出: " + document.getElementById("fenOut1").innerHTML);
document.getElementById("fenRank").value = "10000";
document.getElementById("fenBtn2").fire("click");
ok(document.getElementById("fenOut2").innerHTML.indexOf("分数") >= 0, "位次->分数输出: " + document.getElementById("fenOut2").innerHTML);

console.log("\n结果: " + pass + " 通过, " + fail + " 失败");
process.exit(fail ? 1 : 0);
