/* ==========================================================================
   河小智 · 模拟测试版应用主控
   职责：登录/注册/找回、顶栏与路由、事件委托、弹窗工具、本地资料上传。
   本文件不包含任何 API Key，也不会发起网络请求。
   ========================================================================== */
(function () {
  "use strict";

  const D = window.HXZ_DATA;
  const S = window.HXZ_STORE;
  const U = window.HXZ_UI;
  const P = window.HXZ_PAGES;
  const esc = U.esc;
  const icon = U.icon;

  const PAGES = {
    home: P.home,
    qa: P.qa,
    services: P.services,
    activities: P.activities,
    center: P.center,
    growth: P.growth
  };

  const NAV = [
    { page: "home", label: "首页", icon: "home" },
    { page: "qa", label: "智能问答", icon: "sparkles" },
    { page: "services", label: "办事流程", icon: "route" },
    { page: "activities", label: "校园活动", icon: "compass" },
    { page: "center", label: "个人中心", icon: "layout-grid" },
    { page: "growth", label: "成长档案", icon: "trending-up" }
  ];

  const PAGE_TITLES = {
    home: "首页", qa: "智能问答", services: "办事流程",
    activities: "校园活动", center: "个人事务中心", growth: "成长档案"
  };

  const appRoot = document.getElementById("app-root");
  const authRoot = document.getElementById("auth-root");
  const topbar = document.getElementById("topbar");
  const view = document.getElementById("view");
  const footer = document.getElementById("footer");
  const modalRoot = document.getElementById("modal-root");

  let current = { page: "home" };
  let authMode = "login";
  let recoverStep = 1;
  let recoverIdentifier = "";
  let recoverQuestion = "";
  let loginPrefill = "";

  /* ------------------------------------------------------------------ */
  /* 路由                                                               */
  /* ------------------------------------------------------------------ */
  function routeFromQuery(qs) {
    let page = qs.get("page") || "home";
    if (!Object.prototype.hasOwnProperty.call(PAGES, page)) page = "home";
    const route = { page: page };
    qs.forEach(function (value, key) {
      if (key !== "page" && value !== "") route[key] = value;
    });
    return route;
  }

  function parseRouteHash(hash) {
    if (!hash || hash.indexOf("#page=") !== 0) return null;
    return routeFromQuery(new URLSearchParams(hash.slice(1)));
  }

  function initialRoute() {
    const fromHash = parseRouteHash(location.hash);
    if (fromHash) return fromHash;
    const params = new URLSearchParams(location.search);
    if (params.get("page")) return routeFromQuery(params);
    return { page: "home" };
  }

  function navigate(params) {
    const source = params || {};
    const qs = new URLSearchParams();
    qs.set("page", source.page || "home");
    Object.keys(source).forEach(function (key) {
      if (key === "page") return;
      const value = source[key];
      if (value !== undefined && value !== null && String(value) !== "") qs.set(key, String(value));
    });
    const target = "#" + qs.toString();
    if (location.hash === target) {
      current = parseRouteHash(target) || { page: "home" };
      prepareAutoAsk();
      render();
      return;
    }
    location.hash = qs.toString();
  }

  function prepareAutoAsk() {
    if (!current || current.page !== "qa" || !current.q) return;
    const question = current.q;
    current.q = "";
    if (S.currentUser()) S.askQuestion(question);
    if (location.hash.indexOf("#page=") === 0) {
      try { history.replaceState(null, "", "#page=qa"); } catch (e) { /* ignore */ }
    }
  }

  function handleHash() {
    const route = parseRouteHash(location.hash);
    if (!route) return; // 页面内锚点（如 #service-plan）不触发页面切换
    current = route;
    if (!S.currentUser()) {
      renderAuth();
      return;
    }
    prepareAutoAsk();
    render();
  }

  /* ------------------------------------------------------------------ */
  /* 渲染                                                               */
  /* ------------------------------------------------------------------ */
  function render(options) {
    const user = S.currentUser();
    if (!user) {
      renderAuth();
      return;
    }
    const scrollY = window.scrollY;
    U.closeModal();
    authRoot.hidden = true;
    authRoot.innerHTML = "";
    appRoot.hidden = false;
    topbar.innerHTML = topbarHTML(user);
    const page = PAGES[current.page] || PAGES.home;
    try {
      view.innerHTML = page(current);
    } catch (err) {
      console.error(err);
      view.innerHTML = U.emptyState(
        "页面加载遇到一点问题",
        "请刷新页面重试。你的本地数据仍保存在浏览器中。",
        '<button type="button" class="btn btn-primary btn-sm" data-action="nav-home">返回首页</button>',
        "alert-circle",
        "rose"
      );
    }
    footer.innerHTML = footerHTML();
    document.title = (PAGE_TITLES[current.page] || "首页") + " · 河小智模拟测试版";
    if (options && options.keepScroll) window.scrollTo(0, scrollY);
    else window.scrollTo(0, 0);
    afterRender(current);
  }

  function rerender() {
    render({ keepScroll: true });
  }

  function afterRender(route) {
    if (route.page === "qa") {
      window.setTimeout(function () {
        const body = document.getElementById("chat-body");
        if (body) body.scrollTop = body.scrollHeight;
        if (window.innerWidth > 760) {
          const input = document.getElementById("qa-input");
          if (input) input.focus({ preventScroll: true });
        }
      }, 40);
    }
    if (route.focus === "repair") {
      window.setTimeout(function () {
        const panel = document.getElementById("repair-panel");
        if (panel) panel.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 80);
      delete route.focus;
    }
  }

  function topbarHTML(user) {
    const nav = NAV.map(function (item) {
      const active = current.page === item.page;
      return '<a class="nav-link' + (active ? " active" : "") + '" href="#page=' + item.page + '">' +
        icon(item.icon) + esc(item.label) + "</a>";
    }).join("");
    return '<div class="topbar-inner">' +
      '<a class="brand" href="#page=home" aria-label="河小智首页">' +
        '<img src="assets/logo.svg" alt="">' +
        '<div><div class="brand-name">河小智</div><div class="brand-sub">HENU CAMPUS AI</div></div>' +
      "</a>" +
      '<nav class="nav" aria-label="主导航">' + nav + "</nav>" +
      '<div class="top-actions">' +
        '<span class="local-pill"><span class="dot"></span>本地模拟 · 无需 API</span>' +
        '<button type="button" class="icon-btn" data-action="tool" data-tool="help" title="使用说明" aria-label="使用说明">' + icon("help-circle") + "</button>" +
        '<a class="user-chip" href="#page=center" title="个人中心">' +
          '<span class="avatar">' + esc(U.initials(user.username)) + "</span>" +
          '<span class="user-chip-text"><strong>' + esc(user.username) + "</strong><span>" + esc(user.account_no) + "</span></span>" +
        "</a>" +
        '<button type="button" class="icon-btn" data-action="logout" title="退出登录" aria-label="退出登录">' + icon("log-out") + "</button>" +
      "</div></div>";
  }

  function footerHTML() {
    return '<div class="footer-inner">' +
      '<div class="footer-brand"><img src="assets/logo.svg" alt="">' +
        "<div><strong>河小智 · 模拟测试版</strong><p>河南大学 AI 智慧校园体验原型</p></div></div>" +
      '<p class="footer-note">本页面为纯前端模拟演示，不需要登录服务器、不调用任何大模型 API，也不会上传你的数据。账号、待办、报名与聊天记录只保存在当前浏览器的 localStorage 中，清空浏览器数据后将无法恢复。</p>' +
      '<div class="footer-links">' +
        '<button type="button" data-action="tool" data-tool="help">使用说明</button>' +
        '<button type="button" data-action="tool" data-tool="about">关于模拟版</button>' +
        '<button type="button" data-action="reset-data">重置本地数据</button>' +
      "</div></div>";
  }

  /* ------------------------------------------------------------------ */
  /* 登录 / 注册 / 找回                                                 */
  /* ------------------------------------------------------------------ */
  function renderAuth() {
    U.closeModal();
    appRoot.hidden = true;
    authRoot.hidden = false;
    authRoot.innerHTML = authHTML();
    document.title = "登录 · 河小智模拟测试版";
  }

  function authHTML() {
    const head = {
      login: ["欢迎回来", "登录后，待办、活动报名与问答记录会保存在本机。"],
      register: ["创建本地账号", "账号只保存在当前浏览器，不会发送到任何服务器。"],
      recover: ["找回密码", "通过注册时设置的密保问题，重新设置登录密码。"]
    }[authMode] || ["欢迎回来", ""];

    const tabs = [
      ["login", "登录"],
      ["register", "注册"],
      ["recover", "找回密码"]
    ].map(function (t) {
      return '<button type="button" class="auth-tab' + (authMode === t[0] ? " active" : "") +
        '" data-action="auth-tab" data-mode="' + t[0] + '">' + t[1] + "</button>";
    }).join("");

    let form = "";
    if (authMode === "register") form = registerFormHTML();
    else if (authMode === "recover") form = recoverFormHTML();
    else form = loginFormHTML();

    const features = D.QA_CAPABILITIES.map(function (f) {
      return '<div class="auth-feature">' + icon(f.icon) + "<span>" + esc(f.title) + "</span></div>";
    }).join("");

    return '<section class="auth-story">' +
        '<div class="auth-brand"><img src="assets/logo.svg" alt="河小智">' +
          "<div><strong>河小智</strong><span>HENU CAMPUS AI · 模拟测试版</span></div></div>" +
        '<div class="auth-copy">' +
          '<span class="pill">' + icon("shield") + "本地模拟 · 不需要 API Key</span>" +
          "<h1>校园大小事，<br>问<em>河小智</em>就够了。</h1>" +
          "<p>政策问答、办事流程、校园活动、个人事务与成长档案。一个入口，全部在浏览器里完成。</p>" +
          '<div class="auth-features">' + features + "</div>" +
        "</div>" +
        '<div class="auth-foot"><span>纯前端演示</span><span>数据仅存本机</span><span>0 网络请求</span><span>0 API 费用</span></div>' +
        '<img class="auth-mascot" src="assets/mascot.svg" alt="">' +
      "</section>" +
      '<section class="auth-panel"><div class="auth-card">' +
        '<div class="auth-card-head"><h2>' + esc(head[0]) + "</h2><p>" + esc(head[1]) + "</p></div>" +
        '<div class="auth-tabs">' + tabs + "</div>" +
        '<div id="auth-form-wrap">' + form + "</div>" +
        '<div class="auth-local">' + icon("shield") +
          "<span>本机已有 " + S.accountCount() + " 个账号。所有资料保存在浏览器 localStorage；清除站点数据会一并删除，无法找回。</span></div>" +
      "</div></section>";
  }

  function loginFormHTML() {
    return '<form class="auth-form" data-form="login" autocomplete="on">' +
        '<div class="field"><label for="login-id">账号号 / 用户名</label>' +
          '<input class="input" id="login-id" name="identifier" type="text" value="' + esc(loginPrefill) + '" placeholder="例如 HXZ0001" autocomplete="username" required></div>' +
        '<div class="field"><label for="login-pwd">密码</label>' +
          '<input class="input" id="login-pwd" name="password" type="password" placeholder="输入登录密码" autocomplete="current-password" required></div>' +
        '<button class="btn btn-primary btn-block btn-lg" type="submit">' + icon("arrow-right") + "登录并进入</button>" +
      "</form>" +
      '<div class="auth-demo"><strong>演示账号</strong> HXZ0001 / 演示同学<br>' +
        '密码 <code>demo1234</code> · 密保答案 <code>1024</code>' +
        '<button type="button" class="btn btn-soft btn-sm btn-block mt-10" data-action="demo-login">' + icon("zap") + "一键体验演示账号</button></div>" +
      '<div class="auth-alt">还没有账号？<button type="button" data-action="auth-tab" data-mode="register">立即注册一个本地账号</button></div>';
  }

  function registerFormHTML() {
    return '<form class="auth-form" data-form="register" autocomplete="off">' +
        '<div class="field"><label>用户名</label><input class="input" name="username" type="text" maxlength="16" placeholder="2–16 位中文、字母、数字或下划线" required></div>' +
        '<div class="field"><label>密码</label><input class="input" name="password" type="password" minlength="8" maxlength="32" placeholder="8–32 位，需包含字母和数字" required>' +
          '<span class="hint">示例：campus2026</span></div>' +
        '<div class="field"><label>确认密码</label><input class="input" name="password2" type="password" minlength="8" maxlength="32" placeholder="再输入一次密码" required></div>' +
        '<div class="field"><label>密保问题</label><input class="input" name="question" type="text" maxlength="60" placeholder="例如：你的学号后四位是？" required></div>' +
        '<div class="field"><label>密保答案</label><input class="input" name="answer" type="text" maxlength="50" placeholder="找回密码时使用，不区分大小写" required></div>' +
        '<button class="btn btn-primary btn-block btn-lg" type="submit">' + icon("user") + "创建账号并进入</button>" +
      "</form>" +
      '<div class="auth-alt">已有账号？<button type="button" data-action="auth-tab" data-mode="login">返回登录</button></div>';
  }

  function recoverFormHTML() {
    if (recoverStep === 2) {
      return '<form class="auth-form" data-form="recover-reset" autocomplete="off">' +
          '<div class="form-notice blue">' + icon("help-circle") +
            "<span>账号 <strong>" + esc(recoverIdentifier) + "</strong> 的密保问题：<br>" + esc(recoverQuestion) + "</span></div>" +
          '<div class="field"><label>密保答案</label><input class="input" name="answer" type="text" maxlength="50" placeholder="不区分大小写" required></div>' +
          '<div class="field"><label>新密码</label><input class="input" name="password" type="password" minlength="8" maxlength="32" placeholder="8–32 位，需包含字母和数字" required></div>' +
          '<div class="field"><label>确认新密码</label><input class="input" name="password2" type="password" minlength="8" maxlength="32" placeholder="再输入一次新密码" required></div>' +
          '<button class="btn btn-primary btn-block btn-lg" type="submit">' + icon("refresh") + "重置密码</button>" +
        "</form>" +
        '<div class="auth-alt"><button type="button" data-action="recover-back">换一个账号 / 返回登录</button></div>';
    }
    return '<form class="auth-form" data-form="recover-find" autocomplete="off">' +
        '<div class="field"><label>账号号 / 用户名</label><input class="input" name="identifier" type="text" placeholder="注册时使用的账号或用户名" required></div>' +
        '<button class="btn btn-primary btn-block btn-lg" type="submit">' + icon("help-circle") + "下一步：回答密保问题</button>" +
      "</form>" +
      '<div class="auth-alt">想起来了？<button type="button" data-action="auth-tab" data-mode="login">返回登录</button></div>';
  }

  function enterApp() {
    U.closeModal();
    P.resetTransient();
    current = { page: "home" };
    navigate({ page: "home" });
  }

  /* ------------------------------------------------------------------ */
  /* 弹窗工具                                                           */
  /* ------------------------------------------------------------------ */
  function modalFooter() {
    return '<div class="modal-foot"><button type="button" class="btn btn-soft" data-action="modal-close">关闭</button></div>';
  }

  function openTool(tool) {
    let html = "";
    let size = "wide";
    if (tool === "search") {
      html = U.modalHead("search", "blue", "知识库检索", "输入关键词，先在本地知识库里找一找") +
        '<form class="tool-search" data-form="tool-search" onsubmit="return false">' +
          '<div class="flex" style="gap:8px"><div class="search-box">' + icon("search") +
            '<input class="input" name="q" type="search" placeholder="试试：校园卡、奖学金、校车、医保" autofocus></div>' +
            '<button class="btn btn-primary btn-sm" type="submit">搜索</button></div>' +
        "</form>" +
        '<div id="tool-results"><div class="modal-note">输入关键词后回车，结果只来自本地演示知识库。</div></div>';
    } else if (tool === "faq") {
      html = U.modalHead("help-circle", "gold", "高频问题", "点击任意问题，河小智会直接在问答页作答") +
        '<div class="faq-list">' + D.FAQ_RECOMMENDED.map(function (item) {
          return '<button type="button" class="faq-item" data-action="ask" data-q="' + esc(item.question) + '">' +
            '<span class="q-mark">问</span><span class="grow"><strong>' + esc(item.question) + "</strong>" +
            "<span>" + esc(item.tag) + (item.hot ? " · 热门" : "") + "</span></span></button>";
        }).join("") + "</div>";
    } else if (tool === "notices") {
      html = U.modalHead("bell", "violet", "通知公告", "演示通知 · 点击可直接向河小智追问") +
        '<div class="faq-list">' + D.NOTICES.map(function (n) {
          return '<button type="button" class="faq-item" data-action="ask" data-q="' + esc(n.question) + '">' +
            '<span class="q-mark">通</span><span class="grow"><strong>' + esc(n.title) + "</strong>" +
            "<span>" + esc(n.date) + " · " + esc(n.department) + " · " + esc(n.category) + "</span>" +
            "<span>" + esc(n.summary) + "</span></span></button>";
        }).join("") + "</div>";
    } else if (tool === "aid") {
      html = U.modalHead("award", "gold", "奖助政策速览", "金额、对象与时间以学校当年正式通知为准") +
        '<div class="tool-results">' + D.AID_POLICIES.map(function (p) {
          return '<div class="result-item">' + U.iconTile("award", p.tone) +
            '<div class="grow"><strong>' + esc(p.name) + " · " + esc(p.amount) + "</strong>" +
            "<p>对象：" + esc(p.target) + " · 时间：" + esc(p.deadline) + "</p>" +
            '<div class="mt-6">' + U.tag(p.tone, p.tone) + "</div></div>" +
            '<button type="button" class="btn btn-soft btn-sm" data-action="ask" data-q="' +
              esc(p.name + "怎么申请？") + '">问怎么申请</button></div>';
        }).join("") + "</div>";
    } else if (tool === "processes") {
      html = U.modalHead("route", "teal", "办事流程库", "挑一个事项，让河小智生成材料与步骤清单") +
        '<div class="tool-results">' + D.PROCESSES.map(function (p) {
          return '<div class="result-item">' + U.iconTile(p.icon || "route", p.category === "医疗健康" ? "teal" : p.category === "奖助资助" ? "gold" : "blue") +
            '<div class="grow"><strong>' + esc(p.title) + "</strong><p>" + esc(p.department) + " · " + esc(p.duration) + "</p>" +
            '<div class="mt-6">' + U.tag(p.category, "blue") + "</div></div>" +
            '<button type="button" class="btn btn-soft btn-sm" data-action="process-need" data-need="' + esc(p.title) + '">生成计划</button></div>';
        }).join("") + "</div>";
    } else if (tool === "upload") {
      const docs = S.qaDocs();
      html = U.modalHead("upload", "teal", "上传本地资料", "支持文本文件，最多 5 份，只在当前浏览器中生效") +
        '<label class="upload-zone">' + icon("upload") +
          "<strong>点击选择文本文件</strong><span>.txt / .md / .csv / .json / .log / .html · 单份建议小于 400KB</span>" +
          '<input id="upload-input" type="file" accept=".txt,.md,.markdown,.csv,.json,.log,.html,.htm">' +
        "</label>" +
        '<div class="doc-list">' + (docs.length ? docs.map(function (d) {
          return '<div class="doc-item"><span class="doc-icon">' + icon("file-text") + "</span>" +
            "<div class=\"grow\"><strong>" + esc(d.name) + "</strong><span>" +
            Math.max(1, Math.round(Number(d.size || 0) / 1000)) + "k 字符 · 添加于 " + esc(U.timeHM(d.added_at)) + "</span></div>" +
            '<button type="button" class="btn-icon" data-action="doc-remove" data-id="' + esc(d.id) + '" aria-label="移除资料">' + icon("trash") + "</button></div>";
        }).join("") : '<div class="modal-note">还没有上传资料。上传后，提问时如果匹配到资料内容，河小智会在回答中注明出处。</div>') + "</div>" +
        '<div class="modal-note" style="margin-top:12px">' + icon("shield") + " 文件通过浏览器 FileReader 在本地读取，不会发送到任何服务器。</div>";
    } else if (tool === "about") {
      html = U.modalHead("info", "violet", "关于模拟测试版", "河小智 · 不需要 API 的本地演示") +
        '<div class="modal-body">' +
          '<div class="modal-note">这是「河小智」正式版之外额外制作的模拟版本，用于在没有网络、没有 API Key 的环境中体验产品流程。它不连接后端，也不调用任何大模型接口。</div>' +
          '<div class="faq-list" style="margin-top:12px">' +
            '<div class="result-item">' + U.iconTile("database", "blue") + '<div class="grow"><strong>数据存在哪里？</strong><p>账号、待办、报名、活动任务、报修、办事计划、问答记录都保存在浏览器 localStorage。清理浏览器站点数据会全部丢失。</p></div></div>' +
            '<div class="result-item">' + U.iconTile("cpu", "teal") + '<div class="grow"><strong>回答是怎么生成的？</strong><p>本地知识库关键词命中 + 2-gram 相似度排序，答案标注整理来源，不经过任何模型。</p></div></div>' +
            '<div class="result-item">' + U.iconTile("shield", "gold") + '<div class="grow"><strong>和正式版的区别？</strong><p>正式版可接入大模型与学校系统；模拟版只覆盖主要交互与演示数据，不能作为学校官方信息来源。</p></div></div>' +
          "</div>" +
        "</div>" + modalFooter();
    } else {
      html = U.modalHead("help-circle", "blue", "使用说明", "三分钟熟悉这个本地模拟版") +
        '<div class="modal-body">' +
          '<div class="modal-note">演示账号：<strong>HXZ0001</strong> / 密码 <strong>demo1234</strong>；也可以注册自己的本地账号，或使用页脚的重置数据重新开始。</div>' +
          '<div class="faq-list" style="margin-top:12px">' +
            '<div class="result-item">' + U.iconTile("sparkles", "blue") + '<div class="grow"><strong>智能问答</strong><p>在输入框提问，或点击高频问题。可在右侧工作台检索知识库、查看通知、上传资料。</p></div></div>' +
            '<div class="result-item">' + U.iconTile("route", "teal") + '<div class="grow"><strong>办事流程</strong><p>输入「校园卡丢了」这类需求，系统识别流程并生成可勾选的材料/步骤清单，可一键加入个人待办。</p></div></div>' +
            '<div class="result-item">' + U.iconTile("compass", "gold") + '<div class="grow"><strong>校园活动</strong><p>官方活动可报名/取消；也可以创建自己的活动，并在「活动任务」看板拆解任务。</p></div></div>' +
            '<div class="result-item">' + U.iconTile("clipboard", "violet") + '<div class="grow"><strong>个人中心</strong><p>管理待办、查看课表与一卡通、提交模拟报修；首页和成长档案会同步统计。</p></div></div>' +
            '<div class="result-item">' + U.iconTile("refresh", "rose") + '<div class="grow"><strong>重置数据</strong><p>页脚「重置本地数据」会删除本机所有模拟账号和记录，包括你注册的账号，请谨慎操作。</p></div></div>' +
          "</div>" +
        "</div>" + modalFooter();
    }
    U.openModal(html, size);
  }

  function renderToolResults(query) {
    const root = document.getElementById("tool-results");
    if (!root) return;
    const q = String(query || "").trim();
    if (!q) {
      root.innerHTML = '<div class="modal-note">请输入关键词后再搜索。</div>';
      return;
    }
    const results = S.searchKB(q).slice(0, 10);
    if (!results.length) {
      root.innerHTML = '<div class="modal-note">没有找到「' + esc(q) + '」。换一个说法，或直接回到问答页提问。</div>';
      return;
    }
    root.innerHTML = '<div class="small muted mb-10">在本地知识库中找到 ' + results.length + " 条相关内容</div>" +
      results.map(function (entry) {
        return '<div class="result-item">' +
          U.iconTile(entry.tag === "流程" ? "route" : entry.tag === "政策" ? "shield" : "book-open", entry.tone) +
          '<div class="grow"><strong>' + esc(entry.title) + "</strong><p>" + esc(entry.intro || "") + "</p>" +
            '<div class="mt-6">' + U.tag(entry.tag || "知识", "blue") + "</div></div>" +
          '<button type="button" class="btn btn-soft btn-sm" data-action="ask" data-q="' +
            esc(entry.question || entry.title) + '">问这个</button></div>';
      }).join("");
  }

  /* ------------------------------------------------------------------ */
  /* 任务编辑弹窗                                                       */
  /* ------------------------------------------------------------------ */
  function splitDue(value) {
    const m = String(value || "").match(/^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})/);
    return { date: m ? m[1] : U.todayInput(0), time: m ? m[2] : "18:00" };
  }

  function composeDue(date, time) {
    if (!date) return "";
    return date + "T" + (time || "23:59");
  }

  function selectOptions(options, selected) {
    return options.map(function (option) {
      const value = typeof option === "string" ? option : option.value;
      const label = typeof option === "string" ? option : option.label;
      return '<option value="' + esc(value) + '"' + (String(value) === String(selected) ? " selected" : "") + ">" + esc(label) + "</option>";
    }).join("");
  }

  function openTaskModal(type, id) {
    const isCenter = type === "center";
    let item = null;
    if (id) {
      item = (isCenter ? S.todoStats().items : S.activityTasks()).find(function (x) { return x.id === id; });
      if (!item) {
        U.toast("没有找到这条任务，可能已被删除。", "error");
        return;
      }
    }
    const due = splitDue(item ? (isCenter ? item.due : item.deadline) : "");
    const category = item ? item.category : (isCenter ? "学习" : "科技");
    const priority = item ? item.priority : (isCenter ? "medium" : "中");
    const progress = item && !isCenter ? Number(item.progress) || 0 : 0;
    const title = item ? item.title : "";
    const place = isCenter && item ? item.place : "";
    const note = item ? item.note : "";

    const priorityField = isCenter
      ? '<div class="field"><label>优先级</label><select class="select" name="priority">' +
          selectOptions([{ value: "high", label: "高优先级" }, { value: "medium", label: "中优先级" }, { value: "low", label: "低优先级" }], priority) + "</select></div>"
      : '<div class="field"><label>优先级</label><select class="select" name="priority">' +
          selectOptions(D.ACTIVITY_TASK_PRIORITIES, priority) + "</select></div>";

    U.openModal(
      U.modalHead(isCenter ? "edit" : "clipboard", isCenter ? "violet" : "teal",
        id ? "编辑待办" : "新增活动任务",
        isCenter ? "修改后会立即保存在本机" : "活动任务独立于个人待办，可在活动页查看") +
      '<form data-form="task-edit" data-type="' + type + '" autocomplete="off">' +
        '<input type="hidden" name="id" value="' + esc(id || "") + '">' +
        '<div class="form-grid">' +
          '<div class="field full"><label>任务标题 <span class="required">*</span></label>' +
            '<input class="input" name="title" type="text" maxlength="50" value="' + esc(title) + '" required></div>' +
          '<div class="field"><label>分类</label><select class="select" name="category">' +
            selectOptions(isCenter ? D.TASK_CATEGORIES : D.ACTIVITY_TASK_CATEGORIES, category) + "</select></div>" +
          priorityField +
          '<div class="field"><label>截止日期</label><input class="input" name="date" type="date" value="' + esc(due.date) + '"></div>' +
          '<div class="field"><label>截止时间</label><input class="input" name="time" type="time" value="' + esc(due.time) + '"></div>' +
          (isCenter
            ? '<div class="field full"><label>地点 / 备注</label><input class="input" name="place" type="text" maxlength="40" value="' + esc(place) + '" placeholder="可选"></div>'
            : '<div class="field full"><label>完成进度（0–100）</label><input class="input" name="progress" type="number" min="0" max="100" value="' + progress + '"></div>') +
          '<div class="field full"><label>补充说明</label><textarea class="textarea" name="note" maxlength="200" placeholder="可选">' + esc(note) + "</textarea></div>" +
        "</div>" +
        '<div class="modal-foot"><button type="button" class="btn btn-soft" data-action="modal-close">取消</button>' +
          '<button type="submit" class="btn btn-primary">' + icon("check") + "保存" + "</button></div>" +
      "</form>",
      "wide"
    );
  }

  /* ------------------------------------------------------------------ */
  /* 问答跳转                                                           */
  /* ------------------------------------------------------------------ */
  function ask(question) {
    const q = String(question || "").trim();
    if (!q) {
      U.toast("请先输入一个问题。", "warn");
      return;
    }
    if (!S.currentUser()) {
      renderAuth();
      return;
    }
    U.closeModal();
    S.askQuestion(q);
    current = { page: "qa" };
    navigate({ page: "qa" });
  }

  /* ------------------------------------------------------------------ */
  /* 事件：点击                                                         */
  /* ------------------------------------------------------------------ */
  function onClick(event) {
    const anchor = event.target.closest('a[href^="#"]');
    if (anchor) {
      const href = anchor.getAttribute("href");
      if (href && href !== "#" && href.indexOf("#page=") !== 0) {
        event.preventDefault();
        const target = document.getElementById(href.slice(1));
        if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
        return;
      }
    }

    const el = event.target.closest("[data-action]");
    if (!el) return;
    const action = el.getAttribute("data-action");
    const id = el.getAttribute("data-id") || "";
    event.preventDefault();

    switch (action) {
      /* 认证 */
      case "auth-tab":
        authMode = el.getAttribute("data-mode") || "login";
        recoverStep = 1;
        recoverIdentifier = "";
        recoverQuestion = "";
        renderAuth();
        break;
      case "recover-back":
        authMode = "login";
        recoverStep = 1;
        recoverIdentifier = "";
        recoverQuestion = "";
        renderAuth();
        break;
      case "demo-login": {
        const result = S.login("HXZ0001", "demo1234");
        if (!result.ok) {
          U.toast(result.message, "error");
          break;
        }
        loginPrefill = "";
        enterApp();
        U.toast("已进入演示账号，本地数据只保存在这台设备。", "success", "欢迎回来");
        break;
      }
      case "logout":
        U.confirmDialog({
          title: "退出登录",
          message: "退出后，本机数据仍会保留。下次可用账号和密码重新登录。",
          confirmLabel: "退出登录",
          danger: true,
          onConfirm: function () {
            S.endSession();
            P.resetTransient();
            authMode = "login";
            recoverStep = 1;
            loginPrefill = "";
            renderAuth();
            U.toast("已退出登录。", "success");
          }
        });
        break;
      case "reset-data":
        U.confirmDialog({
          title: "重置本地模拟数据",
          message: "这会删除本机所有账号、待办、报名、聊天记录和上传资料，且无法恢复。确定要继续吗？",
          confirmLabel: "全部删除并重置",
          danger: true,
          onConfirm: function () {
            S.resetAll();
            P.resetTransient();
            authMode = "login";
            recoverStep = 1;
            recoverIdentifier = "";
            recoverQuestion = "";
            loginPrefill = "";
            renderAuth();
            U.toast("本地模拟数据已重置。", "success");
          }
        });
        break;

      /* 工具 */
      case "tool":
        openTool(el.getAttribute("data-tool") || "help");
        break;
      case "modal-close":
        U.closeModal();
        break;
      case "confirm-modal":
        U.resolveConfirm();
        break;
      case "doc-remove":
        S.removeQaDoc(id);
        U.toast("资料已从本机移除。", "success");
        openTool("upload");
        break;
      case "nav-home":
        navigate({ page: "home" });
        break;

      /* 问答 */
      case "ask":
        ask(el.getAttribute("data-q") || "");
        break;
      case "qa-new":
        S.newQaSession();
        U.toast("已开始新的问答会话。", "success");
        rerender();
        break;
      case "qa-clear":
        U.confirmDialog({
          title: "清空问答记录",
          message: "确定清空当前账号在本机的全部问答记录吗？",
          confirmLabel: "清空记录",
          danger: true,
          onConfirm: function () {
            S.clearQaHistory();
            U.toast("问答记录已清空。", "success");
            rerender();
          }
        });
        break;

      /* 办事流程 */
      case "process-need":
        U.closeModal();
        navigate({ page: "services", need: el.getAttribute("data-need") || "" });
        break;
      case "process-add-todo": {
        const process = D.PROCESSES.find(function (p) { return p.id === id; });
        if (!process) break;
        const added = S.addTodo({
          title: "办理：" + process.title,
          category: "工作",
          priority: "medium",
          due: composeDue(U.todayInput(1), "23:59"),
          place: process.location,
          note: process.department + " · 来自办事流程"
        });
        if (added) {
          U.toast("已加入个人待办，明天 23:59 截止。", "success");
          rerender();
        }
        break;
      }
      case "process-toggle":
        P.toggleProcess(id);
        rerender();
        break;
      case "plan-check":
        S.toggleServiceTodo(el.getAttribute("data-pid") || "", el.getAttribute("data-tid") || "");
        rerender();
        break;
      case "plan-reset":
        S.resetServicePlan(el.getAttribute("data-pid") || "");
        U.toast("办理计划的勾选已重置。", "success");
        rerender();
        break;
      case "plan-to-todos": {
        const process = D.PROCESSES.find(function (p) { return p.id === el.getAttribute("data-pid"); });
        if (!process) break;
        const plan = S.buildPlan(process);
        const state = S.getServicePlan(process.id, process.title);
        let count = 0;
        plan.todos.forEach(function (todo) {
          if (state && !state.checked[todo.id]) {
            const added = S.addTodo({
              title: process.title + " · " + todo.label,
              category: "工作",
              priority: "medium",
              due: composeDue(U.todayInput(1), "23:59"),
              place: process.location,
              note: "来自办事计划：" + todo.kind
            });
            if (added) count += 1;
          }
        });
        if (count) U.toast("已加入 " + count + " 个步骤到个人待办。", "success");
        else U.toast("所有步骤都已勾选，没有需要加入的待办。", "warn");
        rerender();
        break;
      }

      /* 待办 */
      case "todo-toggle": {
        const done = S.toggleTodo(id);
        if (typeof done === "boolean") U.toast(done ? "已标记完成。" : "已恢复为未完成。", "success");
        rerender();
        break;
      }
      case "todo-edit":
        openTaskModal("center", id);
        break;
      case "todo-delete":
        U.confirmDialog({
          title: "删除待办",
          message: "确定删除这条待办吗？删除后无法恢复。",
          confirmLabel: "删除",
          danger: true,
          onConfirm: function () {
            if (S.deleteTodo(id)) {
              U.toast("待办已删除。", "success");
              rerender();
            }
          }
        });
        break;
      case "center-tab":
        P.setCenterTab(el.getAttribute("data-tab") || "today");
        rerender();
        break;

      /* 活动任务 */
      case "atask-add":
        openTaskModal("activity", null);
        break;
      case "atask-edit":
        openTaskModal("activity", id);
        break;
      case "atask-toggle": {
        const done = S.toggleActivityTask(id);
        if (done !== null) U.toast(done ? "活动任务已完成。" : "已恢复为进行中。", "success");
        rerender();
        break;
      }
      case "atask-delete":
        U.confirmDialog({
          title: "删除活动任务",
          message: "确定删除这条活动任务吗？",
          confirmLabel: "删除",
          danger: true,
          onConfirm: function () {
            if (S.deleteActivityTask(id)) {
              U.toast("活动任务已删除。", "success");
              rerender();
            }
          }
        });
        break;

      /* 活动 */
      case "join-activity":
        if (S.joinActivity(id)) {
          U.toast("报名成功（本机模拟），不会产生真实报名。", "success");
          rerender();
        } else {
          U.toast("你已经报名过这个活动了。", "warn");
        }
        break;
      case "cancel-activity":
        U.confirmDialog({
          title: "取消报名",
          message: "确定取消这个活动的报名吗？之后仍可重新报名。",
          confirmLabel: "取消报名",
          danger: true,
          onConfirm: function () {
            if (S.cancelActivity(id)) {
              U.toast("已取消报名。", "success");
              rerender();
            }
          }
        });
        break;
      case "activity-toggle":
        P.toggleActivity(id);
        rerender();
        break;
      case "created-delete":
        U.confirmDialog({
          title: "删除自建活动",
          message: "确定删除这个活动吗？仅本机数据会受影响。",
          confirmLabel: "删除活动",
          danger: true,
          onConfirm: function () {
            if (S.deleteCreatedActivity(id)) {
              U.toast("活动已删除。", "success");
              rerender();
            }
          }
        });
        break;

      /* 报修 */
      case "repair-complete":
        if (S.completeRepair(id)) {
          U.toast("报修已确认完成。", "success");
          rerender();
        }
        break;

      default:
        break;
    }
  }

  /* ------------------------------------------------------------------ */
  /* 事件：表单                                                         */
  /* ------------------------------------------------------------------ */
  function formData(form) {
    const data = {};
    new FormData(form).forEach(function (value, key) {
      data[key] = typeof value === "string" ? value : "";
    });
    return data;
  }

  function onSubmit(event) {
    const form = event.target.closest("form[data-form]");
    if (!form) return;
    event.preventDefault();
    const name = form.getAttribute("data-form");
    const data = formData(form);

    if (name === "login") {
      const result = S.login(data.identifier, data.password);
      if (!result.ok) {
        U.showFormError(form, result.message);
        return;
      }
      loginPrefill = "";
      enterApp();
      U.toast("欢迎回来，" + result.user.username + "。", "success");
      return;
    }

    if (name === "register") {
      const result = S.register(data);
      if (!result.ok) {
        U.showFormError(form, result.message);
        return;
      }
      S.startSession(result.account_no);
      loginPrefill = "";
      enterApp();
      U.toast("账号创建成功，账号号是 " + result.account_no + "。", "success", "注册完成");
      return;
    }

    if (name === "recover-find") {
      const result = S.getSecurityQuestion(data.identifier);
      if (!result.ok) {
        U.showFormError(form, result.message);
        return;
      }
      recoverIdentifier = data.identifier.trim();
      recoverQuestion = result.question;
      recoverStep = 2;
      renderAuth();
      return;
    }

    if (name === "recover-reset") {
      if (data.password !== data.password2) {
        U.showFormError(form, "两次输入的新密码不一致。");
        return;
      }
      const result = S.resetPassword(recoverIdentifier, data.answer, data.password);
      if (!result.ok) {
        U.showFormError(form, result.message);
        return;
      }
      loginPrefill = recoverIdentifier;
      authMode = "login";
      recoverStep = 1;
      recoverIdentifier = "";
      recoverQuestion = "";
      U.toast("密码已重置，请使用新密码登录。", "success");
      renderAuth();
      return;
    }

    if (name === "home-ask") {
      ask(data.q);
      return;
    }

    if (name === "qa-ask") {
      const q = String(data.q || "").trim();
      if (!q) return;
      S.askQuestion(q);
      current = { page: "qa" };
      render({ keepScroll: true });
      return;
    }

    if (name === "service-need") {
      const need = String(data.need || "").trim();
      if (!need) {
        U.toast("先写一句你要办什么，例如「校园卡丢了」。", "warn");
        return;
      }
      navigate({ page: "services", need: need });
      return;
    }

    if (name === "services-search") {
      navigate({ page: "services", q: String(data.q || "").trim(), cat: data.cat || "" });
      return;
    }

    if (name === "tool-search") {
      renderToolResults(data.q);
      return;
    }

    if (name === "center-add-task") {
      const title = String(data.title || "").trim();
      if (!title) {
        U.showFormError(form, "请填写待办标题。");
        return;
      }
      const added = S.addTodo({
        title: title,
        category: data.category,
        priority: data.priority,
        due: composeDue(data.date, data.time),
        place: data.place
      });
      if (!added) {
        U.showFormError(form, "添加失败，请检查输入。");
        return;
      }
      U.toast("待办已添加。", "success");
      rerender();
      return;
    }

    if (name === "task-edit") {
      const type = form.getAttribute("data-type") || "center";
      const title = String(data.title || "").trim();
      if (!title) {
        U.showFormError(form, "任务标题不能为空。");
        return;
      }
      if (type === "center") {
        const ok = S.updateTodo(data.id, {
          title: title,
          category: data.category,
          priority: data.priority,
          due: composeDue(data.date, data.time),
          place: data.place,
          note: data.note
        });
        if (!ok) {
          U.showFormError(form, "保存失败，任务可能已不存在。");
          return;
        }
        U.closeModal();
        U.toast("待办已更新。", "success");
        rerender();
        return;
      }
      const fields = {
        title: title,
        category: data.category,
        priority: data.priority,
        deadline: composeDue(data.date, data.time),
        progress: Number(data.progress) || 0,
        note: data.note
      };
      const ok = data.id ? S.updateActivityTask(data.id, fields) : !!S.addActivityTask(fields);
      if (!ok) {
        U.showFormError(form, "保存失败，请重试。");
        return;
      }
      U.closeModal();
      U.toast(data.id ? "活动任务已更新。" : "活动任务已添加。", "success");
      rerender();
      return;
    }

    if (name === "create-activity") {
      const title = String(data.title || "").trim();
      const location = String(data.location || "").trim();
      if (!title || !location) {
        U.showFormError(form, "活动名称和地点为必填项。");
        return;
      }
      const tags = String(data.tags || "").split(/[,，、\s]+/).filter(Boolean).slice(0, 4);
      const created = S.addCreatedActivity({
        title: title,
        category: data.category,
        dateLabel: data.date ? U.dateCn(data.date) + " " + U.weekdayCn(data.date) : "日期待定",
        timeLabel: String(data.time || "").trim() || "时间待定",
        deadlineLabel: data.deadlineDate ? U.dateCn(data.deadlineDate) + " 23:59" : "活动开始前",
        location: location,
        capacity: data.capacity,
        tags: tags,
        detail: data.detail
      });
      if (!created) {
        U.showFormError(form, "活动创建失败，请检查输入。");
        return;
      }
      U.toast("活动已创建，仅保存在本机。", "success");
      navigate({ page: "activities", view: "mine", mtab: "created" });
      return;
    }

    if (name === "repair-form") {
      const repair = S.addRepair({
        title: data.title,
        location: data.location,
        slot: data.slot,
        detail: data.detail
      });
      if (!repair) {
        U.showFormError(form, "报修事项和具体位置为必填项。");
        return;
      }
      U.toast("报修单已提交，进度仅在本机模拟。", "success");
      rerender();
      return;
    }
  }

  /* ------------------------------------------------------------------ */
  /* 事件：上传 / 键盘 / 输入                                           */
  /* ------------------------------------------------------------------ */
  function onFileChange(event) {
    const input = event.target.closest("#upload-input");
    if (!input || !input.files || !input.files[0]) return;
    const file = input.files[0];
    const allowed = /\.(txt|md|markdown|csv|json|log|html|htm)$/i;
    if (!allowed.test(file.name)) {
      U.toast("仅支持 .txt / .md / .csv / .json / .log / .html 文本文件。", "error");
      input.value = "";
      return;
    }
    if (file.size > 400 * 1024) {
      U.toast("文件超过 400KB，请换一个更小的文本文件。", "error");
      input.value = "";
      return;
    }
    const reader = new FileReader();
    reader.onload = function () {
      const result = S.addQaDoc(file.name, String(reader.result || ""));
      if (!result.ok) {
        U.toast(result.message, "error");
        return;
      }
      U.toast("《" + file.name + "》已上传到本机资料库。", "success");
      openTool("upload");
    };
    reader.onerror = function () {
      U.toast("读取文件失败，请重试。", "error");
    };
    reader.readAsText(file, "UTF-8");
  }

  function onKeydown(event) {
    if (event.key === "Escape") {
      if (modalRoot && modalRoot.innerHTML.trim()) U.closeModal();
      return;
    }
    if (event.target && event.target.id === "qa-input" && event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      const form = event.target.closest("form");
      if (form) {
        if (typeof form.requestSubmit === "function") form.requestSubmit();
        else form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
      }
    }
  }

  function onInput(event) {
    if (event.target && event.target.id === "qa-input") {
      const textarea = event.target;
      textarea.style.height = "auto";
      textarea.style.height = Math.min(120, textarea.scrollHeight) + "px";
    }
  }

  /* ------------------------------------------------------------------ */
  /* 启动                                                               */
  /* ------------------------------------------------------------------ */
  function boot() {
    document.addEventListener("click", onClick);
    document.addEventListener("submit", onSubmit);
    document.addEventListener("change", onFileChange);
    document.addEventListener("keydown", onKeydown);
    document.addEventListener("input", onInput);
    window.addEventListener("hashchange", handleHash);
    if (modalRoot) {
      modalRoot.addEventListener("click", function (event) {
        if (event.target === modalRoot || event.target.classList.contains("modal-backdrop")) U.closeModal();
      });
    }

    current = initialRoute();
    if (S.currentUser()) {
      prepareAutoAsk();
      render();
    } else {
      renderAuth();
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
