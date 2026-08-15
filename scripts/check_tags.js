// 渲染结果 HTML 标签配平检查
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
  addEventListener(){},
  body: new StubEl()
};
global.localStorage = { _d:{}, getItem(k){return this._d[k]||null;}, setItem(k,v){this._d[k]=String(v);} };
global.Blob = class { constructor(){} };
global.URL = { createObjectURL: () => "blob:x", revokeObjectURL: () => {} };

const webDir = path.join(__dirname, ".."); // 站点文件在仓库根目录
for (const f of ["data_ruanke.js","data_toudang.js","data_fen.js"]) eval(fs.readFileSync(path.join(webDir,f),"utf8"));
const app = require(path.join(webDir,"app.js"));

// 触发一次带意向专业+位次的渲染
app.S.intent = { "临床医学": true };
app.S.myRank = 30000;
const inp = document.getElementById("schoolKw");
inp.value = "";
inp.fire("input");

const html = document.getElementById("results").innerHTML;
const tags = {};
for (const m of html.matchAll(/<\/?([a-zA-Z][a-zA-Z0-9]*)\b[^>]*>/g)) {
  const full = m[0], t = m[1];
  if (full.startsWith("</")) tags[t] = (tags[t] || 0) - 1;
  else if (!/\/>$/.test(full)) tags[t] = (tags[t] || 0) + 1;
}
let fail = 0;
console.log("== 标签配平 ==");
for (const [t, c] of Object.entries(tags)) {
  if (c !== 0) { console.log("  ✘", t, "不平衡:", c); fail++; }
  else console.log("  ✔", t);
}
const sample = html.slice(0, 600);
console.log("\n== 首行卡片样例 ==");
console.log(sample.replace(/\n/g, " "));
process.exit(fail ? 1 : 0);
