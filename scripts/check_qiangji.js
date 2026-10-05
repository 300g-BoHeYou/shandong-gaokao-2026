// 验证强基页面: 数据结构 + 渲染 + 筛选 + 页面元素
const fs = require("fs");
const path = require("path");

class StubClassList { add(){} remove(){} toggle(){} contains(){return false;} }
class StubEl {
  constructor(){ this.innerHTML=""; this.textContent=""; this.value=""; this.checked=false;
    this.onclick=null; this.classList=new StubClassList(); this.style={}; this._l={}; }
  addEventListener(t,f){ (this._l[t]=this._l[t]||[]).push(f); }
  fire(t,e){ (this._l[t]||[]).forEach(f=>f(e||{target:this})); }
  querySelectorAll(){ return []; } closest(){ return null; } contains(){ return false; }
  appendChild(){} removeChild(){} click(){} setAttribute(){} getAttribute(){ return null; }
}
const els = {};
global.window = {};
global.document = {
  readyState: "complete",
  getElementById: (id) => (els[id] = els[id] || new StubEl()),
  createElement: () => new StubEl(),
  addEventListener(){}, body: new StubEl()
};
global.localStorage = { _d:{}, getItem(k){return this._d[k]||null;}, setItem(k,v){this._d[k]=String(v);} };

const root = path.join(__dirname, "..");
const dataFile = process.argv[2] || "data_qiangji.js";
eval(fs.readFileSync(path.join(root, dataFile), "utf8"));
const qj = require(path.join(root, "qiangji.js"));
const QJ = global.window.QJ2026;

let pass = 0, fail = 0;
function ok(c, m) { if (c) { pass++; console.log("  ✔", m); } else { fail++; console.log("  ✘ FAIL:", m); } }

console.log("== 数据 ==");
ok(QJ && QJ.schools.length === 39, "39 所高校, 实际 " + (QJ ? QJ.schools.length : 0));
const pre = QJ.schools.filter((s) => s.mode === "出分前");
const post = QJ.schools.filter((s) => s.mode === "出分后");
ok(pre.length === 11, "出分前校考(复交南模式) 11 所, 实际 " + pre.length);
ok(post.length === 28, "出分后校考(清北模式) 28 所, 实际 " + post.length);
const noExam = QJ.schools.filter((s) => (s.form || "").indexOf("仅面试") >= 0);
ok(noExam.length === 16, "仅面试(无笔试) 16 所, 实际 " + noExam.length);
const preNames = pre.map((s) => s.name).sort();
ok(JSON.stringify(preNames) === JSON.stringify(["中国人民大学", "中国科学技术大学", "厦门大学", "同济大学", "复旦大学", "南京大学", "北京航空航天大学", "浙江大学", "西安交通大学", "上海交通大学", "东南大学"].sort()),
  "出分前 11 校名单正确");
ok(QJ.schools.filter((s) => s.ratio).length > 0, "部分院校有入围比例数据");

