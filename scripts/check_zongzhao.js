// 综招页测试: 数据完整性 / 渲染 / 校测冲突判定 / 三级专业筛选
const fs = require("fs");
const path = require("path");

class El {
  constructor(id) {
    this.id = id; this.innerHTML = ""; this.textContent = ""; this.value = "";
    this._l = {}; this.attrs = {}; this.hidden = false;
  }
  addEventListener(t, f) { (this._l[t] = this._l[t] || []).push(f); }
  fire(t, e) { (this._l[t] || []).forEach((f) => f(e || { target: this })); }
  setAttribute(k, v) { this.attrs[k] = v; if (k === "hidden") this.hidden = true; }
  getAttribute(k) { return this.attrs[k] === undefined ? null : this.attrs[k]; }
  removeAttribute(k) { delete this.attrs[k]; if (k === "hidden") this.hidden = false; }
  hasAttribute(k) { return !!this.attrs[k]; }
  querySelector() { return null; } querySelectorAll() { return []; }
  insertBefore() {} appendChild() {} contains() { return false; } closest() { return null; }
}
const els = {};
global.window = {};
global.document = {
  readyState: "complete",
  getElementById: (id) => (els[id] = els[id] || new El(id)),
  createElement: (t) => new El(t), addEventListener() {}, body: new El("body"),
};

const root = path.join(__dirname, "..");
for (const f of ["data_catalog.js", "picker.js", process.argv[2] || "data_zongzhao.js"]) {
  eval(fs.readFileSync(path.join(root, f), "utf8"));
}
const zz = require(path.join(root, "zongzhao.js"));
const DATA = zz.DATA;

let pass = 0, fail = 0;
function ok(c, m) { if (c) { pass++; console.log("  ✔", m); } else { fail++; console.log("  ✘ FAIL:", m); } }

console.log("== 数据完整性 ==");
ok(DATA.length === 19, "收录 19 所高校, 实际 " + DATA.length);
const pilot = DATA.filter((s) => s.area === "省内"), ov = DATA.filter((s) => s.area === "省外");
ok(pilot.length === 10 && ov.length === 9, "省内试点 10 / 省外自主 9, 实际 " + pilot.length + "/" + ov.length);
const pilotPlan = pilot.reduce((n, s) => n + (s.plan || 0), 0);
ok(pilotPlan === 1970, "省内试点计划合计 1970 人, 实际 " + pilotPlan);
const names = ["山东大学", "中国海洋大学", "中国石油大学（华东）", "哈尔滨工业大学（威海）", "青岛大学",
  "山东师范大学", "山东科技大学", "青岛科技大学", "山东财经大学", "华南理工大学"];
names.forEach((n) => ok(DATA.some((s) => s.name === n), "含 " + n));
const ovNames = ["北京外国语大学", "中国科学院大学", "南方科技大学", "上海纽约大学", "昆山杜克大学",
  "深圳北理莫斯科大学", "香港中文大学（深圳）", "上海科技大学", "西湖大学"];
ovNames.forEach((n) => ok(DATA.some((s) => s.name === n), "含省外 " + n));
ok(DATA.every((s) => s.url && /^https?:/.test(s.url)), "每所都有官方简章链接");
const withExam = DATA.filter((s) => (s.events || []).length).length;
ok(withExam >= 15, "已确认校测日期的院校 " + withExam + " 所");

console.log("== 校测时间(重点) ==");
const byName = (n) => DATA.find((s) => s.name === n);
const dt = (n) => (byName(n).events || []).map((e) => e.d).join(",");
ok(dt("山东大学") === "06-19", "山东大学 校测 6月19日");
ok(dt("中国海洋大学") === "06-19", "中国海洋大学 校测 6月19日");
ok(byName("中国海洋大学").examPlace.indexOf("崂山校区") >= 0
  && byName("中国海洋大学").examPlace.indexOf("松岭路238号") >= 0, "海大校测地点=崂山校区(松岭路238号)");
ok(dt("哈尔滨工业大学（威海）") === "06-19", "哈工大(威海) 校测 6月19日");
ok(dt("青岛大学") === "06-14,06-16", "青岛大学 笔试6/14 + 面试6/16");
ok(dt("山东师范大学") === "06-14,06-16", "山师 笔试6/14 + 面试6/16");
ok(dt("青岛科技大学") === "06-14,06-17", "青科 笔试6/14 + 面试6/17");
ok(dt("山东财经大学") === "06-14,06-16", "山财 笔试6/14 + 面试6/16");
ok(dt("华南理工大学") === "06-13,06-15", "华南理工 机试6/13 + 面试6/15");
ok(dt("中国科学院大学") === "06-13,06-14", "国科大 面试6/13-14");
ok(dt("香港中文大学（深圳）").indexOf("06-13") >= 0, "港中深 机考6/13");

console.log("== 招生专业: 目录解析 + 软科排名 ==");
const flat = (s) => {
  const out = [];
  (s.groups || []).forEach((g) => (g.entries || []).forEach((e) => {
    if (e.subs && e.subs.length) e.subs.forEach((x) => out.push(x));
    else out.push({ n: e.n, st: "nodir" });
  }));
  return out;
};
const upc = byName("中国石油大学（华东）");
const upcN = upc.groups.reduce((n, g) => n + g.entries.length, 0);
ok(upcN === 26, "中石大 26 个招生专业(类), 实际 " + upcN);
["地质学", "勘查技术与工程", "资源勘查工程", "海洋油气工程", "石油工程", "化工与制药类",
 "环保设备工程", "测控技术与仪器", "智能科学与技术", "汉语言文学"].forEach((m) => {
  ok(upc.groups.some((g) => g.entries.some((e) => e.n === m)), "中石大含 " + m);
});
const upcFlat = flat(upc);
ok(upcFlat.length >= 60, "中石大类展开后具体专业 " + upcFlat.length + " 个");
ok(upcFlat.filter((x) => x.st === "ranked").length >= 20, "中石大有软科排名的专业 " + upcFlat.filter((x) => x.st === "ranked").length + " 个");

