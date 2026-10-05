// 定位"为先书院"行内的"高校专项计划"出现位置
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
global.Blob = class { constructor(){} };
global.URL = { createObjectURL: () => "blob:x", revokeObjectURL: () => {} };

const webDir = path.join(__dirname, "..", "web");
for (const f of ["data_ruanke.js","data_toudang.js","data_fen.js"]) eval(fs.readFileSync(path.join(webDir,f),"utf8"));
const app = require(path.join(webDir,"app.js"));

const inp = document.getElementById("schoolKw");
inp.value = "清华大学";
inp.fire("input");
const html = document.getElementById("results").innerHTML;
const articles = html.split("</article>");
const block = articles.find((a) => a.indexOf("为先书院") >= 0);
console.log("== 为先书院行 HTML ==");
console.log(block);
let idx = -1, n = 0;
while ((idx = block.indexOf("高校专项计划", idx + 1)) >= 0) {
  n++;
  console.log(`\n--- 第${n}次出现 @${idx} 上下文 ---`);
  console.log(block.slice(Math.max(0, idx - 90), idx + 30));
}
