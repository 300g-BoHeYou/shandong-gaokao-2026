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
        });
        LEI_CNT[l.lei] = l.majors.length;
      });
      MEN_CNT[m.men] = MEN_MAJORS[m.men].length;
    });

    // 展开集合(门类/专业类)
    var open = { men: {}, lei: {} };
    var treeRendered = false;   // 目录树较大, 首次展开面板时才渲染

    function selectedCount() {
      return Object.keys(sel.mens).length + Object.keys(sel.leis).length + Object.keys(sel.majors).length;
    }

    // 展开成具体专业集合(用于匹配与高亮)
    function expanded() {
      var out = {};
      Object.keys(sel.majors).forEach(function (n) { out[n] = true; });
      Object.keys(sel.leis).forEach(function (lei) {
        (LEI_MAJORS[lei] || []).forEach(function (n) { out[n] = true; });
      });
      Object.keys(sel.mens).forEach(function (men) {
        (MEN_MAJORS[men] || []).forEach(function (n) { out[n] = true; });
      });
      return out;
    }

    function syncCount() {
      if (elCount) elCount.textContent = selectedCount() ? "已选 " + selectedCount() + " 项" : "";
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
        var menHit = !q || norm(m.men).indexOf(q) >= 0;
        var leisHtml = "";
        m.leis.forEach(function (l) {
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
            + '<input type="checkbox" data-pk="lei" data-v="' + esc(l.lei) + '"' + (sel.leis[l.lei] ? " checked" : "") + ">"
            + '<span class="pk-name" data-open="lei" data-v="' + esc(l.lei) + '">' + esc(l.lei)
            + '<i class="pk-cnt">' + l.majors.length + "个专业</i></span>"
            + '<button class="pk-arrow" data-open="lei" data-v="' + esc(l.lei) + '" title="展开/收起">'
            + (open.lei[l.lei] || q ? "▾" : "▸") + "</button>"
            + "</div>"
            + '<div class="pk-majors"' + ((open.lei[l.lei] || q) ? "" : " hidden") + ">" + majorsHtml + "</div>"
            + "</div>";
        });
        if (!leisHtml && q && !menHit) return;
        html += '<div class="pk-men">'
          + '<div class="pk-row pk-men-row">'
          + '<input type="checkbox" data-pk="men" data-v="' + esc(m.men) + '"' + (sel.mens[m.men] ? " checked" : "") + ">"
          + '<span class="pk-name" data-open="men" data-v="' + esc(m.men) + '">' + esc(m.men)
          + '<i class="pk-cnt">' + MEN_CNT[m.men] + "个专业</i></span>"
          + '<button class="pk-arrow" data-open="men" data-v="' + esc(m.men) + '" title="展开/收起">'
          + (open.men[m.men] || q ? "▾" : "▸") + "</button>"
          + "</div>"
          + '<div class="pk-leis"' + ((open.men[m.men] || q) ? "" : " hidden") + ">" + leisHtml + "</div>"
          + "</div>";
      });
      elTree.innerHTML = html || '<div class="pk-empty">没有匹配的专业</div>';
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
      Object.keys(sel.mens).forEach(function (men) {
        html += chip(men + "（整门类）", "men", men, MEN_CNT[men] + "专业");
      });
      Object.keys(sel.leis).forEach(function (lei) {
        html += chip(lei + "（整类）", "lei", lei, LEI_CNT[lei] + "专业");
      });
      Object.keys(sel.majors).forEach(function (n) {
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
        if (kind === "men") { if (cb.checked) sel.mens[v] = true; else delete sel.mens[v]; }
        else if (kind === "lei") { if (cb.checked) sel.leis[v] = true; else delete sel.leis[v]; }
        else { if (cb.checked) sel.majors[v] = true; else delete sel.majors[v]; }
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
          if (rmk === "men") delete sel.mens[v];
          else if (rmk === "lei") delete sel.leis[v];
          else delete sel.majors[v];
          renderTree(); notify();
          return;
        }
        if (t.getAttribute("data-exp")) openDetail(t.getAttribute("data-exp"), t.getAttribute("data-v"), t);
      });
    }
    if (elClear) {
      elClear.addEventListener("click", function () {
        sel.mens = {}; sel.leis = {}; sel.majors = {};
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
