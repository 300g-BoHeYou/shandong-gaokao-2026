const fs = require("fs");
global.window = {};
eval(fs.readFileSync("data_qiangji.js", "utf8"));
const S = window.QJ2026.schools;
const re = /复试(\d{1,2})月(\d{1,2})日/;
S.forEach((s) => {
  const t = s.examTime || "";
  let flag = "";
  const m = t.match(re);
  if (m && parseInt(m[1], 10) === 6 && parseInt(m[2], 10) < 15) flag = "   <<< 复试日期可疑";
  if (t.length < 6) flag = "   <<< 信息过少";
  console.log(s.name.padEnd(11) + t + flag);
});
