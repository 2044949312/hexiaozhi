/* ==========================================================================
   河小智 · 模拟测试版共享 UI 层
   图标全部为内联 SVG（Feather 风格），不加载任何外部字体 / 图标库。
   ========================================================================== */
(function () {
  "use strict";

  const ICONS = {
    home: '<path d="m3 10 9-7 9 7v10a2 2 0 0 1-2 2h-4v-7H9v7H5a2 2 0 0 1-2-2z"/>',
    sparkles: '<path d="m12 3 1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7z"/><path d="m19 15 .9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9z"/>',
    route: '<circle cx="6" cy="19" r="3"/><path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/><circle cx="18" cy="5" r="3"/>',
    compass: '<circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>',
    "layout-grid": '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    "arrow-right": '<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/>',
    "arrow-up-right": '<path d="M7 17 17 7M8 7h9v9"/>',
    send: '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
    shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/>',
    zap: '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "book-open": '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    check: '<path d="m20 6-11 11-5-5"/>',
    "check-circle": '<circle cx="12" cy="12" r="10"/><path d="m8 12 3 3 5-6"/>',
    calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "trending-up": '<path d="m3 17 6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    x: '<path d="M18 6 6 18M6 6l12 12"/>',
    "chevron-right": '<path d="m9 18 6-6-6-6"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    users: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
    "map-pin": '<path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "alert-circle": '<circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>',
    info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
    flag: '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><path d="M4 22v-7"/>',
    chart: '<path d="M3 3v18h18"/><path d="m7 16 4-5 4 3 5-7"/>',
    award: '<circle cx="12" cy="8" r="6"/><path d="m8.2 13.9-1.7 7.1L12 18l5.5 3-1.7-7.1"/>',
    heart: '<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8l1.1 1.1L12 21l7.8-7.5 1.1-1.1a5.5 5.5 0 0 0-.1-7.8Z"/>',
    library: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/>',
    "credit-card": '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/>',
    wrench: '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.1 2.1-2.9-2.9z"/>',
    bus: '<path d="M6 17h12M4 17V8a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v9M4 10h16"/><circle cx="7" cy="19.5" r="1.5"/><circle cx="17" cy="19.5" r="1.5"/>',
    "file-text": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>',
    message: '<path d="M21 11.5a8.5 8.5 0 0 1-8.5 8.5 9 9 0 0 1-3.9-.9L3 21l1.9-5.6A8.5 8.5 0 1 1 21 11.5Z"/>',
    trophy: '<path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0z"/><path d="M17 5h3v2a3 3 0 0 1-3 3M7 5H4v2a3 3 0 0 0 3 3"/>',
    search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 0 1-3.4 0"/>',
    trash: '<path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6M10 11v6M14 11v6"/>',
    edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    upload: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m17 8-5-5-5 5M12 3v12"/>',
    database: '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.7 4 3 9 3s9-1.3 9-3V5"/><path d="M3 12c0 1.7 4 3 9 3s9-1.3 9-3"/>',
    flame: '<path d="M12 22c4 0 7-2.9 7-7 0-3.2-2-6.1-4.5-8.2.3 2.2-.7 3.8-1.8 4.2.3-3.8-1.7-6.7-3.7-8.5.3 4.2-1.2 5.8-2.7 7.8C4.8 12.5 5 14.7 5 15c0 4.1 3 7 7 7Z"/>',
    target: '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "graduation-cap": '<path d="m22 10-10-5L2 10l10 5 10-5Z"/><path d="M6 12v5c0 1.7 2.7 3 6 3s6-1.3 6-3v-5"/>',
    code: '<path d="m16 18 6-6-6-6M8 6l-6 6 6 6"/>',
    music: '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>',
    cpu: '<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 2v2M15 2v2M9 20v2M15 20v2M2 9h2M2 15h2M20 9h2M20 15h2"/>',
    activity: '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    "id-card": '<rect x="2" y="4" width="20" height="16" rx="2"/><circle cx="8" cy="10" r="2"/><path d="M5 16c0-1.7 1.3-3 3-3s3 1.3 3 3M14 9h4M14 13h4"/>',
    globe: '<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 0 1 0 20 15 15 0 0 1 0-20Z"/>',
    bookmark: '<path d="M19 21 12 16 5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>',
    filter: '<path d="M22 3H2l8 9.5V19l4 2v-8.5z"/>',
    paperclip: '<path d="m21.4 11.05-9.2 9.2a6 6 0 0 1-8.5-8.5l9.2-9.2a4 4 0 0 1 5.7 5.7l-9.2 9.2a2 2 0 0 1-2.8-2.8l8.5-8.5"/>',
    refresh: '<path d="M21 12a9 9 0 1 1-2.6-6.4"/><path d="M21 3v6h-6"/>',
    link: '<path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7"/><path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7"/>',
    lock: '<rect x="3" y="11" width="18" height="10" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    user: '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "log-out": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5M21 12H9"/>',
    menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
    layers: '<path d="m12 2 9 5-9 5-9-5z"/><path d="m3 12 9 5 9-5M3 17l9 5 9-5"/>',
    list: '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    clipboard: '<rect x="4" y="4" width="16" height="18" rx="2"/><path d="M9 4V2h6v2M8 11h8M8 15h6"/>',
    briefcase: '<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>',
    coffee: '<path d="M18 8h1a4 4 0 0 1 0 8h-1"/><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4Z"/><path d="M6 2v2M10 2v2M14 2v2"/>',
    presentation: '<path d="M2 3h20M4 3v11h16V3M12 14v5M8 22l4-3 4 3"/>',
    star: '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
    "external-link": '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><path d="M15 3h6v6M10 14 21 3"/>',
    eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    leaf: '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.5 19 2c1 2 2 4.2 2 8 0 5.5-4.8 10-10 10Z"/><path d="M2 21c0-3 1.9-5.4 4-6"/>',
    "shopping-bag": '<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/><path d="M3 6h18M16 10a4 4 0 0 1-8 0"/>',
    key: '<circle cx="7.5" cy="15.5" r="5.5"/><path d="m12 11 8-8M17 6l2 2M15 8l2 2"/>',
    "file-check": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M9 15l2 2 4-4"/>',
    "help-circle": '<circle cx="12" cy="12" r="10"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 2.5-3 4M12 17h.01"/>'
  };

  const TONES = ["blue", "teal", "gold", "violet", "rose", "green"];

  function esc(value) {
    return String(value === null || value === undefined ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function icon(name, cls) {
    const body = ICONS[name] || ICONS.sparkles;
    return '<svg class="' + esc(cls || "") + '" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + body + "</svg>";
  }

  function toneOf(t) {
    return TONES.indexOf(t) >= 0 ? t : "blue";
  }

  function iconTile(name, tone, extra) {
    return '<span class="icon-tile ' + esc(toneOf(tone)) + " " + esc(extra || "") + '">' + icon(name) + "</span>";
  }

  function pill(text, cls) {
    return '<span class="pill ' + esc(cls || "") + '">' + esc(text) + "</span>";
  }

  function tag(text, cls) {
    return '<span class="tag ' + esc(cls || "") + '">' + esc(text) + "</span>";
  }

  function emptyState(title, desc, actionHtml, iconName, tone) {
    return '<div class="empty">' + iconTile(iconName || "sparkles", tone || "blue") +
      "<h4>" + esc(title) + "</h4><p>" + esc(desc) + "</p>" +
      (actionHtml ? '<div class="mt-14">' + actionHtml + "</div>" : "") + "</div>";
  }

  function nl2br(text) {
    return esc(text).replace(/\r?\n/g, "<br>");
  }

  function timeHM(value) {
    const d = value instanceof Date ? value : new Date(String(value || "").replace(" ", "T"));
    if (isNaN(d.getTime())) return "";
    return String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0");
  }

  function dateCn(value) {
    if (!value) return "";
    const m = String(value).match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (m) return parseInt(m[2], 10) + " 月 " + parseInt(m[3], 10) + " 日";
    return String(value);
  }

  function weekdayCn(value) {
    const d = value ? new Date(String(value).replace(" ", "T")) : new Date();
    if (isNaN(d.getTime())) return "";
    return "周" + "日一二三四五六".charAt(d.getDay());
  }

  function initials(name) {
    const s = String(name || "河").trim();
    return s ? s.charAt(0).toUpperCase() : "河";
  }

  function todayInput(offset) {
    const d = new Date();
    d.setDate(d.getDate() + (offset || 0));
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }

  function pageHead(title, subtitle, eyebrow, rightHtml) {
    return '<div class="page-head' + (rightHtml ? " page-head-row" : "") + '">' +
      "<div>" + (eyebrow ? '<div class="eyebrow">' + esc(eyebrow) + "</div>" : "") +
      "<h1>" + esc(title) + "</h1>" +
      (subtitle ? "<p>" + esc(subtitle) + "</p>" : "") + "</div>" +
      (rightHtml || "") + "</div>";
  }

  function modalHead(iconName, tone, title, subtitle) {
    return '<div class="modal-head">' + iconTile(iconName, tone) +
      "<div><h3>" + esc(title) + "</h3>" +
      (subtitle ? "<p>" + esc(subtitle) + "</p>" : "") + "</div>" +
      '<button type="button" class="icon-btn modal-close" data-action="modal-close" aria-label="关闭">' + icon("x") + "</button></div>";
  }

  function toast(message, type, title) {
    const root = document.getElementById("toast-root");
    if (!root) return;
    const el = document.createElement("div");
    el.className = "toast " + (type || "success");
    const ico = type === "error" ? "alert-circle" : type === "warn" ? "info" : "check-circle";
    el.innerHTML = icon(ico) + "<div>" + (title ? "<strong>" + esc(title) + "</strong>" : "") + "<span>" + esc(message) + "</span></div>";
    root.appendChild(el);
    window.setTimeout(function () {
      el.classList.add("out");
      window.setTimeout(function () { el.remove(); }, 240);
    }, 3400);
  }

  let confirmHandler = null;

  function openModal(inner, size) {
    const root = document.getElementById("modal-root");
    if (!root) return;
    root.innerHTML = '<div class="modal-backdrop" data-backdrop="1"><div class="modal ' + esc(size || "") + '" role="dialog" aria-modal="true">' + inner + "</div></div>";
    document.body.classList.add("modal-open");
  }

  function closeModal() {
    const root = document.getElementById("modal-root");
    if (root) root.innerHTML = "";
    document.body.classList.remove("modal-open");
  }

  function confirmDialog(opts) {
    confirmHandler = opts.onConfirm || null;
    openModal(
      modalHead("alert-circle", opts.danger ? "rose" : "gold", opts.title || "请确认", opts.subtitle || "") +
      '<div class="confirm-text">' + (opts.html || esc(opts.message || "")) + "</div>" +
      '<div class="modal-foot"><button type="button" class="btn btn-soft" data-action="modal-close">取消</button>' +
      '<button type="button" class="btn ' + (opts.danger ? "btn-danger" : "btn-primary") + '" data-action="confirm-modal">' + esc(opts.confirmLabel || "确定") + "</button></div>",
      "narrow"
    );
  }

  function resolveConfirm() {
    const fn = confirmHandler;
    confirmHandler = null;
    closeModal();
    if (typeof fn === "function") fn();
  }

  function showFormError(form, message) {
    if (!form) return;
    let box = form.querySelector(".form-error");
    if (!box) {
      box = document.createElement("div");
      box.className = "form-error";
      box.innerHTML = icon("alert-circle") + "<span></span>";
      const actions = form.querySelector(".form-actions");
      if (actions) form.insertBefore(box, actions);
      else form.appendChild(box);
    }
    const span = box.querySelector("span");
    if (span) span.textContent = message;
    box.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  function progress(value, tone) {
    const v = Math.max(0, Math.min(100, Number(value) || 0));
    return '<div class="progress-track"><div class="progress-fill ' + esc(tone || "") + '" style="width:' + v + '%"></div></div>';
  }

  function priorityMeta(priority) {
    const map = {
      high: { label: "高优先级", short: "高", cls: "high" },
      medium: { label: "中优先级", short: "中", cls: "mid" },
      low: { label: "低优先级", short: "低", cls: "low" }
    };
    return map[priority] || map.medium;
  }

  function activityPriority(priority) {
    return priority === "高" ? "high" : priority === "低" ? "low" : "mid";
  }

  function statusTag(status) {
    if (status === "已完成") return tag(status, "green");
    if (status === "维修中") return tag(status, "gold");
    return tag(status, "blue");
  }

  function chipLink(label, href, active) {
    return '<a class="cat-chip' + (active ? " active" : "") + '" href="' + esc(href) + '">' + esc(label) + "</a>";
  }

  function taskRow(opts) {
    // opts: {title, done, priority, category, due, place, note, progress, onToggle, onEdit, onDelete}
    return '<div class="task-item' + (opts.done ? " done" : "") + '">' +
      '<button type="button" class="checkbox' + (opts.done ? " on" : "") + '" data-action="' + esc(opts.toggleAction) + '" data-id="' + esc(opts.id) + '" aria-label="' + (opts.done ? "标记为未完成" : "标记为完成") + '">' + icon("check") + "</button>" +
      '<div class="task-main"><div class="task-title">' + esc(opts.title) + "</div>" +
      '<div class="task-meta">' +
      (opts.priority ? '<span class="priority ' + esc(activityPriority(opts.priority)) + '">' + esc(opts.priority) + "</span>" : "") +
      (opts.category ? "<span>" + icon("bookmark") + esc(opts.category) + "</span>" : "") +
      (opts.due ? "<span>" + icon("clock") + esc(opts.due) + "</span>" : "") +
      (opts.place ? "<span>" + icon("map-pin") + esc(opts.place) + "</span>" : "") +
      "</div>" +
      (opts.note ? '<div class="task-note">' + esc(opts.note) + "</div>" : "") + "</div>" +
      '<div class="task-side">' +
      (opts.progress !== undefined ? '<div class="pct">' + esc(opts.progress) + "%</div>" +
        '<div class="progress-track"><div class="progress-fill' + (opts.done ? " green" : "") + '" style="width:' + Math.max(0, Math.min(100, opts.progress)) + '%"></div></div>' : "") +
      '<div class="task-actions">' +
      (opts.editAction ? '<button type="button" class="btn-icon" data-action="' + esc(opts.editAction) + '" data-type="' + esc(opts.type || "") + '" data-id="' + esc(opts.id) + '" aria-label="编辑">' + icon("edit") + "</button>" : "") +
      (opts.deleteAction ? '<button type="button" class="btn-icon" data-action="' + esc(opts.deleteAction) + '" data-type="' + esc(opts.type || "") + '" data-id="' + esc(opts.id) + '" aria-label="删除">' + icon("trash") + "</button>" : "") +
      "</div></div></div>";
  }

  function ring(id, percent, label, sublabel, tone) {
    const p = Math.max(0, Math.min(100, Number(percent) || 0));
    const r = 56;
    const c = 2 * Math.PI * r;
    const dash = (p / 100 * c).toFixed(1) + " " + c.toFixed(1);
    return '<div class="ring"><svg viewBox="0 0 132 132">' +
      '<defs><linearGradient id="' + esc(id) + '" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="' + (tone === "teal" ? "#5ee0d1" : "#7ea7f5") + '"/><stop offset="100%" stop-color="' + (tone === "teal" ? "#0f9e8e" : "#2f63ef") + '"/></linearGradient></defs>' +
      '<circle class="bg" cx="66" cy="66" r="56"></circle>' +
      '<circle class="fg" cx="66" cy="66" r="56" stroke="url(#' + esc(id) + ')" stroke-dasharray="' + dash + '"></circle>' +
      '</svg><div class="ring-label"><strong>' + esc(label) + "</strong><span>" + esc(sublabel || "") + "</span></div></div>";
  }

  window.HXZ_UI = {
    icon: icon,
    esc: esc,
    iconTile: iconTile,
    toneOf: toneOf,
    pill: pill,
    tag: tag,
    emptyState: emptyState,
    nl2br: nl2br,
    timeHM: timeHM,
    dateCn: dateCn,
    weekdayCn: weekdayCn,
    initials: initials,
    todayInput: todayInput,
    pageHead: pageHead,
    modalHead: modalHead,
    toast: toast,
    openModal: openModal,
    closeModal: closeModal,
    confirmDialog: confirmDialog,
    resolveConfirm: resolveConfirm,
    showFormError: showFormError,
    progress: progress,
    priorityMeta: priorityMeta,
    activityPriority: activityPriority,
    statusTag: statusTag,
    chipLink: chipLink,
    taskRow: taskRow,
    ring: ring
  };
})();
