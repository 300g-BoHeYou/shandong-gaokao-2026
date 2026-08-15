// 交叉检查: app.js 引用的元素 id 是否都存在于 index.html
const fs = require("fs");
const path = require("path");

const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const js = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");

const htmlIds = new Set([...html.matchAll(/id="([^"]+)"/g)].map((m) => m[1]));
const jsRefs = new Set([...js.matchAll(/\$\("([^"]+)"\)/g)].map((m) => m[1]));

const DYNAMIC = new Set(["pgPrev", "pgNext", "pgSize"]); // 渲染时动态生成到 #pager 内
let fail = 0;
for (const id of [...jsRefs].sort()) {
  if (!htmlIds.has(id) && !DYNAMIC.has(id)) { console.log("✘ JS 引用但 HTML 缺失:", id); fail++; }
}
console.log("JS 引用的 id 数:", jsRefs.size, " 全部存在于 HTML:", fail === 0);
console.log("HTML id 总数:", htmlIds.size);

// 脚本引用检查
for (const f of ["data_ruanke.js", "data_toudang.js", "data_fen.js", "app.js"]) {
  const ok = html.includes(`src="${f}"`);
  console.log((ok ? "✔" : "✘"), "script:", f);
  if (!ok) fail++;
}
process.exit(fail ? 1 : 0);