console.log("== 关键字段(考生关注) ==");
const qh = QJ.schools.find((s) => s.name === "清华大学");
ok(qh.ratio === "6倍", "清华入围比例 6倍");
ok(qh.majors.length === 11, "清华 11 个强基专业类, 实际 " + qh.majors.length);
ok(qh.majors.some((m) => m.cat === "数理基础科学"), "清华含'数理基础科学'(类名与目录无关)");
ok(qh.majors.find((m) => m.cat === "数理基础科学").subj === "数学、物理、化学", "清华理科笔试科目=数学、物理、化学");
ok(qh.majors.find((m) => m.cat === "哲学类").subj === "数学、语文、历史", "清华文科笔试科目=数学、语文、历史");
const pku = QJ.schools.find((s) => s.name === "北京大学");
ok(pku.ratio === "6倍" && pku.majors.length === 10, "北大 6倍/10 专业类");
const fd = QJ.schools.find((s) => s.name === "复旦大学");
ok(fd.examTime.indexOf("6月15日") >= 0, "复旦初试6月15日前(官方简章): " + fd.examTime);
ok(fd.majors.find((m) => m.cat === "基础医学").subj === "数理化综合", "复旦基础医学考查数理化综合");
const ustc = QJ.schools.find((s) => s.name === "中国科学技术大学");
ok(ustc.majors.length === 9 && ustc.majors[0].subj === "数学、物理", "中科大 9 类, 笔试数学+物理");
const csu = QJ.schools.find((s) => s.name === "中南大学");
ok(csu.ratio === "5倍", "中南入围比例 5倍(官方简章)");
ok((csu.entry + csu.brk + csu.note).indexOf("145") >= 0, "中南 数学≥145 破格/直接入围");
const scut = QJ.schools.find((s) => s.name === "华南理工大学");
ok(scut.note.indexOf("取消竞赛破格") >= 0, "华南理工取消竞赛破格");
const gk = QJ.schools.find((s) => s.name === "国防科技大学");
ok(gk && gk.majors.length === 3, "国防科大 3 个专业类");

console.log("== 普通批参考分(自动匹配) ==");
const matched = QJ.schools.reduce((n, s) => n + s.majors.reduce((a, m) => a + m.items.filter((i) => i.s != null).length, 0), 0);
ok(matched > 50, "自动匹配到分专业参考分的专业条数 " + matched);
ok(qh.schoolScore === undefined, "已移除院校级分数(第3条要求)");
let sample = null;
QJ.schools.forEach((s) => s.majors.forEach((m) => m.items.forEach((i) => { if (i.s != null && !sample) sample = { s: s.name, i: i }; })));
ok(!!sample, "存在同名专业匹配样例: " + (sample ? sample.s + " " + sample.i.n + " → " + sample.i.s + "分/" + sample.i.r + "名" : "-"));

console.log("== 渲染 ==");
const out = document.getElementById("results").innerHTML;
ok(out.indexOf("清华大学") >= 0, "渲染含清华");
ok(out.indexOf("出分前校考") >= 0 && out.indexOf("出分后校考") >= 0, "出分前/后校考徽章均出现");
ok(out.indexOf("清北模式") < 0 && out.indexOf("复交南模式") < 0, "不再使用民间俗称");
ok(out.indexOf("待查证") >= 0, "未填字段显示'待查证'");
ok(out.indexOf("无笔试") >= 0, "仅面试院校考查科目显示'无笔试'");
ok(out.indexOf("class=\"rk") >= 0, "包含专业带软科排名标签");
ok(out.indexOf("class=\"dirc\"") >= 0, "方向备注以醒目徽章显示");
ok(out.indexOf("简章原名：") < 0, "不再显示冗长的'简章原名'提示(仅保留括号内容)");
ok(out.indexOf("refscore") >= 0 && out.indexOf("refrank") >= 0, "参考分显示为 分数（排名）");
ok(out.indexOf("score-box") < 0, "不再展示院校级分数块");
ok(out.indexOf("官方简章（阳光高考） ↗") >= 0, "院校卡片含阳光高考官方简章链接");
ok(out.indexOf("bm.chsi.com.cn/jcxkzs/sch/") >= 0, "链接指向阳光高考强基报名平台");
ok(qj.DATA.filter((x) => x.jzLink).length >= 10, "部分院校附学校官网简章直链: " + qj.DATA.filter((x) => x.jzLink).length + " 所");
ok(out.indexOf("该校未收录软科") >= 0, "软科未收录院校显示'该校未收录软科'(而非'未排名')");
ok(out.indexOf('class="majors"') >= 0, "专业类表格渲染");
const stats = document.getElementById("stats").innerHTML;
ok(stats.indexOf("39") >= 0 && stats.indexOf("11") >= 0 && stats.indexOf("28") >= 0 && stats.indexOf("16") >= 0,
  "统计条含 39/11/28/16");

