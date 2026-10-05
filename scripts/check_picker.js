// 三级专业选择器测试: 树渲染 / 单选专业 / 整类全勾 / 半打钩 / 全选-全不选 / chips 展开与取消 / 搜索
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
eval(fs.readFileSync(path.join(root, "data_catalog.js"), "utf8"));
eval(fs.readFileSync(path.join(root, "picker.js"), "utf8"));

let pass = 0, fail = 0;
function ok(c, m) { if (c) { pass++; console.log("  ✔", m); } else { fail++; console.log("  ✘ FAIL:", m); } }

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

// 模拟点击某个复选框
function click(kind, v, checked) {
  els.pkTree.fire("change", { target: { getAttribute: (k) => (k === "data-pk" ? kind : k === "data-v" ? v : null), checked: !!checked } });
}
function treeHas(ind) { return els.pkTree.innerHTML.indexOf(ind) >= 0; }

console.log("== 树渲染 ==");
const t = els.pkTree.innerHTML;
ok(t.indexOf("理学") >= 0 && t.indexOf("数学类") >= 0, "渲染门类与专业类");
ok(t.indexOf("数学与应用数学") >= 0 && t.indexOf("软件工程") >= 0, "渲染全部专业");
ok(t.indexOf('data-pk="men"') >= 0 && t.indexOf('data-pk="lei"') >= 0 && t.indexOf('data-pk="major"') >= 0, "三级均可勾选");

console.log("== 选择单个专业 ==");
click("major", "软件工程", true);
ok(sel.majors["软件工程"] === true && pk.expanded()["软件工程"], "勾选单个专业");
ok(els.selChips.innerHTML.indexOf("软件工程") >= 0, "chips 显示该专业");
ok(els.pkCount.textContent.indexOf("1") >= 0, "计数=1 个专业");

console.log("== 选择整个专业类: 类内所有专业都打钩 ==");
click("lei", "数学类", true);
ok(pk.expanded()["数学与应用数学"] && pk.expanded()["信息与计算科学"], "整类选择 -> 类内所有专业均被选中");
ok(sel.majors["数学与应用数学"] && sel.majors["信息与计算科学"], "选择状态写入两个专业");
ok(els.selChips.innerHTML.indexOf("数学类（整类）") >= 0, "chips 显示“数学类（整类）”");
ok(els.selChips.innerHTML.indexOf("2专业") >= 0, "整类 chip 标注专业数");

console.log("== 部分选择 -> 大类名半打钩 ==");
click("major", "信息与计算科学", false);   // 取消类内一个专业
ok(!sel.majors["信息与计算科学"] && sel.majors["数学与应用数学"], "取消类内一个专业");
ok(treeHas('data-pk="lei" data-v="数学类" data-ind="1"'), "专业类复选框变为半打钩(indeterminate)");
ok(!treeHas('data-pk="lei" data-v="数学类" checked'), "半打钩时不再显示为全选");
ok(els.selChips.innerHTML.indexOf("数学类（整类）") < 0 && els.selChips.innerHTML.indexOf("数学与应用数学") >= 0,
  "chips 改为显示具体专业");
ok(treeHas("已选该类部分专业"), "树中提示“已选该类部分专业”");

console.log("== 半打钩时再次点击 -> 全选; 再点 -> 全不选 ==");
click("lei", "数学类", false);   // 半选状态下点击(=勾选) -> 全选
ok(pk.expanded()["数学与应用数学"] && pk.expanded()["信息与计算科学"], "半打钩时点击 -> 全选该类");
ok(treeHas('data-pk="lei" data-v="数学类" checked'), "复选框恢复为全选");
click("lei", "数学类", false);   // 全选状态下点击 -> 全不选
ok(!pk.expanded()["数学与应用数学"] && !pk.expanded()["信息与计算科学"], "全选后再次点击 -> 全不选该类");

console.log("== 整个门类 ==");
click("men", "工学", true);
ok(pk.expanded()["计算机科学与技术"] && pk.expanded()["软件工程"], "整门类选择 -> 其下全部专业被选中");
ok(els.selChips.innerHTML.indexOf("工学（整门类）") >= 0, "chips 显示“工学（整门类）”");
click("major", "软件工程", false);
ok(treeHas('data-pk="men" data-v="工学" data-ind="1"'), "门类复选框半打钩");

console.log("== chips 上直接取消 ==");
els.selChips.fire("click", { target: { getAttribute: (k) => (k === "data-rmk" ? "lei" : k === "data-v" ? "数学类" : null) } });
ok(!sel.majors["数学与应用数学"], "点击 × 直接取消整类选择(无需回到目录)");

console.log("== 展开 chip 查看包含专业 ==");
let inserted = null;
els.selChips.fire("click", {
  target: {
    getAttribute: (k) => (k === "data-exp" ? "men" : k === "data-v" ? "工学" : null),
    parentNode: { insertBefore: (n) => { inserted = n; } },
  },
});
ok(inserted && inserted.innerHTML.indexOf("计算机类") >= 0, "整门类 chip 可展开查看包含的专业类");

console.log("== 搜索与清空 ==");
els.pkSearch.value = "软件";
els.pkSearch.fire("input");
const t2 = els.pkTree.innerHTML;
ok(t2.indexOf("软件工程") >= 0 && t2.indexOf("数学与应用数学") < 0, "搜索“软件”只显示匹配专业");
els.pkClear.fire("click");
ok(Object.keys(sel.majors).length === 0 && Object.keys(pk.expanded()).length === 0, "清空已选");

console.log("\n结果: " + pass + " 通过, " + fail + " 失败");
process.exit(fail ? 1 : 0);
