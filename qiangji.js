/* ============================================================
 * 强基计划页面逻辑 (qiangji.js)
 * 依赖: data_qiangji.js (window.QJ2026)
 * 规则: 不展示院校级分数/位次; 仅面试院校考查科目显示“无笔试”;
 *       已确定专业标注软科2026排名状态; 带方向括号的给出简章原名提示
 * ============================================================ */
(function () {
  "use strict";

  var DATA = (window.QJ2026 && window.QJ2026.schools) || [];
  var S = { mode: "全部", form: "全部", kw: "", mkw: "" };

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function todo() { return '<span class="todo">待查证</span>'; }
  function val(v) { return (v === undefined || v === null || String(v).trim() === "") ? todo() : esc(v); }

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
    if (S.mkw) {
      var hit = false;
      for (var i = 0; i < s.majors.length; i++) {
        var m = s.majors[i];
        if ((m.cat || "").indexOf(S.mkw) >= 0 || (m.inc || "").indexOf(S.mkw) >= 0) { hit = true; break; }
      }
      if (!hit) return false;
    }
    return true;
  }

  // 包含专业单元格: 专业名 + 软科排名标签 + 方向备注徽章
  function incCell(m) {
    var html = "";
    if (m.inc) {
      var parts = String(m.inc).split("、");
      var rkMap = {};
      (m.incRk || []).forEach(function (x) { rkMap[x.n] = x; });
      html = parts.map(function (n) {
        return esc(n) + rkBadge(rkMap[n]);
      }).join("　");
    } else {
      html = todo();
    }
    if (m.note) {
      html += '<span class="dirc" title="简章中该专业类的括号说明（培养方向）">' + esc(m.note) + "</span>";
    }
    return html;
  }

  // 对应普通批参考: 分数（排名），并注明所参考的志愿类
  function refCell(m) {
    if (m.r == null) return '<span class="dim" title="该校普通批无同名专业及包含该专业的大类（多以试验班招生）">—</span>';
    var t = m.ref ? "参考志愿类：" + m.ref : "";
    return '<span class="refscore">' + m.s + ' 分</span><span class="refrank">（' + m.r + " 名）</span>"
      + (t ? '<span class="refsrc">' + esc(t) + "</span>" : "");
  }

  function majorRows(s) {
    if (!s.majors.length || (!s.majors[0].cat && !s.majors[0].subj)) {
      return '<tr><td colspan="4" class="dim">专业类待查证（官方简章专业表为图片，请在查证清单 Sheet2 中补充）</td></tr>';
    }
    var html = "";
    for (var i = 0; i < s.majors.length; i++) {
      var m = s.majors[i];
      if (S.mkw && (m.cat || "").indexOf(S.mkw) < 0 && (m.inc || "").indexOf(S.mkw) < 0) continue;
      html += "<tr>"
        + "<td>" + esc(m.cat) + "</td>"
        + "<td>" + incCell(m) + "</td>"
        + "<td>" + val(m.subj) + "</td>"
        + "<td>" + refCell(m) + "</td>"
        + "</tr>";
    }
    return html || '<tr><td colspan="4" class="dim">无匹配专业类</td></tr>';
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
    var mkw = document.getElementById("mkw");
    mkw.addEventListener("input", function () { S.mkw = mkw.value.trim(); render(); });
    document.getElementById("resetBtn").addEventListener("click", function () {
      S = { mode: "全部", form: "全部", kw: "", mkw: "" };
      kw.value = ""; mkw.value = "";
      init(); render();
    });

    render();
  }

  if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
    else init();
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { DATA: DATA, schoolMatches: schoolMatches, S: S };
  }
})();
