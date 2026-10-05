/* ============================================================
 * 三级专业选择器 (门类 → 专业类 → 专业)
 * 用法: MajorPicker.create({tree, sel, onChange, ids:{toggle,panel,search,chips,clear,count}})
 *   tree: [{men, leis:[{lei, majors:[{n, cnt}]}]}]   （cnt 为可选计数）
 *   sel : {mens:{}, leis:{}, majors:{}}  会被就地修改
 * 支持: 勾选单个专业 / 整个专业类 / 整个门类; 已选区 chips 可展开、可单独取消
 * ============================================================ */
(function () {
  "use strict";

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function norm(s) { return String(s || "").toLowerCase().replace(/\s+/g, ""); }

  function isHidden(el) {
    if (!el) return false;
    if (typeof el.hasAttribute === "function") return el.hasAttribute("hidden");
    return !!el.hidden;
  }

  function create(opts) {
    var tree = opts.tree || [];
    var sel = opts.sel || (opts.sel = { mens: {}, leis: {}, majors: {} });
    if (!sel.majors) sel.majors = {};
    var MAJOR2MEN = {};   // 专业名 -> [门类, 专业类]
    var ids = opts.ids || {};
    var $ = function (id) { return id ? document.getElementById(id) : null; };
    var elToggle = $(ids.toggle), elPanel = $(ids.panel), elSearch = $(ids.search);
    var elTree = $(ids.tree), elChips = $(ids.chips), elClear = $(ids.clear), elCount = $(ids.count);
    var LEI_MAJORS = {}, MEN_LEIS = {}, MEN_MAJORS = {}, MEN_CNT = {}, LEI_CNT = {};

    tree.forEach(function (m) {
      MEN_LEIS[m.men] = [];
      MEN_MAJORS[m.men] = [];
      m.leis.forEach(function (l) {
        MEN_LEIS[m.men].push(l.lei);
        LEI_MAJORS[l.lei] = [];
        l.majors.forEach(function (x) {
          LEI_MAJORS[l.lei].push(x.n);
          MEN_MAJORS[m.men].push(x.n);
          MAJOR2MEN[x.n] = [m.men, l.lei];
        });
        LEI_CNT[l.lei] = l.majors.length;
      });
      MEN_CNT[m.men] = MEN_MAJORS[m.men].length;
    });

    // 展开集合(门类/专业类)
    var open = { men: {}, lei: {} };
    var treeRendered = false;   // 目录树较大, 首次展开面板时才渲染

    /* ---- 选择模型: 只维护"已选专业"集合, 专业类/门类状态由它推导 ----
       stateOf(names): "all"(全选) / "some"(部分, 复选框半打钩) / "none" */
    function stateOf(names) {
      var hit = 0, i;
      for (i = 0; i < names.length; i++) if (sel.majors[names[i]]) hit++;
      if (!hit) return "none";
      return hit === names.length ? "all" : "some";
    }
    function setAll(names, on) {
      for (var i = 0; i < names.length; i++) {
        if (on) sel.majors[names[i]] = true; else delete sel.majors[names[i]];
      }
    }
    // 该类/门类是否被"整类选择"覆盖(用于 chips 归并; 仅统计显式整选的层级)
    function coveredBy(men, lei) {
      if (men && stateOf(MEN_MAJORS[men]) === "all" && sel.mens[men]) return true;
      return !!(lei && stateOf(LEI_MAJORS[lei]) === "all" && sel.leis[lei]);
    }
    function menOfLei(lei) {
      var keys = Object.keys(MEN_LEIS);
      for (var i = 0; i < keys.length; i++) if ((MEN_LEIS[keys[i]] || []).indexOf(lei) >= 0) return keys[i];
      return "";
    }

    function selectedCount() { return Object.keys(sel.majors).length; }

    // 展开成具体专业集合(用于匹配与高亮)
    function expanded() {
      var out = {};
      Object.keys(sel.majors).forEach(function (n) { out[n] = true; });
      return out;
    }

    function syncCount() {
      var n = selectedCount();
      if (elCount) elCount.textContent = n ? "已选 " + n + " 个专业" : "";
    }

    function notify() {
      renderChips();
      syncCount();
      if (opts.onChange) opts.onChange(expanded(), sel);
    }

    function renderTree() {
      if (!elTree) return;
      treeRendered = true;
      var q = norm(elSearch ? elSearch.value : "");
      var html = "";
      tree.forEach(function (m) {
        var menState = stateOf(MEN_MAJORS[m.men] || []);
        var menHit = !q || norm(m.men).indexOf(q) >= 0;
        var leisHtml = "";
        m.leis.forEach(function (l) {
          var leiState = stateOf(LEI_MAJORS[l.lei] || []);
          var leiHit = menHit || norm(l.lei).indexOf(q) >= 0;
          var majorsHtml = "";
          l.majors.forEach(function (x) {
            var hit = leiHit || norm(x.n).indexOf(q) >= 0;
            if (!hit) return;
            majorsHtml += '<label class="pk-major"><input type="checkbox" data-pk="major" data-v="' + esc(x.n) + '"'
              + (sel.majors[x.n] ? " checked" : "") + "><span>" + esc(x.n) + "</span>"
              + (x.cnt != null ? '<i class="pk-cnt">' + x.cnt + "</i>" : "") + "</label>";
          });
          if (!majorsHtml && q && !leiHit) return;
          leisHtml += '<div class="pk-lei">'
            + '<div class="pk-row pk-lei-row">'
            + '<input type="checkbox" data-pk="lei" data-v="' + esc(l.lei) + '"'
            + (leiState === "all" ? " checked" : "") + (leiState === "some" ? ' data-ind="1"' : "") + ">"
            + '<span class="pk-name" data-open="lei" data-v="' + esc(l.lei) + '">' + esc(l.lei)
            + '<i class="pk-cnt">' + l.majors.length + "个专业</i>"
            + (leiState === "some" ? '<i class="pk-cnt pk-sel">已选该类部分专业</i>' : "") + "</span>"
            + '<button class="pk-arrow" data-open="lei" data-v="' + esc(l.lei) + '" title="展开/收起">'
            + (open.lei[l.lei] || q ? "▾" : "▸") + "</button>"
            + "</div>"
            + '<div class="pk-majors"' + ((open.lei[l.lei] || q) ? "" : " hidden") + ">" + majorsHtml + "</div>"
            + "</div>";
        });
        if (!leisHtml && q && !menHit) return;
        html += '<div class="pk-men">'
          + '<div class="pk-row pk-men-row">'
          + '<input type="checkbox" data-pk="men" data-v="' + esc(m.men) + '"'
          + (menState === "all" ? " checked" : "") + (menState === "some" ? ' data-ind="1"' : "") + ">"
          + '<span class="pk-name" data-open="men" data-v="' + esc(m.men) + '">' + esc(m.men)
          + '<i class="pk-cnt">' + MEN_CNT[m.men] + "个专业</i></span>"
          + '<button class="pk-arrow" data-open="men" data-v="' + esc(m.men) + '" title="展开/收起">'
          + (open.men[m.men] || q ? "▾" : "▸") + "</button>"
          + "</div>"
          + '<div class="pk-leis"' + ((open.men[m.men] || q) ? "" : " hidden") + ">" + leisHtml + "</div>"
          + "</div>";
      });
      elTree.innerHTML = html || '<div class="pk-empty">没有匹配的专业</div>';
      // 部分选中 -> 复选框半打钩(浏览器生效; 测试环境用 data-ind 标记断言)
      if (typeof elTree.querySelectorAll === "function") {
        var cbs = elTree.querySelectorAll('input[data-ind="1"]');
        for (var i = 0; i < cbs.length; i++) cbs[i].indeterminate = true;
      }
    }

    function chip(label, kind, key, extra) {
      var cntTxt = extra ? '<i class="pk-cnt">' + extra + "</i>" : "";
      return '<span class="chip sel-chip" data-kind="' + kind + '" data-v="' + esc(key) + '">'
        + '<span class="sch-name">' + esc(label) + "</span>" + cntTxt
        + '<button class="pk-exp" data-exp="' + kind + '" data-v="' + esc(key) + '" title="展开包含的专业">▾</button>'
        + '<button class="x" data-rmk="' + kind + '" data-v="' + esc(key) + '" title="取消选择">×</button>'
        + "</span>";
    }

    function renderChips() {
      if (!elChips) return;
      var html = "";
      // 整门类(显式勾选门类且其下专业已全选)
      Object.keys(MEN_MAJORS).forEach(function (men) {
        if (stateOf(MEN_MAJORS[men]) === "all" && sel.mens[men]) {
          html += chip(men + "（整门类）", "men", men, MEN_CNT[men] + "专业");
        }
      });
      // 整专业类(显式勾选专业类, 且其门类未整选)
      Object.keys(LEI_MAJORS).forEach(function (lei) {
        if (stateOf(LEI_MAJORS[lei]) === "all" && sel.leis[lei] && !coveredBy(menOfLei(lei), null)) {
          html += chip(lei + "（整类）", "lei", lei, LEI_CNT[lei] + "专业");
        }
      });
      // 未并入整类/整门类的单个专业
      Object.keys(sel.majors).forEach(function (n) {
        var mm = MAJOR2MEN[n] || ["", ""];
        if (coveredBy(mm[0], mm[1])) return;
        html += chip(n, "major", n, "");
      });
      elChips.innerHTML = html || '<span class="pk-hint">尚未选择专业（可只选某个专业，也可整类/整门类选择）</span>';
    }

    function openDetail(kind, key, btn) {
      // 在 chip 下展开包含的专业列表
      var box = elChips.querySelector('[data-detail="' + kind + "|" + key + '"]');
      var existing = elChips.querySelector('.pk-detail[data-detail="' + kind + "|" + key + '"]');
      if (existing) { existing.parentNode.removeChild(existing); return; }
      var list = kind === "men" ? (MEN_LEIS[key] || []) : (LEI_MAJORS[key] || []);
      var label = kind === "men" ? "包含的专业类" : "包含的专业";
      var d = document.createElement("div");
      d.className = "pk-detail";
      d.setAttribute("data-detail", kind + "|" + key);
      d.innerHTML = "<b>" + esc(label) + "（" + list.length + "）：</b>" + list.map(function (x) { return esc(x); }).join("、")
        + '<button class="pk-detail-x" title="收起">×</button>';
      btn.parentNode.insertBefore(d, btn.nextSibling);
    }

    if (elTree) {
      elTree.addEventListener("change", function (e) {
        var cb = e.target;
        if (!cb || !cb.getAttribute) return;
        var kind = cb.getAttribute("data-pk"), v = cb.getAttribute("data-v");
        if (!kind) return;
        if (kind === "men") {
          // 整门类: 未全选(含半选) -> 全选并记为整门类; 已全选 -> 全不选
          var menAll = stateOf(MEN_MAJORS[v] || []) === "all";
          setAll(MEN_MAJORS[v] || [], !menAll);
          if (menAll) delete sel.mens[v]; else sel.mens[v] = true;
        } else if (kind === "lei") {
          var leiAll = stateOf(LEI_MAJORS[v] || []) === "all";
          setAll(LEI_MAJORS[v] || [], !leiAll);
          if (leiAll) delete sel.leis[v]; else sel.leis[v] = true;
        } else {
          if (cb.checked) sel.majors[v] = true; else delete sel.majors[v];
        }
        renderTree();
        notify();
      });
      elTree.addEventListener("click", function (e) {
        var t = e.target;
        if (t && t.getAttribute && t.getAttribute("data-open")) {
          var kind = t.getAttribute("data-open"), v = t.getAttribute("data-v");
          if (kind === "men") open.men[v] = !open.men[v];
          else open.lei[v] = !open.lei[v];
          renderTree();
        }
      });
    }
    if (elSearch) {
      elSearch.addEventListener("input", renderTree);
      elSearch.addEventListener("keydown", function (e) { if (e.key === "Escape") elSearch.value = ""; renderTree(); });
    }
    if (elChips) {
      elChips.addEventListener("click", function (e) {
        var t = e.target;
        if (!t || !t.getAttribute) return;
        var rmk = t.getAttribute("data-rmk");
        if (rmk) {
          var v = t.getAttribute("data-v");
          if (rmk === "men") { setAll(MEN_MAJORS[v] || [], false); delete sel.mens[v]; }
          else if (rmk === "lei") { setAll(LEI_MAJORS[v] || [], false); delete sel.leis[v]; }
          else delete sel.majors[v];
          renderTree(); notify();
          return;
        }
        if (t.getAttribute("data-exp")) openDetail(t.getAttribute("data-exp"), t.getAttribute("data-v"), t);
      });
    }
    if (elClear) {
      elClear.addEventListener("click", function () {
        sel.majors = {}; sel.mens = {}; sel.leis = {};
        renderTree(); notify();
      });
    }
    if (elToggle && elPanel) {
      elToggle.addEventListener("click", function () {
        if (isHidden(elPanel)) {
          elPanel.removeAttribute("hidden");
          if (!treeRendered) renderTree();
          elToggle.textContent = "按目录选择专业 ▴";
        } else {
          elPanel.setAttribute("hidden", "");
          elToggle.textContent = "按目录选择专业 ▾";
        }
      });
    }

    // 面板默认可见时才立即渲染目录树(否则首次展开时渲染)
    if (elPanel && elTree && !isHidden(elPanel)) renderTree();
    renderChips();
    syncCount();
    return {
      expanded: expanded,
      sel: sel,
      render: function () {
        if (elPanel && isHidden(elPanel) && !treeRendered) { renderChips(); syncCount(); return; }
        renderTree(); renderChips(); syncCount();
      },
      count: selectedCount
    };
  }

  window.MajorPicker = { create: create };
})();