console.log("== 报名时间/官方链接(官方汇总) ==");
const allSignup = qj.DATA.filter((s) => s.signup).length;
ok(allSignup === 39, "39 校报名时间齐全, 实际 " + allSignup);
ok(qj.DATA.every((s) => s.link), "39 校均有官方链接");
ok(qj.DATA.find((s) => s.name === "北京大学").signup.indexOf("2026-04-15") >= 0, "北大报名时间为阳光高考平台精确时间");
ok(qj.DATA.filter((x) => x.ratio).length === 39, "39 校入围比例齐全");

console.log("== 第2条: 大类含该专业则填其分数(非专项最低分) ==");
const xmu = qj.DATA.find((s) => s.name === "厦门大学").majors.find((m) => m.cat === "数学类").items.find((i) => i.n === "数学与应用数学");
ok(xmu.s === 648 && xmu.r === 5370, "厦大数学类-数学与应用数学=648分/5370名(排除马来西亚分校600分): " + xmu.s + "/" + xmu.r);
const sjtu = qj.DATA.find((s) => s.name === "上海交通大学").majors.find((m) => m.cat === "数学与应用数学").items[0];
ok(sjtu.s === 682 && sjtu.r === 451, "上交数学与应用数学=682分/451名(试验班查证含该专业): " + sjtu.s + "/" + sjtu.r);
const ouc = qj.DATA.find((s) => s.name === "中国海洋大学").majors.find((m) => m.cat === "海洋科学").items[0];
ok(ouc.s === 627 && ouc.r === 12910, "海大海洋科学=627分/12910名(排除专项625/中外合作597): " + ouc.s + "/" + ouc.r);
const withRef = qj.DATA.reduce((n, s) => n + s.majors.reduce((a, m) => a + m.items.filter((i) => i.r != null).length, 0), 0);
ok(withRef >= 150, "有分专业参考分的专业条数 " + withRef + " (≥150)");
const totalItems = qj.DATA.reduce((n, s) => n + s.majors.reduce((a, m) => a + m.items.length, 0), 0);
ok(totalItems > 300, "专业类已按专业拆分为独立条目: " + totalItems + " 条");
const rankedItems = qj.DATA.reduce((n, s) => n + s.majors.reduce((a, m) => a + m.items.filter((i) => i.st === "ranked").length, 0), 0);
ok(rankedItems > 250, "逐专业软科排名条数 " + rankedItems);

console.log("== 第4条规则: 专业名直接落入包含专业 ==");
const chemRow = qj.DATA.find((s) => s.name === "清华大学").majors.find((m) => m.cat === "化学").items[0];
ok(chemRow.n === "化学", "'化学'(具体专业) 逐条列出");
const chemLei = qj.DATA.find((s) => s.name === "厦门大学").majors.find((m) => m.cat === "化学类");
ok(chemLei.items.length > 1, "'化学类'已拆分多个专业: " + chemLei.items.map((i) => i.n).join("/"));
const gzw = qj.DATA.find((s) => s.name === "中国人民大学").majors.find((m) => m.cat.indexOf("古文字学") >= 0);
ok(gzw.items[0].n === "汉语言文学" && gzw.note.indexOf("古文字学") >= 0, "带括号方向: 去括号后作为专业+备注仅保留括号内容");
const jlu = qj.DATA.find((s) => s.name === "吉林大学");
ok(jlu.majors.length === 4, "吉林大学 4 个专业(官方简章), 实际 " + jlu.majors.length);
ok(jlu.majors.map((m) => m.cat).join("、") === "数学与应用数学、物理学、化学、古文字学", "吉大专业与官方一致");
const seu = qj.DATA.find((s) => s.name === "东南大学");
ok(seu.majors.filter((m) => m.cat).length >= 2, "东南大学已补专业类: " + seu.majors.filter((m) => m.cat).map((m) => m.cat).join("/"));
ok(seu.ratio.indexOf("4倍") >= 0, "东南大学入围比例 4倍(官网)");

