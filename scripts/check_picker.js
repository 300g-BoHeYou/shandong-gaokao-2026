// 三级专业选择器测试: 树渲染 / 单选专业 / 整类 / 整门类 / chips 展开与取消 / 搜索
const fs = require("fs");
const path = require("path");

class El {
  constructor(id) {
    this.id = id; this.innerHTML = ""; this.textContent = ""; this.value = "";
    this._l = {}; this.attrs = {}; this.hidden = false; this.parentNode = null;
  }
  addEventListener(t, f) { (this._l[t] = this._l[t] || []).push(f); }
  fire(t, e) { (this._l[t] || []).forEach((f) => f(e || { target: this })); }
  setAttribute(k, v) { this.attrs[k] = v; if (k === "hidden") this.hidden = true; }
  getAttribute(k) { return this.attrs[k] === undefined ? null : this.attrs[k]; }
  removeAttribute(k) { delete this.attrs[k]; if (k === "hidden") this.hidden = false; }
  hasAttribute(k) { return this.attrs[k] !== undefined; }
  querySelector() { return null; } querySelectorAll() { return []; }
  insertBefore() {} appendChild() {} contains() { return false; } closest() { return null; }
  removeChild() {}
}
const els = {};
global.window = {};
global.document = {
  readyState: "complete",
  getElementById: (id) => (els[id] = els[id] || new El(id)),
  createElement: (t) => new El(t), addEventListener() {}, body: new El("body"),
};

const root = path.join(__dirname, "..");
eval(fs.readFileSync(path.join(root, "data_catalog.js"), "utf8"));
eval(fs.readFileSync(path.join(root, "picker.js"), "utf8"));

let pass = 0, fail = 0;
function ok(c, m) { if (c) { pass++; console.log("  ✔", m); } else { fail++; console.log("  ✘ FAIL:", m); } }

// 构造一棵只含少量专业的小树(模拟强基页过滤后的树)
const tree = [
  { men: "理学", leis: [{ lei: "数学类", majors: [{ n: "数学与应用数学", cnt: 30 }, { n: "信息与计算科学", cnt: 12 }] }] },
  { men: "工学", leis: [{ lei: "计算机类", majors: [{ n: "计算机科学与技术", cnt: 40 }, { n: "软件工程", cnt: 35 }] }] },
  { men: "其他（不在本科专业目录中）", leis: [{ lei: "其他名称", majors: [{ n: "数理基础科学班", cnt: 2 }] }] },
];
const sel = { mens: {}, leis: {}, majors: {} };
let expanded = null;
const pk = window.MajorPicker.create({
  tree: tree, sel: sel,
  ids: { toggle: "pkToggle", panel: "pkPanel", search: "pkSearch", tree: "pkTree", chips: "selChips", clear: "pkClear", count: "pkCount" },
  onChange: (e) => { expanded = e; },
});

console.log("== 树渲染 ==");
const t = els.pkTree.innerHTML;
ok(t.indexOf("理学") >= 0 && t.indexOf("数学类") >= 0, "渲染门类与专业类");
ok(t.indexOf("数学与应用数学") >= 0 && t.indexOf("软件工程") >= 0, "渲染全部专业");
ok(t.indexOf("data-pk=\"men\"") >= 0 && t.indexOf("data-pk=\"lei\"") >= 0 && t.indexOf("data-pk=\"major\"") >= 0, "三级均可勾选");
ok(els.selChips.innerHTML.indexOf("尚未选择") >= 0, "初始提示未选择");
ok((els.pkCount.textContent || "") === "", "初始计数为空");

console.log("== 选择单个专业 ==");
sel.majors["软件工程"] = true;
pk.render(); expanded = pk.expanded();
ok(expanded["软件工程"] === true && Object.keys(expanded).length === 1, "选中单个专业 → 展开集合仅含该专业");
ok(els.selChips.innerHTML.indexOf("软件工程") >= 0, "chips 显示该专业");
ok(els.pkCount.textContent.indexOf("1") >= 0, "计数=1");

console.log("== 选择整个专业类 ==");
sel.leis["数学类"] = true;
pk.render(); expanded = pk.expanded();
ok(expanded["数学与应用数学"] && expanded["信息与计算科学"] && expanded["软件工程"], "整类选择展开为类内全部专业(并与已选专业并集)");
ok(els.selChips.innerHTML.indexOf("数学类（整类）") >= 0, "chips 显示“数学类（整类）”");
ok(els.selChips.innerHTML.indexOf("2专业") >= 0, "整类 chip 标注专业数");

console.log("== 选择整个门类 ==");
sel.mens["工学"] = true;
pk.render(); expanded = pk.expanded();
ok(expanded["计算机科学与技术"] && expanded["软件工程"], "整门类选择展开为其下全部专业");
ok(els.selChips.innerHTML.indexOf("工学（整门类）") >= 0, "chips 显示“工学（整门类）”");

console.log("== 直接取消(chips 上的 ×) ==");
els.selChips.fire("click", { target: { getAttribute: (k) => (k === "data-rmk" ? "men" : k === "data-v" ? "工学" : null) } });
ok(!sel.mens["工学"], "点击 × 直接取消整门类选择(无需回到目录)");
pk.render(); expanded = pk.expanded();
ok(!expanded["计算机科学与技术"], "取消后展开集合同步移除");

console.log("== 展开 chip 查看包含专业 ==");
let inserted = null;
els.selChips.querySelector = () => null;
const savedInsert = El.prototype.insertBefore;
El.prototype.insertBefore = function (n) { inserted = n; };
els.selChips.fire("click", { target: { getAttribute: (k) => (k === "data-exp" ? "lei" : k === "data-v" ? "数学类" : null), parentNode: { insertBefore: (n) => { inserted = n; } } } });
El.prototype.insertBefore = savedInsert;
ok(inserted && inserted.innerHTML.indexOf("数学与应用数学") >= 0, "整类 chip 可展开查看包含的专业");

console.log("== 搜索过滤 ==");
els.pkSearch.value = "软件";
els.pkSearch.fire("input");
const t2 = els.pkTree.innerHTML;
ok(t2.indexOf("软件工程") >= 0 && t2.indexOf("数学与应用数学") < 0, "搜索“软件”只显示匹配专业");

console.log("== 清空 ==");
els.pkClear.fire("click");
ok(Object.keys(sel.mens).length + Object.keys(sel.leis).length + Object.keys(sel.majors).length === 0, "清空已选");
ok(pk.expanded() && Object.keys(pk.expanded()).length === 0, "清空后展开集合为空");

console.log("\n结果: " + pass + " 通过, " + fail + " 失败");
process.exit(fail ? 1 : 0);
