/* 2026 山东本科综合评价招生（综招）页面逻辑
   重点: 校测时间对照 + 兼报冲突分析（同日/同时段） */
(function () {
  "use strict";

  var DATA = (window.ZZ2026 && window.ZZ2026.schools) || [];
  var META = (window.ZZ2026 && window.ZZ2026.meta) || {};
  var S = { area: "全部", dates: {}, kw: "", sel: { mens: {}, leis: {}, majors: {} }, picked: {} };
  var SEL = {}, HAS_SEL = false, PICKER = null;

  function esc(s) {
    return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function norm(s) { return String(s || "").toLowerCase().replace(/\s+/g, ""); }
  function $(id) { return document.getElementById(id); }
  function baseName(n) {
    var s = String(n || "");
    for (var i = 0; i < 3; i++) s = s.replace(/[（(][^（()）]*[)）]\s*$/, "");
    return s.trim();
  }
  function allMajors(s) {
    var out = [];
    (s.groups || []).forEach(function (g) {
      (g.entries || []).forEach(function (e) {
        if (e.subs && e.subs.length) e.subs.forEach(function (x) { out.push({ n: x.n }); });
        else out.push({ n: e.n });
      });
    });
    return out;
  }

  /* ---------- 选择器 ---------- */
  function buildTree(cnt) {
    var cat = window.CAT2026 || null, tree = [], known = {};
    if (cat && cat.men) {
      cat.men.forEach(function (men) {
        var obj = cat.tree[men] || {}, leis = [];
        Object.keys(obj).forEach(function (lei) {
          var majs = [];
          obj[lei].forEach(function (n) {
            known[n] = true;
            if (cnt[n]) majs.push({ n: n, cnt: cnt[n] });
          });
          if (majs.length) leis.push({ lei: lei, majors: majs });
        });
        if (leis.length) tree.push({ men: men, leis: leis });
      });
    }
    var extra = Object.keys(cnt).filter(function (n) { return !known[n]; })
      .map(function (n) { return { n: n, cnt: cnt[n] }; });
    if (extra.length) {
      tree.push({ men: "其他（不在本科专业目录，如试验班/实验班）",
        leis: [{ lei: "其他名称", majors: extra }] });
    }
    return tree;
  }

  function initPicker() {
    if (!window.MajorPicker) return;
    var cnt = {};
    DATA.forEach(function (s) {
      allMajors(s).forEach(function (m) {
        var b = baseName(m.n);
        if (b) cnt[b] = (cnt[b] || 0) + 1;
      });
    });
    PICKER = window.MajorPicker.create({
      tree: buildTree(cnt), sel: S.sel,
      ids: { toggle: "pkToggle", panel: "pkPanel", search: "pkSearch", tree: "pkTree",
             chips: "selChips", clear: "pkClear", count: "pkCount" },
      onChange: function (expanded) {
        SEL = expanded;
        HAS_SEL = Object.keys(expanded).length > 0;
        render();
      }
    });
  }

  function schoolMatches(s) {
    if (S.area !== "全部" && s.area !== S.area) return false;
    if (S.kw && String(s.name).indexOf(S.kw) < 0) return false;
    if (Object.keys(S.dates).length) {
      var hit = (s.events || []).some(function (e) { return S.dates[e.d]; });
      if (!hit) return false;
    }
    if (HAS_SEL) {
      var ok = allMajors(s).some(function (m) { return SEL[baseName(m.n)]; });
      if (!ok) return false;
    }
    return true;
  }

  /* ---------- 兼报分析 ---------- */
  function pickedList() {
    return DATA.filter(function (s) { return S.picked[s.name]; });
  }

  function renderPlan() {
    var picked = pickedList(), el = $("planBody"), hint = $("planHint");
    hint.textContent = picked.length
      ? "已加入 " + picked.length + " 所，点击卡片「移出兼报」可取消"
      : "在下方院校卡片点「加入兼报」即可比较校测时间";
    if (!picked.length) {
      el.innerHTML = '<div class="plan-empty">尚未加入院校。建议先加入你的目标院校（如 山东大学 + 华南理工 + 青岛大学），即可看到哪几天冲突。</div>';
      return;
    }
    // 按日期聚合
    var byDate = {};
    picked.forEach(function (s) {
      (s.events || []).forEach(function (e) {
        (byDate[e.d] = byDate[e.d] || []).push({ sch: s.name, label: e.label, slot: e.slot || "" });
      });
    });
    var days = Object.keys(byDate).sort();
    if (!days.length) {
      el.innerHTML = '<div class="plan-empty">所选院校的校测日期尚未公布（见各卡片校测时间）。</div>';
      return;
    }
    var html = "", badDays = 0;
    days.forEach(function (d) {
      var items = byDate[d];
      // 冲突判定: 同一天且时段重叠(都未公布 或 时段相同)
      var conflict = false;
      for (var i = 0; i < items.length && !conflict; i++) {
        for (var j = i + 1; j < items.length; j++) {
          if (!items[i].slot || !items[j].slot || items[i].slot === items[j].slot) { conflict = true; break; }
        }
      }
      if (conflict) badDays++;
      var md = d.replace("-", "月").replace(/^0/, "") + "日";
      html += '<div class="day-row' + (conflict ? " conflict" : "") + '">'
        + '<div class="day-label">' + esc(md) + (conflict ? " ⚠" : "") + "</div>"
        + '<div class="day-items">' + items.map(function (x) {
          return '<span class="ev' + (conflict ? " bad" : "") + '">' + esc(x.sch) + "·" + esc(x.label)
            + (x.slot ? "（" + esc(x.slot) + "）" : "") + "</span>";
        }).join("") + "</div></div>";
    });
    html += '<div class="plan-verdict ' + (badDays ? "bad" : "ok") + '">'
      + (badDays
        ? "有 " + badDays + " 天校测时间冲突：报名系统内这些学校只能确认 1 所参加测试（其余须放弃）。"
        : "所选 " + picked.length + " 所校测时间均不冲突，可以全部参加测试。")
      + "　注：提前批填报志愿时仍只能填报 1 所。" + "</div>";
    el.innerHTML = html;
  }

  /* ---------- 卡片 ---------- */
  function rkBadge(sub) {
    if (!sub) return '<span class="rk nosc" title="无数据">—</span>';
    var st = sub.st, txt = "—", cls = "rk", tip = "";
    if (st === "ranked") {
      txt = "#" + sub.rk; cls += " ranked";
      tip = "软科2026 全国第" + sub.rk + "名（该专业全国上榜 " + sub.cnt + " 所）";
    } else if (st === "special") {
      txt = "特色"; cls += " special";
      tip = "软科2026特色专业（开设<4所，不计算排名）";
    } else if (st === "unranked") {
      txt = "未上榜"; cls += " unranked";
      tip = "软科2026该专业有排名，但该校未进前50%（或未开设），全国上榜 " + sub.cnt + " 所";
    } else if (st === "notpub") {
      txt = "未发布"; cls += " notpub";
      tip = "该专业在《本科专业目录》内，但软科2026未发布其排名";
    } else if (st === "nosc") {
      txt = "—"; cls += " nosc";
      tip = "该校未收录于软科2026专业排名";
    }
    return '<span class="' + cls + '" title="' + tip + '">' + txt + "</span>";
  }

  function majorsTable(s) {
    var hasG = !!s.hasGroup, hasC = !!s.hasClass;
    var groups = s.groups || [];
    if (!groups.length) return "";
    var head = "<tr>";
    if (hasG) head += "<th>专业组</th>";
    if (hasC) head += "<th>招生专业（类）</th><th>具体专业（目录）</th>";
    else head += "<th>招生专业</th>";
    head += "<th>软科排名</th></tr>";

    var body = "";
    groups.forEach(function (g) {
      var rows = 0, cells = "";
      (g.entries || []).forEach(function (e) {
        var subs = e.subs || [];
        if (hasC) {
          if (e.kind === "lei" && subs.length) {
            rows += subs.length;
            subs.forEach(function (sub, i) {
              cells += "<tr>";
              if (i === 0) {
                cells += '<td class="cls" rowspan="' + subs.length + '">' + esc(e.n)
                  + (e.req ? '<div class="mini">' + esc(e.req) + "</div>" : "") + "</td>";
              }
              cells += "<td>" + (HAS_SEL && SEL[sub.n] ? '<span class="hit">' + esc(sub.n) + "</span>"
                : esc(sub.n)) + "</td><td>" + rkBadge(sub) + "</td></tr>";
            });
          } else {
            rows += 1;
            cells += '<tr><td colspan="2">' + esc(e.n)
              + (e.req ? ' <span class="mini">' + esc(e.req) + "</span>" : "") + "</td><td>"
              + (subs.length ? rkBadge(subs[0]) : rkBadge(null)) + "</td></tr>";
          }
        } else {
          var list = subs.length ? subs : [{ n: e.n, st: "nodir" }];
          rows += list.length;
          list.forEach(function (sub) {
            cells += "<tr><td>" + (HAS_SEL && SEL[sub.n] ? '<span class="hit">' + esc(sub.n) + "</span>"
              : esc(sub.n))
              + (sub.st === "nodir" && e.req ? ' <span class="mini">' + esc(e.req) + "</span>" : "")
              + "</td><td>" + rkBadge(sub.st === "nodir" ? null : sub) + "</td></tr>";
          });
        }
      });
      if (hasG) {
        // 组单元格(行合并)
        var first = cells.indexOf("<tr>");
        if (first >= 0) {
          cells = cells.slice(0, first) + '<tr><td class="grp" rowspan="' + rows + '">' + esc(g.name)
            + (g.req ? '<div class="mini">' + esc(g.req) + "</div>" : "") + "</td>"
            + cells.slice(first + 4);
        }
      }
      body += cells;
    });
    return '<table class="majors"><thead>' + head + "</thead><tbody>" + body + "</tbody></table>"
      + '<div class="mini" style="margin-top:3px;">'
      + (hasC ? "「类」按《本科专业目录(2026)》展开为具体专业；" : "")
      + "软科排名为该专业该校在全国的名次（前50%上榜）。实际招生包含专业以院校简章为准。</div>";
  }

  function card(s) {
    var evs = (s.events || []).map(function (e) {
      return '<span class="ev">' + esc(e.md) + "·" + esc(e.label) + (e.slot ? "（" + esc(e.slot) + "）" : "") + "</span>";
    }).join("") || '<span class="mini">待查证（见简章说明）</span>';
    var nEntry = 0, nSub = 0;
    (s.groups || []).forEach(function (g) {
      (g.entries || []).forEach(function (e) {
        nEntry++;
        nSub += (e.subs && e.subs.length) ? e.subs.length : 1;
      });
    });
    var mjHtml = nEntry
      ? '<details class="mjd"' + (nSub > 40 ? "" : " open") + '><summary>招生专业（'
        + nEntry + " 个招生条目 → " + nSub + " 个具体专业）</summary>" + majorsTable(s) + "</details>"
      : "";
    var tl = (s.schedule || []).map(function (x) {
      return "<span><b>" + esc(x[0]) + "</b> " + esc(x[1]) + "</span>";
    }).join("");
    var picked = !!S.picked[s.name];
    return '<article class="school' + (picked ? " picked" : "") + '" data-name="' + esc(s.name) + '">'
      + '<div class="sch-head">'
      + '<span class="sch-name">' + esc(s.name) + "</span>"
      + '<span class="badge area' + (s.area === "省外" ? " overseas" : "") + '">' + esc(s.area) + "</span>"
      + (s.level ? '<span class="badge">' + esc(s.level) + "</span>" : "")
      + (s.plan != null ? '<span class="badge plan">计划 ' + esc(s.plan) + " 人</span>"
                        : '<span class="badge plan">计划：见备注</span>')
      + '<button class="btn pick-btn' + (picked ? " primary" : "") + '" data-pick="' + esc(s.name) + '">'
      + (picked ? "移出兼报" : "加入兼报") + "</button></div>"
      + '<div class="sch-body">'
      + '<div class="kv">'
      + '<div class="k">校测时间</div><div><span class="exam-time">' + esc(s.examDate || "待查证") + "</span> " + evs + "</div>"
      + '<div class="k">校测形式</div><div>' + esc(s.examForm || "待查证")
      + (s.examPlace ? '　<span class="mini">地点：' + esc(s.examPlace) + "</span>" : "") + "</div>"
      + (s.examDetail ? '<div class="k">考核说明</div><div>' + esc(s.examDetail) + "</div>" : "")
      + '<div class="k">报名时间</div><div>' + esc(s.signup || "待查证") + "</div>"
      + '<div class="k">入围比例</div><div>' + esc(s.ratio || "待查证") + "</div>"
      + '<div class="k">综合成绩</div><div><b>' + esc(s.score || "待查证") + "</b></div>"
      + '<div class="k">高考要求</div><div>' + esc(s.gaokao || "待查证") + "</div>"
      + "</div>"
      + (s.conditions ? '<div class="cond"><b>报考条件要点：</b>' + esc(s.conditions) + "</div>" : "")
      + (s.planNote ? '<div class="cond"><b>计划说明：</b>' + esc(s.planNote) + "</div>" : "")
      + mjHtml
      + (tl ? '<div class="tl">' + tl + "</div>" : "")
      + (s.note ? '<div class="micro mini" style="margin-top:6px;">' + esc(s.note) + "</div>" : "")
      + '<div class="links">官方简章：<a href="' + esc(s.url) + '" target="_blank" rel="noopener">'
      + esc(s.name) + ' · 2026 招生简章 ↗</a>　<span class="mini">批次：' + esc(s.batch || "") + "</span></div>"
      + "</div></article>";
  }

  /* ---------- 渲染 ---------- */
  function renderTop() {
    var areas = [["全部", "全部院校"], ["省内", "省内试点（提前批）"], ["省外", "省外自主综招"]];
    $("areaBox").innerHTML = areas.map(function (a) {
      var n = a[0] === "全部" ? DATA.length : DATA.filter(function (s) { return s.area === a[0]; }).length;
      return '<button class="chip' + (S.area === a[0] ? " on" : "") + '" data-area="' + a[0] + '">'
        + a[1] + "（" + n + "）</button>";
    }).join("");
    // 日期 chips
    var cnt = {};
    DATA.forEach(function (s) {
      (s.events || []).forEach(function (e) { cnt[e.d] = (cnt[e.d] || 0) + 1; });
    });
    var ds = Object.keys(cnt).sort();
    $("dateBox").innerHTML = ds.map(function (d) {
      var md = d.replace("-", "月").replace(/^0/, "") + "日";
      return '<button class="chip date' + (S.dates[d] ? " on" : "") + '" data-date="' + d + '">'
        + md + "（" + cnt[d] + "）</button>";
    }).join("") || '<span class="mini">暂无</span>';
  }

  function render() {
    renderTop();
    var rows = DATA.filter(schoolMatches);
    $("stats").innerHTML = "共 <b>" + DATA.length + "</b> 所（省内试点 " + (META.pilotCount || 10)
      + " / 省外自主 " + (META.overseasCount || 9) + "）　计划合计 <b>"
      + (META.pilotPlan || 0) + "</b> 人（省外多为全国统一、不分省）　当前显示 <b>" + rows.length + "</b> 所";
    $("results").innerHTML = rows.length ? rows.map(card).join("")
      : '<div class="empty">没有符合条件的院校，试试清空筛选</div>';
    renderPlan();
  }

  function init() {
    initPicker();
    document.addEventListener("click", function (e) {
      var t = e.target;
      if (!t || !t.getAttribute) return;
      if (t.getAttribute("data-area")) {
        S.area = t.getAttribute("data-area");
        render();
        return;
      }
      if (t.getAttribute("data-date")) {
        var d = t.getAttribute("data-date");
        if (S.dates[d]) delete S.dates[d]; else S.dates[d] = true;
        render();
        return;
      }
      if (t.getAttribute("data-pick")) {
        var n = t.getAttribute("data-pick");
        if (S.picked[n]) delete S.picked[n]; else S.picked[n] = true;
        render();
        return;
      }
    });
    var kw = $("kw");
    kw.addEventListener("input", function () { S.kw = kw.value.trim(); render(); });
    $("resetBtn").addEventListener("click", function () {
      S.area = "全部"; S.dates = {}; S.kw = "";
      S.sel.mens = {}; S.sel.leis = {}; S.sel.majors = {};
      SEL = {}; HAS_SEL = false;
      kw.value = "";
      if (PICKER) PICKER.render();
      render();
    });
    $("planClear").addEventListener("click", function () { S.picked = {}; render(); });
    render();
  }

  if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
    else init();
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { DATA: DATA, META: META, S: S, schoolMatches: schoolMatches,
      setSel: function (m) { SEL = m || {}; HAS_SEL = Object.keys(SEL).length > 0; },
      baseName: baseName, buildTree: buildTree, allMajors: allMajors,
      render: render, renderPlan: renderPlan };
  }
})();