const sdu = byName("山东大学");
ok(sdu.hasGroup && sdu.hasClass, "山大 有专业组 + 有「类」展开(3 层)");
const sduCs = sdu.groups[1].entries.find((e) => e.cls === "计算机类");
ok(!!sduCs && sduCs.kind === "lei" && sduCs.subs.length > 10, "山大 2 组「计算机类」展开为 " + (sduCs ? sduCs.subs.length : 0) + " 个具体专业");
ok(sduCs.subs.some((x) => x.n === "计算机科学与技术" && x.st === "ranked" && x.rk > 0),
  "计算机科学与技术 带软科排名: #" + (sduCs.subs.find((x) => x.n === "计算机科学与技术") || {}).rk);
const haida = byName("中国海洋大学");
ok(!haida.hasGroup && !haida.hasClass, "海大 无专业组、无「类」(1 层)");
ok(flat(haida).length === 4, "海大 4 个具体专业");
const others = DATA.reduce((n, s) => n + flat(s).filter((x) => x.st === "nodir").length, 0);
ok(others <= 6, "无法解析到目录的条目仅 " + others + " 条(试验班等)");
const rankedAll = DATA.reduce((n, s) => n + flat(s).filter((x) => x.st === "ranked").length, 0);
ok(rankedAll > 250, "全部院校有软科排名的专业条目 " + rankedAll + " 条");

console.log("== 渲染 ==");
const html = els.results.innerHTML;
ok((html.match(/<article class="school/g) || []).length === 19, "渲染 19 张院校卡片");
ok(html.indexOf("校测时间") >= 0 && html.indexOf("exam-time") >= 0, "卡片含醒目的校测时间");
ok((html.match(/rowspan=/g) || []).length > 20, "专业组/类单元格合并(rowspan " + (html.match(/rowspan=/g) || []).length + ")");
ok(html.indexOf("加入兼报") >= 0, "含加入兼报按钮");
ok(html.indexOf("软科排名") >= 0 && html.indexOf('class="rk ranked"') >= 0, "专业表含软科排名徽章");
ok(html.indexOf("<th>计划</th>") < 0 && html.indexOf("<th>校区</th>") < 0, "已去掉计划/校区列");
ok(html.indexOf("<th>专业组</th>") >= 0 && html.indexOf("<th>招生专业（类）</th>") >= 0
  && html.indexOf("<th>具体专业（目录）</th>") >= 0, "山大等含 组/类/具体专业 三列");
ok(els.stats.innerHTML.indexOf("19") >= 0, "统计条含院校总数");
ok(els.dateBox.innerHTML.indexOf("6月14日") >= 0, "日期筛选含 6月14日");

console.log("== 兼报冲突判定 ==");
const S = zz.S;
// 山大 + 哈工大(威海) 均为 6月19日 -> 冲突
S.picked = { "山东大学": true, "哈尔滨工业大学（威海）": true };
zz.renderPlan();
const p1 = els.planBody.innerHTML;
ok(p1.indexOf("冲突") >= 0, "6/19 山大+哈工大(威海) 判为冲突");
ok(p1.indexOf("只能确认") >= 0, "提示只能确认 1 所");
// 山大 + 华南理工(6/13 机试、6/15 面试) -> 不冲突
S.picked = { "山东大学": true, "华南理工大学": true };
zz.renderPlan();
const p2 = els.planBody.innerHTML;
ok(p2.indexOf("均不冲突") >= 0, "山大 + 华南理工 判为不冲突");
// 五所省属(6/14 笔试同日) -> 冲突且同日多校
S.picked = { "青岛大学": true, "山东师范大学": true, "山东财经大学": true };
zz.renderPlan();
const p3 = els.planBody.innerHTML;
ok(p3.indexOf("冲突") >= 0 && p3.indexOf("青岛大学") >= 0 && p3.indexOf("山东财经大学") >= 0,
  "省属三校 6/14 笔试同日冲突");
// 上纽大(3月) + 山大(6/19) -> 不冲突
S.picked = { "上海纽约大学": true, "山东大学": true };
zz.renderPlan();
ok(els.planBody.innerHTML.indexOf("均不冲突") >= 0, "上纽大(3月) + 山大(6/19) 不冲突");
S.picked = {};

console.log("== 三级专业筛选 ==");
zz.setSel({ "临床医学": true });
const nClin = DATA.filter(zz.schoolMatches).length;
ok(nClin >= 1, "筛'临床医学'命中 " + nClin + " 所");
zz.setSel({ "计算机科学与技术": true, "软件工程": true });
const nCs = DATA.filter(zz.schoolMatches).length;
ok(nCs >= 2, "筛计算机类命中 " + nCs + " 所");
zz.setSel({});
ok(DATA.filter(zz.schoolMatches).length === 19, "清空后恢复 19 所");

console.log("== 专业名规范化 ==");
ok(zz.baseName("汉语言文学（文化创意产业人才卓越班）") === "汉语言文学", "去掉方向括号");
ok(zz.baseName("工科试验班（未来信息）") === "工科试验班", "试验班去括号");
ok(zz.baseName("数据科学与大数据技术") === "数据科学与大数据技术", "无括号保持原样");

console.log("\n结果: " + pass + " 通过, " + fail + " 失败");
process.exit(fail ? 1 : 0);
