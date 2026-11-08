/* ==========================================================================
   河小智 · 模拟测试版本地数据层
   - 账号、任务、报名、自建活动、问答记录全部保存在浏览器 localStorage；
   - 不发起任何网络请求，不需要 API Key，双击 index.html 即可使用；
   - 密码 / 密保答案仅做本地演示哈希，不具备真实安全强度，请勿使用真实密码。
   ========================================================================== */
(function () {
  "use strict";

  const D = window.HXZ_DATA;
  const DB_KEY = "hxz_mock_db_v1";
  const SESSION_KEY = "hxz_mock_session_v1";
  const SESSION_DAYS = 30;

  /* ------------------------------------------------------------------ */
  /* 通用工具                                                           */
  /* ------------------------------------------------------------------ */
  function pad(n, w) {
    return String(n).padStart(w || 2, "0");
  }

  function isoDate(d) {
    return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
  }

  function isoLocal(d) {
    return isoDate(d) + "T" + pad(d.getHours()) + ":" + pad(d.getMinutes());
  }

  function dateInputValue(d) {
    return isoDate(d);
  }

  function nowStamp() {
    return isoLocal(new Date());
  }

  function cyrb53(str, seed) {
    let h1 = 0xdeadbeef ^ (seed || 0);
    let h2 = 0x41c6ce57 ^ (seed || 0);
    for (let i = 0; i < str.length; i++) {
      const ch = str.charCodeAt(i);
      h1 = Math.imul(h1 ^ ch, 2654435761);
      h2 = Math.imul(h2 ^ ch, 1597334677);
    }
    h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507);
    h1 ^= Math.imul(h2 ^ (h2 >>> 13), 3266489909);
    h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507);
    h2 ^= Math.imul(h1 ^ (h1 >>> 13), 3266489909);
    return 4294967296 * (2097151 & h2) + (h1 >>> 0);
  }

  function hashSecret(text, salt) {
    const a = cyrb53(String(salt) + "|" + String(text), 1013).toString(16);
    const b = cyrb53(String(text) + "|" + String(salt), 2027).toString(16);
    return ("00000000" + a).slice(-14) + ("00000000" + b).slice(-14);
  }

  function randomSalt() {
    const bytes = new Uint8Array(12);
    if (window.crypto && window.crypto.getRandomValues) {
      window.crypto.getRandomValues(bytes);
    } else {
      for (let i = 0; i < bytes.length; i++) bytes[i] = Math.floor(Math.random() * 256);
    }
    return Array.from(bytes).map(function (b) { return ("0" + b.toString(16)).slice(-2); }).join("");
  }

  function normalizeAnswer(raw) {
    return String(raw || "").normalize("NFKC").trim().toLowerCase().replace(/\s+/g, " ");
  }

  function cleanText(text) {
    return String(text || "").toLowerCase().replace(/[\s，。！？、；：,.!?;:~～（）()【】\[\]“”"'《》<>·—\-_/\\|]+/g, "");
  }

  function grams(text, size) {
    size = size || 2;
    const cleaned = cleanText(text);
    if (!cleaned) return new Set();
    if (cleaned.length < size) return new Set([cleaned]);
    const out = new Set();
    for (let i = 0; i <= cleaned.length - size; i++) out.add(cleaned.slice(i, i + size));
    return out;
  }

  function overlap(queryGrams, text) {
    if (!queryGrams || !queryGrams.size) return 0;
    const target = grams(text);
    let hit = 0;
    queryGrams.forEach(function (g) { if (target.has(g)) hit++; });
    return hit / queryGrams.size;
  }

  function uid(prefix) {
    return (prefix || "id") + "-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8);
  }

  function nextMonthDay(month, day, hour, minute) {
    const now = new Date();
    let year = now.getFullYear();
    let d = new Date(year, month - 1, day, hour || 0, minute || 0, 0, 0);
    // 如果这个日期已经过去超过 30 天，视为明年的安排。
    if (d.getTime() < now.getTime() - 30 * 24 * 3600 * 1000) {
      d = new Date(year + 1, month - 1, day, hour || 0, minute || 0, 0, 0);
    }
    return d;
  }

  function startOfToday() {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    return d;
  }

  function parseDue(value) {
    if (value instanceof Date) return value;
    const d = new Date(String(value || "").replace(" ", "T"));
    return isNaN(d.getTime()) ? new Date() : d;
  }

  function dueLabel(value, done, isActivity) {
    const dt = parseDue(value);
    if (isNaN(dt.getTime())) return "未设置";
    const now = new Date();
    const today = startOfToday();
    const day = new Date(dt.getFullYear(), dt.getMonth(), dt.getDate());
    const delta = Math.round((day - today) / 86400000);
    const hhmm = pad(dt.getHours()) + ":" + pad(dt.getMinutes());
    let base;
    if (delta === 0) base = "今天 " + hhmm;
    else if (delta === 1) base = "明天 " + hhmm;
    else if (delta === -1) base = "昨天 " + hhmm;
    else base = (dt.getMonth() + 1) + " 月 " + dt.getDate() + " 日 " + hhmm;
    if (done) return base;
    if (dt.getTime() < now.getTime()) {
      const overdue = Math.max(1, Math.ceil((now - dt) / 86400000));
      return base + " · 已逾期 " + overdue + " 天";
    }
    if (delta === 0) return base + " · 今日截止";
    if (delta === 1) return base + " · 明天截止";
    return base + " · 还剩 " + delta + " 天";
  }

  /* ------------------------------------------------------------------ */
  /* 账号库                                                             */
  /* ------------------------------------------------------------------ */
  let DB = null;
  let SESSION_MEM = null;

  function readSession() {
    try {
      const raw = localStorage.getItem(SESSION_KEY);
      if (raw) return JSON.parse(raw);
    } catch (e) { /* 隐私模式 / 禁用存储时使用内存会话 */ }
    return SESSION_MEM;
  }

  function seedDemoUser() {
    const salt = randomSalt();
    return {
      account_no: "HXZ0001",
      username: "演示同学",
      salt: salt,
      password_hash: hashSecret("demo1234", salt),
      question: "你的学号后四位是？",
      answer_hash: hashSecret(normalizeAnswer("1024"), salt),
      created_at: nowStamp()
    };
  }

  function emptyState() {
    return {
      todos: seedTodos(),
      registrations: [],
      createdActivities: [],
      activityTasks: seedActivityTasks(),
      repairs: [seedRepair()],
      servicePlans: {},
      qa: { messages: [], session: 1, docs: [] }
    };
  }

  function load() {
    if (DB) return DB;
    try {
      const raw = localStorage.getItem(DB_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && Array.isArray(parsed.users)) {
          DB = parsed;
          if (!DB.states || typeof DB.states !== "object") DB.states = {};
          if (!DB.seq) DB.seq = DB.users.length;
          ensureDemoUser();
          return DB;
        }
      }
    } catch (e) { /* 损坏时重新初始化 */ }
    DB = { seq: 1, users: [seedDemoUser()], states: {} };
    save();
    return DB;
  }

  function ensureDemoUser() {
    if (!DB.users.some(function (u) { return u.account_no === "HXZ0001"; })) {
      DB.users.unshift(seedDemoUser());
    }
    const maxNo = DB.users.reduce(function (max, u) {
      const n = parseInt(String(u.account_no || "").replace(/^HXZ/i, ""), 10) || 0;
      return Math.max(max, n);
    }, 0);
    DB.seq = Math.max(Number(DB.seq) || 1, maxNo);
  }

  function save() {
    try {
      localStorage.setItem(DB_KEY, JSON.stringify(DB));
    } catch (e) { /* 隐私模式 / 配额不足时静默降级为内存数据 */ }
  }

  function currentUser() {
    const session = readSession();
    if (!session || !session.account_no) return null;
    if (Number(session.expires || 0) < Date.now()) {
      SESSION_MEM = null;
      try { localStorage.removeItem(SESSION_KEY); } catch (e) { /* ignore */ }
      return null;
    }
    const db = load();
    return db.users.find(function (u) { return u.account_no === session.account_no; }) || null;
  }

  function startSession(accountNo) {
    const session = {
      account_no: accountNo,
      expires: Date.now() + SESSION_DAYS * 24 * 3600 * 1000
    };
    SESSION_MEM = session;
    try { localStorage.setItem(SESSION_KEY, JSON.stringify(session)); } catch (e) { /* 使用内存会话 */ }
  }

  function endSession() {
    SESSION_MEM = null;
    try { localStorage.removeItem(SESSION_KEY); } catch (e) { /* ignore */ }
  }

  function stateFor(accountNo) {
    const db = load();
    if (!db.states[accountNo]) {
      db.states[accountNo] = emptyState();
      save();
    } else {
      normalizeState(db.states[accountNo]);
    }
    return db.states[accountNo];
  }

  function state() {
    const user = currentUser();
    if (!user) return null;
    return stateFor(user.account_no);
  }

  function normalizeState(st) {
    if (!Array.isArray(st.todos)) st.todos = seedTodos();
    if (!Array.isArray(st.registrations)) st.registrations = [];
    if (!Array.isArray(st.createdActivities)) st.createdActivities = [];
    if (!Array.isArray(st.activityTasks)) st.activityTasks = seedActivityTasks();
    if (!Array.isArray(st.repairs)) st.repairs = [seedRepair()];
    if (!st.servicePlans || typeof st.servicePlans !== "object") st.servicePlans = {};
    if (!st.qa || typeof st.qa !== "object") st.qa = { messages: [], session: 1, docs: [] };
    if (!Array.isArray(st.qa.messages)) st.qa.messages = [];
    if (!Array.isArray(st.qa.docs)) st.qa.docs = [];
    if (!st.qa.session) st.qa.session = 1;
    return st;
  }

  function saveState() {
    const user = currentUser();
    if (user && DB && DB.states[user.account_no]) save();
  }

  /* ------------------------------------------------------------------ */
  /* 注册 / 登录 / 找回密码                                              */
  /* ------------------------------------------------------------------ */
  const USERNAME_RE = /^[A-Za-z0-9_一-鿿]{2,16}$/;

  function validatePassword(password) {
    const p = String(password || "");
    if (p.length < 8 || p.length > 32) return "密码长度需为 8–32 位。";
    if (!/[A-Za-z]/.test(p) || !/[0-9]/.test(p)) return "密码需同时包含字母和数字。";
    return "";
  }

  function findByIdentifier(identifier) {
    const key = String(identifier || "").trim().toLowerCase();
    if (!key) return null;
    return load().users.find(function (u) {
      return String(u.account_no).toLowerCase() === key || String(u.username).toLowerCase() === key;
    }) || null;
  }

  function register(payload) {
    const db = load();
    const username = String(payload.username || "").normalize("NFKC").trim();
    const password = String(payload.password || "");
    const question = String(payload.question || "").trim().replace(/\s+/g, " ");
    const answer = normalizeAnswer(payload.answer);
    if (!USERNAME_RE.test(username)) return { ok: false, message: "用户名需为 2–16 位中文、字母、数字或下划线。" };
    if (/^HXZ\d+$/i.test(username)) return { ok: false, message: "用户名不能使用 HXZ + 数字的账号号格式。" };
    if (db.users.some(function (u) { return String(u.username).toLowerCase() === username.toLowerCase(); })) {
      return { ok: false, message: "该用户名已被使用，请换一个。" };
    }
    const pwdError = validatePassword(password);
    if (pwdError) return { ok: false, message: pwdError };
    if (String(payload.password2 || "") !== password) return { ok: false, message: "两次输入的密码不一致。" };
    if (question.length < 2 || question.length > 60) return { ok: false, message: "密保问题需为 2–60 个字符。" };
    if (answer.length < 2 || answer.length > 50) return { ok: false, message: "密保答案需为 2–50 个字符。" };
    db.seq = Math.max(Number(db.seq) || 1, db.users.length) + 1;
    const accountNo = "HXZ" + String(db.seq).padStart(4, "0");
    const salt = randomSalt();
    db.users.push({
      account_no: accountNo,
      username: username,
      salt: salt,
      password_hash: hashSecret(password, salt),
      question: question,
      answer_hash: hashSecret(answer, salt),
      created_at: nowStamp()
    });
    db.states[accountNo] = emptyState();
    save();
    return { ok: true, account_no: accountNo, username: username };
  }

  function login(identifier, password) {
    const user = findByIdentifier(identifier);
    if (!user) return { ok: false, message: "未找到该账号，请先注册或检查账号号 / 用户名。" };
    if (hashSecret(String(password || ""), user.salt) !== user.password_hash) {
      return { ok: false, message: "密码不正确，请重新输入。" };
    }
    startSession(user.account_no);
    return { ok: true, user: user };
  }

  function getSecurityQuestion(identifier) {
    const user = findByIdentifier(identifier);
    if (!user) return { ok: false, message: "未找到该账号，请检查账号号 / 用户名。" };
    if (!user.question || !user.answer_hash) return { ok: false, message: "该账号未设置密保问答，无法自助找回。" };
    return { ok: true, user: user, question: user.question };
  }

  function resetPassword(identifier, answer, newPassword) {
    const user = findByIdentifier(identifier);
    if (!user) return { ok: false, message: "未找到该账号。" };
    if (hashSecret(normalizeAnswer(answer), user.salt) !== user.answer_hash) {
      return { ok: false, message: "密保答案不正确，请再试一次。" };
    }
    const pwdError = validatePassword(newPassword);
    if (pwdError) return { ok: false, message: pwdError };
    user.password_hash = hashSecret(newPassword, user.salt);
    save();
    return { ok: true, account_no: user.account_no, username: user.username };
  }

  function accountCount() {
    return load().users.length;
  }

  /* ------------------------------------------------------------------ */
  /* 待办种子与增删改                                                   */
  /* ------------------------------------------------------------------ */
  function seedTodos() {
    const today = startOfToday();
    function todayAt(h, m) {
      const d = new Date(today);
      d.setHours(h, m, 0, 0);
      return d;
    }
    const scholarshipDue = new Date(today);
    scholarshipDue.setDate(scholarshipDue.getDate() + 3);
    scholarshipDue.setHours(23, 59, 0, 0);
    const completedAt = new Date(today);
    completedAt.setHours(9, 20, 0, 0);
    return [
      { id: "t1", title: "提交《人工智能导论》课程作业", category: "学习", priority: "high", due: isoLocal(todayAt(18, 0)), place: "线上 · 雨课堂", note: "", done: false, created_at: nowStamp(), completed_at: "" },
      { id: "t2", title: "预约图书馆小组研讨间", category: "学习", priority: "medium", due: isoLocal(todayAt(20, 0)), place: "图书馆 3F", note: "", done: false, created_at: nowStamp(), completed_at: "" },
      { id: "t3", title: "一卡通余额不足，记得充值", category: "生活", priority: "low", due: isoLocal(todayAt(23, 59)), place: "余额 ¥86.40", note: "", done: false, created_at: nowStamp(), completed_at: "" },
      { id: "t4", title: "填写 2026 年秋季学期奖学金申请", category: "工作", priority: "high", due: isoLocal(scholarshipDue), place: "学生事务大厅", note: "", done: true, created_at: nowStamp(), completed_at: isoLocal(completedAt) },
      { id: "t5", title: "回复「挑战杯」小组会议时间", category: "活动", priority: "medium", due: isoLocal(todayAt(21, 0)), place: "项目微信群", note: "", done: false, created_at: nowStamp(), completed_at: "" }
    ];
  }

  function addTodo(fields) {
    const st = state();
    if (!st) return null;
    const item = {
      id: uid("todo"),
      title: String(fields.title || "").trim(),
      category: D.TASK_CATEGORIES.indexOf(fields.category) >= 0 ? fields.category : "其他",
      priority: D.TASK_PRIORITIES[fields.priority] ? fields.priority : "medium",
      due: fields.due || nowStamp(),
      place: String(fields.place || "").trim(),
      note: String(fields.note || "").trim(),
      done: false,
      created_at: nowStamp(),
      completed_at: ""
    };
    if (!item.title) return null;
    st.todos.push(item);
    saveState();
    return item;
  }

  function updateTodo(id, fields) {
    const st = state();
    if (!st) return false;
    const item = st.todos.find(function (t) { return t.id === id; });
    if (!item) return false;
    if (fields.title !== undefined) item.title = String(fields.title).trim() || item.title;
    if (fields.category !== undefined && D.TASK_CATEGORIES.indexOf(fields.category) >= 0) item.category = fields.category;
    if (fields.priority !== undefined && D.TASK_PRIORITIES[fields.priority]) item.priority = fields.priority;
    if (fields.due !== undefined) item.due = fields.due;
    if (fields.place !== undefined) item.place = String(fields.place || "").trim();
    if (fields.note !== undefined) item.note = String(fields.note || "").trim();
    if (fields.done !== undefined) setTodoDone(item, !!fields.done);
    saveState();
    return true;
  }

  function setTodoDone(item, done) {
    if (item.done === done) return;
    item.done = done;
    item.completed_at = done ? nowStamp() : "";
  }

  function toggleTodo(id) {
    const st = state();
    if (!st) return false;
    const item = st.todos.find(function (t) { return t.id === id; });
    if (!item) return false;
    setTodoDone(item, !item.done);
    saveState();
    return item.done;
  }

  function deleteTodo(id) {
    const st = state();
    if (!st) return false;
    const before = st.todos.length;
    st.todos = st.todos.filter(function (t) { return t.id !== id; });
    if (st.todos.length !== before) { saveState(); return true; }
    return false;
  }

  function todoStats() {
    const st = state();
    const items = st ? st.todos.slice() : [];
    const now = new Date();
    const today = startOfToday();
    const tomorrow = new Date(today); tomorrow.setDate(tomorrow.getDate() + 1);
    const sorted = items.slice().sort(function (a, b) { return parseDue(a.due) - parseDue(b.due); });
    const doneItems = sorted.filter(function (t) { return t.done; });
    const open = sorted.filter(function (t) { return !t.done; });
    const todayItems = open.filter(function (t) { return parseDue(t.due) < tomorrow; });
    const upcoming = open.filter(function (t) { return parseDue(t.due) >= tomorrow; });
    const overdue = open.filter(function (t) { return parseDue(t.due) < now; });
    const total = items.length;
    const done = doneItems.length;
    return {
      items: sorted,
      open: open,
      today: todayItems,
      upcoming: upcoming,
      doneItems: doneItems.slice().sort(function (a, b) { return parseDue(b.completed_at || b.due) - parseDue(a.completed_at || a.due); }),
      overdue: overdue,
      total: total,
      done: done,
      percent: total ? Math.round(done / total * 100) : 0
    };
  }

  /* ------------------------------------------------------------------ */
  /* 校园活动报名 / 自建活动                                             */
  /* ------------------------------------------------------------------ */
  function registrations() {
    const st = state();
    return st ? st.registrations.slice() : [];
  }

  function isRegistered(id) {
    return registrations().indexOf(id) >= 0;
  }

  function joinActivity(id) {
    const st = state();
    if (!st) return false;
    if (st.registrations.indexOf(id) >= 0) return false;
    st.registrations.push(id);
    saveState();
    return true;
  }

  function cancelActivity(id) {
    const st = state();
    if (!st) return false;
    const before = st.registrations.length;
    st.registrations = st.registrations.filter(function (x) { return x !== id; });
    if (st.registrations.length !== before) { saveState(); return true; }
    return false;
  }

  function createdActivities() {
    const st = state();
    return st ? st.createdActivities.slice() : [];
  }

  function addCreatedActivity(fields) {
    const st = state();
    if (!st) return null;
    const cat = String(fields.category || "其他");
    const coverMap = { "科技": "activity-ai.svg", "文艺": "activity-music.svg", "讲座": "activity-lecture.svg", "运动": "activity-run.svg", "其他": "activity-ai.svg" };
    const accentMap = { "科技": "#2563EB", "文艺": "#F59E0B", "讲座": "#14B8A6", "运动": "#22C55E", "其他": "#7C3AED" };
    const item = {
      id: uid("myact"),
      category: D.ACTIVITY_TASK_CATEGORIES.indexOf(cat) >= 0 ? cat : "其他",
      title: String(fields.title || "").trim(),
      date: fields.dateLabel || "",
      time: fields.timeLabel || "",
      location: String(fields.location || "").trim(),
      capacity: Number(fields.capacity) || 60,
      participants: 0,
      deadline: fields.deadlineLabel || "",
      tags: Array.isArray(fields.tags) ? fields.tags.slice(0, 4) : [],
      detail: String(fields.detail || "").trim(),
      cover: coverMap[cat] || "activity-ai.svg",
      accent: accentMap[cat] || "#7C3AED",
      hot: false,
      created_at: nowStamp()
    };
    st.createdActivities.unshift(item);
    saveState();
    return item;
  }

  function deleteCreatedActivity(id) {
    const st = state();
    if (!st) return false;
    const before = st.createdActivities.length;
    st.createdActivities = st.createdActivities.filter(function (a) { return a.id !== id; });
    if (st.createdActivities.length !== before) { saveState(); return true; }
    return false;
  }

  /* ------------------------------------------------------------------ */
  /* 活动任务                                                           */
  /* ------------------------------------------------------------------ */
  function seedActivityTasks() {
    const today = startOfToday();
    function dayAt(offset, h, m) {
      const d = new Date(today);
      d.setDate(d.getDate() + offset);
      d.setHours(h, m, 0, 0);
      return isoLocal(d);
    }
    return [
      { id: uid("atask"), title: "组队并提交 AI 创客马拉松报名", category: "科技", priority: "高", deadline: dayAt(0, 21, 0), progress: 60, note: "官方报名截止 11 月 12 日 18:00，先完成组队再提交报名表。", done: false, linkId: "ai-hackathon", created_at: nowStamp() },
      { id: uid("atask"), title: "报名秋日声浪草坪音乐节", category: "文艺", priority: "中", deadline: dayAt(1, 12, 0), progress: 100, note: "免费入场，周日 17:30 大礼堂前草坪开场，记得带野餐垫。", done: true, linkId: "music-festival", created_at: nowStamp() },
      { id: uid("atask"), title: "准备创客马拉松开发环境与选题", category: "科技", priority: "高", deadline: dayAt(4, 20, 0), progress: 35, note: "48 小时极限开发，提前装好环境、想好「AI + 校园」命题。", done: false, linkId: "ai-hackathon", created_at: nowStamp() },
      { id: uid("atask"), title: "预约名师公开课「大模型与未来教育」", category: "讲座", priority: "中", deadline: dayAt(5, 12, 0), progress: 0, note: "周四 19:00 计算机学院报告厅，可盖章、计通识讲座。", done: false, linkId: "ai-lecture", created_at: nowStamp() },
      { id: uid("atask"), title: "领取荧光夜跑装备并确认集合时间", category: "运动", priority: "低", deadline: dayAt(6, 17, 0), progress: 0, note: "周五 19:30 东操场集合，完赛有限定奖牌、计第二课堂。", done: false, linkId: "night-run", created_at: nowStamp() },
      { id: uid("atask"), title: "复盘马拉松作品并归档代码仓库", category: "科技", priority: "中", deadline: dayAt(10, 21, 0), progress: 0, note: "活动结束后两天内完成复盘，优秀作品可进入孵化计划。", done: false, linkId: "ai-hackathon", created_at: nowStamp() }
    ];
  }

  function activityTasks() {
    const st = state();
    return st ? st.activityTasks.slice().sort(function (a, b) { return parseDue(a.deadline) - parseDue(b.deadline); }) : [];
  }

  function addActivityTask(fields) {
    const st = state();
    if (!st) return null;
    const item = {
      id: uid("atask"),
      title: String(fields.title || "").trim(),
      category: D.ACTIVITY_TASK_CATEGORIES.indexOf(fields.category) >= 0 ? fields.category : "其他",
      priority: D.ACTIVITY_TASK_PRIORITIES.indexOf(fields.priority) >= 0 ? fields.priority : "中",
      deadline: fields.deadline || nowStamp(),
      progress: Math.max(0, Math.min(100, Number(fields.progress) || 0)),
      note: String(fields.note || "").trim(),
      done: !!fields.done,
      linkId: "",
      created_at: nowStamp()
    };
    if (!item.title) return null;
    st.activityTasks.push(item);
    saveState();
    return item;
  }

  function updateActivityTask(id, fields) {
    const st = state();
    if (!st) return false;
    const item = st.activityTasks.find(function (t) { return t.id === id; });
    if (!item) return false;
    if (fields.title !== undefined) item.title = String(fields.title).trim() || item.title;
    if (fields.category !== undefined && D.ACTIVITY_TASK_CATEGORIES.indexOf(fields.category) >= 0) item.category = fields.category;
    if (fields.priority !== undefined && D.ACTIVITY_TASK_PRIORITIES.indexOf(fields.priority) >= 0) item.priority = fields.priority;
    if (fields.deadline !== undefined) item.deadline = fields.deadline;
    if (fields.progress !== undefined) item.progress = Math.max(0, Math.min(100, Number(fields.progress) || 0));
    if (fields.note !== undefined) item.note = String(fields.note || "").trim();
    if (fields.done !== undefined) item.done = !!fields.done;
    if (item.done) item.progress = 100;
    saveState();
    return true;
  }

  function toggleActivityTask(id) {
    const st = state();
    if (!st) return null;
    const item = st.activityTasks.find(function (t) { return t.id === id; });
    if (!item) return null;
    item.done = !item.done;
    item.progress = item.done ? 100 : Math.min(item.progress || 0, 95);
    saveState();
    return item.done;
  }

  function deleteActivityTask(id) {
    const st = state();
    if (!st) return false;
    const before = st.activityTasks.length;
    st.activityTasks = st.activityTasks.filter(function (t) { return t.id !== id; });
    if (st.activityTasks.length !== before) { saveState(); return true; }
    return false;
  }

  function activityTaskStats() {
    const items = activityTasks();
    const now = new Date();
    const today = startOfToday();
    const tomorrow = new Date(today); tomorrow.setDate(tomorrow.getDate() + 1);
    const open = items.filter(function (t) { return !t.done; });
    const done = items.filter(function (t) { return t.done; });
    const buckets = [];
    const weekdays = "日一二三四五六";
    for (let i = 0; i < 7; i++) {
      const day = new Date(today); day.setDate(day.getDate() + i);
      const next = new Date(day); next.setDate(next.getDate() + 1);
      const count = open.filter(function (t) {
        const d = parseDue(t.deadline);
        return d >= day && d < next;
      }).length;
      buckets.push({ label: i === 0 ? "今天" : i === 1 ? "明天" : "周" + weekdays[day.getDay()], count: count });
    }
    const priorityCounts = { "高": 0, "中": 0, "低": 0 };
    open.forEach(function (t) { priorityCounts[t.priority] = (priorityCounts[t.priority] || 0) + 1; });
    return {
      items: items,
      open: open,
      done: done,
      today: open.filter(function (t) { return parseDue(t.deadline) < tomorrow; }),
      soon: open.filter(function (t) { return parseDue(t.deadline) >= tomorrow; }),
      overdue: open.filter(function (t) { return parseDue(t.deadline) < now; }),
      high: open.filter(function (t) { return t.priority === "高"; }),
      completion: items.length ? Math.round(items.reduce(function (s, t) { return s + (Number(t.progress) || 0); }, 0) / items.length) : 0,
      priorityCounts: priorityCounts,
      buckets: buckets
    };
  }

  /* ------------------------------------------------------------------ */
  /* 报修                                                               */
  /* ------------------------------------------------------------------ */
  function seedRepair() {
    const d = new Date();
    d.setHours(d.getHours() - 2, 12, 0, 0);
    return {
      id: "BX" + d.getFullYear() + pad(d.getMonth() + 1) + pad(d.getDate()) + "012",
      title: "空调不制冷",
      location: "31 号宿舍楼 512",
      detail: "空调开启后只出风不制冷，已尝试重启仍无效。",
      slot: "今天 15:00—17:00",
      submitted_at: isoLocal(d),
      status: "维修中",
      progress: 60
    };
  }

  function repairs() {
    const st = state();
    return st ? st.repairs.slice() : [];
  }

  function addRepair(fields) {
    const st = state();
    if (!st) return null;
    const d = new Date();
    const item = {
      id: "BX" + d.getFullYear() + pad(d.getMonth() + 1) + pad(d.getDate()) + pad(d.getHours()) + pad(d.getMinutes()),
      title: String(fields.title || "").trim(),
      location: String(fields.location || "").trim(),
      detail: String(fields.detail || "").trim(),
      slot: String(fields.slot || "尽快安排").trim(),
      submitted_at: nowStamp(),
      status: "已提交",
      progress: 20
    };
    if (!item.title || !item.location) return null;
    st.repairs.unshift(item);
    saveState();
    return item;
  }

  function completeRepair(id) {
    const st = state();
    if (!st) return false;
    const item = st.repairs.find(function (r) { return r.id === id; });
    if (!item) return false;
    item.status = "已完成";
    item.progress = 100;
    saveState();
    return true;
  }

  /* ------------------------------------------------------------------ */
  /* 办事流程识别与计划                                                 */
  /* ------------------------------------------------------------------ */
  const PUNCT_RE = /[\s，。！？、；：,.!?;:~～（）()【】\[\]“”"'《》<>·—\-_/\\|]+/g;

  function scoreProcess(question, queryGrams, item) {
    const cleaned = cleanText(question);
    let score = 0;
    const hits = [];
    (item.keywords || []).forEach(function (keyword) {
      const key = cleanText(keyword);
      if (key && cleaned.indexOf(key) >= 0) {
        score += 14 + Math.min(key.length, 8) * 1.6;
        hits.push(String(keyword));
      }
    });
    score += overlap(queryGrams, item.title) * 30;
    score += overlap(queryGrams, item.summary) * 8;
    score += overlap(queryGrams, (item.steps || []).join(" ")) * 5;
    score += overlap(queryGrams, [item.category, item.department, item.location].join(" ")) * 5;
    return { score: score, hits: hits };
  }

  function recognize(need) {
    const raw = String(need || "").trim();
    if (!raw) {
      return { matched: false, process: null, confidence: 0, keywords: [], alternatives: [], hint: "请先输入你的办事需求。", need: raw };
    }
    const queryGrams = grams(raw);
    const scored = D.PROCESSES.map(function (item) {
      const result = scoreProcess(raw, queryGrams, item);
      return { score: result.score, item: item, hits: result.hits };
    }).sort(function (a, b) { return b.score - a.score; });
    const best = scored[0];
    const alternatives = scored.slice(1, 4).filter(function (x) { return x.score > 0; }).slice(0, 2).map(function (x) {
      return { id: x.item.id, title: x.item.title };
    });
    if (!best || best.score < 10) {
      return {
        matched: false,
        process: null,
        confidence: 0,
        keywords: [],
        alternatives: alternatives,
        hint: "暂时没有匹配到具体流程。你可以换一种说法，例如「校园卡丢了」「想转专业」「生病没法参加考试」「医保怎么报销」。",
        need: raw
      };
    }
    return {
      matched: true,
      process: best.item,
      confidence: Math.round(Math.min(0.97, best.score / 40) * 100) / 100,
      keywords: best.hits,
      alternatives: alternatives,
      hint: "",
      need: raw
    };
  }

  function buildPlan(process) {
    const todos = [];
    (process.materials || []).forEach(function (material, i) {
      todos.push({ id: process.id + "-m" + (i + 1), label: "准备材料：" + material, kind: "材料", tone: "gold" });
    });
    (process.steps || []).forEach(function (step, i) {
      todos.push({ id: process.id + "-s" + (i + 1), label: step, kind: "步骤 " + (i + 1), tone: "blue" });
    });
    return { process: process, todos: todos };
  }

  function getServicePlan(processId, need) {
    const st = state();
    if (!st) return null;
    if (!st.servicePlans[processId]) {
      st.servicePlans[processId] = { checked: {}, need: need || "", created_at: nowStamp() };
      saveState();
    }
    return st.servicePlans[processId];
  }

  function toggleServiceTodo(processId, todoId) {
    const st = state();
    if (!st) return false;
    if (!st.servicePlans[processId]) st.servicePlans[processId] = { checked: {}, need: "", created_at: nowStamp() };
    const plan = st.servicePlans[processId];
    plan.checked[todoId] = !plan.checked[todoId];
    saveState();
    return plan.checked[todoId];
  }

  function resetServicePlan(processId) {
    const st = state();
    if (!st || !st.servicePlans[processId]) return;
    st.servicePlans[processId].checked = {};
    saveState();
  }

  /* ------------------------------------------------------------------ */
  /* 问答知识库匹配                                                     */
  /* ------------------------------------------------------------------ */
  function processAsEntry(process) {
    return {
      id: "process-" + process.id,
      title: process.title,
      intro: process.summary,
      steps: process.steps,
      tip: process.notice,
      source: process.source,
      links: [
        { label: "查看完整办事流程", href: "#page=services&need=" + encodeURIComponent(process.title) },
        { label: "个人事务中心", href: "#page=center" }
      ],
      tone: process.category === "医疗健康" ? "teal" : process.category === "奖助资助" ? "gold" : "blue",
      tag: "流程",
      keywords: process.keywords,
      question: process.title,
      isProcess: true
    };
  }

  function allEntries() {
    const list = D.QA_KB.concat(D.EXTRA_KB);
    D.PROCESSES.forEach(function (p) { list.push(processAsEntry(p)); });
    return list;
  }

  function scoreEntry(question, queryGrams, entry) {
    const cleaned = cleanText(question);
    let score = 0;
    const hits = [];
    (entry.keywords || []).forEach(function (keyword) {
      const key = cleanText(keyword);
      if (key && cleaned.indexOf(key) >= 0) {
        score += 14 + Math.min(key.length, 8) * 1.6;
        hits.push(String(keyword));
      }
    });
    score += overlap(queryGrams, entry.title) * 34;
    score += overlap(queryGrams, entry.question) * 20;
    score += overlap(queryGrams, entry.intro) * 10;
    score += overlap(queryGrams, (entry.steps || []).join(" ")) * 4;
    return { score: score, hits: hits };
  }

  const GREETINGS = ["你好", "您好", "嗨", "hello", "hi", "在吗", "早上好", "上午好", "下午好", "晚上好", "谢谢", "感谢"];
  const FALLBACK_QUESTIONS = [
    "校园卡丢了怎么补办？",
    "图书馆今天开到几点？",
    "怎么申请国家奖学金？",
    "宿舍东西坏了怎么报修？",
    "三校区校车怎么坐？"
  ];

  function makeFallback() {
    return {
      title: "我暂时没找到完全匹配的答案",
      intro: "模拟版使用的是本地关键词知识库（没有接入大模型 API），所以换个说法通常更容易命中。你可以试试下面这些问题。",
      steps: FALLBACK_QUESTIONS.slice(),
      tip: "如果问题涉及个人权益或紧急事项，请以学校主管部门最新通知为准，或直接联系辅导员 / 对应部门。",
      source: "河小智本地模拟知识库",
      links: [
        { label: "浏览办事流程", href: "#page=services" },
        { label: "查看通知公告", href: "#page=qa&view=notices" }
      ],
      tone: "violet",
      tag: "提示",
      matched: false
    };
  }

  function makeGreeting() {
    return {
      title: "你好，我是河小智 👋",
      intro: "我是河小智的本地模拟版，不需要联网、不需要 API Key。政策、办事流程、校园活动和个人事务都可以问我。",
      steps: [
        "直接输入问题，例如「校园卡丢了怎么补办？」。",
        "也可以点击下方的高频问题，或者打开「功能工作台」检索知识库。",
        "所有回答都来自本地演示知识库，并标注整理来源。"
      ],
      tip: "模拟版回答是关键词匹配生成的，正式版可接入大模型获得更自然的回答。",
      source: "河小智 · 模拟测试版",
      links: [
        { label: "看看校园活动", href: "#page=activities" },
        { label: "办事流程导航", href: "#page=services" }
      ],
      tone: "blue",
      tag: "问候",
      matched: true
    };
  }

  function matchUploadedDoc(question, queryGrams, docs) {
    if (!docs || !docs.length) return null;
    let best = null;
    docs.forEach(function (doc) {
      const text = String(doc.text || "");
      const score = overlap(queryGrams, text);
      if (!best || score > best.score) best = { doc: doc, score: score };
    });
    if (!best || best.score < 0.42) return null;
    const lines = best.doc.text.split(/\n+/).map(function (s) { return s.trim(); }).filter(function (s) { return s.length > 8; });
    const ranked = lines.map(function (line) {
      return { line: line, score: overlap(queryGrams, line) };
    }).sort(function (a, b) { return b.score - a.score; });
    const picked = ranked.filter(function (x) { return x.score > 0.2; }).slice(0, 5).map(function (x) { return x.line; });
    return {
      title: "在你上传的资料中找到了相关内容",
      intro: "以下内容摘自你本次上传的《" + best.doc.name + "》，仅用于当前模拟问答。",
      steps: picked.length ? picked : [String(best.doc.text).slice(0, 260) + "…"],
      tip: "上传资料只保存在本机浏览器中，不会发送到任何服务器。",
      source: "本地资料 · " + best.doc.name,
      links: [{ label: "管理上传资料", href: "#page=qa&view=upload" }],
      tone: "teal",
      tag: "资料",
      matched: true
    };
  }

  function findAnswer(question) {
    const raw = String(question || "").trim();
    const cleaned = cleanText(raw);
    if (!cleaned) return makeFallback();
    if (GREETINGS.some(function (g) { return cleaned === cleanText(g) || (cleaned.length <= 8 && cleaned.indexOf(cleanText(g)) >= 0); })) {
      return makeGreeting();
    }
    const queryGrams = grams(raw);
    const st = state();
    const docs = st && st.qa ? st.qa.docs : [];
    const uploaded = matchUploadedDoc(raw, queryGrams, docs);
    if (uploaded) return uploaded;

    const scored = allEntries().map(function (entry) {
      const r = scoreEntry(raw, queryGrams, entry);
      return { score: r.score, hits: r.hits, entry: entry };
    }).sort(function (a, b) { return b.score - a.score; });

    const best = scored[0];
    if (!best || best.score < 10) {
      return makeFallback();
    }
    const alternatives = scored.slice(1, 4).filter(function (x) { return x.score > 0; }).slice(0, 2);
    return {
      title: best.entry.title,
      intro: best.entry.intro,
      steps: best.entry.steps,
      tip: best.entry.tip,
      source: best.entry.source,
      links: best.entry.links || [],
      tone: best.entry.tone || "blue",
      tag: best.entry.tag || "问答",
      matched: true,
      confidence: Math.round(Math.min(0.97, best.score / 42) * 100) / 100,
      keywords: best.hits,
      alternatives: alternatives.map(function (x) { return { question: x.entry.question, title: x.entry.title }; }),
      followups: alternatives.map(function (x) { return x.entry.question; })
    };
  }

  function searchKB(query) {
    const q = String(query || "").trim();
    if (!q) return [];
    const queryGrams = grams(q);
    return allEntries().map(function (entry) {
      const r = scoreEntry(q, queryGrams, entry);
      return { score: r.score, entry: entry };
    }).filter(function (x) { return x.score > 0; })
      .sort(function (a, b) { return b.score - a.score; })
      .map(function (x) { return x.entry; });
  }

  function kbCount() {
    return D.QA_KB.length + D.EXTRA_KB.length + D.PROCESSES.length;
  }

  /* ------------------------------------------------------------------ */
  /* 问答会话                                                           */
  /* ------------------------------------------------------------------ */
  function qaState() {
    const st = state();
    if (!st) return null;
    if (!st.qa) st.qa = { messages: [], session: 1, docs: [] };
    return st.qa;
  }

  function askQuestion(question) {
    const qa = qaState();
    if (!qa) return null;
    const q = String(question || "").trim();
    if (!q) return null;
    const answer = findAnswer(q);
    qa.messages.push({ role: "user", text: q, time: nowStamp() });
    qa.messages.push({ role: "assistant", answer: answer, time: nowStamp() });
    if (qa.messages.length > 40) qa.messages = qa.messages.slice(-40);
    saveState();
    return answer;
  }

  function newQaSession() {
    const qa = qaState();
    if (!qa) return;
    qa.session = (Number(qa.session) || 1) + 1;
    qa.messages = [];
    saveState();
  }

  function clearQaHistory() {
    const qa = qaState();
    if (!qa) return;
    qa.messages = [];
    saveState();
  }

  function qaRounds() {
    const qa = qaState();
    return qa ? qa.messages.filter(function (m) { return m.role === "assistant"; }).length : 0;
  }

  function addQaDoc(name, text) {
    const qa = qaState();
    if (!qa) return { ok: false, message: "请先登录。" };
    if (qa.docs.length >= 5) return { ok: false, message: "最多上传 5 份资料，请先移除一份。" };
    const clean = String(text || "").slice(0, 60000);
    if (!clean.trim()) return { ok: false, message: "文件内容为空。" };
    qa.docs.push({ id: uid("doc"), name: String(name || "未命名资料"), text: clean, size: clean.length, added_at: nowStamp() });
    saveState();
    return { ok: true };
  }

  function removeQaDoc(id) {
    const qa = qaState();
    if (!qa) return;
    qa.docs = qa.docs.filter(function (d) { return d.id !== id; });
    saveState();
  }

  function qaDocs() {
    const qa = qaState();
    return qa ? qa.docs.slice() : [];
  }

  /* ------------------------------------------------------------------ */
  /* 重置全部模拟数据                                                   */
  /* ------------------------------------------------------------------ */
  function resetAll() {
    try {
      localStorage.removeItem(DB_KEY);
      localStorage.removeItem(SESSION_KEY);
    } catch (e) { /* ignore */ }
    DB = null;
    SESSION_MEM = null;
  }

  window.HXZ_STORE = {
    // 通用
    hashSecret: hashSecret,
    normalizeAnswer: normalizeAnswer,
    isoDate: isoDate,
    isoLocal: isoLocal,
    dateInputValue: dateInputValue,
    parseDue: parseDue,
    dueLabel: dueLabel,
    startOfToday: startOfToday,
    // 账号
    currentUser: currentUser,
    startSession: startSession,
    endSession: endSession,
    register: register,
    login: login,
    getSecurityQuestion: getSecurityQuestion,
    resetPassword: resetPassword,
    accountCount: accountCount,
    // 状态
    state: state,
    saveState: saveState,
    // 待办
    todoStats: todoStats,
    addTodo: addTodo,
    updateTodo: updateTodo,
    toggleTodo: toggleTodo,
    deleteTodo: deleteTodo,
    // 活动
    registrations: registrations,
    isRegistered: isRegistered,
    joinActivity: joinActivity,
    cancelActivity: cancelActivity,
    createdActivities: createdActivities,
    addCreatedActivity: addCreatedActivity,
    deleteCreatedActivity: deleteCreatedActivity,
    // 活动任务
    activityTasks: activityTasks,
    addActivityTask: addActivityTask,
    updateActivityTask: updateActivityTask,
    toggleActivityTask: toggleActivityTask,
    deleteActivityTask: deleteActivityTask,
    activityTaskStats: activityTaskStats,
    // 报修
    repairs: repairs,
    addRepair: addRepair,
    completeRepair: completeRepair,
    // 办事流程
    recognize: recognize,
    buildPlan: buildPlan,
    getServicePlan: getServicePlan,
    toggleServiceTodo: toggleServiceTodo,
    resetServicePlan: resetServicePlan,
    // 问答
    findAnswer: findAnswer,
    searchKB: searchKB,
    kbCount: kbCount,
    askQuestion: askQuestion,
    newQaSession: newQaSession,
    clearQaHistory: clearQaHistory,
    qaRounds: qaRounds,
    qaDocs: qaDocs,
    addQaDoc: addQaDoc,
    removeQaDoc: removeQaDoc,
    qaState: qaState,
    // 重置
    resetAll: resetAll
  };
})();
