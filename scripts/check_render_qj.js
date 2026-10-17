// 强基页渲染检查: 三级选择器挂载 / 专业类合并(rowspan) / 无修改痕迹 / 选择器高亮
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
for (const f of ["data_catalog.js", "picker.js", process.argv[2] || "data_qiangji.js"]) {
  eval(fs.readFileSync(path.join(root, f), "utf8"));
}
const qj = require(path.join(root, "qiangji.js"));

let pass = 0, fail = 0;
function ok(c, m) { if (c) { pass++; console.log("  ✔", m); } else { fail++; console.log("  ✘ FAIL:", m); } }

const html = els.results.innerHTML;
console.log("== 渲染 ==");
ok(html.indexOf('class="school"') >= 0, "渲染院校卡片");
ok((html.match(/rowspan=/g) || []).length > 100, "专业类/考查科目单元格合并(rowspan " + (html.match(/rowspan=/g) || []).length + " 处)");
ok(html.indexOf("已修正名称") < 0 && html.indexOf("待核") < 0, "不含我的修改痕迹");
ok(html.indexOf("官方简章（阳光高考）") >= 0, "含官方简章链接");
const dircCount = (html.match(/class="dirc"/g) || []).length;
ok(dircCount === 22, "方向徽章只出现在 22 个带括号的专业类上, 实际 " + dircCount + " 个");

console.log("== 三级目录选择器(强基) ==");
ok(!!els.pkTree && els.pkTree.innerHTML.length > 500, "目录树已渲染(" + (els.pkTree ? els.pkTree.innerHTML.length : 0) + " 字符)");
ok(els.pkTree.innerHTML.indexOf('data-pk="men"') >= 0 && els.pkTree.innerHTML.indexOf('data-pk="lei"') >= 0
  && els.pkTree.innerHTML.indexOf('data-pk="major"') >= 0, "门类/专业类/专业三级可勾选");
ok(!!els.selChips, "已选区容器存在");
ok((els.selChips.innerHTML || "").indexOf("尚未选择") >= 0, "初始未选择提示");

console.log("== 命中高亮 ==");
qj.setSel({ "数学与应用数学": true, "信息与计算科学": true });
ok(QJ_count() > 20, "整类口径(数学类两专业)命中院校 " + QJ_count() + " 所");
function QJ_count() { return qj.DATA.filter(qj.schoolMatches).length; }

console.log("\n结果: " + pass + " 通过, " + fail + " 失败");
process.exit(fail ? 1 : 0);
