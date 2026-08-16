/* ============================================================
 * 2026山东高考志愿参考 · 应用逻辑 (app.js)
 * 依赖: data_ruanke.js / data_toudang.js / data_fen.js (window 全局)
 * 纯逻辑函数可在 Node 中测试; DOM 部分仅在浏览器环境执行。
 * ============================================================ */
(function () {
  "use strict";

  var W = window;

  /* ---------------- 基础工具 ---------------- */
  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function normStr(s) { return String(s == null ? "" : s).replace(/\s+/g, ""); }

  /* ---------------- 数据索引 ---------------- */
  var TD = W.TD2026 || [];
  var TD_SCHOOL_RK = W.TD_SCHOOL_RK || {};
  var RK_META = W.RK_META || {};
  var RK_LEI2MAJOR = W.RK_LEI2MAJOR || {};
  var FEN = W.FEN2026 || [];

  // majorKey -> {name, men, lei, count}
  var META = {};
  // 专业名 -> [majorKey,...]
  var NAME2KEYS = {};
  // majorKey -> {schoolName: rank}
  var RK_FLAT = {};
  // 特色专业集合 (软科只发布开设名单, 不计算排名)
  var RK_SPECIAL = W.RK_SPECIAL || {};
  // 本科专业目录专业名集合 (用于区分"目录内未排名"与"非目录专业")
  var CAT_SET = {};
  (function () {
    var men, lei, majors, key, meta, rks;
    var catArr = W.CAT_NAMES || [];
    for (var c = 0; c < catArr.length; c++) CAT_SET[catArr[c]] = true;
    for (men in RK_META) {
      meta = RK_META[men];
      META[men] = meta;
      (NAME2KEYS[meta.name] = NAME2KEYS[meta.name] || []).push(men);
    }
    for (men in RK_META) {
      meta = RK_META[men];
      rks = W.RK2026 && W.RK2026[meta.men] && W.RK2026[meta.men][meta.lei] && W.RK2026[meta.men][meta.lei][men];
      if (rks) RK_FLAT[men] = rks;
    }
  })();

  var LEI_NAMES = {};
  (function () { for (var l in RK_LEI2MAJOR) LEI_NAMES[l] = true; })();

  // 缓存: core -> 包含的 majorKey 列表 ([])
  var CONTAINED_CACHE = {};
  var TEST_BAN_RE = /试验班|实验班|试点班/;
  function containedKeys(core) {
    if (CONTAINED_CACHE.hasOwnProperty(core)) return CONTAINED_CACHE[core];
    var out;
    if (LEI_NAMES[core]) {
      out = RK_LEI2MAJOR[core].slice(); // 大类 -> 目录包含的专业
    } else if (TEST_BAN_RE.test(core)) {
      out = [];                          // 试验班/特色班, 具体专业未公开
    } else if (NAME2KEYS[core]) {
      out = NAME2KEYS[core].slice();     // 具体专业
    } else {
      out = [core];                      // 未收录专业/特色名称 (pseudo key)
    }
    CONTAINED_CACHE[core] = out;
    return out;
  }
  function keyName(key) {
    var m = META[key];
    return m ? m.name : key;
  }
  function keyMeta(key) {
    var m = META[key];
    return m ? { name: m.name, men: m.men, lei: m.lei, count: m.count } : { name: key, men: "", lei: "", count: 0 };
  }
  // 软科专业排名页 URL: https://www.shanghairanking.cn/rankings/bcmr/2026/{专业代码}
  // majorKey 形如 "080901 计算机科学与技术", code 为前缀; pseudo key 无代码返回 null
  function ruankeUrl(key) {
    var meta = META[key];
    if (!meta) return null;
    var code = key.split(" ")[0];
    if (!code || code === key) return null;
    return "https://www.shanghairanking.cn/rankings/bcmr/2026/" + code;
  }
  // 专业排名状态:
  //   ranked    -> 软科2026上榜 (rank=名次, count=全国上榜数)
  //   unranked  -> 专业在软科838个发布专业内, 但该校未进前50% (或未开设)
  //   special   -> 软科"特色专业"(开设<4校), 只发布开设名单, 不计算排名
  //   notpub    -> 专业不在软科2026发布的838个专业内 (inCat=是否在本科专业目录)
  function majorStatus(key, rkSchool) {
    if (RK_SPECIAL[key]) {
      var inList = !!(rkSchool && RK_FLAT[key] && RK_FLAT[key].hasOwnProperty(rkSchool));
      return { st: "special", inList: inList };
    }
    if (!rkSchool) return { st: "notpub", inCat: !!CAT_SET[keyName(key)] };
    var rks = RK_FLAT[key];
    if (!rks) return { st: "notpub", inCat: !!CAT_SET[keyName(key)] };
    if (rks.hasOwnProperty(rkSchool)) {
      return { st: "ranked", rank: rks[rkSchool], count: (META[key] && META[key].count) || 0 };
    }
    return { st: "unranked" };
  }
  // 兼容旧调用: 返回排名或 null (仅对 ranked 状态)
  function rankOf(key, rkSchool) {
    var s = majorStatus(key, rkSchool);
    return s.st === "ranked" ? s.rank : null;
  }

  // 括号备注拆分: 嵌套括号 ")(/）(" 视为分隔; 按逗号/分号拆分; 顿号不拆
  function splitNote(note) {
    if (!note) return [];
    var t = String(note).replace(/[)）]\s*[（(]/g, "，");
    var out = [];
    var parts = t.split(/[，,；;]/);
    for (var i = 0; i < parts.length; i++) {
      var s = parts[i].trim();
      if (s) out.push(s);
    }
    return out;
  }
  // 备注徽章列表: 拆分段 且 与招生类型徽章去重(相等或为其前缀, 如"高校专项"⊂"高校专项计划")
  function noteBadges(note, typ) {
    var parts = splitNote(note);
    var out = [];
    for (var i = 0; i < parts.length; i++) {
      if (typ && typ !== "普通" && (parts[i] === typ || typ.indexOf(parts[i]) === 0)) continue;
      out.push(parts[i]);
    }
    return out;
  }

  /* ---------------- 意向专业列表 ---------------- */
  // {n:名称, m:门类, l:专业类, code:代码, from:'rk'|'td'}
  var INTENT = [];
  (function () {
    var menOrder = W.RK_MEN_ORDER || [];
    var leiOrder = W.RK_LEI_ORDER || [];
    var key, meta;
    var list = [];
    for (key in META) {
      meta = META[key];
      list.push({ n: meta.name, m: meta.men, l: meta.lei, code: key.split(" ")[0] === meta.name ? "" : key.split(" ")[0], from: "rk" });
    }
    list.sort(function (a, b) {
      var am = menOrder.indexOf(a.m), bm = menOrder.indexOf(b.m);
      if (am !== bm) return (am < 0 ? 999 : am) - (bm < 0 ? 999 : bm);
      var al = leiOrder.indexOf(a.l), bl = leiOrder.indexOf(b.l);
      if (al !== bl) return (al < 0 ? 999 : al) - (bl < 0 ? 999 : bl);
      return a.n < b.n ? -1 : a.n > b.n ? 1 : 0;
    });
    // 投档表特有核心名(未收录软科、非类、非试验班)
    var seen = {};
    for (var i = 0; i < list.length; i++) seen[list[i].n] = true;
    var extraSet = {};
    for (var j = 0; j < TD.length; j++) {
      var c = TD[j][2];
      if (!seen[c] && !LEI_NAMES[c] && !TEST_BAN_RE.test(c)) extraSet[c] = true;
    }
    var extras = Object.keys(extraSet).sort();
    for (var k = 0; k < extras.length; k++) {
      list.push({ n: extras[k], m: "其他(未在软科2026收录)", l: "投档表名称", code: "", from: "td" });
    }
    INTENT = list;
  })();

  /* ---------------- 志愿类 与 意向专业匹配 ---------------- */
  // 该志愿类是否包含意向专业 (大类: 该校实际开设∩目录; 试验班: 查证列表)
  function rowMatchesIntent(r, intentNames, onlyDirect) {
    var core = r[2];
    if (intentNames[core]) return true;          // 直接招生
    if (onlyDirect) return false;
    var keys = rowMajors(r);
    for (var i = 0; i < keys.length; i++) {
      if (intentNames[keyName(keys[i])]) return true;
    }
    return false;
  }

  // 返回该志愿类中, 命中意向专业的专业名集合(用于高亮)
  function matchedNamesInRow(r, intentNames) {
    var out = {};
    var core = r[2];
    if (intentNames[core]) out[core] = true;
    var keys = rowMajors(r);
    for (var i = 0; i < keys.length; i++) {
      var n = keyName(keys[i]);
      if (intentNames[n]) out[n] = true;
    }
    return out;
  }

  // 试验班查证: 返回该行的有效包含专业 keys (null=无查证)
  function sybKeys(r) {
    var syb = r[8];
    if (!syb || syb.mode !== "list") return null;
    var keys = [];
    for (var i = 0; i < syb.majors.length; i++) {
      var n = syb.majors[i];
      keys.push((NAME2KEYS[n] && NAME2KEYS[n][0]) || n);
    }
    return keys;
  }

  // 行级包含专业 keys (优先级):
  //   1) 大类预计算: 该校实际开设∩目录类 (r[9], 构建期生成; null=回退目录全集)
  //   2) 具体专业/未收录名称: containedKeys(core)
  //   3) 试验班查证列表: sybKeys(r)
  function rowMajors(r) {
    if (r[9]) return r[9];
    var keys = containedKeys(r[2]);
    if (keys.length) return keys;
    var sk = sybKeys(r);
    return sk || [];
  }

  /* ---------------- 冲稳保 ---------------- */
  // R=我的位次, W=投档位次; 返回 '保'|'稳'|'冲'|'难'|null
  function bandOf(R, W, c1, c2) {
    if (R == null || W == null) return null;
    if (W > c2 * R) return "保";
    if (W > R) return "稳";
    if (W >= c1 * R) return "冲";
    return "难";
  }

  /* ---------------- 筛选状态 ---------------- */
  var SUBJ_ALL = ["物理", "化学", "生物", "思想政治", "历史", "地理"]; // 3+3 选科
  var ALL_TYPES = (function () { var s = {}, i; for (i = 0; i < TD.length; i++) s[TD[i][7]] = 1; return Object.keys(s).sort(); })();

  var S = {
    intent: {},            // 意向专业名 -> true
    schoolKw: "",
    textKw: "",
    subject: {},           // 我的选科: 科目名 -> true (3+3, 最多3科)
    types: {},             // 招生类型 -> true (空=全部)
    scoreMin: null,
    scoreMax: null,
    rankMin: null,
    rankMax: null,
    onlyDirect: false,
    onlyFav: false,
    myRank: null,
    c1: 0.8,
    c2: 1.15,
    sort: "rankAsc",
    page: 0,
    pageSize: 80
  };
  (function () { for (var i = 0; i < ALL_TYPES.length; i++) S.types[ALL_TYPES[i]] = true; })();

  /* 选科判定: 志愿类选科要求 vs 考生所选科目
   *  reqText 形如 "物理、化学" / "不限"
   *  subjects 为考生已选科目集合
   *  返回 { state: 'full'|'partial'|'none', missing: [缺的科目] }
   *  full    = 要求全部满足或"不限"
   *  partial = 要求未全满足但与已选科目有交集(宽松判定, 标记缺科)
   *  none    = 要求与已选科目无交集
   */
  function subjectState(reqText, subjects) {
    if (!reqText || reqText === "不限") return { state: "full", missing: [] };
    if (!Object.keys(subjects).length) return { state: "full", missing: [] }; // 未填选科, 不限制
    var req = reqText.split("、").map(function (s) { return s.trim(); }).filter(Boolean);
    if (!req.length) return { state: "full", missing: [] };
    var has = 0, missing = [];
    for (var i = 0; i < req.length; i++) {
      if (subjects[req[i]]) has++; else missing.push(req[i]);
    }
    if (!has) return { state: "none", missing: missing };
    if (missing.length) return { state: "partial", missing: missing };
    return { state: "full", missing: [] };
  }

  var favSet = {};
  var FAV_KEY = "sd2026_fav_v1";
  function loadFav() {
    favSet = {};
    try {
      var raw = localStorage.getItem(FAV_KEY);
      if (raw) { var arr = JSON.parse(raw); for (var i = 0; i < arr.length; i++) favSet[arr[i]] = true; }
    } catch (e) { favSet = {}; }
  }
  function saveFav() {
    try { localStorage.setItem(FAV_KEY, JSON.stringify(Object.keys(favSet).map(Number))); } catch (e) { }
  }
  function toggleFav(i) {
    if (favSet[i]) delete favSet[i]; else favSet[i] = true;
    saveFav();
  }

  /* ---------------- 核心筛选 ---------------- */
  function testRow(i, r) {
    if (S.onlyFav && !favSet[i]) return false;
    if (S.schoolKw && normStr(r[1]).indexOf(S.schoolKw) < 0) return false;
    if (S.textKw && (r[2] + " " + r[3] + " " + r[1]).indexOf(S.textKw) < 0) return false;
    var subjCnt = Object.keys(S.subject).length;
    if (subjCnt) {
      var subjSt = subjectState(r[4], S.subject);
      if (subjSt.state === "none") return false;
      if (subjCnt === 3 && subjSt.state === "partial") return false; // 选满3科: 精确匹配
    }
    if (S.types && !S.types[r[7]]) return false;
    if (S.scoreMin != null && (r[5] == null || r[5] < S.scoreMin)) return false;
    if (S.scoreMax != null && (r[5] == null || r[5] > S.scoreMax)) return false;
    if (S.rankMin != null && (r[6] == null || r[6] < S.rankMin)) return false;
    if (S.rankMax != null && (r[6] == null || r[6] > S.rankMax)) return false;
    var intents = Object.keys(S.intent);
    if (intents.length && !rowMatchesIntent(r, S.intent, S.onlyDirect)) return false;
    return true;
  }

  // 数字输入校验: 仅正整数且不超过上限; 0/负数/小数/超范围/非数字 一律返回 null
  function cleanNum(v, max) {
    var s = String(v == null ? "" : v).trim();
    if (!/^[1-9]\d*$/.test(s)) return null;
    var n = parseInt(s, 10);
    if (max != null && n > max) return null;
    return n;
  }

  var SORT_FNS = {
    rankAsc: function (a, b) { return (a[6] == null ? 1e15 : a[6]) - (b[6] == null ? 1e15 : b[6]); },
    rankDesc: function (a, b) { return (b[6] == null ? -1e15 : b[6]) - (a[6] == null ? -1e15 : a[6]); },
    scoreDesc: function (a, b) { return (b[5] == null ? -1e9 : b[5]) - (a[5] == null ? -1e9 : a[5]); },
    scoreAsc: function (a, b) { return (a[5] == null ? 1e9 : a[5]) - (b[5] == null ? 1e9 : b[5]); },
    school: function (a, b) {
      var c = a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0;
      if (c) return c;
      return (a[6] == null ? 1e15 : a[6]) - (b[6] == null ? 1e15 : b[6]);
    }
  };

  // 返回筛选后的行索引数组 (已排序)
  function filteredIndices() {
    var out = [], i, r;
    for (i = 0; i < TD.length; i++) {
      r = TD[i];
      if (testRow(i, r)) out.push(i);
    }
    var fn = SORT_FNS[S.sort] || SORT_FNS.rankAsc;
    var subjOn = Object.keys(S.subject).length > 0;
    out.sort(function (x, y) {
      if (subjOn) { // 启用我的选科时, 完全满足的排在需补选之前
        var sx = subjectState(TD[x][4], S.subject).state === "full" ? 0 : 1;
        var sy = subjectState(TD[y][4], S.subject).state === "full" ? 0 : 1;
        if (sx !== sy) return sx - sy;
      }
      return fn(TD[x], TD[y]);
    });
    return out;
  }

  /* ---------------- 一分一段换算 ---------------- */
  // 分数 -> 位次 (二分)
  function scoreToRank(sc) {
    if (FEN.length === 0) return null;
    if (sc >= FEN[0][0]) return { rank: FEN[0][1], exact: sc === FEN[0][0] };
    if (sc < FEN[FEN.length - 1][0]) return { rank: FEN[FEN.length - 1][1], exact: false };
    var lo = 0, hi = FEN.length - 1;
    while (lo < hi) {
      var mid = (lo + hi + 1) >> 1;
      if (FEN[mid][0] >= sc) lo = mid; else hi = mid - 1;
    }
    return { rank: FEN[lo][1], exact: FEN[lo][0] === sc };
  }
  // 位次 -> 分数 (该位次对应的最低分数)
  function rankToScore(rk) {
    if (FEN.length === 0) return null;
    if (rk < FEN[0][1]) return { score: FEN[0][0], note: "高于最高分段" };
    if (rk > FEN[FEN.length - 1][1]) return { score: FEN[FEN.length - 1][0], note: "低于最低分段" };    var lo = 0, hi = FEN.length - 1;
    while (lo < hi) {
      var mid = (lo + hi) >> 1;
      if (FEN[mid][1] < rk) lo = mid + 1; else hi = mid;
    }
    return { score: FEN[lo][0], note: "" };
  }
  // 某分数的同分人数 (FEN 降序: 分数越大名次越小)
  function countAtScore(sc) {
    var i = 0;
    while (i < FEN.length && FEN[i][0] > sc) i++;
    if (i >= FEN.length || FEN[i][0] !== sc) return null;
    var higher = i - 1 >= 0 ? FEN[i - 1][1] : 0; // 更高一分的累计名次
    return FEN[i][1] - higher;
  }

  /* ============================================================
   * DOM 部分 (仅浏览器)
   * ============================================================ */
  if (typeof document !== "undefined") {
    var $ = function (id) { return document.getElementById(id); };
    var resultsEl, statsEl, pageEl, intentChipsEl, intentInput, intentDrop;

    function setIntents(list) {
      S.intent = {};
      for (var i = 0; i < list.length; i++) S.intent[list[i]] = true;
      S.page = 0;
      renderIntentChips();
      applyAndRender();
    }
    function addIntent(name) { setIntents(Object.keys(S.intent).concat([name])); }
    function removeIntent(name) {
      var k = Object.keys(S.intent).filter(function (x) { return x !== name; });
      setIntents(k);
    }

    function renderIntentChips() {
      var names = Object.keys(S.intent);
      intentChipsEl.innerHTML = names.map(function (n) {
        return '<span class="chip intent-chip">' + esc(n) + '<button class="x" data-rm="' + esc(n) + '" title="移除">×</button></span>';
      }).join("");
    }

    /* ---- 意向专业自动补全 ---- */
    function intentMatches(q) {
      var nq = normStr(q);
      if (!nq) return [];
      var out = [], i, it;
      var hay;
      for (i = 0; i < INTENT.length; i++) {
        it = INTENT[i];
        hay = normStr(it.n + it.code + it.l);
        if (hay.indexOf(nq) >= 0) {
          out.push(it);
          if (out.length >= 60) break;
        }
      }
      return out;
    }
    function renderDrop(items) {
      if (!items.length) { intentDrop.classList.add("hidden"); return; }
      var html = "", lastMen = null;
      for (var i = 0; i < items.length; i++) {
        var it = items[i];
        if (it.m !== lastMen) { html += '<div class="drop-men">' + esc(it.m) + '</div>'; lastMen = it.m; }
        html += '<div class="drop-item" data-n="' + esc(it.n) + '"><span class="dn">' + esc(it.n) + "</span>"
          + '<span class="dl">' + esc(it.l) + (it.code ? " · " + esc(it.code) : "") + "</span></div>";
      }
      intentDrop.innerHTML = html;
      intentDrop.classList.remove("hidden");
    }

    /* ---- 渲染 ---- */
    function bandText(b) { return { 冲: "冲", 稳: "稳", 保: "保", 难: "难" }[b] || ""; }

    function rowHtml(i, r, idx) {
      var core = r[2], note = r[3], school = r[1], xk = r[4], sc = r[5], rk = r[6], typ = r[7];
      var syb = r[8];
      var rkSchool = TD_SCHOOL_RK[school] || "";
      var band = bandOf(S.myRank, rk, S.c1, S.c2);
      var matched = matchedNamesInRow(r, S.intent);
      var isLei = !!LEI_NAMES[core];
      var leiFallback = isLei && !r[9];              // 大类但构建期无该校数据 -> 回退目录全集
      var leiManual = isLei && r[9] && !TD_SCHOOL_RK[school];  // 软科未收录但有人工查证
      var isSybList = !!syb && syb.mode === "list";
      var keys = rowMajors(r);

      var chips = "";
      var entries = [];
      for (var k = 0; k < keys.length; k++) {
        var key = keys[k];
        var meta = keyMeta(key);
        var st = majorStatus(key, rkSchool);
        entries.push({ key: key, name: meta.name, men: meta.men, count: meta.count, st: st, hit: !!matched[meta.name] });
      }
      if (syb && syb.mode === "renxuan") {
        chips = '<span class="chip none" title="可任选该校开设的专业，方向限制：' + esc(syb.dir) + '，具体以院校培养方案为准">任选该校开设专业（' + esc(syb.dir) + "）</span>";
      } else if (!rkSchool && keys.length) {
        chips = '<span class="chip none" title="该校未收录于软科2026专业排名，无排名数据">该校未收录于软科2026</span>';
      } else {
        for (var e = 0; e < entries.length; e++) {
          var ent = entries[e];
          var cls = "chip";
          if (ent.hit) cls += " hit";
          var label, tip;
          if (ent.st.st === "ranked") {
            cls += " has-rank";
            label = esc(ent.name) + ' <b>#' + ent.st.rank + "</b>";
            tip = "软科2026 第" + ent.st.rank + "名，全国上榜" + ent.st.count + "所";
          } else if (ent.st.st === "special") {
            cls += " chip-special";
            label = esc(ent.name) + ' <i>特色专业</i>';
            tip = ent.st.inList
              ? "软科2026特色专业，开设院校<4所，该校在软科开设名单中，不计算排名"
              : "软科2026特色专业，开设院校<4所，不计算排名，是否开设以院校为准";
          } else if (ent.st.st === "notpub") {
            cls += " chip-notpub";
            label = esc(ent.name) + ' <i>未排名</i>';
            tip = ent.st.inCat
              ? "该专业在《本科专业目录》内，但软科2026未发布其排名"
              : "非本科目录专业，软科2026未排名";
          } else {
            cls += " no-rank";
            label = esc(ent.name) + ' <i>未上榜</i>';
            tip = "该专业软科2026发布排名，但该校未进前50%，或未开设此专业";
          }
          chips += '<button class="' + cls + '" data-pick="' + esc(ent.name) + '" title="' + tip + "｜点击设为意向专业\">" + label + "</button>";
        }
      }

      var badges = "";
      if (typ !== "普通") badges += '<span class="badge t-' + esc(typ) + '">' + esc(typ) + "</span>";
      var nb = noteBadges(note, typ);
      for (var nbI = 0; nbI < nb.length; nbI++) {
        badges += '<span class="badge note">' + esc(nb[nbI]) + "</span>";
      }
      if (isLei) badges += '<span class="badge lei" title="' + (leiManual
        ? "所含专业来自院校官网2026年招生信息，人工查证整理"
        : "所含专业已按该校实际开设情况筛减（软科收录/2026投档/查证口径），实际以院校当年招生简章为准") + '">大类招生' + (leiManual ? "·已查证" : "") + (leiFallback ? "·目录口径" : "") + "</span>";
      if (isSybList) badges += '<span class="badge syb" title="包含专业来自院校2026年招生信息，人工查证整理">试验班·已查证</span>';
      if (syb && syb.mode === "renxuan") badges += '<span class="badge syb" title="可任选该校开设的专业，方向限制：' + esc(syb.dir) + '">试验班·任选</span>';
      if (rkSchool && rkSchool !== school) badges += '<span class="badge rk" title="该校排名按校本部口径">排名按校本部「' + esc(rkSchool) + '」</span>';
      if (Object.keys(S.subject).length && Object.keys(S.subject).length < 3) {
        var subjSt = subjectState(xk, S.subject);
        if (subjSt.state === "partial") {
          badges += '<span class="badge miss" title="您的选科未完全满足该志愿类要求，需补选：' + esc(subjSt.missing.join("、")) + '">缺：' + esc(subjSt.missing.join("、")) + "</span>";
        }
      }

      var metaLine = [];
      metaLine.push("最低分 <b>" + (sc == null ? "—" : sc) + "</b>");
      metaLine.push("最低位次 <b>" + (rk == null ? "—" : rk) + "</b>");
      metaLine.push("选科 " + esc(xk));
      if (S.myRank != null && rk != null) {
        var d = rk - S.myRank;
        metaLine.push(d >= 0
          ? '<span class="ok">我的位次比投档线靠前 <b>' + d + "</b> 名</span>"
          : '<span class="bad">我的位次比投档线靠后 <b>' + (-d) + "</b> 名</span>");
      }

      var warn = "";
      if (isLei && keys.length > 1 && Object.keys(S.intent).length) {
        var others = entries.map(function (x) { return x.name; }).filter(function (n) { return !matched[n]; });
        warn = '<div class="warn">⚠ 该志愿类为「' + esc(core) + '」大类招生，除所选专业外还包含：'
          + esc(others.slice(0, 12).join("、")) + (others.length > 12 ? " 等共" + keys.length + "个专业" : "")
          + "。所列专业" + (leiManual ? "来自院校官网人工查证" : leiFallback ? "为目录口径" : "已按该校实际开设情况筛减（软科收录/2026投档/查证口径）") + "，以院校当年招生简章为准</div>";
      } else if (isLei && keys.length > 1) {
        warn = '<div class="hint">该志愿类为「' + esc(core) + '」大类招生，含 ' + keys.length
          + " 个专业，" + (leiManual ? "来自院校官网人工查证" : leiFallback ? "为目录口径" : "已按该校实际开设情况筛减（软科收录/2026投档/查证口径）") + "，以院校当年招生简章为准</div>";
      } else if (syb && syb.mode === "list") {
        if (keys.length > 1 && Object.keys(S.intent).length) {
          var others2 = entries.map(function (x) { return x.name; }).filter(function (n) { return !matched[n]; });
          warn = '<div class="warn">⚠ 该试验班除所选专业外还包含：'
            + esc(others2.slice(0, 12).join("、")) + (others2.length > 12 ? " 等共" + keys.length + "个专业" : "")
            + "。含专业来自院校2026年招生信息，入学后以院校培养方案为准</div>";
        } else {
          warn = '<div class="hint">含专业来自院校2026年招生信息（人工查证），入学后以院校培养方案为准。</div>';
        }
      } else if (syb && syb.mode === "renxuan") {
        warn = '<div class="hint">可任选该校开设的专业，方向限制：' + esc(syb.dir) + "。具体以院校培养方案为准。</div>";
      } else if (!keys.length) {
        warn = '<div class="hint">该志愿类为试验班/特色班，具体包含专业未公开，请查阅院校招生简章。</div>';
      }

      var detail = '<table class="rk-detail"><thead><tr><th>专业</th><th>全国上榜院校数</th><th>该校软科排名</th></tr></thead><tbody>';
      if (syb && syb.mode === "renxuan") {
        detail += '<tr><td colspan="3">可任选该校开设的专业，方向限制：' + esc(syb.dir) + "。具体专业以院校培养方案为准。</td></tr>";
      } else if (!rkSchool && keys.length) {
        detail += '<tr><td colspan="3">院校未收录于软科2026专业排名，无排名数据。</td></tr>';
      } else if (!keys.length) {
        detail += '<tr><td colspan="3">' + (syb && syb.mode === "notfound" ? "官网未查到该试验班包含专业。" : "具体包含专业未公开。") + "</td></tr>";
      } else {
        for (var d2 = 0; d2 < entries.length; d2++) {
          var en = entries[d2];
          var rankCell;
          if (en.st.st === "ranked") {
            rankCell = '<b class="ok">第' + en.st.rank + "名</b>";
          } else if (en.st.st === "special") {
            rankCell = '<span class="dim">软科特色专业，不排名' + (en.st.inList ? "，该校在开设名单中" : "") + "</span>";
          } else if (en.st.st === "notpub") {
            rankCell = '<span class="dim">' + (en.st.inCat ? "目录内专业，软科未发布排名" : "非目录专业，软科未排名") + "</span>";
          } else {
            rankCell = '<span class="dim">未上榜，前50%以外或未开设</span>';
          }
          var url = ruankeUrl(en.key);
          var nameHtml = url
            ? '<a href="' + url + '" target="_blank" rel="noopener" title="在软科官网查看该专业排名，新窗口打开">' + esc(en.name) + " ↗</a>"
            : esc(en.name);
          detail += "<tr><td>" + nameHtml + (en.men ? '<span class="dim"> ' + esc(en.men) + "</span>" : "") + "</td>"
            + "<td>" + (en.count ? en.count : "—") + "</td>"
            + "<td>" + rankCell + "</td></tr>";
        }
      }
      detail += "</tbody></table>";

      var star = favSet[i] ? "★" : "☆";
      return '<article class="row" data-i="' + i + '">'
        + '<div class="row-top">'
        + (band ? '<span class="band b-' + band + '" title="冲稳保判断：基于我的位次 ' + S.myRank + '">' + bandText(band) + "</span>" : "")
        + '<button class="star" data-act="fav" title="收藏">' + star + "</button>"
        + '<span class="school">' + esc(school) + "</span>"
        + '<span class="core">' + esc(core) + "</span>"
        + badges
        + "</div>"
        + '<div class="row-meta">' + metaLine.join(" · ") + "</div>"
        + '<div class="chips">' + chips + "</div>"
        + warn
        + "<details class=\"det\"><summary>排名明细与说明</summary>" + detail + "</details>"
        + "</article>";
    }

    function render() {
      var indices = filteredIndices();
      var total = indices.length;
      var pages = Math.max(1, Math.ceil(total / S.pageSize));
      if (S.page >= pages) S.page = pages - 1;
      var start = S.page * S.pageSize;
      var slice = indices.slice(start, start + S.pageSize);

      var html = "";
      for (var k = 0; k < slice.length; k++) {
        var i = slice[k];
        html += rowHtml(i, TD[i], k);
      }
      resultsEl.innerHTML = html || '<div class="empty">没有符合条件的志愿类。请调整筛选条件。</div>';

      // 统计
      var parts = ["共 <b>" + total + "</b> 个志愿类"];
      if (Object.keys(S.subject).length) {
        var sf = 0, sp = 0;
        for (var t2 = 0; t2 < indices.length; t2++) {
          var st2 = subjectState(TD[indices[t2]][4], S.subject).state;
          if (st2 === "full") sf++; else if (st2 === "partial") sp++;
        }
        parts.push('选科完全满足 <b class="c-bao">' + sf + "</b> · 需补选科目 <b class=\"c-chong\">" + sp + "</b>");
      }
      if (S.myRank != null) {
        var c = { 冲: 0, 稳: 0, 保: 0, 难: 0 };
        for (var t = 0; t < indices.length; t++) {
          var b = bandOf(S.myRank, TD[indices[t]][6], S.c1, S.c2);
          if (b) c[b]++;
        }
        parts.push('冲 <b class="c-chong">' + c["冲"] + "</b> · 稳 <b class=\"c-wen\">" + c["稳"]
          + "</b> · 保 <b class=\"c-bao\">" + c["保"] + "</b> · 差距大 <b class=\"c-nan\">" + c["难"] + "</b>");
      }
      statsEl.innerHTML = parts.join("　");
      pageEl.innerHTML = '<button id="pgPrev" ' + (S.page === 0 ? "disabled" : "") + ">« 上一页</button>"
        + '<span>第 ' + (S.page + 1) + " / " + pages + " 页</span>"
        + '<button id="pgNext" ' + (S.page >= pages - 1 ? "disabled" : "") + ">下一页 »</button>"
        + '<span class="dim">每页 <select id="pgSize">'
        + [50, 80, 150, 300].map(function (n) { return '<option value="' + n + '"' + (S.pageSize === n ? " selected" : "") + ">" + n + "</option>"; }).join("")
        + "</select> 条</span>";
      bindPage();
    }

    function bindPage() {
      var p = $("pgPrev"), n = $("pgNext"), s = $("pgSize");
      if (p) p.onclick = function () { S.page--; applyAndRender(); };
      if (n) n.onclick = function () { S.page++; applyAndRender(); };
      if (s) s.onchange = function () { S.pageSize = +s.value; S.page = 0; applyAndRender(); };
    }

    function applyAndRender() { render(); }

    /* ---- CSV 导出 ---- */
    function statusText(st) {
      if (st.st === "ranked") return "软科第" + st.rank + "名";
      if (st.st === "special") return "软科特色专业，不排名";
      if (st.st === "notpub") return st.inCat ? "目录内专业，软科未排名" : "非目录专业，软科未排名";
      return "未上榜，前50%外";
    }
    function exportCSV() {
      var indices = filteredIndices();
      var rows = [["院校代码", "院校名称", "志愿类(专业)", "备注", "选科要求", "最低分", "最低位次", "招生类型", "包含专业(目录口径, 软科排名)", "冲稳保"]];
      for (var t = 0; t < indices.length; t++) {
        var i = indices[t], r = TD[i];
        var rkSchool = TD_SCHOOL_RK[r[1]] || "";
        var keys = rowMajors(r);
        var syb = r[8];
        var majors = [];
        if (syb && syb.mode === "renxuan") {
          majors.push("任选该校开设专业(" + syb.dir + ")");
        } else {
          for (var k = 0; k < keys.length; k++) {
            var meta = keyMeta(keys[k]);
            var st = majorStatus(keys[k], rkSchool);
            majors.push(meta.name + "(" + statusText(st) + ")");
          }
        }
        var band = bandOf(S.myRank, r[6], S.c1, S.c2) || "";
        rows.push([r[0], r[1], r[2], noteBadges(r[3], r[7]).join("; "), r[4], r[5], r[6], r[7], majors.join(" | "), band]);
      }
      var csv = "\uFEFF" + rows.map(function (row) {
        return row.map(function (cell) {
          var s = String(cell == null ? "" : cell);
          return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
        }).join(",");
      }).join("\r\n");
      var blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
      var a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "山东2026志愿参考_筛选结果.csv";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(function () { URL.revokeObjectURL(a.href); }, 3000);
    }

    /* ---- 一分一段 (第①步) ---- */
    function fenScoreToRank() {
      var v = cleanNum($("fenScore").value, 750);
      if (v == null) { $("fenOut1").textContent = "请输入正整数分数"; return; }
      var r = scoreToRank(v);
      if (!r) { $("fenOut1").textContent = "超出一分一段表范围"; return; }
      var cnt = countAtScore(v);
      $("fenOut1").innerHTML = "分数 " + v + " 分 ≈ 位次 <b>" + r.rank + "</b>"
        + (r.exact ? "" : "，表中无此分数，按更高分数段近似")
        + (cnt != null ? "，该分数段约 " + cnt + " 人" : "")
        + '　<button class="btn ghost" id="fillRank">填入冲稳保位次</button>';
    }
    function fenRankToScore() {
      var v = cleanNum($("fenRank").value, 1000000);
      if (v == null) { $("fenOut2").textContent = "请输入正整数位次"; return; }
      var r = rankToScore(v);
      if (!r) { $("fenOut2").textContent = "超出一分一段表范围"; return; }
      $("fenOut2").innerHTML = "位次 " + v + " ≈ 分数 <b>" + r.score + "</b> 分"
        + (r.note ? "<span class=\"dim\">，" + r.note + "</span>" : "");
    }

    /* ---- 事件绑定 ---- */
    function init() {
      loadFav();
      resultsEl = $("results");
      statsEl = $("stats");
      pageEl = $("pager");
      intentChipsEl = $("intentChips");
      intentInput = $("intentInput");
      intentDrop = $("intentDrop");

      // 意向专业输入
      intentInput.addEventListener("input", function () {
        var q = intentInput.value;
        if (!q) { intentDrop.classList.add("hidden"); return; }
        renderDrop(intentMatches(q));
      });
      intentInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          var q = intentInput.value;
          var items = intentMatches(q);
          if (items.length) { addIntent(items[0].n); intentInput.value = ""; intentDrop.classList.add("hidden"); }
        } else if (e.key === "Escape") {
          intentDrop.classList.add("hidden");
        }
      });
      intentDrop.addEventListener("click", function (e) {
        var el = e.target.closest(".drop-item");
        if (!el) return;
        addIntent(el.getAttribute("data-n"));
        intentInput.value = "";
        intentDrop.classList.add("hidden");
      });
      document.addEventListener("click", function (e) {
        if (!intentDrop.contains(e.target) && e.target !== intentInput) intentDrop.classList.add("hidden");
      });
      intentChipsEl.addEventListener("click", function (e) {
        var b = e.target.closest("[data-rm]");
        if (b) removeIntent(b.getAttribute("data-rm"));
      });
      $("intentClear").addEventListener("click", function () { setIntents([]); });
      $("intentOnlyDirect").addEventListener("change", function (e) { S.onlyDirect = e.target.checked; S.page = 0; applyAndRender(); });
      $("onlyFav").addEventListener("change", function (e) { S.onlyFav = e.target.checked; S.page = 0; applyAndRender(); });

      // 热门专业
      var hot = ["计算机科学与技术", "软件工程", "人工智能", "数据科学与大数据技术", "临床医学", "口腔医学",
        "法学", "会计学", "电气工程及其自动化", "自动化", "电子信息工程", "通信工程", "金融学", "汉语言文学", "英语", "数学与应用数学"];
      $("hotRow").innerHTML = hot.map(function (n) {
        return '<button class="chip hot" data-hot="' + esc(n) + '">' + esc(n) + "</button>";
      }).join("");
      $("hotRow").addEventListener("click", function (e) {
        var b = e.target.closest("[data-hot]");
        if (b) addIntent(b.getAttribute("data-hot"));
      });

      // 院校/全文搜索
      $("schoolKw").addEventListener("input", function (e) { S.schoolKw = normStr(e.target.value); S.page = 0; applyAndRender(); });
      $("textKw").addEventListener("input", function (e) { S.textKw = e.target.value.trim(); S.page = 0; applyAndRender(); });

      // 我的选科 (3+3, 最多3科)
      $("subjBox").innerHTML = SUBJ_ALL.map(function (x) {
        return '<button class="chip sj" data-sj="' + esc(x) + '">' + esc(x) + "</button>";
      }).join("");
      $("subjBox").addEventListener("click", function (e) {
        var b = e.target.closest("[data-sj]");
        if (!b) return;
        var v = b.getAttribute("data-sj");
        var n = Object.keys(S.subject).length;
        if (S.subject[v]) {
          delete S.subject[v];
        } else if (n >= 3) {
          $("subjHint").innerHTML = "3+3 模式最多选择 3 科，请先取消已选科目";
          return;
        } else {
          S.subject[v] = true;
        }
        S.page = 0;
        applyAndRender();
        renderSubj();
        updateSubjHint();
      });
      $("subjClear").addEventListener("click", function () {
        S.subject = {};
        S.page = 0;
        applyAndRender();
        renderSubj();
        updateSubjHint();
      });

      // 招生类型
      $("typeBox").innerHTML = ['<button class="xk-all" data-t="__all__">全选</button>',
        '<button class="xk-all" data-t="__normal__">仅普通批</button>']
        .concat(ALL_TYPES.map(function (x) {
          var on = S.types[x] ? " on" : "";
          return '<button class="chip xk' + on + '" data-t="' + esc(x) + '">' + esc(x) + "</button>";
        })).join("");
      $("typeBox").addEventListener("click", function (e) {
        var b = e.target.closest("[data-t]");
        if (!b) return;
        var v = b.getAttribute("data-t");
        if (v === "__all__") {
          for (var i = 0; i < ALL_TYPES.length; i++) S.types[ALL_TYPES[i]] = true;
        } else if (v === "__normal__") {
          for (var i = 0; i < ALL_TYPES.length; i++) delete S.types[ALL_TYPES[i]];
          S.types["普通"] = true;
        } else if (S.types[v]) { delete S.types[v]; } else { S.types[v] = true; }
        S.page = 0; applyAndRender(); renderTypeButtons();
      });

      // 分数/位次区间 (仅正整数, 拒绝 0/负数/小数; 分数≤750, 位次≤1000000)
      $("scoreMin").addEventListener("input", function (e) { S.scoreMin = cleanNum(e.target.value, 750); S.page = 0; applyAndRender(); });
      $("scoreMax").addEventListener("input", function (e) { S.scoreMax = cleanNum(e.target.value, 750); S.page = 0; applyAndRender(); });
      $("rankMin").addEventListener("input", function (e) { S.rankMin = cleanNum(e.target.value, 1000000); S.page = 0; applyAndRender(); });
      $("rankMax").addEventListener("input", function (e) { S.rankMax = cleanNum(e.target.value, 1000000); S.page = 0; applyAndRender(); });

      // 我的位次 & 冲稳保
      $("myRank").addEventListener("input", function (e) {
        S.myRank = cleanNum(e.target.value, 1000000);
        S.page = 0;
        var c1v = parseFloat($("c1").value), c2v = parseFloat($("c2").value);
        if (!isNaN(c1v)) S.c1 = c1v;
        if (!isNaN(c2v)) S.c2 = c2v;
        applyAndRender();
      });
      $("c1").addEventListener("input", function (e) { S.c1 = parseFloat(e.target.value) || 0.8; $("c1v").textContent = S.c1.toFixed(2); applyAndRender(); });
      $("c2").addEventListener("input", function (e) { S.c2 = parseFloat(e.target.value) || 1.15; $("c2v").textContent = S.c2.toFixed(2); applyAndRender(); });

      // 排序
      $("sortSel").addEventListener("change", function (e) { S.sort = e.target.value; S.page = 0; applyAndRender(); });

      // 结果区事件委托
      resultsEl.addEventListener("click", function (e) {
        var star = e.target.closest("[data-act='fav']");
        if (star) {
          var rowEl = star.closest(".row");
          var i = +rowEl.getAttribute("data-i");
          toggleFav(i);
          star.textContent = favSet[i] ? "★" : "☆";
          if (S.onlyFav) applyAndRender();
          return;
        }
        var pick = e.target.closest("[data-pick]");
        if (pick) addIntent(pick.getAttribute("data-pick"));
      });

      // 导出
      $("exportBtn").addEventListener("click", exportCSV);
      $("resetBtn").addEventListener("click", function () {
        S.schoolKw = ""; S.textKw = ""; S.intent = {};
        S.subject = {};
        for (var j = 0; j < ALL_TYPES.length; j++) S.types[ALL_TYPES[j]] = true;
        S.scoreMin = S.scoreMax = S.rankMin = S.rankMax = null;
        S.myRank = null; S.onlyDirect = false; S.onlyFav = false;
        S.sort = "rankAsc"; S.page = 0;
        ["schoolKw", "textKw", "scoreMin", "scoreMax", "rankMin", "rankMax", "myRank"].forEach(function (id) { $(id).value = ""; });
        $("intentOnlyDirect").checked = false;
        $("onlyFav").checked = false;
        renderIntentChips();
        renderSubj();
        updateSubjHint();
        renderTypeButtons();
        applyAndRender();
      });

      // 一分一段
      $("fenBtn1").addEventListener("click", fenScoreToRank);
      $("fenBtn2").addEventListener("click", fenRankToScore);
      // "填入冲稳保位次": 将换算出的位次填入 myRank
      $("fenOut1").addEventListener("click", function (e) {
        var b = e.target && e.target.closest ? e.target.closest("#fillRank") : null;
        if (!b) return;
        var m = $("fenOut1").innerHTML.match(/位次 <b>(\d+)<\/b>/);
        if (!m) return;
        $("myRank").value = m[1];
        S.myRank = cleanNum(m[1], 1000000);
        $("fenOut1").innerHTML = "已填入：我的位次 = <b>" + m[1] + "</b>，见下方「③ 我的位次」冲稳保";
        S.page = 0;
        applyAndRender();
      });

      applyAndRender();
    }

    function renderSubj() {
      var boxes = $("subjBox").querySelectorAll("[data-sj]");
      for (var i = 0; i < boxes.length; i++) {
        var v = boxes[i].getAttribute("data-sj");
        boxes[i].classList.toggle("on", !!S.subject[v]);
      }
    }
    function updateSubjHint() {
      var el = $("subjHint");
      var keys = Object.keys(S.subject);
      if (!keys.length) {
        el.innerHTML = "未填写选科：显示全部志愿类。选择您的选科组合后，可查看可报考范围。选科要求为 2026 年口径，2027 年以省考试院公布为准。";
      } else if (keys.length < 3) {
        el.innerHTML = "您已选 <b>" + esc(keys.join("、")) + "</b> 共 " + keys.length
          + " 科。未选科目可模糊匹配：红色标记的志愿类需补选相应科目，补全选科后结果更准确。";
      } else {
        el.innerHTML = "您的选科：" + esc(keys.join("、")) + "。选满 3 科按精确匹配，仅显示选科要求完全满足的志愿类。";
      }
    }
    function renderTypeButtons() {
      var boxes = $("typeBox").querySelectorAll("[data-t]");
      for (var i = 0; i < boxes.length; i++) {
        var v = boxes[i].getAttribute("data-t");
        if (v === "__all__") { boxes[i].classList.toggle("on", Object.keys(S.types).length === ALL_TYPES.length); continue; }
        if (v === "__normal__") { boxes[i].classList.toggle("on", Object.keys(S.types).length === 1 && S.types["普通"]); continue; }
        boxes[i].classList.toggle("on", !!S.types[v]);
      }
    }

    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", init);
    } else {
      init();
    }
  }

  /* ---------------- Node 测试导出 ---------------- */
  if (typeof module !== "undefined" && module.exports) {
    module.exports = {
      TD: TD, RK_META: META, INTENT: INTENT,
      containedKeys: containedKeys, keyName: keyName, rankOf: rankOf, majorStatus: majorStatus, ruankeUrl: ruankeUrl,
      sybKeys: sybKeys,
      splitNote: splitNote, noteBadges: noteBadges,
      rowMatchesIntent: rowMatchesIntent, matchedNamesInRow: matchedNamesInRow,
      bandOf: bandOf, scoreToRank: scoreToRank, rankToScore: rankToScore,
      filteredIndices: filteredIndices, S: S, subjectState: subjectState, cleanNum: cleanNum,
      rowMajors: rowMajors,
      SUBJ_ALL: SUBJ_ALL, ALL_TYPES: ALL_TYPES
    };
  }
})();
