// 验证生成的 JS 数据: 加载 + 抽查
const fs = require("fs");
const path = require("path");

global.window = {};
for (const f of ["data_ruanke.js", "data_toudang.js", "data_fen.js"]) {
  const code = fs.readFileSync(path.join(__dirname, "..", f), "utf8");
  eval(code);
}
const W = global.window;

console.log("TD rows:", W.TD2026.length);
console.log("RK majors:", Object.keys(W.RK_META).length);
console.log("FEN rows:", W.FEN2026.length);

// 抽查1: 清华大学 计算机类
const rows = W.TD2026.filter((r) => r[1] === "清华大学" && r[2] === "计算机类");
console.log("\n== 清华大学 计算机类 ==", rows.length, "行");
for (const r of rows.slice(0, 2)) console.log(JSON.stringify(r), "软科名:", W.TD_SCHOOL_RK[r[1]]);

// 计算机类包含的专业
const keys = W.RK_LEI2MAJOR["计算机类"];
console.log("计算机类目录包含专业数:", keys.length);
const th = W.TD_SCHOOL_RK["清华大学"];
for (const k of keys.slice(0, 6)) {
  const meta = W.RK_META[k];
  const rk = W.RK2026[meta.men][meta.lei][k] ? W.RK2026[meta.men][meta.lei][k][th] : undefined;
  console.log(`  ${meta.name}: 软科排名=${rk ?? "未上榜(前50%外)"} (上榜${meta.count}所)`);
}

// 抽查2: 哈尔滨工业大学(威海) 校区回退
const hit = W.TD2026.find((r) => r[1].includes("哈尔滨工业大学(威海)"));
console.log("\n== 哈工大(威海)样例 ==\n", JSON.stringify(hit));
console.log("软科回退名:", W.TD_SCHOOL_RK["哈尔滨工业大学(威海)"]);
const hit2 = W.TD2026.find((r) => r[1] === "上海交通大学医学院");
console.log("上交医学部行:", hit2 && JSON.stringify(hit2), "→", hit2 && W.TD_SCHOOL_RK[hit2[1]]);
const hit3 = W.TD2026.find((r) => r[1] === "东北大学秦皇岛分校");
console.log("东大秦皇岛行:", hit3 && JSON.stringify(hit3), "→", hit3 && W.TD_SCHOOL_RK[hit3[1]]);

// 抽查3: 试验班 (无目录映射)
const sy = W.TD2026.find((r) => r[2].startsWith("工科试验班"));
console.log("\n== 试验班样例 ==\n", JSON.stringify(sy));

// 抽查4: 中外合作
const hz = W.TD2026.find((r) => r[7] === "中外合作办学" && r[2] === "计算机科学与技术");
console.log("\n== 中外合作样例 ==\n", JSON.stringify(hz));

// 抽查5: 意向专业列表构建
const intentNames = new Set();
// 从 RK_META 收集
for (const k in W.RK_META) intentNames.add(W.RK_META[k].name);
// 从 TD 收集非类名核心
const cores = new Set(W.TD2026.map((r) => r[2]));
const extra = [...cores].filter((c) => !W.RK_LEI2MAJOR[c] && !intentNames.has(c) && !/试验班|实验班|试点班/.test(c));
console.log("\n意向专业: 软科", intentNames.size, "+ 投档表特有", extra.length);

// 抽查6: 意向专业筛选模拟 - "数据科学与大数据技术"
const target = "数据科学与大数据技术";
let cnt = 0;
for (const r of W.TD2026) {
  const c = r[2];
  let contains = false;
  if (c === target) contains = true;
  else if (W.RK_LEI2MAJOR[c] && W.RK_LEI2MAJOR[c].some((k) => W.RK_META[k].name === target)) contains = true;
  if (contains) cnt++;
}
console.log(`意向专业"${target}" 命中志愿类数:`, cnt);

// 抽查7: 一分一段换算
console.log("\n一分一段: 697->", W.FEN2026.find((f) => f[0] === 697));
