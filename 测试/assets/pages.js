/* ==========================================================================
   河小智 · 模拟测试版页面渲染层
   所有数据来自 data.js + store.js 的浏览器本地状态，不访问网络。
   ========================================================================== */
(function () {
  "use strict";

  const D = window.HXZ_DATA;
  const S = window.HXZ_STORE;
  const U = window.HXZ_UI;
  const esc = U.esc;
  const icon = U.icon;

  const openActs = new Set();
  const openProcs = new Set();
  let centerTab = "today";

  /* ------------------------------------------------------------------ */
  /* 通用小工具                                                         */
  /* ------------------------------------------------------------------ */
  function greetingWord() {
    const h = new Date().getHours();
    if (h < 5) return "夜深了";
    if (h < 9) return "早上好";
    if (h < 12) return "上午好";
    if (h < 14) return "中午好";
    if (h < 18) return "下午好";
    return "晚上好";
  }

  function stampLabel(value) {
    if (!value) return "";
    const d = new Date(String(value).replace(" ", "T"));
    if (isNaN(d.getTime())) return String(value);
    return (d.getMonth() + 1) + "/" + d.getDate() + " " + U.timeHM(d);
  }

  function activityFind(id) {
    return D.ACTIVITIES.find(function (a) { return a.id === id; }) || S.createdActivities().find(function (a) { return a.id === id; }) || null;
  }

  function activityOfRegistration(id) {
    return D.ACTIVITIES.find(function (a) { return a.id === id; }) || null;
  }

  function processTone(category) {
    if (category === "医疗健康") return "teal";
    if (category === "奖助资助") return "gold";
    if (category === "图书服务") return "violet";
    if (category === "生活服务") return "rose";
    return "blue";
  }

  function selectOptions(list, selected) {
    return list.map(function (x) {
      const value = typeof x === "string" ? x : x.value;
      const label = typeof x === "string" ? x : x.label;
      return '<option value="' + esc(value) + '"' + (value === selected ? " selected" : "") + ">" + esc(label) + "</option>";
    }).join("");
  }

  function answerIcon(tag) {
    const map = {
      "流程": "route", "政策": "shield", "生活": "compass", "医疗": "heart",
      "活动": "trophy", "学习": "book-open", "资料": "file-text", "提示": "info", "问候": "sparkles"
    };
    return map[tag] || "sparkles";
  }

  /* ------------------------------------------------------------------ */
  /* 首页                                                               */
  /* ------------------------------------------------------------------ */
  function home() {
    const user = S.currentUser();
    const stats = S.todoStats();
    const regs = S.registrations();
    const name = user ? user.username : "同学";
    const todayList = stats.today.slice(0, 4);

    const featureCards = D.FEATURES.map(function (f) {
      return '<a class="feature-card" href="#page=' + esc(f.page) + '">' +
        U.iconTile(f.icon, f.tone) +
        "<h3>" + esc(f.title) + "</h3>" +
        "<p>" + esc(f.desc) + "</p>" +
        '<div class="feature-more"><span>' + esc(f.tag) + "</span>" + icon("arrow-right") + "</div></a>";
    }).join("");

    const suggestions = D.QA_SUGGESTIONS.slice(0, 3).map(function (q) {
      return '<button type="button" data-action="ask" data-q="' + esc(q) + '">' + esc(q) + "</button>";
    }).join("");

    const todoRows = todayList.length ? todayList.map(function (t) {
      return '<div class="home-todo' + (t.done ? " done" : "") + '">' +
        '<button type="button" class="checkbox' + (t.done ? " on" : "") + '" data-action="todo-toggle" data-id="' + esc(t.id) + '" aria-label="切换完成状态">' + icon("check") + "</button>" +
        "<div><strong>" + esc(t.title) + "</strong><span>" + esc(S.dueLabel(t.due, t.done)) + "</span></div></div>";
    }).join("") : '<div class="small muted" style="padding:10px 0">今天没有未完成待办，享受校园生活吧。</div>';

    const noticeRows = D.NOTICES.slice(0, 4).map(function (n) {
      return '<button type="button" class="brief-item" data-action="ask" data-q="' + esc(n.question) + '">' +
        '<span class="dot"></span><span><strong>' + esc(n.title) + "</strong>" +
        "<span>" + esc(n.date) + " · " + esc(n.department) + "</span></span></button>";
    }).join("");

    const quickServices = D.SERVICES.slice(0, 4).map(function (s) {
      return '<a href="' + esc(s.href) + '">' + icon(s.icon) + esc(s.name) + "</a>";
    }).join("");

    return '' +
      '<section class="hero">' +
        '<div class="hero-grid">' +
          '<div>' +
            '<span class="hero-badge">' + icon("shield") + "本地模拟运行 · 不需要 API Key</span>" +
            "<h1>" + esc(greetingWord()) + "，" + esc(name) + '<br><span class="accent">今天想办点什么？</span></h1>' +
            '<p class="hero-lead">政策问答、办事流程、校园活动和个人事务，一个入口收好。所有内容都在你的浏览器里运行。</p>' +
            '<form class="hero-ask" data-form="home-ask" autocomplete="off">' +
              icon("sparkles") +
              '<input name="q" id="home-q" type="text" placeholder="问点什么，比如：校园卡丢了怎么补办？" aria-label="向河小智提问" required>' +
              '<button class="btn btn-primary" type="submit">' + icon("send") + "问河小智</button>" +
            "</form>" +
            '<div class="hero-suggest">' + suggestions + "</div>" +
            '<div class="hero-metrics">' +
              '<div class="hero-metric"><strong>' + stats.today.length + '</strong><span>今日安排</span></div>' +
              '<div class="hero-metric"><strong>' + stats.percent + '%</strong><span>待办完成率</span></div>' +
              '<div class="hero-metric"><strong>' + regs.length + '</strong><span>已报名活动</span></div>' +
            "</div>" +
          "</div>" +
          '<div class="hero-visual">' +
            '<span class="hero-float f1">' + icon("shield") + "本地知识库 · 随时可问</span>" +
            '<span class="hero-float f2">' + icon("sparkles") + "0 网络请求 · 0 API 费用</span>" +
            '<img class="hero-mascot" src="assets/mascot.svg" alt="河小智 AI 助手吉祥物">' +
          "</div>" +
        "</div>" +
      "</section>" +

      '<div class="stat-strip">' +
        '<div class="stat-cell">' + U.iconTile("trending-up", "violet") + "<div><strong>" + D.USER.growth_value + '</strong><span>成长值 · ' + esc(D.USER.level) + "</span></div></div>" +
        '<div class="stat-cell">' + U.iconTile("credit-card", "teal") + "<div><strong>¥" + esc(D.USER.card_balance) + '</strong><span>一卡通余额</span></div></div>' +
        '<div class="stat-cell">' + U.iconTile("calendar", "gold") + "<div><strong>" + esc(D.USER.week) + '</strong><span>' + esc(D.USER.semester) + "</span></div></div>" +
        '<div class="stat-cell">' + U.iconTile("sparkles", "blue") + "<div><strong>" + S.kbCount() + '</strong><span>本地知识条目</span></div></div>' +
      "</div>" +

      '<section class="section">' +
        '<div class="section-head"><div><div class="eyebrow">核心功能</div><h2>一个入口，办完校园里的小事</h2><p>四个核心场景全部可用，数据只保存在本机。</p></div></div>' +
        '<div class="feature-grid">' + featureCards + "</div>" +
      "</section>" +

      '<section class="section growth-banner">' +
        "<div><h3>你的校园成长档案</h3><p>把每一次活动、任务与志愿时长，积累成看得见的成长。</p>" +
          '<div class="growth-banner-stats mt-14">' +
            "<div><strong>" + D.GROWTH.score + "</strong><span>成长值</span></div>" +
            "<div><strong>" + esc(D.GROWTH.level) + "</strong><span>当前等级</span></div>" +
            "<div><strong>26h</strong><span>志愿时长</span></div>" +
            "<div><strong>5</strong><span>已获徽章</span></div>" +
          "</div></div>" +
        '<a class="btn btn-dark" href="#page=growth">' + icon("award") + "查看成长档案" + icon("arrow-right") + "</a>" +
      "</section>" +

      '<div class="home-split">' +
        '<div class="card card-pad">' +
          '<div class="between"><div><div class="eyebrow">今天</div><h3 style="font-size:17px;margin-top:2px">待办速览</h3></div>' +
            '<a class="section-link" href="#page=center">全部待办' + icon("arrow-right") + "</a></div>" +
          '<div class="mt-10">' + todoRows + "</div>" +
        "</div>" +
        '<div class="card card-pad">' +
          '<div class="between"><div><div class="eyebrow teal">通知</div><h3 style="font-size:17px;margin-top:2px">校园新鲜事</h3></div>' +
            '<button type="button" class="section-link" style="border:0;background:none;padding:0" data-action="tool" data-tool="notices">全部通知' + icon("arrow-right") + "</button></div>" +
          '<div class="brief-list mt-10">' + noticeRows + "</div>" +
          '<div class="home-quick">' + quickServices + "</div>" +
        "</div>" +
      "</div>";
  }

  /* ------------------------------------------------------------------ */
  /* 智能问答                                                           */
  /* ------------------------------------------------------------------ */
  function answerHTML(answer) {
    const tone = U.toneOf(answer.tone);
    const steps = (answer.steps || []).map(function (s, i) {
      return '<div class="answer-step"><span class="n">' + (i + 1) + "</span><div>" + esc(s) + "</div></div>";
    }).join("");
    const tips = answer.tip ? '<div class="answer-tip">' + icon("info") + "<span>" + esc(answer.tip) + "</span></div>" : "";
    const source = answer.source ? '<div class="answer-source">' + icon("shield") + "<span>依据来源：" + esc(answer.source) + " · 本地检索</span></div>" : "";
    const links = (answer.links || []).map(function (l) {
      return '<a href="' + esc(l.href) + '">' + esc(l.label) + icon("arrow-up-right") + "</a>";
    }).join("");
    const confidence = answer.confidence
      ? U.tag("匹配度 " + Math.round(Number(answer.confidence) * 100) + "%", "teal")
      : "";
    const keywords = (answer.keywords || []).length
      ? '<div class="answer-badges" style="margin-top:7px">' + answer.keywords.slice(0, 4).map(function (k) { return U.tag(k, "blue"); }).join("") + "</div>"
      : "";
    const alternatives = (answer.alternatives || []).length
      ? '<div class="ai-alts">你可能还想问：' + answer.alternatives.map(function (a) {
        return '<button type="button" data-action="ask" data-q="' + esc(a.question) + '">' + esc(a.title) + "</button>";
      }).join("") + "</div>"
      : "";

    return '<div class="answer">' +
      '<div class="answer-head">' + U.iconTile(answerIcon(answer.tag), tone) +
        "<div><h4>" + esc(answer.title) + "</h4>" +
          '<div class="answer-badges">' + U.tag(answer.tag || "问答", tone) + U.tag("本地模拟 · 未接 API", "teal") + confidence + "</div>" +
        "</div></div>" +
      '<div class="answer-intro">' + U.nl2br(answer.intro) + "</div>" +
      keywords +
      (steps ? '<div class="answer-steps">' + steps + "</div>" : "") +
      tips + source +
      (links ? '<div class="answer-links">' + links + "</div>" : "") +
      alternatives +
      "</div>";
  }

  function qa() {
    const user = S.currentUser();
    const st = S.state();
    const messages = st.qa.messages;
    const docs = S.qaDocs();
    const rounds = S.qaRounds();

    const messageHTML = messages.length ? messages.map(function (m) {
      if (m.role === "user") {
        return '<div class="msg msg-user"><div class="msg-avatar">' + esc(U.initials(user ? user.username : "我")) + '</div>' +
          '<div class="msg-main"><div class="bubble">' + U.nl2br(m.text) + '</div><div class="msg-time">' + esc(U.timeHM(m.time)) + "</div></div></div>";
      }
      return '<div class="msg msg-bot"><div class="msg-avatar bot"><img src="assets/mascot.svg" alt=""></div>' +
        '<div class="msg-main"><div class="bubble">' + answerHTML(m.answer) + '</div><div class="msg-time">河小智 · ' + esc(U.timeHM(m.time)) + "</div></div></div>";
    }).join("") : '<div class="chat-welcome">' +
      '<img src="assets/mascot.svg" alt="河小智">' +
      "<h3>今天想了解什么？</h3>" +
      "<p>政策、流程、校园生活都能问。模拟版用本地知识库作答，答案会标注来源。</p>" +
      '<div class="welcome-chips">' + D.QA_SUGGESTIONS.map(function (q) {
        return '<button type="button" data-action="ask" data-q="' + esc(q) + '">' + esc(q) + "</button>";
      }).join("") + "</div></div>";

    const suggest = D.QA_SUGGESTIONS.slice(0, 4).map(function (q) {
      return '<button type="button" data-action="ask" data-q="' + esc(q) + '">' + icon("sparkles") + esc(q) + "</button>";
    }).join("");

    const tools = [
      { tool: "search", icon: "search", label: "知识库检索" },
      { tool: "faq", icon: "help-circle", label: "高频问题" },
      { tool: "notices", icon: "bell", label: "通知公告" },
      { tool: "aid", icon: "award", label: "资助政策" },
      { tool: "processes", icon: "route", label: "办事流程" },
      { tool: "upload", icon: "upload", label: "上传资料" }
    ].map(function (t) {
      return '<button type="button" class="tool-btn" data-action="tool" data-tool="' + t.tool + '">' + icon(t.icon) + esc(t.label) + "</button>";
    }).join("");

    return U.pageHead("智能问答", "本地知识库 + 关键词匹配，完全不需要联网或 API。", "河小智 AI") +
      '<div class="qa-layout">' +
        '<section class="card chat-card">' +
          '<div class="chat-head"><img src="assets/mascot.svg" alt="">' +
            "<div><strong>河小智 · 校园助手</strong><span>本地知识库 · 无需 API · 回答标注来源</span></div>" +
            U.pill("在线", "live") +
          "</div>" +
          '<div class="chat-body" id="chat-body">' + messageHTML + "</div>" +
          '<div class="chat-compose">' +
            '<form data-form="qa-ask" autocomplete="off">' +
              '<div class="compose-box">' +
                '<textarea name="q" id="qa-input" rows="1" placeholder="输入你的问题，例如：图书馆今天开到几点？" required></textarea>' +
                '<button class="btn btn-primary" type="submit" aria-label="发送">' + icon("send") + "</button>" +
              "</div>" +
              '<div class="compose-foot"><span>按 Enter 发送，Shift + Enter 换行</span><span>回答来自本地演示知识库 · 未接入大模型</span></div>' +
            "</form>" +
          "</div>" +
        "</section>" +
        '<aside class="qa-rail">' +
          '<div class="card rail-card">' +
            "<h4>本地问答状态</h4><p>所有匹配在你的浏览器中完成，没有请求离开本机。</p>" +
            '<div class="rail-stats">' +
              '<div class="rail-stat"><strong>' + S.kbCount() + '</strong><span>知识条目</span></div>' +
              '<div class="rail-stat"><strong>' + rounds + '</strong><span>本次对话轮数</span></div>' +
              '<div class="rail-stat"><strong>' + docs.length + '</strong><span>上传资料</span></div>' +
              '<div class="rail-stat"><strong>0</strong><span>网络请求</span></div>' +
            "</div>" +
            '<div class="flex mt-14" style="gap:7px">' +
              '<button type="button" class="btn btn-soft btn-sm grow" data-action="qa-new">' + icon("refresh") + "新会话</button>" +
              '<button type="button" class="btn btn-ghost btn-sm" data-action="qa-clear">清空记录</button>' +
            "</div>" +
          "</div>" +
          '<div class="card rail-card">' +
            "<h4>功能工作台</h4><p>检索知识库、看通知、上传自己的资料。</p>" +
            '<div class="tool-grid">' + tools + "</div>" +
          "</div>" +
          '<div class="card rail-card">' +
            "<h4>试试这样问</h4>" +
            '<div class="rail-suggest">' + suggest + "</div>" +
          "</div>" +
          '<div class="rail-note">' + icon("shield") + "<span>模拟版为关键词 + 2-gram 匹配，复杂问题可能答不全；正式版可接入大模型，但本版本不需要任何 API。</span></div>" +
        "</aside>" +
      "</div>";
  }

  /* ------------------------------------------------------------------ */
  /* 办事流程                                                           */
  /* ------------------------------------------------------------------ */
  function processDetail(p) {
    const materials = (p.materials || []).map(function (m) { return "<li>" + esc(m) + "</li>"; }).join("");
    const steps = (p.steps || []).map(function (s, i) {
      return '<div class="answer-step"><span class="n">' + (i + 1) + "</span><div>" + esc(s) + "</div></div>";
    }).join("");
    return '<div class="process-detail">' +
      '<div class="detail-block"><h5>' + icon("clipboard") + "所需材料</h5><ul>" + materials + "</ul></div>" +
      '<div class="detail-block"><h5>' + icon("list") + '办理步骤</h5><div class="answer-steps">' + steps + "</div></div>" +
      '<div class="detail-block"><h5>' + icon("info") + '注意事项</h5><p style="font-size:11.5px;color:var(--muted);line-height:1.65">' + esc(p.notice) + "</p></div>" +
      '<div class="detail-source">依据来源：' + esc(p.source) + "</div>" +
      "</div>";
  }

  function processPlanCard(rec) {
    if (!rec || !rec.matched) return "";
    const p = rec.process;
    const plan = S.buildPlan(p);
    const st = S.getServicePlan(p.id, rec.need);
    const done = plan.todos.filter(function (t) { return !!st.checked[t.id]; }).length;
    const pct = plan.todos.length ? Math.round(done / plan.todos.length * 100) : 0;
    const rows = plan.todos.map(function (t) {
      const checked = !!st.checked[t.id];
      return '<div class="check-row' + (checked ? " done" : "") + '">' +
        '<button type="button" class="checkbox' + (checked ? " on teal" : "") + '" data-action="plan-check" data-pid="' + esc(p.id) + '" data-tid="' + esc(t.id) + '" aria-label="勾选">' + icon("check") + "</button>" +
        '<div class="check-text"><span class="kind' + (t.tone === "gold" ? " gold" : "") + '">' + esc(t.kind) + '</span><span class="label">' + esc(t.label) + "</span></div></div>";
    }).join("");
    return '<section class="card plan-panel" id="service-plan">' +
      '<div class="plan-head">' + U.iconTile("clipboard", "teal") +
        "<div><h3>「" + esc(p.title) + "」办理计划</h3><p>根据你的需求自动拆成 " + plan.todos.length + " 个可勾选步骤 · 进度保存在本机</p></div>" +
        '<div class="plan-actions">' +
          '<button type="button" class="btn btn-soft btn-sm" data-action="plan-reset" data-pid="' + esc(p.id) + '">' + icon("refresh") + "重置勾选</button>" +
          '<button type="button" class="btn btn-primary btn-sm" data-action="plan-to-todos" data-pid="' + esc(p.id) + '">' + icon("plus") + "加入个人待办</button>" +
        "</div></div>" +
      '<div class="plan-progress"><div class="between"><span>办理进度</span><span>' + done + " / " + plan.todos.length + " · " + pct + '%</span></div>' +
        U.progress(pct, "teal") + "</div>" +
      '<div class="plan-list">' + rows + "</div>" +
      '<div class="plan-note">' + icon("info") + "<span>模拟版把勾选进度保存到浏览器；正式版可对接学校办事大厅，实现真实进度同步。地点：" + esc(p.location) + "</span></div>" +
      "</section>";
  }

  function processCard(p) {
    const open = openProcs.has(p.id);
    return '<article class="card process-card' + (open ? " open" : "") + '" id="process-' + esc(p.id) + '">' +
      '<div class="process-top">' + U.iconTile(p.icon || "route", processTone(p.category)) +
        "<div><h3>" + esc(p.title) + "</h3><div class=\"process-meta\">" + esc(p.department) + " · " + esc(p.duration) + "</div></div>" +
        U.tag(p.category, processTone(p.category)) +
      "</div>" +
      '<p class="process-summary">' + esc(p.summary) + "</p>" +
      '<div class="process-tags">' +
        (p.online ? U.tag("可在线办理", "teal") : U.tag("线下办理", "blue")) +
        (p.hot ? U.tag("高频事项", "gold") : "") +
        U.tag((p.materials || []).length + " 项材料", "violet") +
      "</div>" +
      '<div class="process-actions">' +
        '<button type="button" class="btn btn-primary btn-sm" data-action="process-need" data-need="' + esc(p.title) + '">' + icon("sparkles") + "生成办理计划</button>" +
        '<button type="button" class="btn btn-soft btn-sm" data-action="process-add-todo" data-id="' + esc(p.id) + '">' + icon("plus") + "加入待办</button>" +
        '<button type="button" class="btn btn-ghost btn-sm" data-action="process-toggle" data-id="' + esc(p.id) + '">' + (open ? "收起" : "展开流程") + icon(open ? "chevron-down" : "chevron-right") + "</button>" +
      "</div>" +
      (open ? processDetail(p) : "") +
      "</article>";
  }

  function services(route) {
    const need = String(route.need || "").trim();
    const rec = need ? S.recognize(need) : null;
    const q = String(route.q || "").trim();
    const cat = route.cat || "全部";
    const cleanQ = q.toLowerCase();

    const filtered = D.PROCESSES.filter(function (p) {
      if (cat !== "全部" && p.category !== cat) return false;
      if (!cleanQ) return true;
      const hay = [p.title, p.summary, p.category, p.department, (p.keywords || []).join(" "), (p.steps || []).join(" ")].join(" ").toLowerCase();
      return hay.indexOf(cleanQ) >= 0;
    });

    const catChips = D.PROCESS_CATEGORIES.map(function (c) {
      const href = "#page=services&cat=" + encodeURIComponent(c) + (q ? "&q=" + encodeURIComponent(q) : "");
      return U.chipLink(c, href, c === cat);
    }).join("");

    const examples = ["校园卡丢了", "想开电子成绩单", "生病不能参加考试", "怎么申请国家奖学金", "医保怎么报销"].map(function (x) {
      return '<button type="button" data-action="process-need" data-need="' + esc(x) + '">' + esc(x) + "</button>";
    }).join("");

    let result = "";
    if (rec && rec.matched) {
      const p = rec.process;
      const pct = Math.round(Number(rec.confidence) * 100);
      const alts = rec.alternatives && rec.alternatives.length
        ? '<div class="ai-alts">也可能想办：' + rec.alternatives.map(function (a) {
          return '<button type="button" data-action="process-need" data-need="' + esc(a.title) + '">' + esc(a.title) + "</button>";
        }).join("") + "</div>"
        : "";
      result = '<div class="ai-result">' +
        '<div class="ai-result-head">' + U.iconTile(p.icon || "route", processTone(p.category)) +
          "<div><h3>" + esc(p.title) + "</h3><p>识别需求「" + esc(rec.need) + "」· " + esc(p.department) + " · " + esc(p.duration) + "</p></div>" +
          '<div class="ai-confidence"><div class="conf-ring" style="--p:' + pct + '"><span>' + pct + "%</span></div></div>" +
        "</div>" +
        '<div class="ai-kw">' +
          rec.keywords.map(function (k) { return U.tag(k, "teal"); }).join("") +
          U.tag("本地识别", "blue") +
        "</div>" +
        '<p class="mt-10" style="font-size:12px;color:var(--muted);line-height:1.65">' + esc(p.summary) + "</p>" +
        '<div class="form-actions mt-10">' +
          '<a class="btn btn-primary btn-sm" href="#service-plan">' + icon("clipboard") + "查看办理计划</a>" +
          '<a class="btn btn-soft btn-sm" href="#process-' + esc(p.id) + '">' + icon("eye") + "查看完整流程</a>" +
          '<button type="button" class="btn btn-ghost btn-sm" data-action="process-add-todo" data-id="' + esc(p.id) + '">' + icon("plus") + "加入待办</button>" +
        "</div>" + alts +
        "</div>";
    } else if (rec && !rec.matched) {
      result = '<div class="ai-result"><div class="ai-result-head">' + U.iconTile("info", "gold") +
        "<div><h3>还差一点信息</h3><p>" + esc(rec.hint) + "</p></div></div>" +
        '<div class="ai-kw"><button type="button" class="btn btn-soft btn-sm" data-action="process-need" data-need="校园卡丢了">校园卡丢了</button>' +
        '<button type="button" class="btn btn-soft btn-sm" data-action="process-need" data-need="想开电子成绩单">想开电子成绩单</button>' +
        '<button type="button" class="btn btn-soft btn-sm" data-action="process-need" data-need="生病不能参加考试">生病不能参加考试</button></div></div>';
    }

    return U.pageHead("办事流程导航", "说一句你要办什么，河小智帮你识别流程、拆材料、列步骤。", "AI · 办事") +
      '<section class="ai-panel">' +
        '<span class="hero-badge">' + icon("sparkles") + "本地需求识别 · 无需 API</span>" +
        "<h2>把「要办什么」变成一张办理清单</h2>" +
        '<p class="lead">覆盖校园卡、成绩单、缓考、请销假、转专业、图书借阅、医保报销、国家奖学金等高频事项。</p>' +
        '<form class="ai-ask" data-form="service-need" autocomplete="off">' +
          icon("search") +
          '<input name="need" type="text" value="' + esc(need) + '" placeholder="例如：我校园卡丢了，应该先去哪补办？" aria-label="描述办事需求" required>' +
          '<button class="btn btn-gold" type="submit">' + icon("sparkles") + "识别需求</button>" +
        "</form>" +
        '<div class="ai-examples">' + examples + "</div>" +
        result +
      "</section>" +
      processPlanCard(rec) +
      '<div class="card services-toolbar">' +
        '<form data-form="services-search">' +
          '<div class="search-box">' + icon("search") + '<input class="input" name="q" type="search" value="' + esc(q) + '" placeholder="搜索流程、材料或部门" aria-label="搜索流程"></div>' +
          (cat !== "全部" ? '<input type="hidden" name="cat" value="' + esc(cat) + '">' : "") +
          '<button class="btn btn-primary btn-sm" type="submit">搜索</button>' +
          (q ? '<a class="btn btn-ghost btn-sm" href="#page=services' + (cat !== "全部" ? "&cat=" + encodeURIComponent(cat) : "") + '">清除</a>' : "") +
        "</form>" +
        '<div class="cat-chips">' + catChips + "</div>" +
      "</div>" +
      '<div class="section">' +
        '<div class="section-head"><div><div class="eyebrow teal">流程库</div><h2>常用办事流程</h2><p>' +
          (q ? "关键词「" + esc(q) + "」匹配到 " + filtered.length + " 条" : "共 " + filtered.length + " 条 · 均标注校内公开依据") +
        "</p></div>" +
        '<span class="pill blue">' + icon("shield") + "来源可查</span></div>" +
        (filtered.length ? '<div class="service-grid">' + filtered.map(processCard).join("") + "</div>" :
          U.emptyState("没有匹配的办事流程", "换一个关键词，或直接在上方输入你的需求让河小智识别。", '<a class="btn btn-primary btn-sm" href="#page=services">查看全部流程</a>', "search", "blue")) +
      "</div>";
  }

  /* ------------------------------------------------------------------ */
  /* 校园活动                                                           */
  /* ------------------------------------------------------------------ */
  function activityCard(a) {
    const joined = S.isRegistered(a.id);
    const full = a.participants >= a.capacity && !joined;
    const open = openActs.has(a.id);
    const signups = a.participants + (joined ? 1 : 0);
    const isMine = S.createdActivities().some(function (x) { return x.id === a.id; });
    const btn = joined
      ? '<span class="joined-mark">' + icon("check-circle") + '已报名</span><button type="button" class="btn btn-soft btn-sm" data-action="cancel-activity" data-id="' + esc(a.id) + '" data-from="' + (isMine ? "mine" : "official") + '">取消报名</button>'
      : full
        ? '<button type="button" class="btn btn-soft btn-sm" disabled>名额已满</button>'
        : '<button type="button" class="btn btn-primary btn-sm" data-action="join-activity" data-id="' + esc(a.id) + '">' + icon("plus") + "立即报名</button>";
    return '<article class="card activity-card card-hover" id="activity-' + esc(a.id) + '">' +
      '<div class="activity-cover">' +
        '<img src="assets/' + esc(a.cover) + '" alt="' + esc(a.title) + '活动封面">' +
        U.tag(a.category, "blue") +
        (a.hot ? '<span class="hot">' + icon("flame") + " 热门</span>" : "") +
        '<div class="cover-title">' + esc(a.title) + "</div>" +
      "</div>" +
      '<div class="activity-body">' +
        '<p class="activity-desc">' + esc(a.summary) + "</p>" +
        '<div class="activity-meta">' +
          "<div>" + icon("calendar") + esc(a.date) + " · " + esc(a.time) + "</div>" +
          "<div>" + icon("map-pin") + esc(a.location) + "</div>" +
          "<div>" + icon("clock") + "报名截止 " + esc(a.deadline) + "</div>" +
        "</div>" +
        '<div class="activity-tags">' + (a.tags || []).map(function (t) { return U.tag(t, "violet"); }).join("") + "</div>" +
        '<div class="activity-foot">' +
          '<div class="signups">已有 <strong>' + signups + "</strong> 人报名 · 名额 " + a.capacity + " 人</div>" +
          '<div class="flex" style="gap:6px">' +
            '<button type="button" class="btn btn-ghost btn-sm" data-action="activity-toggle" data-id="' + esc(a.id) + '">' + (open ? "收起详情" : "活动详情") + icon(open ? "chevron-down" : "chevron-right") + "</button>" +
            btn +
          "</div>" +
        "</div>" +
        (open ? '<div class="activity-detail"><p>' + esc(a.detail) + "</p>" +
          '<div class="detail-row">' + icon("users") + "组织方：校团委 / 学生社团 · 以最新通知为准</div>" +
          (isMine ? '<div class="detail-row">' + icon("user") + "这是你创建的活动，仅在本机可见</div>" : "") +
          "</div>" : "") +
      "</div></article>";
  }

  function mineTabs(mtab) {
    const tabs = [
      { id: "joined", label: "我报名的活动" },
      { id: "create", label: "创建活动" },
      { id: "created", label: "我创建的活动" },
      { id: "tasks", label: "活动任务" }
    ];
    return '<div class="mine-tabs">' + tabs.map(function (t) {
      return '<a class="mine-tab' + (mtab === t.id ? " active" : "") + '" href="#page=activities&view=mine&mtab=' + t.id + '">' + esc(t.label) + "</a>";
    }).join("") + "</div>";
  }

  function joinedPanel() {
    const regs = S.registrations();
    const items = regs.map(activityOfRegistration).filter(Boolean);
    if (!items.length) {
      return U.emptyState("还没有报名活动", "去官方活动里看看，找到同频的人。", '<a class="btn btn-primary btn-sm" href="#page=activities&view=official">去逛官方活动</a>', "compass", "gold");
    }
    return '<div class="grid-2">' + items.map(activityCard).join("") + "</div>";
  }

  function createPanel() {
    return '<div class="mine-grid">' +
      '<div class="card card-pad">' +
        "<h3 style=\"font-size:17px\">发起一场校园活动</h3>" +
        '<p class="small muted mt-6">活动只保存在本机浏览器，不会发布到任何服务器，适合模拟演示。</p>' +
        '<form class="form-grid mt-18" data-form="create-activity" autocomplete="off">' +
          '<div class="field full"><label>活动名称 <span class="required">*</span></label><input class="input" name="title" type="text" maxlength="40" placeholder="例如：秋日读书分享会" required></div>' +
          '<div class="field"><label>活动分类</label><select class="select" name="category">' + selectOptions(D.ACTIVITY_TASK_CATEGORIES, "学习") + "</select></div>" +
          '<div class="field"><label>活动日期 <span class="required">*</span></label><input class="input" name="date" type="date" value="' + U.todayInput(7) + '" required></div>' +
          '<div class="field"><label>活动时间</label><input class="input" name="time" type="text" maxlength="30" placeholder="例如：周六 19:00 — 21:00"></div>' +
          '<div class="field"><label>活动地点 <span class="required">*</span></label><input class="input" name="location" type="text" maxlength="50" placeholder="例如：图书馆 3F 研讨间" required></div>' +
          '<div class="field"><label>报名人数上限</label><input class="input" name="capacity" type="number" min="5" max="500" value="60"></div>' +
          '<div class="field"><label>报名截止日期</label><input class="input" name="deadlineDate" type="date" value="' + U.todayInput(5) + '"></div>' +
          '<div class="field full"><label>活动标签</label><input class="input" name="tags" type="text" maxlength="60" placeholder="用逗号分隔，例如：读书、分享、可盖章"></div>' +
          '<div class="field full"><label>活动介绍</label><textarea class="textarea" name="detail" maxlength="300" placeholder="简单介绍一下活动内容和适合人群"></textarea></div>' +
          '<div class="form-actions full"><button class="btn btn-primary" type="submit">' + icon("plus") + "发布活动（仅本机）</button></div>" +
        "</form>" +
      "</div>" +
      '<aside class="flex-col" style="gap:14px">' +
        '<div class="form-side-note"><h5>发布后会发生什么？</h5><ul><li>活动出现在「我创建的活动」中。</li><li>可以随时删除，不影响官方活动。</li><li>不会生成真实报名、短信或通知。</li><li>数据只写入本机 localStorage。</li></ul></div>' +
        '<div class="form-side-note"><h5>演示提示</h5><ul><li>官方活动报名与自建活动彼此独立。</li><li>活动任务可在「活动任务」标签继续拆解。</li><li>换浏览器或清空数据后不会保留。</li></ul></div>' +
      "</aside></div>";
  }

  function createdPanel() {
    const items = S.createdActivities();
    if (!items.length) {
      return U.emptyState("还没有创建活动", "发起一场属于你的校园活动，数据只留在本机。", '<a class="btn btn-primary btn-sm" href="#page=activities&view=mine&mtab=create">创建活动</a>', "plus", "violet");
    }
    return '<div class="created-list">' + items.map(function (a) {
      return '<div class="created-item">' +
        '<span class="cover-dot" style="background:' + esc(a.accent) + '"></span>' +
        "<div class=\"grow\"><h4>" + esc(a.title) + "</h4><p>" + esc(a.category) + " · " + esc(a.date) + " " + esc(a.time) + " · " + esc(a.location) + "</p>" +
          '<p style="margin-top:3px">' + esc(a.detail || "暂无活动介绍") + "</p></div>" +
        '<div class="created-actions"><button type="button" class="btn-icon" data-action="created-delete" data-id="' + esc(a.id) + '" aria-label="删除活动">' + icon("trash") + "</button></div>" +
        "</div>";
    }).join("") + "</div>";
  }

  function activitiesTasksPanel() {
    const stats = S.activityTaskStats();
    const max = Math.max.apply(null, stats.buckets.map(function (b) { return b.count; }).concat([1]));
    const chart = stats.buckets.map(function (b, i) {
      const h = Math.max(6, Math.round(b.count / max * 100));
      return '<div class="col"><div class="bar' + (i === 0 ? " today" : "") + '" style="height:' + h + '%"></div><span>' + esc(b.label) + "</span></div>";
    }).join("");

    function group(title, items) {
      if (!items.length) return "";
      return '<div class="task-group-title">' + esc(title) + '<span class="count">' + items.length + "</span></div>" +
        '<div class="task-board">' + items.map(function (t) {
          return U.taskRow({
            id: t.id,
            title: t.title,
            done: t.done,
            priority: t.priority,
            category: t.category,
            due: S.dueLabel(t.deadline, t.done),
            note: t.note,
            progress: Number(t.progress) || 0,
            toggleAction: "atask-toggle",
            editAction: "atask-edit",
            deleteAction: "atask-delete",
            type: "activity"
          });
        }).join("") + "</div>";
    }

    return '<div class="task-summary">' +
        '<div class="stat-cell">' + U.iconTile("clipboard", "blue") + "<div><strong>" + stats.items.length + '</strong><span>全部任务</span></div></div>' +
        '<div class="stat-cell">' + U.iconTile("flame", "gold") + "<div><strong>" + stats.open.length + '</strong><span>进行中</span></div></div>' +
        '<div class="stat-cell">' + U.iconTile("clock", "rose") + "<div><strong>" + stats.today.length + '</strong><span>今日待办</span></div></div>' +
        '<div class="stat-cell">' + U.iconTile("trending-up", "teal") + "<div><strong>" + stats.completion + '%</strong><span>平均完成度</span></div></div>' +
      "</div>" +
      '<div class="tasks-toolbar between mt-18"><div class="flex wrap"><span class="pill blue">' + icon("flag") + "高优先级 " + stats.high.length + "</span>" +
        '<span class="pill warn">' + icon("clock") + "逾期 " + stats.overdue.length + "</span></div>" +
        '<button type="button" class="btn btn-primary btn-sm" data-action="atask-add">' + icon("plus") + "新增活动任务</button></div>" +
      '<div class="task-chart-card"><div class="between"><strong style="font-size:12px">未来 7 天任务分布</strong><span class="tiny muted">按截止时间统计</span></div>' +
        '<div class="mini-chart">' + chart + "</div></div>" +
      '<div class="mt-18">' +
        group("今日待办", stats.today) +
        group("近期任务", stats.soon) +
        group("已完成", stats.done) +
        (!stats.open.length ? '<div class="small muted mt-10">所有任务都完成了，给自己一点奖励吧。</div>' : "") +
      "</div>";
  }

  function activities(route) {
    const view = route.view === "mine" ? "mine" : "official";
    const mtab = ["joined", "create", "created", "tasks"].indexOf(route.mtab) >= 0 ? route.mtab : "joined";
    const cat = route.cat || "全部";

    const subnav = '<div class="subnav"><a class="' + (view === "official" ? "active" : "") + '" href="#page=activities&view=official">官方活动</a>' +
      '<a class="' + (view === "mine" ? "active" : "") + '" href="#page=activities&view=mine">我的活动</a></div>';

    let body = "";
    if (view === "official") {
      const cats = ["全部"].concat(D.ACTIVITIES.map(function (a) { return a.category; }).filter(function (v, i, arr) { return arr.indexOf(v) === i; }));
      const chips = cats.map(function (c) {
        return U.chipLink(c, "#page=activities&view=official&cat=" + encodeURIComponent(c), c === cat);
      }).join("");
      let list = D.ACTIVITIES.filter(function (a) { return cat === "全部" || a.category === cat; });
      if (route.id) {
        list = list.slice().sort(function (a, b) { return (b.id === route.id ? 1 : 0) - (a.id === route.id ? 1 : 0); });
        if (route.id) openActs.add(route.id);
      }
      body = '<div class="subnav-wrap">' + subnav +
          '<div class="flex wrap"><span class="pill live"><span class="dot"></span>本周 ' + D.ACTIVITIES.length + " 场活动</span>" +
          '<a class="btn btn-soft btn-sm" href="#page=activities&view=mine">' + icon("bookmark") + "我报名的活动</a></div></div>" +
        '<div class="cat-chips mb-18">' + chips + "</div>" +
        '<div class="activity-grid">' + list.map(activityCard).join("") + "</div>";
    } else {
      body = '<div class="subnav-wrap">' + subnav +
          '<a class="btn btn-soft btn-sm" href="#page=activities&view=mine&mtab=tasks">' + icon("clipboard") + "活动任务看板</a></div>" +
        mineTabs(mtab);
      if (mtab === "joined") body += joinedPanel();
      else if (mtab === "create") body += createPanel();
      else if (mtab === "created") body += createdPanel();
      else body += activitiesTasksPanel();
    }

    return '<div class="activities-hero"><div><div class="eyebrow gold">校园活动</div><h1>发现同频的人</h1><p>' +
      (view === "official" ? "官方活动展示，报名与取消全部在本机模拟。" : "报名记录、自建活动与活动任务按账号保存在本机。") +
      "</p></div>" +
      '<div class="flex wrap"><span class="pill">' + icon("shield") + "本地模拟 · 无真实报名" + "</span></div></div>" + body;
  }

  /* ------------------------------------------------------------------ */
  /* 个人事务中心                                                       */
  /* ------------------------------------------------------------------ */
  function centerTaskList(stats, tab) {
    const items = tab === "today" ? stats.today : tab === "upcoming" ? stats.upcoming : stats.doneItems;
    if (!items.length) {
      const desc = tab === "done" ? "完成一项任务后，它会出现在这里。" : "这个分组暂时没有任务，切换看看或新增一条。";
      return U.emptyState("这里空空如也", desc, "", "coffee", "teal");
    }
    return '<div class="task-board">' + items.map(function (t) {
      return U.taskRow({
        id: t.id,
        title: t.title,
        done: t.done,
        category: t.category,
        due: S.dueLabel(t.due, t.done),
        place: t.place,
        note: t.note,
        toggleAction: "todo-toggle",
        editAction: "todo-edit",
        deleteAction: "todo-delete",
        type: "center"
      });
    }).join("") + "</div>";
  }

  function center() {
    const user = S.currentUser();
    const stats = S.todoStats();
    const repairs = S.repairs();
    const counts = { today: stats.today.length, upcoming: stats.upcoming.length, done: stats.doneItems.length };

    const courseRows = D.COURSES.map(function (c) {
      return '<div class="course-row"><div class="course-time"><strong>' + esc(c.time) + "</strong><span>" + esc(c.state) + "</span></div>" +
        '<div class="course-main"><strong>' + esc(c.name) + "</strong><span>" + esc(c.place) + " · " + esc(c.teacher) + "</span></div>" +
        '<span class="tag ' + esc(c.tone) + '">' + esc(c.state === "已签到" ? "进行中" : "待上课") + "</span></div>";
    }).join("");

    const repairRows = repairs.length ? repairs.map(function (r) {
      const thresholds = [20, 40, 60, 80, 100];
      const steps = thresholds.map(function (v) { return '<span class="' + (r.progress >= v ? "on" : "") + '"></span>'; }).join("");
      return '<div class="repair-item"><div class="repair-top"><div class="grow"><h4>' + esc(r.title) + " · " + esc(r.location) + "</h4>" +
        "<p>单号 " + esc(r.id) + " · 提交于 " + esc(stampLabel(r.submitted_at)) + " · 预约时段 " + esc(r.slot) + "</p></div>" +
        U.statusTag(r.status) + "</div>" +
        (r.detail ? "<p>" + esc(r.detail) + "</p>" : "") +
        '<div class="repair-progress"><div class="between"><span>处理进度</span><span>' + Number(r.progress) + '%</span></div>' +
          '<div class="progress-track"><div class="progress-fill' + (r.progress >= 100 ? " green" : "") + '" style="width:' + Math.max(0, Math.min(100, r.progress)) + '%"></div></div></div>' +
        '<div class="repair-steps">' + steps + "</div>" +
        (r.status !== "已完成" ? '<div class="flex mt-10" style="justify-content:flex-end"><button type="button" class="btn btn-soft btn-sm" data-action="repair-complete" data-id="' + esc(r.id) + '">' + icon("check") + "确认完成" + "</button></div>" : '<div class="flex mt-10" style="justify-content:flex-end"><span class="joined-mark">' + icon("check-circle") + "维修已完成</span></div>") +
        "</div>";
    }).join("") : U.emptyState("还没有报修记录", "宿舍设施有问题？提交一条报修试试。", "", "wrench", "blue");

    const priorityCounts = { high: 0, medium: 0, low: 0 };
    stats.open.forEach(function (t) { priorityCounts[t.priority] = (priorityCounts[t.priority] || 0) + 1; });
    const maxPriority = Math.max(1, priorityCounts.high, priorityCounts.medium, priorityCounts.low);
    const priorityBars = ["high", "medium", "low"].map(function (key) {
      const meta = U.priorityMeta(key);
      return '<div class="bar-row"><span class="bar-label">' + esc(meta.label) + '</span><div class="bar-track"><div class="bar-fill ' + (key === "high" ? "rose" : key === "medium" ? "" : "teal") + '" style="width:' + Math.round(priorityCounts[key] / maxPriority * 100) + '%"></div></div><span class="bar-value">' + priorityCounts[key] + "</span></div>";
    }).join("");

    const catCounts = {};
    stats.items.forEach(function (t) { catCounts[t.category] = (catCounts[t.category] || 0) + 1; });
    const maxCat = Math.max.apply(null, Object.keys(catCounts).map(function (k) { return catCounts[k]; }).concat([1]));
    const catBars = Object.keys(catCounts).sort(function (a, b) { return catCounts[b] - catCounts[a]; }).slice(0, 4).map(function (k, i) {
      return '<div class="bar-row"><span class="bar-label">' + esc(k) + '</span><div class="bar-track"><div class="bar-fill ' + (["", "teal", "gold", "violet"][i] || "") + '" style="width:' + Math.round(catCounts[k] / maxCat * 100) + '%"></div></div><span class="bar-value">' + catCounts[k] + "</span></div>";
    }).join("");

    const weekMax = Math.max.apply(null, D.GROWTH.weekly.concat([1]));
    const weekBars = D.GROWTH.weekly.map(function (v, i) {
      return '<div class="col"><div class="bar' + (v === weekMax ? " peak" : "") + '" style="height:' + Math.max(6, Math.round(v / weekMax * 100)) + '%"></div><span>周' + "一二三四五六日".charAt(i) + "</span></div>";
    }).join("");

    const upcoming = stats.open.slice(0, 4).map(function (t) {
      return '<div class="dash-li"><span class="dot"></span><span class="grow"><strong>' + esc(t.title) + "</strong> · " + esc(S.dueLabel(t.due, false)) + "</span></div>";
    }).join("") || '<div class="small muted">暂无待办，去活动页看看吧。</div>';

    return U.pageHead("个人事务中心", "待办、课表、一卡通、报修和数据概览，都放在这一页。", "一站式") +
      '<div class="profile-card card">' +
        '<span class="avatar lg">' + esc(U.initials(user ? user.username : "河")) + "</span>" +
        "<div><h2>" + esc(user ? user.username : "同学") + '</h2><div class="profile-sub">' + esc(user ? user.account_no : "") + " · " + esc(D.USER.college) + " · " + esc(D.USER.major) + "</div>" +
          '<div class="profile-tags">' + U.tag(D.USER.level, "violet") + U.tag(D.USER.campus, "teal") + U.tag(D.USER.grade, "blue") + U.tag("演示账号", "gold") + "</div></div>" +
        '<div class="profile-actions"><a class="btn btn-soft btn-sm" href="#page=growth">' + icon("award") + "成长档案</a>" +
          '<button type="button" class="btn btn-primary btn-sm" data-action="ask" data-q="我的待办怎么安排比较合理？">' + icon("sparkles") + "问问河小智" + "</button></div>" +
      "</div>" +

      '<div class="center-grid mt-18">' +
        '<div class="balance-card"><div class="small-label">一卡通余额 · ONE CARD</div><div class="amount"><small>¥</small>' + esc(D.USER.card_balance) + "</div>" +
          '<div class="balance-foot"><span>卡号 **** 1024 · ' + esc(D.USER.campus) + '</span><button type="button" class="btn" data-action="ask" data-q="一卡通余额不足怎么充值？">去充值</button></div></div>' +
        '<div class="card card-pad"><div class="between"><div><div class="eyebrow">课程表</div><h3 style="font-size:16px;margin-top:2px">' + esc(D.USER.week) + " · 今天</h3></div>" +
          '<span class="pill live"><span class="dot"></span>' + D.COURSES.length + " 门课</span></div>" +
          '<div class="mt-6">' + courseRows + "</div></div>" +
      "</div>" +

      '<section class="section" id="repair-panel">' +
        '<div class="section-head"><div><div class="eyebrow">后勤报修</div><h2>宿舍报修</h2><p>模拟提交报修工单，进度只保存在本机。</p></div><span class="pill warn">' + icon("wrench") + "后勤 24h 响应（演示）</span></div>" +
        '<div class="repair-layout">' +
          '<div class="card card-pad"><h3 style="font-size:16px">提交新报修</h3>' +
            '<form class="mt-14 flex-col" data-form="repair-form" autocomplete="off" style="gap:12px">' +
              '<div class="field"><label>报修事项 <span class="required">*</span></label><input class="input" name="title" type="text" maxlength="40" placeholder="例如：空调不制冷 / 水龙头漏水" required></div>' +
              '<div class="field"><label>具体位置 <span class="required">*</span></label><input class="input" name="location" type="text" maxlength="50" placeholder="例如：31 号宿舍楼 512" required></div>' +
              '<div class="field"><label>方便上门时段</label><select class="select" name="slot">' + selectOptions(["尽快安排", "今天 15:00—17:00", "明天 09:00—11:00", "明天 15:00—17:00", "工作日下午"], "尽快安排") + "</select></div>" +
              '<div class="field"><label>补充说明</label><textarea class="textarea" name="detail" maxlength="200" placeholder="简单描述问题，方便维修师傅提前准备工具"></textarea></div>' +
              '<div class="form-actions"><button class="btn btn-primary" type="submit">' + icon("wrench") + "提交报修" + "</button></div>" +
            "</form></div>" +
          '<div class="card card-pad"><div class="between"><h3 style="font-size:16px">我的报修单</h3><span class="pill blue">' + repairs.length + " 条</span></div>" +
            '<div class="mt-14">' + repairRows + "</div></div>" +
        "</div>" +
      "</section>" +

      '<section class="section">' +
        '<div class="section-head"><div><div class="eyebrow">待办清单</div><h2>我的待办</h2><p>新增、编辑、勾选、删除都会实时保存到本机。</p></div>' +
          '<div class="seg"><button type="button" class="' + (centerTab === "today" ? "active" : "") + '" data-action="center-tab" data-tab="today">今日 ' + counts.today + '</button>' +
          '<button type="button" class="' + (centerTab === "upcoming" ? "active" : "") + '" data-action="center-tab" data-tab="upcoming">近期 ' + counts.upcoming + '</button>' +
          '<button type="button" class="' + (centerTab === "done" ? "active" : "") + '" data-action="center-tab" data-tab="done">已完成 ' + counts.done + "</button></div></div>" +
        '<div class="card card-pad">' +
          '<form class="center-todo-add" data-form="center-add-task" autocomplete="off">' +
            '<div class="field grow" style="min-width:200px"><label>新增待办</label><input class="input" name="title" type="text" maxlength="50" placeholder="例如：预约图书馆研讨间" required></div>' +
            '<div class="field" style="width:112px"><label>分类</label><select class="select" name="category">' + selectOptions(D.TASK_CATEGORIES, "学习") + "</select></div>" +
            '<div class="field" style="width:120px"><label>优先级</label><select class="select" name="priority">' + selectOptions([{ value: "high", label: "高优先级" }, { value: "medium", label: "中优先级" }, { value: "low", label: "低优先级" }], "medium") + "</select></div>" +
            '<div class="field" style="width:142px"><label>截止日期</label><input class="input" name="date" type="date" value="' + U.todayInput(0) + '"></div>' +
            '<div class="field" style="width:112px"><label>截止时间</label><input class="input" name="time" type="time" value="18:00"></div>' +
            '<div class="field" style="width:150px"><label>地点 / 备注</label><input class="input" name="place" type="text" maxlength="40" placeholder="可选"></div>' +
            '<button class="btn btn-primary" type="submit">' + icon("plus") + "添加</button>" +
          "</form>" +
          '<div class="between mb-10"><span class="small muted">当前完成率 <strong style="color:var(--ink)">' + stats.percent + "%</strong> · 已完成 " + stats.done + " / " + stats.total + "</span>" +
            '<a class="section-link" href="#page=activities&view=mine&mtab=tasks">活动任务' + icon("arrow-right") + "</a></div>" +
          U.progress(stats.percent, "teal") +
          '<div class="mt-18">' + centerTaskList(stats, centerTab) + "</div>" +
        "</div>" +
      "</section>" +

      '<section class="section">' +
        '<div class="section-head"><div><div class="eyebrow teal">数据概览</div><h2>今天的状态</h2><p>根据本机待办实时计算，不连接任何统计服务。</p></div></div>' +
        '<div class="dash-grid">' +
          '<div class="card card-pad"><div class="ring-block">' +
            U.ring("centerRing", stats.percent, stats.percent + "%", "待办完成率", "teal") +
            '<div class="small muted">已完成 ' + stats.done + " 项 · 剩余 " + (stats.total - stats.done) + " 项</div></div>" +
            '<hr class="divider">' +
            '<div class="between"><strong style="font-size:12px">优先级分布</strong><span class="tiny muted">未完成</span></div>' + priorityBars +
            '<div class="between mt-18"><strong style="font-size:12px">任务分类</strong><span class="tiny muted">全部</span></div>' + catBars +
          "</div>" +
          '<div class="card card-pad">' +
            '<div class="between"><strong style="font-size:12px">近 7 天活跃度</strong><span class="tiny muted">演示数据</span></div>' +
            '<div class="week-bars">' + weekBars + "</div>" +
            '<hr class="divider">' +
            '<div class="between"><strong style="font-size:12px">即将到期</strong><a class="section-link" href="#page=center">查看全部' + icon("arrow-right") + "</a></div>" +
            '<div class="dash-list mt-10">' + upcoming + "</div>" +
          "</div>" +
        "</div>" +
      "</section>";
  }

  /* ------------------------------------------------------------------ */
  /* 个人成长档案                                                       */
  /* ------------------------------------------------------------------ */
  function growth() {
    const user = S.currentUser();
    const regs = S.registrations();
    const created = S.createdActivities();
    const stats = S.todoStats();
    const atStats = S.activityTaskStats();
    const score = D.GROWTH.score;
    const circumference = (2 * Math.PI * 58).toFixed(1);
    const dash = (score / 100 * Number(circumference)).toFixed(1) + " " + circumference;

    const statCards = D.GROWTH.stats.map(function (s) {
      return '<div class="growth-stat"><strong>' + esc(s.value) + ' <span style="font-size:11px;font-weight:500;color:var(--muted-2)">' + esc(s.unit) + "</span></strong><span>" + esc(s.label) + "</span><small>" + esc(D.USER.semester) + "</small></div>";
    }).join("");

    const skills = D.GROWTH.skills.map(function (s) {
      return '<div class="skill-row"><div class="between"><span>' + esc(s.name) + "</span><span>" + s.value + "</span></div>" +
        '<div class="bar-track"><div class="bar-fill ' + (s.tone === "blue" ? "" : esc(s.tone)) + '" style="width:' + s.value + '%"></div></div></div>';
    }).join("");

    const badges = D.GROWTH.badges.map(function (b) {
      return '<div class="badge-card' + (b.earned ? "" : " locked") + '"><span class="badge-icon">' + icon(b.icon) + "</span><strong>" + esc(b.name) + "</strong><span>" + esc(b.desc) + "</span></div>";
    }).join("");

    const goals = D.GROWTH.goals.map(function (g) {
      return '<div class="goal-item"><span class="goal-dot" style="background:' + (g.tone === "gold" ? "#f5b942" : g.tone === "teal" ? "#14b8a6" : "#2f63ef") + '"></span>' +
        '<div class="grow"><div class="between"><strong>' + esc(g.name) + '</strong><span class="tiny muted">' + g.progress + '%</span></div>' +
        '<div class="bar-track" style="margin-top:5px"><div class="bar-fill ' + (g.tone === "blue" ? "" : esc(g.tone)) + '" style="width:' + g.progress + '%"></div></div>' +
        "<span>" + esc(g.deadline) + "</span></div></div>";
    }).join("");

    const timeline = D.GROWTH.timeline.map(function (t) {
      return '<div class="tl-item"><strong>' + esc(t.title) + "</strong><span>" + esc(t.date) + " · " + esc(t.tag) + "</span><p>" + esc(t.desc) + "</p></div>";
    }).join("");

    const completed = stats.doneItems.slice(0, 6).map(function (t) {
      return '<div class="gc-item">' + icon("check-circle") + "<div><strong>" + esc(t.title) + "</strong><span>" + esc(stampLabel(t.completed_at || t.due)) + " · " + esc(t.category) + "</span></div></div>";
    }).join("") || '<div class="small muted mt-10">还没有已完成的待办，去个人中心添加一条吧。</div>';

    const joined = regs.map(activityFind).filter(Boolean);
    const joinedRows = joined.slice(0, 4).map(function (a) {
      return '<div class="gc-item">' + icon("compass") + "<div><strong>" + esc(a.title) + "</strong><span>" + esc(a.date) + " · " + esc(a.location) + "</span></div></div>";
    }).join("") || '<div class="small muted mt-10">还没有报名活动，去活动页看看。</div>';

    return '<div class="growth-hero">' +
        "<div><div class=\"eyebrow\" style=\"color:#8ff3e5\">个人成长档案</div>" +
          "<h1>" + esc(user ? user.username : "同学") + " 的校园成长</h1>" +
          "<p>成长值、能力标签、徽章与时间线均来自演示数据；待办与报名数据按账号实时统计。</p>" +
          '<div class="growth-tags">' + U.pill(esc(D.GROWTH.level), "") + U.pill(D.USER.college, "") + U.pill(D.USER.campus, "") + "</div>" +
        "</div>" +
        '<div class="score-wrap"><div class="score-ring"><svg viewBox="0 0 136 136">' +
          '<circle class="bg" cx="68" cy="68" r="58"></circle>' +
          '<circle class="fg" cx="68" cy="68" r="58" stroke-dasharray="' + dash + '"></circle>' +
          '</svg><div class="score-label"><strong>' + score + "</strong><span>成长值 / 100</span></div></div>" +
          '<div class="score-side"><strong>下一个等级</strong>' + esc(D.GROWTH.next_level) +
            '<span class="level-pill">再积累 ' + (100 - score) + " 成长值</span></div></div>" +
      "</div>" +
      '<div class="growth-stats">' + statCards + "</div>" +

      '<div class="growth-grid">' +
        '<div class="growth-col">' +
          '<section class="card growth-panel"><h3>' + icon("chart") + "能力画像</h3><p class=\"panel-sub\">根据课程、活动与项目经历综合评估</p>" + skills + "</section>" +
          '<section class="card growth-panel"><h3>' + icon("award") + "徽章收藏</h3><p class=\"panel-sub\">已获得 " + D.GROWTH.badges.filter(function (b) { return b.earned; }).length + " / " + D.GROWTH.badges.length + " 枚</p>" +
            '<div class="badge-grid">' + badges + "</div></section>" +
          '<section class="card growth-panel"><h3>' + icon("target") + "本学期目标</h3><p class=\"panel-sub\">来自成长档案的演示目标</p>" +
            '<div class="goal-list">' + goals + "</div></section>" +
        "</div>" +
        '<div class="growth-col">' +
          '<section class="card growth-panel"><h3>' + icon("clipboard") + "待办完成情况</h3><p class=\"panel-sub\">实时统计 · 共 " + stats.total + " 项</p>" +
            '<div class="between mt-10"><span class="small muted">完成率</span><strong>' + stats.percent + "%</strong></div>" + U.progress(stats.percent, "teal") +
            '<div class="flex wrap mt-14"><span class="pill blue">进行中 ' + stats.open.length + '</span><span class="pill ok">已完成 ' + stats.done + '</span><span class="pill warn">逾期 ' + stats.overdue.length + "</span></div>" +
            '<div class="growth-completed">' + completed + "</div>" +
            '<a class="btn btn-soft btn-sm mt-14" href="#page=center">' + icon("layout-grid") + "去个人中心管理待办" + icon("arrow-right") + "</a></section>" +
          '<section class="card growth-panel"><h3>' + icon("compass") + "活动与参与</h3><p class=\"panel-sub\">官方报名 + 自建活动，按账号保存</p>" +
            '<div class="flex wrap mt-10"><span class="pill blue">已报名 ' + regs.length + '</span><span class="pill violet">自建 ' + created.length + '</span><span class="pill teal">活动任务 ' + atStats.open.length + " 项进行中</span></div>" +
            '<div class="growth-completed">' + joinedRows + "</div>" +
            (created.length ? '<div class="small muted mt-10">你创建了：' + created.slice(0, 3).map(function (a) { return esc(a.title); }).join("、") + "</div>" : "") +
            '<a class="btn btn-soft btn-sm mt-14" href="#page=activities&view=mine">' + icon("compass") + "查看我的活动" + icon("arrow-right") + "</a></section>" +
          '<section class="card growth-panel"><h3>' + icon("star") + "成长时间线</h3><p class=\"panel-sub\">演示经历 · 记录每一步</p><div class='timeline'>" + timeline + "</div></section>" +
          '<section class="card growth-panel"><h3>' + icon("id-card") + "基础信息</h3><p class=\"panel-sub\">账号资料仅保存在本机</p>" +
            '<div class="dash-list mt-10">' +
              '<div class="dash-li"><span class="dot"></span><span>账号：<strong>' + esc(user ? user.account_no : "-") + "</strong></span></div>" +
              '<div class="dash-li"><span class="dot"></span><span>学号：<strong>' + esc(D.USER.student_id) + "</strong></span></div>" +
              '<div class="dash-li"><span class="dot"></span><span>学院：<strong>' + esc(D.USER.college) + "</strong></span></div>" +
              '<div class="dash-li"><span class="dot"></span><span>专业：<strong>' + esc(D.USER.major) + "</strong></span></div>" +
              '<div class="dash-li"><span class="dot"></span><span>宿舍：<strong>' + esc(D.USER.dorm) + "</strong></span></div>" +
            "</div></section>" +
        "</div>" +
      "</div>";
  }

  /* ------------------------------------------------------------------ */
  /* 导出                                                               */
  /* ------------------------------------------------------------------ */
  window.HXZ_PAGES = {
    home: home,
    qa: qa,
    services: services,
    activities: activities,
    center: center,
    growth: growth,
    answerHTML: answerHTML,
    toggleActivity: function (id) {
      if (openActs.has(id)) openActs.delete(id); else openActs.add(id);
    },
    toggleProcess: function (id) {
      if (openProcs.has(id)) openProcs.delete(id); else openProcs.add(id);
    },
    setCenterTab: function (tab) {
      if (["today", "upcoming", "done"].indexOf(tab) >= 0) centerTab = tab;
    },
    resetTransient: function () {
      openActs.clear();
      openProcs.clear();
      centerTab = "today";
    }
  };
})();
