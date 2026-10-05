const fs = require("fs");
class E {
  constructor() { this.innerHTML = ""; this.value = ""; this._l = {}; this.attrs = {}; }
  addEventListener(t, f) { (this._l[t] = this._l[t] || []).push(f); }
  fire(t, e) { (this._l[t] || []).forEach((f) => f(e || { target: this })); }
  setAttribute(k, v) { this.attrs[k] = v; }
  getAttribute(k) { return this.attrs[k]; }
  closest() { return null; }
  querySelectorAll() { return []; }
  appendChild() {}
}
const els = {};
global.window = {};
global.document = {
  readyState: "complete",
  getElementById: (id) => (els[id] = els[id] || new E()),
  createElement: () => new E(), addEventListener() {}, body: new E(),
};
eval(fs.readFileSync("data_qiangji_new.js", "utf8"));
const qj = require(require("path").join(__dirname, "..", "qiangji.js"));
const html = els.results.innerHTML;
console.log("rowspan 次数:", (html.match(/rowspan=/g) || []).length);
console.log("含'已修正名称':", html.indexOf("已修正名称") >= 0, " 含'待核':", html.indexOf("待核") >= 0);
console.log("下拉选项数:", (els.majorSel.innerHTML.match(/<option/g) || []).length);
const m = html.match(/<tr class="grp-start"><td rowspan="(\d+)">([^<]*)<\/td>/);
console.log("首个分组 rowspan:", m ? m[1] + " / " + m[2] : "-");
// 选一个专业后的渲染
qj.S.major = "数学与应用数学";
els.majorSel.value = "数学与应用数学";
els.results.innerHTML = "";
els.majorSel.fire("change", { target: els.majorSel });
const h2 = els.results.innerHTML;
console.log("筛选'数学与应用数学'后卡片数:", (h2.match(/class="school"/g) || []).length);
console.log("筛选后是否只出现该专业行:", h2.indexOf("信息与计算科学") < 0);
console.log("筛选后学校示例:", (h2.match(/class="sname">([^<]+)</g) || []).slice(0, 6).map((x) => x.replace(/.*>/, "")).join("、"));
