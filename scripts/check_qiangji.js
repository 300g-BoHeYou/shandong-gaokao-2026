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
eval(fs.readFileSync(path.join(root, "data_qiangji.js"), "utf8"));
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
ok(fd.examTime.indexOf("6月12日") >= 0, "复旦初试6月12日");
ok(fd.majors.find((m) => m.cat === "基础医学").subj === "数理化综合", "复旦基础医学考查数理化综合");
const ustc = QJ.schools.find((s) => s.name === "中国科学技术大学");
ok(ustc.majors.length === 9 && ustc.majors[0].subj === "数学、物理", "中科大 9 类, 笔试数学+物理");
const csu = QJ.schools.find((s) => s.name === "中南大学");
ok(csu.ratio === "5倍" && csu.entry.indexOf("145") >= 0, "中南 5倍 + 数学≥145破格");
const scut = QJ.schools.find((s) => s.name === "华南理工大学");
ok(scut.note.indexOf("取消竞赛破格") >= 0, "华南理工取消竞赛破格");
const gk = QJ.schools.find((s) => s.name === "国防科技大学");
ok(gk && gk.majors.length === 3, "国防科大 3 个专业类");

console.log("== 普通批参考分(自动匹配) ==");
const matched = QJ.schools.reduce((n, s) => n + s.majors.filter((m) => m.s != null).length, 0);
ok(matched > 50, "自动匹配到分专业参考分的专业类 " + matched + " 条");
ok(qh.schoolScore === undefined, "已移除院校级分数(第3条要求)");
// 找一个确实匹配到的样例
let sample = null;
QJ.schools.forEach((s) => s.majors.forEach((m) => { if (m.s != null && !sample) sample = { s: s.name, m: m }; }));
ok(!!sample, "存在同名专业匹配样例: " + (sample ? sample.s + " " + sample.m.cat + " → " + sample.m.s + "分/" + sample.m.r + "名" : "-"));

console.log("== 渲染 ==");
const out = document.getElementById("results").innerHTML;
ok(out.indexOf("清华大学") >= 0, "渲染含清华");
ok(out.indexOf("出分前校考") >= 0 && out.indexOf("出分后校考") >= 0, "出分前/后校考徽章均出现");
ok(out.indexOf("清北模式") < 0 && out.indexOf("复交南模式") < 0, "不再使用民间俗称");
ok(out.indexOf("待查证") >= 0, "未填字段显示'待查证'");
ok(out.indexOf("无笔试") >= 0, "仅面试院校考查科目显示'无笔试'");
ok(out.indexOf("class=\"rk") >= 0, "包含专业带软科排名标签");
ok(out.indexOf("简章原名：") >= 0, "带方向括号的给出简章原名提示");
ok(out.indexOf("score-box") < 0, "不再展示院校级分数块");
ok(out.indexOf('class="majors"') >= 0, "专业类表格渲染");
const stats = document.getElementById("stats").innerHTML;
ok(stats.indexOf("39") >= 0 && stats.indexOf("11") >= 0 && stats.indexOf("28") >= 0 && stats.indexOf("16") >= 0,
  "统计条含 39/11/28/16");

console.log("== 第4条规则: 专业名直接落入包含专业 ==");
const chemRow = qj.DATA.find((s) => s.name === "清华大学").majors.find((m) => m.cat === "化学");
ok(chemRow.inc === "化学", "'化学'(具体专业) 直接预填为包含专业");
const chemLei = qj.DATA.find((s) => s.name === "厦门大学").majors.find((m) => m.cat === "化学类");
ok(chemLei.inc === "", "'化学类'(大类名) 保留待查证");
const gzw = qj.DATA.find((s) => s.name === "中国人民大学").majors.find((m) => m.cat.indexOf("古文字学") >= 0);
ok(gzw.inc === "汉语言文学" && gzw.raw.indexOf("古文字学") >= 0, "带括号方向: 去括号后预填+保留原名提示");
const jlu = qj.DATA.find((s) => s.name === "吉林大学");
ok(jlu.majors.length === 4, "吉林大学 4 个专业(官方简章), 实际 " + jlu.majors.length);
ok(jlu.majors.map((m) => m.cat).join("、") === "数学与应用数学、物理学、化学、古文字学", "吉大专业与官方一致");
const seu = qj.DATA.find((s) => s.name === "东南大学");
ok(seu.majors.length === 1 && !seu.majors[0].cat, "东南大学专业类留空(官方专业表为图片)");
ok(seu.ratio.indexOf("4倍") >= 0, "东南大学入围比例 4倍(官网)");

console.log("== 第7条: 清华按文理试验班标注 ==");
const tsinghua = qj.DATA.find((s) => s.name === "清华大学");
const thMath = tsinghua.majors.find((m) => m.cat === "数学与应用数学");
ok(thMath.r != null && thMath.s != null, "清华数学与应用数学=理科试验班参考: " + (thMath.s + "分/" + thMath.r + "名"));
const thWen = tsinghua.majors.find((m) => m.cat === "哲学类");
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
qj.S.form = "全部"; qj.S.mkw = "古文字";
const gkSchools = QJ.schools.filter(qj.schoolMatches).length;
ok(gkSchools > 5, "按专业类关键词'古文字'筛选 = " + gkSchools + " 所");
qj.S.mkw = "";

console.log("== 页面元素 ==");
const qjHtml = fs.readFileSync(path.join(root, "qiangji.html"), "utf8");
["modeBox", "formBox", "kw", "mkw", "resetBtn", "results", "stats"].forEach((id) => {
  ok(qjHtml.indexOf('id="' + id + '"') >= 0, "qiangji.html 含 #" + id);
});
ok(qjHtml.indexOf('href="index.html"') >= 0 && qjHtml.indexOf('href="qiangji.html"') >= 0, "强基页含切换入口");
const idxHtml = fs.readFileSync(path.join(root, "index.html"), "utf8");
ok(idxHtml.indexOf('href="qiangji.html"') >= 0, "一批次页含强基入口");
ok(idxHtml.indexOf("综合评价（敬请期待）") >= 0 && qjHtml.indexOf("综合评价（敬请期待）") >= 0, "两页均含综招占位");

console.log("\n结果: " + pass + " 通过, " + fail + " 失败");
process.exit(fail ? 1 : 0);