console.log("== 第7条: 清华按文理试验班标注 ==");
const tsinghua = qj.DATA.find((s) => s.name === "清华大学");
const thMath = tsinghua.majors.find((m) => m.cat === "数学与应用数学").items[0];
ok(thMath.r != null && thMath.s != null, "清华数学与应用数学=理科试验班参考: " + (thMath.s + "分/" + thMath.r + "名"));
const thWen = tsinghua.majors.find((m) => m.cat === "哲学类").items[0];
ok(thWen.r != null && thWen.r > thMath.r, "清华文科类=文科试验班参考(位次更靠后): " + (thWen.s + "分/" + thWen.r + "名"));

console.log("== 仅面试院校考查科目 ==");
const scutM = qj.DATA.find((s) => s.name === "华南理工大学").majors[0];
ok(scutM.subj === "无笔试", "华南理工考查科目='无笔试'");
const fdChem = qj.DATA.find((s) => s.name === "复旦大学").majors.find((m) => m.cat === "化学");
ok(fdChem.subj === "化学", "复旦化学考查科目=化学");

console.log("== 筛选 ==");
ok(qj.schoolMatches({ name: "复旦大学", mode: "出分前", form: "笔试+面试+体测", majors: [] }) === true, "出分前筛选命中");
qj.S.mode = "出分前";
ok(QJ.schools.filter(qj.schoolMatches).length === 11, "筛选出分前 = 11 所");
qj.S.mode = "全部"; qj.S.form = "仅面试";
ok(QJ.schools.filter(qj.schoolMatches).length === 16, "筛选仅面试 = 16 所");
qj.S.form = "全部"; qj.S.major = "汉语言文学";
const gkSchools = QJ.schools.filter(qj.schoolMatches).length;
ok(gkSchools > 8, "按专业'汉语言文学'筛选 = " + gkSchools + " 所");
qj.S.major = "古文字学";
ok(QJ.schools.filter(qj.schoolMatches).length >= 1, "按专业'古文字学'(仅少数校直接开设)筛选: "
  + QJ.schools.filter(qj.schoolMatches).length + " 所");
qj.S.major = "数学与应用数学";
const mathSchools = QJ.schools.filter(qj.schoolMatches).length;
ok(mathSchools > 20, "按专业'数学与应用数学'筛选 = " + mathSchools + " 所");
qj.S.major = "";

const uni = new Set();
QJ.schools.forEach((s) => s.majors.forEach((m) => m.items.forEach((i) => { if (i.n) uni.add(i.n); })));
ok(uni.size > 50, "可选专业(去重) " + uni.size + " 个, 适合下拉列表");
ok(QJ.schools.every((s) => s.majors.every((m) => m.items.every((i) => i.fix === undefined))), "数据中不含我的修改痕迹字段");

console.log("== 页面元素 ==");
const qjHtml = fs.readFileSync(path.join(root, "qiangji.html"), "utf8");
["modeBox", "formBox", "kw", "majorSel", "resetBtn", "results", "stats"].forEach((id) => {
  ok(qjHtml.indexOf('id="' + id + '"') >= 0, "qiangji.html 含 #" + id);
});
ok(qjHtml.indexOf('href="index.html"') >= 0 && qjHtml.indexOf('href="qiangji.html"') >= 0, "强基页含切换入口");
const idxHtml = fs.readFileSync(path.join(root, "index.html"), "utf8");
ok(idxHtml.indexOf('href="qiangji.html"') >= 0, "一批次页含强基入口");
ok(idxHtml.indexOf("综合评价（敬请期待）") >= 0 && qjHtml.indexOf("综合评价（敬请期待）") >= 0, "两页均含综招占位");

console.log("\n结果: " + pass + " 通过, " + fail + " 失败");
process.exit(fail ? 1 : 0);
