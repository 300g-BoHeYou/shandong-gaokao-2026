/* ============================================================
 * 强基计划页面逻辑 (qiangji.js)
 * 依赖: data_qiangji.js (window.QJ2026)
 * 规则: 不展示院校级分数/位次; 仅面试院校考查科目显示“无笔试”;
 *       已确定专业标注软科2026排名状态; 带方向括号的给出简章原名提示
 * ============================================================ */
(function () {
  "use strict";

  var DATA = (window.QJ2026 && window.QJ2026.schools) || [];
  var S = { mode: "全部", form: "全部", kw: "", major: "", sel: { mens: {}, leis: {}, majors: {} } };
  var SEL = {};          // 展开后的专业名集合(用于匹配与高亮)
  var HAS_SEL = false;   // 是否有选择
  var PICKER = null;

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function todo() { return '<span class="todo">待查证</span>'; }
  function val(v) { return (v === undefined || v === null || String(v).trim() === "") ? todo() : esc(v); }

  // 按 2026 本科专业目录三级结构, 只保留强基实际招生的专业(带计数); 目录查不到的归入"其他"
  function buildTree(cnt) {
    var cat = window.CAT2026 || null;
    var tree = [], known = {};
    if (cat && cat.men) {
      for (var i = 0; i < cat.men.length; i++) {
        var men = cat.men[i], leisObj = cat.tree[men] || {}, leis = [];
        var leiNames = Object.keys(leisObj);
        for (var j = 0; j < leiNames.length; j++) {
          var lei = leiNames[j], majs = [];
          for (var k = 0; k < leisObj[lei].length; k++) {
            var n = leisObj[lei][k];
            known[n] = true;
            if (cnt[n]) majs.push({ n: n, cnt: cnt[n] });
          }
          if (majs.length) leis.push({ lei: lei, majors: majs });
        }
        if (leis.length) tree.push({ men: men, leis: leis });
      }
    }
    var extra = [];
    Object.keys(cnt).forEach(function (n) { if (!known[n]) extra.push({ n: n, cnt: cnt[n] }); });
    if (extra.length) tree.push({ men: "其他（不在本科专业目录中）", leis: [{ lei: "其他名称", majors: extra }] });
    return tree;
  }

  // 软科2026排名状态标签
  function rkBadge(info) {
    if (!info) return "";
    if (info.st === "ranked") {
      return '<span class="rk ranked" title="软科2026 第' + info.rk + '名，全国上榜' + info.cnt + '所">#' + info.rk + "</span>";
    }
    if (info.st === "special") {
      return '<span class="rk special" title="软科2026特色专业（开设院校<4所），只发布开设名单、不计算排名">特色专业</span>';
    }
    if (info.st === "nosc") {
      return '<span class="rk nosc" title="该校未收录于软科2026专业排名，无排名数据">该校未收录软科</span>';
    }
    if (info.st === "notpub") {
      return '<span class="rk notpub" title="该专业不在软科2026发布的838个专业内，无排名">未排名</span>';
    }
    return '<span class="rk" title="该专业软科2026发布排名，但该校未进前50%">未上榜</span>';
  }

  function schoolMatches(s) {
    if (S.mode !== "全部" && (s.mode || "") !== S.mode) return false;
    if (S.form !== "全部") {
      var f = s.form || "";
      if (S.form === "仅面试" && f.indexOf("仅面试") < 0) return false;
      if (S.form === "笔试" && f.indexOf("笔试") < 0) return false;
    }
    if (S.kw && s.name.indexOf(S.kw) < 0) return false;
    if (HAS_SEL) {
      var hit = false;
      for (var i = 0; i < s.majors.length; i++) {
        for (var j = 0; j < (s.majors[i].items || []).length; j++) {
          if (SEL[s.majors[i].items[j].n]) { hit = true; break; }
        }
        if (hit) break;
      }
      if (!hit) return false;
    }
    return true;
  }

  // 包含专业单元格: 单个专业 + 软科排名标签 (+命中高亮)
  function majorCell(it) {
    var hit = HAS_SEL && SEL[it.n];
    return '<span' + (hit ? ' class="hit"' : "") + ">" + esc(it.n) + "</span>"
      + rkBadge({ st: it.st, rk: it.rk, cnt: it.cnt, inList: it.inList });
  }

  // 对应普通批参考: 分数（排名），并注明所参考的志愿类
  function refCell(it) {
    if (it.r == null) {
      return '<span class="dim" title="该校普通批无该专业及含该专业的大类（多以试验班招生）">—</span>';
    }
    var k = it.kind ? it.kind : (it.ref ? "参考" : "");
    var t = it.ref ? (k + "：" + it.ref) : "";
    return '<span class="refscore">' + it.s + ' 分</span><span class="refrank">（' + it.r + " 名）</span>"
      + (t ? '<span class="refsrc">' + esc(t) + "</span>" : "");
  }

  function majorRows(s) {
    var groups = [];
    for (var i = 0; i < s.majors.length; i++) {
      var g = s.majors[i];
      var items = [], matched = 0;
      for (var k = 0; k < g.items.length; k++) {
        items.push(g.items[k]);                       // 组内专业全部展示
        if (SEL[g.items[k].n]) matched++;
      }
      // 有选择时: 组内任一专业命中即保留该组(用户口径)
      if (HAS_SEL && !matched) continue;
      if (!items.length) continue;
      groups.push({ g: g, items: items });
    }
    if (!groups.length) {
      if (!s.majors.length) return '<tr><td colspan="4" class="dim">专业类待查证</td></tr>';
      return '<tr><td colspan="4" class="dim">该校无匹配专业</td></tr>';
    }
    var html = "";
    for (var gi = 0; gi < groups.length; gi++) {
      var grp = groups[gi];
      for (var j = 0; j < grp.items.length; j++) {
        var first = j === 0;
        var it2 = grp.items[j];
        html += "<tr" + (first ? ' class="grp-start"' : "") + ">";
        if (first) {
          html += '<td rowspan="' + grp.items.length + '">' + esc(grp.g.cat) + "</td>";
        }
        html += "<td>" + (it2.n ? majorCell(it2) : todo()) + "</td>";
        if (first) {
          html += '<td rowspan="' + grp.items.length + '">' + val(grp.g.subj) + "</td>";
        }
        html += "<td>" + refCell(it2) + "</td></tr>";
      }
    }
    return html;
  }

  function render() {
    var rows = DATA.filter(schoolMatches);
    var html = "";
    for (var i = 0; i < rows.length; i++) {
      var s = rows[i];
      var modeText = (s.mode === "出分前") ? "出分前校考" : (s.mode === "出分后" ? "出分后校考" : "校考时间待查证");
      html += '<article class="school">'
        + '<div class="school-top">'
        + '<span class="sname">' + esc(s.name) + "</span>"
        + (s.mode ? '<span class="badge b-mode">' + esc(modeText) + "</span>" : "")
        + (s.form ? '<span class="badge b-form">' + esc(s.form) + "</span>" : "")
        + (s.link ? '<a class="badge b-link" href="' + esc(s.link) + '" target="_blank" rel="noopener" title="阳光高考·强基计划报名平台（官方）">官方简章（阳光高考） ↗</a>' : "")
        + (s.jzLink ? '<a class="badge b-link2" href="' + esc(s.jzLink) + '" target="_blank" rel="noopener" title="学校本科招生网发布的简章原文">学校官网简章 ↗</a>' : "")
        + "</div>"
        + '<div class="meta">'
        + "<b>校考时间：</b>" + val(s.examTime)
        + "　<b>入围比例：</b>" + val(s.ratio)
        + "　<b>校考形式：</b>" + val(s.form)
        + "</div>"
        + '<div class="meta"><b>入围方式：</b>' + val(s.entry) + "</div>"
        + (s.entryScore ? '<div class="meta"><b>入围成绩计算：</b>' + esc(s.entryScore) + "</div>" : "")
        + (s.brk ? '<div class="meta"><b>竞赛破格：</b>' + esc(s.brk) + "</div>" : "")
        + (s.signup ? '<div class="meta"><b>报名时间：</b>' + esc(s.signup) + "</div>" : "")
        + (s.note ? '<div class="meta"><b>2026 要点：</b>' + esc(s.note) + "</div>" : "")
        + '<table class="majors"><thead><tr><th style="width:23%;">强基专业类</th><th style="width:37%;">包含专业（含软科2026排名）</th>'
        + '<th style="width:18%;">考查科目</th><th style="width:22%;">对应普通批分数（排名）</th></tr></thead><tbody>'
        + majorRows(s)
        + "</tbody></table></article>";
    }
    document.getElementById("results").innerHTML = html || '<div class="dim" style="padding:20px;">无匹配院校</div>';

    var pre = DATA.filter(function (s) { return s.mode === "出分前"; }).length;
    var noExam = DATA.filter(function (s) { return (s.form || "").indexOf("仅面试") >= 0; }).length;
    document.getElementById("stats").innerHTML = "共 <b>" + DATA.length + "</b> 所　出分前校考 <b>"
      + pre + "</b> 所　出分后校考 <b>" + (DATA.length - pre) + "</b> 所　仅面试（无笔试）<b>"
      + noExam + "</b> 所　当前显示 <b>" + rows.length + "</b> 所";
  }

  function init() {
    var modes = ["全部", "出分前", "出分后"];
    document.getElementById("modeBox").innerHTML = modes.map(function (m) {
      return '<button class="chip' + (S.mode === m ? " on" : "") + '" data-mode="' + m + '">'
        + (m === "出分前" ? "出分前校考" : m === "出分后" ? "出分后校考" : "全部") + "</button>";
    }).join("");
    var forms = ["全部", "笔试", "仅面试"];
    document.getElementById("formBox").innerHTML = forms.map(function (f) {
      return '<button class="chip' + (S.form === f ? " on" : "") + '" data-form="' + f + '">'
        + (f === "全部" ? "全部" : f === "仅面试" ? "仅面试（无笔试）" : "有笔试") + "</button>";
    }).join("");

    // 三级目录选择器(门类→专业类→专业), 仅列出强基实际招生的专业
    if (window.MajorPicker && !PICKER) {
      var cnt = {};
      for (var a = 0; a < DATA.length; a++) {
        for (var b2 = 0; b2 < DATA[a].majors.length; b2++) {
          for (var c2 = 0; c2 < DATA[a].majors[b2].items.length; c2++) {
            var nm = DATA[a].majors[b2].items[c2].n;
            if (nm) cnt[nm] = (cnt[nm] || 0) + 1;
          }
        }
      }
      PICKER = window.MajorPicker.create({
        tree: buildTree(cnt),
        sel: S.sel,
        ids: { toggle: "pkToggle", panel: "pkPanel", search: "pkSearch", tree: "pkTree",
               chips: "selChips", clear: "pkClear", count: "pkCount" },
        onChange: function (expanded) { SEL = expanded; HAS_SEL = Object.keys(expanded).length > 0; render(); }
      });
    }

    document.getElementById("modeBox").addEventListener("click", function (e) {
      var b = e.target.closest("[data-mode]");
      if (!b) return;
      S.mode = b.getAttribute("data-mode");
      init(); render();
    });
    document.getElementById("formBox").addEventListener("click", function (e) {
      var b = e.target.closest("[data-form]");
      if (!b) return;
      S.form = b.getAttribute("data-form");
      init(); render();
    });
    var kw = document.getElementById("kw");
    kw.addEventListener("input", function () { S.kw = kw.value.trim(); render(); });
    document.getElementById("resetBtn").addEventListener("click", function () {
      S.mode = "全部"; S.form = "全部"; S.kw = "";
      S.sel.mens = {}; S.sel.leis = {}; S.sel.majors = {};   // 就地清空(选择器持有同一对象)
      SEL = {}; HAS_SEL = false;
      kw.value = "";
      if (PICKER) PICKER.render();
      init(); render();
    });

    render();
  }

  if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
    else init();
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = {
      DATA: DATA, schoolMatches: schoolMatches, S: S,
      setSel: function (map) { SEL = map || {}; HAS_SEL = Object.keys(SEL).length > 0; },
      buildTree: buildTree
    };
  }
})();
