# -*- coding: utf-8 -*-
"""河小智 · 全局视觉系统（Streamlit 注入 CSS）。"""

from __future__ import annotations

import streamlit as st

CSS = r"""
:root{
  --bg:#F4F7FB;
  --surface:#FFFFFF;
  --surface-soft:#F8FAFF;
  --ink:#0F1B33;
  --ink-soft:#2C3A55;
  --muted:#64748B;
  --muted-light:#94A3B8;
  --primary:#1D4ED8;
  --primary-2:#2563EB;
  --primary-soft:#EEF4FF;
  --teal:#0EA5A4;
  --teal-2:#14B8A6;
  --teal-soft:#ECFDF9;
  --gold:#F5B942;
  --gold-soft:#FFF8E8;
  --violet:#7C3AED;
  --violet-soft:#F5F0FF;
  --rose:#E11D48;
  --rose-soft:#FFF1F4;
  --green:#16A34A;
  --border:#E7EDF6;
  --border-strong:#D7E2F2;
  --shadow-xs:0 2px 8px rgba(15,27,51,.035);
  --shadow-sm:0 10px 28px rgba(15,27,51,.055);
  --shadow-md:0 20px 50px rgba(15,27,51,.09);
  --shadow-lg:0 32px 80px rgba(15,42,92,.18);
  --radius:22px;
  --font:"Microsoft YaHei UI","Microsoft YaHei","PingFang SC","Noto Sans SC","Segoe UI",system-ui,-apple-system,sans-serif;
}

/* ---------- Streamlit 壳层 ---------- */
html, body, .stApp, [data-testid="stAppViewContainer"]{
  font-family:var(--font);
  color:var(--ink);
  background:
    radial-gradient(1100px 560px at 95% -12%, rgba(37,99,235,.11), transparent 62%),
    radial-gradient(900px 520px at -8% 8%, rgba(20,184,166,.09), transparent 58%),
    var(--bg);
}
[data-testid="stAppViewContainer"] > .main{background:transparent;}
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], [data-testid="stFooter"], #MainMenu, footer[data-testid="stFooter"]{
  display:none!important;
}
[data-testid="stSidebar"]{display:none!important;}
[data-testid="stAppViewBlockContainer"], [data-testid="stMainBlockContainer"]{
  max-width:1260px;
  padding:1.15rem 2rem 2.4rem;
  margin:0 auto;
}
[data-testid="stVerticalBlock"]{gap:.65rem;}
[data-testid="stMain"]{scroll-behavior:smooth;}
[data-testid="stMain"] > div{background:transparent;}
.stMarkdown, [data-testid="stMarkdownContainer"]{color:var(--ink);}
a{color:inherit;}
::selection{background:rgba(37,99,235,.18);}
::-webkit-scrollbar{width:10px;height:10px;}
::-webkit-scrollbar-thumb{background:#CBD8EA;border-radius:20px;border:3px solid var(--bg);}
::-webkit-scrollbar-track{background:transparent;}

/* ---------- 顶部导航 ---------- */
.topbar{
  position:sticky;top:0;z-index:999;
  display:flex;align-items:center;justify-content:space-between;gap:22px;
  margin:0 -10px 16px;padding:11px 10px 10px;
  background:linear-gradient(180deg, rgba(244,247,251,.97) 0%, rgba(244,247,251,.88) 72%, rgba(244,247,251,0) 100%);
  backdrop-filter:blur(16px);
}
.brand{display:flex;align-items:center;gap:11px;text-decoration:none;color:var(--ink);flex:0 0 auto;}
.brand-logo{
  width:42px;height:42px;border-radius:13px;display:block;object-fit:cover;
  box-shadow:0 8px 20px rgba(29,78,216,.23);
}
.brand-text{display:flex;flex-direction:column;line-height:1.08;}
.brand-text strong{font-size:20px;font-weight:800;letter-spacing:.04em;}
.brand-text small{font-size:9px;color:var(--muted);letter-spacing:.16em;margin-top:4px;font-weight:600;}
.main-nav{
  display:flex;align-items:center;gap:3px;padding:4px;
  background:rgba(255,255,255,.72);border:1px solid rgba(226,234,246,.95);
  border-radius:15px;box-shadow:var(--shadow-xs);
}
.nav-link{
  padding:8px 15px;border-radius:11px;text-decoration:none;color:#4A5873;
  font-size:13.5px;font-weight:650;white-space:nowrap;transition:all .18s ease;
}
.nav-link:hover{background:#F0F5FF;color:var(--primary);}
.nav-link.active{
  color:#fff;background:linear-gradient(135deg,#1D4ED8,#2F6BFF);
  box-shadow:0 7px 16px rgba(29,78,216,.25);
}
.top-actions{display:flex;align-items:center;gap:10px;flex:0 0 auto;}
.ai-status{
  display:inline-flex;align-items:center;gap:6px;font-size:10.5px;font-weight:700;color:#0F766E;
  background:#ECFDF9;border:1px solid #CBF5EB;border-radius:999px;padding:6px 9px;
}
.ai-status i{width:6px;height:6px;border-radius:50%;background:#14B8A6;box-shadow:0 0 0 4px rgba(20,184,166,.13);animation:pulse 2.2s infinite;}
.icon-btn{
  width:38px;height:38px;border-radius:12px;display:grid;place-items:center;position:relative;
  color:#53627C;background:rgba(255,255,255,.78);border:1px solid var(--border);text-decoration:none;
  transition:all .18s ease;
}
.icon-btn:hover{color:var(--primary);border-color:#C9DAF9;transform:translateY(-1px);}
.logout-btn:hover{color:#BE123C;background:#FFF5F6;border-color:#FBD5DB;}
.notify-dot{position:absolute;top:9px;right:9px;width:6px;height:6px;background:#EF4444;border-radius:50%;border:1.5px solid #fff;}
.user-chip{
  display:flex;align-items:center;gap:9px;padding:4px 11px 4px 4px;text-decoration:none;
  background:rgba(255,255,255,.82);border:1px solid var(--border);border-radius:999px;
  transition:all .18s ease;box-shadow:var(--shadow-xs);
}
.user-chip:hover{border-color:#C9DAF9;transform:translateY(-1px);}
.avatar{
  width:32px;height:32px;border-radius:50%;display:grid;place-items:center;color:#fff;
  font-size:13px;font-weight:800;background:linear-gradient(135deg,#1D4ED8,#14B8A6);
  box-shadow:inset 0 0 0 2px rgba(255,255,255,.25);
}
.user-meta{display:flex;flex-direction:column;line-height:1.1;}
.user-meta b{font-size:12px;color:var(--ink);}
.user-meta small{font-size:8.5px;color:var(--muted);margin-top:3px;}
.mobile-nav{display:none;}

/* ---------- 首页 Hero ---------- */
.hero{
  position:relative;isolation:isolate;overflow:hidden;
  display:grid;grid-template-columns:minmax(0,1.22fr) minmax(300px,.78fr);
  gap:18px;min-height:424px;padding:46px 48px 42px;
  border-radius:30px;color:#fff;
  background:
    radial-gradient(700px 420px at 82% 18%, rgba(20,184,166,.28), transparent 62%),
    radial-gradient(500px 380px at 15% 110%, rgba(37,99,235,.5), transparent 65%),
    linear-gradient(125deg,#081733 0%,#0D2A62 46%,#0A6076 100%);
  box-shadow:0 32px 80px rgba(15,42,92,.24);
  animation:fadeUp .55s ease both;
}
.hero::before{
  content:"";position:absolute;inset:0;z-index:-1;pointer-events:none;
  background-image:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px);
  background-size:54px 54px;
  mask-image:radial-gradient(circle at 55% 45%, #000 10%, transparent 74%);
  -webkit-mask-image:radial-gradient(circle at 55% 45%, #000 10%, transparent 74%);
}
.hero::after{
  content:"";position:absolute;width:420px;height:420px;right:-110px;bottom:-220px;z-index:-1;
  border-radius:50%;border:1px solid rgba(255,255,255,.12);
  box-shadow:0 0 0 55px rgba(255,255,255,.025),0 0 0 110px rgba(255,255,255,.018);
}
.hero-copy{position:relative;z-index:2;display:flex;flex-direction:column;align-items:flex-start;justify-content:center;min-width:0;}
.eyebrow{
  display:inline-flex;align-items:center;gap:8px;
  font-size:10.5px;font-weight:750;letter-spacing:.15em;text-transform:uppercase;
  color:rgba(255,255,255,.72);
}
.eyebrow-dot{
  width:7px;height:7px;border-radius:50%;background:#3EE6C4;
  box-shadow:0 0 0 4px rgba(62,230,196,.14);animation:pulse 2.2s infinite;
}
.hero h1{
  margin:17px 0 14px;font-size:clamp(31px,3.4vw,45px);line-height:1.17;letter-spacing:-.05em;
  font-weight:850;color:#fff;
}
.hero h1 .grad{
  background:linear-gradient(95deg,#8EF7E1 0%,#A9D3FF 48%,#FFD580 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent;
}
.hero-desc{
  max-width:570px;margin:0 0 4px;font-size:14.5px;line-height:1.9;color:rgba(255,255,255,.71);
}
.hero-desc b{color:#fff;font-weight:700;}
.ai-form{
  width:100%;max-width:590px;margin-top:26px;display:flex;align-items:center;gap:7px;
  padding:7px 7px 7px 10px;border-radius:18px;background:rgba(255,255,255,.98);
  box-shadow:0 18px 38px rgba(3,15,40,.28),inset 0 0 0 1px rgba(255,255,255,.5);
}
.ai-form-icon{color:var(--primary);display:grid;place-items:center;padding-left:4px;flex:0 0 auto;}
.ai-form input{
  flex:1;min-width:0;border:0;outline:0;background:transparent;color:var(--ink);
  font-family:var(--font);font-size:14px;padding:10px 4px;
}
.ai-form input::placeholder{color:#8A99B0;}
.ai-form button{
  flex:0 0 auto;display:inline-flex;align-items:center;gap:7px;border:0;cursor:pointer;
  border-radius:13px;padding:12px 17px;color:#fff;font-family:var(--font);font-size:13px;font-weight:750;
  background:linear-gradient(135deg,#1D4ED8,#2563EB);box-shadow:0 8px 18px rgba(29,78,216,.3);
  transition:all .2s ease;
}
.ai-form button:hover{transform:translateY(-1px);box-shadow:0 12px 22px rgba(29,78,216,.42);}
.suggest-row{display:flex;flex-wrap:wrap;gap:7px;margin-top:12px;max-width:630px;}
.suggest-chip{
  display:inline-flex;align-items:center;gap:5px;padding:7px 11px;border-radius:999px;
  border:1px solid rgba(255,255,255,.17);background:rgba(255,255,255,.075);
  color:rgba(255,255,255,.8)!important;font-size:11.5px;text-decoration:none;transition:all .18s ease;
  backdrop-filter:blur(6px);
}
.suggest-chip:visited{color:rgba(255,255,255,.8)!important;}
.hero a.suggest-chip:hover{background:rgba(255,255,255,.16);color:#fff!important;border-color:rgba(255,255,255,.28);}
.hero-trust{display:flex;align-items:center;gap:7px;margin-top:18px;font-size:10.5px;color:rgba(255,255,255,.5);}
.hero-trust svg{color:#7BE8D4;}
.hero-visual{position:relative;z-index:2;display:grid;place-items:center;min-height:340px;}
.hero-orbit{
  position:absolute;width:410px;height:410px;border-radius:50%;
  border:1px solid rgba(255,255,255,.13);
  display:grid;place-items:center;
}
.hero-orbit.orbit-2{width:302px;height:302px;border-style:dashed;border-color:rgba(255,255,255,.18);animation:spin 38s linear infinite;}
.hero-orbit.orbit-3{width:490px;height:490px;border-color:rgba(255,255,255,.06);}
.orbit-dot{position:absolute;width:7px;height:7px;border-radius:50%;background:#5EEAD4;top:34px;right:82px;box-shadow:0 0 15px #5EEAD4;}
.hero-mascot{position:relative;z-index:3;width:min(100%,370px);filter:drop-shadow(0 30px 36px rgba(1,8,23,.4));animation:floaty 6.5s ease-in-out infinite;}
.hero-mascot img{display:block;width:100%;height:auto;}
.hero-mascot .img-fallback{
  width:310px;height:310px;border-radius:44% 56% 50% 50%;display:grid;place-items:center;
  background:linear-gradient(145deg,rgba(255,255,255,.2),rgba(20,184,166,.12));
  border:1px solid rgba(255,255,255,.22);color:#CCFBF1;
}
.float-card{
  position:absolute;z-index:4;display:flex;align-items:center;gap:9px;padding:10px 12px;
  border-radius:15px;border:1px solid rgba(255,255,255,.2);
  background:rgba(10,30,60,.55);backdrop-filter:blur(12px);
  box-shadow:0 12px 26px rgba(2,10,30,.22);font-size:10.5px;color:rgba(255,255,255,.78);
}
.float-card b{display:block;color:#fff;font-size:11.5px;margin-bottom:2px;}
.float-card .float-icon{width:30px;height:30px;border-radius:9px;background:rgba(94,234,212,.16);color:#5EEAD4;display:grid;place-items:center;}
.float-card.top{top:22px;right:2px;}
.float-card.bottom{bottom:24px;left:-4px;}
.float-card.bottom .float-icon{background:rgba(245,185,66,.16);color:#F5B942;}

/* ---------- 指标条 ---------- */
.metric-strip{
  position:relative;z-index:5;display:grid;grid-template-columns:repeat(4,1fr);
  margin:-28px 34px 34px;background:#fff;border:1px solid var(--border);
  border-radius:21px;box-shadow:0 18px 45px rgba(15,27,51,.09);overflow:hidden;
  animation:fadeUp .6s .08s ease both;
}
.metric{display:flex;align-items:center;gap:12px;padding:15px 20px;border-right:1px solid #EFF3F9;}
.metric:last-child{border-right:0;}
.metric-icon{width:38px;height:38px;border-radius:11px;display:grid;place-items:center;flex:0 0 auto;background:var(--primary-soft);color:var(--primary);}
.metric:nth-child(2) .metric-icon{background:var(--teal-soft);color:#0F9488;}
.metric:nth-child(3) .metric-icon{background:var(--gold-soft);color:#C88B15;}
.metric:nth-child(4) .metric-icon{background:var(--violet-soft);color:var(--violet);}
.metric-value{font-size:19px;font-weight:800;line-height:1;letter-spacing:-.02em;color:var(--ink);}
.metric-value small{font-size:10px;font-weight:600;color:var(--muted-light);margin-left:3px;letter-spacing:0;}
.metric-label{font-size:10.5px;color:var(--muted);margin-top:5px;}

/* ---------- 区块标题 ---------- */
.section-head{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;margin:0 2px 17px;}
.section-eyebrow{
  display:inline-flex;align-items:center;gap:5px;font-size:10px;font-weight:750;
  letter-spacing:.14em;text-transform:uppercase;color:var(--primary);margin-bottom:7px;
}
.section-title{margin:0;font-size:25px;line-height:1.25;font-weight:830;letter-spacing:-.025em;color:var(--ink);}
.section-sub{margin:6px 0 0;font-size:12px;line-height:1.7;color:var(--muted);}
.section-link{
  display:inline-flex;align-items:center;gap:5px;flex:0 0 auto;padding:8px 11px;border-radius:10px;
  color:var(--primary);font-size:12px;font-weight:700;text-decoration:none;transition:all .18s ease;
}
.section-link:hover{background:var(--primary-soft);gap:8px;}

/* ---------- 核心功能 ---------- */
.feature-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;}
.feature-card{
  position:relative;overflow:hidden;display:flex;flex-direction:column;
  min-height:200px;padding:21px 20px 18px;border-radius:22px;
  background:#fff;border:1px solid var(--border);box-shadow:var(--shadow-sm);
  text-decoration:none;color:inherit;transition:transform .22s ease,box-shadow .22s ease,border-color .22s ease;
}
.feature-card::after{
  content:"";position:absolute;width:150px;height:150px;right:-70px;top:-70px;border-radius:50%;
  background:radial-gradient(circle,rgba(37,99,235,.11),transparent 68%);transition:transform .3s ease;
}
.feature-card:hover{transform:translateY(-5px);border-color:#D3E2FB;box-shadow:0 20px 44px rgba(15,27,51,.11);}
.feature-card:hover::after{transform:scale(1.35);}
.feature-card.teal::after{background:radial-gradient(circle,rgba(20,184,166,.14),transparent 68%);}
.feature-card.gold::after{background:radial-gradient(circle,rgba(245,185,66,.18),transparent 68%);}
.feature-card.violet::after{background:radial-gradient(circle,rgba(124,58,237,.12),transparent 68%);}
.feature-icon{
  width:47px;height:47px;border-radius:14px;display:grid;place-items:center;margin-bottom:16px;
  background:linear-gradient(140deg,#E9F1FF,#F7FAFF);color:var(--primary);
  border:1px solid #DFEAFF;box-shadow:inset 0 1px 0 rgba(255,255,255,.8);
}
.feature-card.teal .feature-icon{background:linear-gradient(140deg,#E8FBF7,#F6FFFD);color:#0D9488;border-color:#D4F4EE;}
.feature-card.gold .feature-icon{background:linear-gradient(140deg,#FFF6DE,#FFFCF4);color:#C88B15;border-color:#FAEBC7;}
.feature-card.violet .feature-icon{background:linear-gradient(140deg,#F2ECFF,#FBF8FF);color:#7C3AED;border-color:#E8DDFF;}
.feature-title{font-size:16.5px;font-weight:800;color:var(--ink);letter-spacing:-.01em;}
.feature-desc{font-size:12px;line-height:1.75;color:var(--muted);margin:7px 0 15px;}
.feature-bottom{display:flex;align-items:center;justify-content:space-between;margin-top:auto;}
.feature-tag{font-size:9.5px;font-weight:700;color:var(--muted);background:#F5F7FB;border-radius:999px;padding:4px 8px;}
.feature-arrow{
  width:27px;height:27px;border-radius:9px;display:grid;place-items:center;color:var(--primary);
  background:var(--primary-soft);transition:all .2s ease;
}
.feature-card:hover .feature-arrow{background:var(--primary);color:#fff;transform:translateX(2px);}
.growth-banner{
  position:relative;overflow:hidden;display:flex;align-items:center;gap:15px;
  margin-top:15px;padding:17px 21px;border-radius:19px;text-decoration:none;color:inherit;
  background:linear-gradient(110deg,#EEF5FF 0%,#F0FCFA 58%,#FFF9ED 100%);
  border:1px solid #DAE9FC;box-shadow:var(--shadow-xs);transition:all .2s ease;
}
.growth-banner:hover{transform:translateY(-2px);box-shadow:var(--shadow-sm);}
.growth-icon{width:43px;height:43px;border-radius:13px;display:grid;place-items:center;flex:0 0 auto;background:#fff;color:var(--primary);box-shadow:0 6px 16px rgba(29,78,216,.12);}
.growth-copy{min-width:0;flex:1;}
.growth-copy b{display:block;font-size:14.5px;font-weight:800;color:var(--ink);}
.growth-copy span{display:block;font-size:11px;color:var(--muted);margin-top:3px;}
.growth-stats{display:flex;align-items:center;gap:18px;flex:0 0 auto;}
.growth-stat{font-size:10px;color:var(--muted);}
.growth-stat strong{display:block;font-size:16px;color:var(--ink);line-height:1.1;margin-bottom:3px;}
.growth-cta{display:inline-flex;align-items:center;gap:5px;padding:9px 13px;border-radius:10px;background:#fff;color:var(--primary);font-size:11.5px;font-weight:750;border:1px solid #D8E6FB;flex:0 0 auto;}

/* ---------- 活动卡片 ---------- */
.activity-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;}
.activity-grid.two{grid-template-columns:repeat(2,1fr);}
.activity-card{
  display:flex;flex-direction:column;overflow:hidden;border-radius:23px;text-decoration:none;color:inherit;
  background:#fff;border:1px solid var(--border);box-shadow:var(--shadow-sm);
  transition:transform .24s ease,box-shadow .24s ease,border-color .24s ease;
}
.activity-card:hover{transform:translateY(-6px);box-shadow:0 24px 48px rgba(15,27,51,.12);border-color:#D5E2F6;}
.activity-cover{position:relative;aspect-ratio:16/9;overflow:hidden;background:linear-gradient(135deg,#0F2A5C,#14B8A6);}
.activity-cover img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .5s ease;}
.activity-card:hover .activity-cover img{transform:scale(1.045);}
.activity-cover .img-fallback{
  width:100%;height:100%;display:grid;place-items:center;color:rgba(255,255,255,.85);
  background:linear-gradient(135deg,#143C8F,#0E7490);
}
.cover-badges{position:absolute;top:12px;left:12px;right:12px;display:flex;justify-content:space-between;align-items:center;z-index:2;}
.cover-date{
  display:inline-flex;align-items:center;gap:5px;padding:6px 9px;border-radius:9px;
  background:rgba(8,20,40,.48);border:1px solid rgba(255,255,255,.22);backdrop-filter:blur(10px);
  font-size:10px;font-weight:700;color:#fff;
}
.cover-hot{display:inline-flex;align-items:center;gap:4px;padding:6px 9px;border-radius:9px;background:rgba(245,185,66,.92);color:#4A2B00;font-size:10px;font-weight:800;}
.activity-body{display:flex;flex-direction:column;flex:1;padding:16px 18px 15px;}
.activity-cat{font-size:9.5px;font-weight:800;letter-spacing:.08em;color:var(--primary);text-transform:uppercase;margin-bottom:6px;}
.activity-title{font-size:16.5px;line-height:1.45;font-weight:800;letter-spacing:-.01em;color:var(--ink);}
.activity-summary{font-size:11.5px;line-height:1.65;color:var(--muted);margin-top:6px;}
.activity-meta{display:flex;flex-direction:column;gap:6px;margin:12px 0 13px;font-size:11.5px;color:var(--muted);}
.activity-meta span{display:flex;align-items:center;gap:6px;line-height:1.45;}
.activity-meta svg{color:#8FA0B9;flex:0 0 auto;}
.activity-foot{display:flex;align-items:center;justify-content:space-between;gap:8px;padding-top:12px;border-top:1px solid #F0F3F8;margin-top:auto;}
.people{display:flex;align-items:center;gap:6px;font-size:10.5px;color:var(--muted);}
.people-avatars{display:flex;}
.p-avatar{
  width:20px;height:20px;border-radius:50%;border:2px solid #fff;margin-left:-6px;
  display:grid;place-items:center;font-size:8px;font-weight:800;color:#fff;
  background:linear-gradient(135deg,#2563EB,#14B8A6);
}
.p-avatar:first-child{margin-left:0;}
.p-avatar:nth-child(2){background:linear-gradient(135deg,#7C3AED,#DB2777);}
.p-avatar:nth-child(3){background:linear-gradient(135deg,#F59E0B,#EF4444);}
.activity-arrow{
  width:29px;height:29px;border-radius:9px;display:grid;place-items:center;background:var(--primary-soft);
  color:var(--primary);transition:all .2s ease;
}
.activity-card:hover .activity-arrow{background:var(--primary);color:#fff;transform:translateX(2px);}

/* ---------- 首页下半区 ---------- */
.lower-grid{display:grid;grid-template-columns:1.08fr .92fr;gap:18px;}
.panel{
  background:#fff;border:1px solid var(--border);border-radius:23px;padding:21px 22px;
  box-shadow:var(--shadow-sm);
}
.panel-head{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;margin-bottom:14px;}
.panel-title{display:flex;align-items:center;gap:9px;font-size:16.5px;font-weight:800;color:var(--ink);letter-spacing:-.01em;}
.panel-title .panel-icon{width:33px;height:33px;border-radius:10px;display:grid;place-items:center;background:var(--primary-soft);color:var(--primary);}
.panel-sub{font-size:10.5px;color:var(--muted);margin-top:5px;padding-left:42px;}
.panel-link{display:inline-flex;align-items:center;gap:4px;color:var(--primary);font-size:10.5px;font-weight:700;text-decoration:none;white-space:nowrap;}
a.panel-link{color:var(--primary)!important;text-decoration:none!important;}
a.panel-link:hover{text-decoration:underline!important;}
.todo-progress-row{display:flex;align-items:center;justify-content:space-between;font-size:10.5px;color:var(--muted);margin:3px 0 8px;}
.todo-progress-row b{color:var(--ink);font-size:12px;}
.progress-track{height:6px;border-radius:999px;background:#EEF2F8;overflow:hidden;margin-bottom:7px;}
.progress-fill{height:100%;border-radius:999px;background:linear-gradient(90deg,#1D4ED8,#14B8A6);transition:width .3s ease;}
.todo-list{display:flex;flex-direction:column;}
.todo-row{
  display:flex;align-items:flex-start;gap:11px;padding:11px 0;border-bottom:1px dashed #EDF1F8;
  text-decoration:none;color:inherit;transition:all .16s ease;
}
.todo-row:last-child{border-bottom:0;padding-bottom:2px;}
.todo-row:hover{background:#F8FAFF;margin:0 -9px;padding-left:9px;padding-right:9px;border-radius:11px;}
.todo-check{
  width:19px;height:19px;border-radius:6px;border:1.8px solid #C7D4E8;flex:0 0 auto;margin-top:2px;
  display:grid;place-items:center;color:#fff;font-size:11px;font-weight:900;background:#fff;transition:all .16s ease;
}
.todo-row:hover .todo-check{border-color:#93B4EA;}
.todo-row.done .todo-check{background:linear-gradient(135deg,#1D4ED8,#14B8A6);border-color:transparent;}
.todo-row.done .todo-title{text-decoration:line-through;color:#9AA8BD;}
.todo-main{min-width:0;flex:1;}
.todo-title{font-size:12.8px;font-weight:650;line-height:1.45;color:var(--ink);}
.todo-meta{display:flex;align-items:center;flex-wrap:wrap;gap:7px;font-size:10px;color:var(--muted);margin-top:3px;}
.todo-meta span{display:inline-flex;align-items:center;gap:3px;}
.todo-tag{flex:0 0 auto;margin-top:1px;font-size:8.5px;font-weight:800;padding:4px 7px;border-radius:999px;background:#F5F7FB;color:var(--muted);}
.todo-tag.red{background:#FFF1F2;color:#DC2626;}
.todo-tag.blue{background:#EFF5FF;color:#2563EB;}
.todo-tag.gold{background:#FFF8E7;color:#B7790B;}
.todo-tag.violet{background:#F5F0FF;color:#7C3AED;}
.todo-tag.teal{background:#ECFDF9;color:#0F9488;}
.service-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;}
.service-grid a.service-tile{
  display:flex;align-items:center;gap:10px;padding:11px;border-radius:13px;text-decoration:none!important;
  color:inherit!important;border:1px solid transparent;transition:all .18s ease;
}
.service-grid a.service-tile:hover{background:#F8FAFF;border-color:#E3ECFA;transform:translateY(-1px);}
.service-icon{width:35px;height:35px;border-radius:10px;display:grid;place-items:center;flex:0 0 auto;background:var(--primary-soft);color:var(--primary);}
.service-grid a.service-tile:nth-child(2n) .service-icon{background:var(--teal-soft);color:#0F9488;}
.service-grid a.service-tile:nth-child(3n) .service-icon{background:var(--gold-soft);color:#B7790B;}
.service-grid a.service-tile:nth-child(4n) .service-icon{background:var(--violet-soft);color:var(--violet);}
.service-grid a.service-tile .service-name{display:block;font-size:11.5px;font-weight:700;color:var(--ink)!important;line-height:1.3;}
.service-grid a.service-tile .service-desc{display:block;font-size:9px;color:var(--muted)!important;margin-top:3px;line-height:1.3;}

/* ---------- 子页面 Hero ---------- */
.page-hero{
  position:relative;isolation:isolate;overflow:hidden;display:flex;align-items:center;justify-content:space-between;
  gap:24px;min-height:210px;padding:34px 40px;margin-bottom:22px;border-radius:28px;color:#fff;
  background:radial-gradient(600px 300px at 88% 20%,rgba(94,234,212,.28),transparent 64%),linear-gradient(120deg,#081733,#103275 58%,#0C627A);
  box-shadow:0 24px 60px rgba(15,42,92,.2);animation:fadeUp .45s ease both;
}
.page-hero::before{
  content:"";position:absolute;inset:0;z-index:-1;opacity:.6;
  background-image:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px);
  background-size:44px 44px;mask-image:linear-gradient(90deg,#000,transparent 85%);
}
.page-hero.teal{background:radial-gradient(600px 300px at 88% 20%,rgba(245,185,66,.22),transparent 64%),linear-gradient(120deg,#052E2B,#0F5F5C 60%,#0E7490);}
.page-hero.gold{background:radial-gradient(600px 300px at 88% 20%,rgba(255,255,255,.18),transparent 64%),linear-gradient(120deg,#3B2608,#8A5A12 62%,#B7790B);}
.page-hero.violet{background:radial-gradient(600px 300px at 88% 20%,rgba(94,234,212,.2),transparent 64%),linear-gradient(120deg,#1D1246,#4C2890 60%,#6D28D9);}
.page-hero.rose{background:linear-gradient(120deg,#3B0A1B,#9F1239 62%,#BE185D);}
.page-hero-copy{position:relative;z-index:2;max-width:780px;}
.page-hero h1{margin:12px 0 9px;font-size:clamp(28px,3.6vw,42px);line-height:1.2;font-weight:850;letter-spacing:-.035em;color:#fff;}
.page-hero p{margin:0;max-width:690px;font-size:13.5px;line-height:1.8;color:rgba(255,255,255,.72);}
.page-hero-meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px;}
.page-hero-meta span{display:inline-flex;align-items:center;gap:5px;padding:6px 10px;border-radius:999px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.16);font-size:10.5px;color:rgba(255,255,255,.82);}
.page-hero-art{position:relative;flex:0 0 150px;height:150px;display:grid;place-items:center;color:rgba(255,255,255,.9);}
.page-hero-ring{position:absolute;inset:0;border-radius:50%;border:1px dashed rgba(255,255,255,.25);box-shadow:0 0 0 24px rgba(255,255,255,.035);animation:spin 40s linear infinite;}

/* ---------- 通用布局 / 卡片 ---------- */
.card{background:#fff;border:1px solid var(--border);border-radius:22px;padding:23px;box-shadow:var(--shadow-sm);}
.card.soft{background:var(--surface-soft);box-shadow:none;}
.glass-panel{
  background:rgba(255,255,255,.8);border:1px solid rgba(226,234,246,.95);border-radius:22px;padding:22px;
  box-shadow:var(--shadow-sm);backdrop-filter:blur(12px);
}
.grid-2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:17px;}
.grid-3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:17px;}
.grid-4{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:15px;}
.split-2{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(280px,.65fr);gap:18px;align-items:start;}
.stack{display:flex;flex-direction:column;gap:14px;}
.section-space{margin-top:28px;}
.mt-8{margin-top:8px;}.mt-14{margin-top:14px;}.mt-22{margin-top:22px;}
.muted{color:var(--muted);}
.small{font-size:11px;line-height:1.7;}
.center{text-align:center;}
.data-note{display:flex;align-items:flex-start;gap:8px;font-size:10px;line-height:1.7;color:var(--muted-light);padding:10px 13px;border-radius:11px;background:#F8FAFC;border:1px dashed #E5EBF4;}
.data-note svg{flex:0 0 auto;margin-top:1px;color:#94A3B8;}

/* ---------- 标签 / 按钮 / 表单 ---------- */
.tag{display:inline-flex;align-items:center;gap:4px;padding:4px 8px;border-radius:7px;font-size:9px;font-weight:750;background:var(--primary-soft);color:var(--primary);white-space:nowrap;}
.tag.teal{background:var(--teal-soft);color:#0F9488;}
.tag.gold{background:var(--gold-soft);color:#B7790B;}
.tag.violet{background:var(--violet-soft);color:var(--violet);}
.tag.rose{background:var(--rose-soft);color:var(--rose);}
.tag.green{background:#ECFDF3;color:#15803D;}
.tag.gray{background:#F3F6FA;color:var(--muted);}
.pill{display:inline-flex;align-items:center;gap:5px;padding:6px 10px;border-radius:999px;font-size:10px;font-weight:700;background:var(--primary-soft);color:var(--primary);border:1px solid transparent;}
.pill.teal{background:var(--teal-soft);color:#0F9488;}
.pill.gold{background:var(--gold-soft);color:#B7790B;}
.pill.violet{background:var(--violet-soft);color:var(--violet);}
.pill.rose{background:var(--rose-soft);color:var(--rose);}
.pill.gray{background:#F5F7FB;color:var(--muted);}
.chip-row{display:flex;flex-wrap:wrap;gap:8px;}
.chip{
  display:inline-flex;align-items:center;gap:5px;padding:8px 13px;border-radius:999px;
  background:#fff;border:1px solid var(--border);color:var(--muted);font-size:11px;font-weight:650;
  text-decoration:none;transition:all .18s ease;cursor:pointer;
}
.chip:hover{border-color:#BCD1F1;color:var(--primary);background:#F8FAFF;}
.chip.active{background:linear-gradient(135deg,#1D4ED8,#2563EB);border-color:transparent;color:#fff;box-shadow:0 7px 15px rgba(29,78,216,.22);}
.btn{
  display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:10px 15px;border-radius:11px;
  border:1px solid var(--border);background:#fff;color:var(--ink);font-family:var(--font);
  font-size:12px;font-weight:700;text-decoration:none;cursor:pointer;transition:all .18s ease;
}
.btn:hover{border-color:#C9DAF9;color:var(--primary);transform:translateY(-1px);}
.btn-primary{background:linear-gradient(135deg,#1D4ED8,#2563EB);border-color:transparent;color:#fff;box-shadow:0 8px 18px rgba(29,78,216,.22);}
.btn-primary:hover{color:#fff;box-shadow:0 11px 24px rgba(29,78,216,.32);}
.btn-ghost{background:var(--primary-soft);border-color:transparent;color:var(--primary);}
.btn-ghost:hover{background:#E4EEFF;}
.btn-sm{padding:7px 11px;font-size:10.5px;border-radius:9px;}
.search-form{display:flex;align-items:center;gap:8px;max-width:620px;padding:7px;border-radius:15px;background:#fff;border:1px solid var(--border);box-shadow:var(--shadow-sm);}
.search-form .search-ico{color:var(--muted);display:grid;place-items:center;padding-left:5px;flex:0 0 auto;}
.search-form input{flex:1;min-width:0;border:0;outline:0;background:transparent;font-family:var(--font);font-size:12.5px;color:var(--ink);padding:8px 4px;}
.search-form button{border:0;cursor:pointer;border-radius:10px;padding:9px 14px;background:linear-gradient(135deg,#1D4ED8,#2563EB);color:#fff;font-family:var(--font);font-size:11px;font-weight:700;}

/* ---------- 问答页 ---------- */
.chat-shell{background:#fff;border:1px solid var(--border);border-radius:24px;padding:22px;box-shadow:var(--shadow-sm);}
.chat-stream{display:flex;flex-direction:column;gap:15px;margin-bottom:16px;}
.chat-row{display:flex;gap:10px;align-items:flex-start;}
.chat-row.user{justify-content:flex-end;}
.chat-avatar{width:30px;height:30px;border-radius:10px;display:grid;place-items:center;flex:0 0 auto;background:linear-gradient(135deg,#1D4ED8,#14B8A6);color:#fff;box-shadow:0 5px 12px rgba(29,78,216,.18);}
.bubble-user{max-width:76%;padding:11px 15px;border-radius:17px 17px 4px 17px;background:linear-gradient(135deg,#1D4ED8,#2563EB);color:#fff;font-size:12.8px;line-height:1.7;box-shadow:0 8px 18px rgba(29,78,216,.18);}
.bubble-ai{max-width:calc(100% - 44px);padding:17px 18px;border-radius:5px 17px 17px 17px;background:#F8FAFF;border:1px solid #E7EEFB;color:var(--ink);font-size:12.5px;line-height:1.75;}
.answer-title{font-size:16px;font-weight:820;color:var(--ink);margin-bottom:5px;letter-spacing:-.01em;}
.answer-intro{color:var(--ink-soft);font-size:12.5px;line-height:1.8;}
.answer-steps{display:flex;flex-direction:column;gap:7px;margin:12px 0;}
.answer-step{display:flex;gap:8px;align-items:flex-start;font-size:12px;line-height:1.65;color:var(--ink-soft);}
.step-num{width:20px;height:20px;border-radius:7px;background:#fff;border:1px solid #DDE8F9;color:var(--primary);display:grid;place-items:center;font-size:9px;font-weight:800;flex:0 0 auto;margin-top:1px;}
.answer-tip{display:flex;gap:7px;align-items:flex-start;padding:9px 11px;border-radius:9px;background:#FFF9EA;border:1px solid #FBEBC6;color:#8A5B0B;font-size:10.5px;line-height:1.7;margin-top:10px;}
.answer-tip svg{flex:0 0 auto;margin-top:1px;}
.answer-source{display:flex;align-items:center;gap:5px;font-size:9px;color:var(--muted-light);margin-top:11px;padding-top:9px;border-top:1px dashed #E5EBF5;}
.answer-links{display:flex;flex-wrap:wrap;gap:7px;margin-top:10px;}
.answer-links a{display:inline-flex;align-items:center;gap:4px;padding:7px 10px;border-radius:8px;background:#fff;border:1px solid #DCE8FB;color:var(--primary);font-size:10px;font-weight:700;text-decoration:none;transition:all .18s ease;}
.answer-links a:hover{background:var(--primary);color:#fff;border-color:transparent;}
.chat-form{display:flex;align-items:center;gap:8px;padding:7px;border-radius:15px;background:#fff;border:1px solid var(--border);box-shadow:var(--shadow-sm);}
.chat-form input{flex:1;min-width:0;border:0;outline:0;background:transparent;padding:9px 6px;font-family:var(--font);font-size:12.5px;color:var(--ink);}
.chat-form button{border:0;cursor:pointer;border-radius:10px;padding:10px 14px;background:linear-gradient(135deg,#1D4ED8,#2563EB);color:#fff;font-family:var(--font);font-size:11px;font-weight:700;display:inline-flex;align-items:center;gap:5px;}

/* ---------- 流程页 ---------- */
.process-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;}
.process-card{background:#fff;border:1px solid var(--border);border-radius:21px;padding:20px;box-shadow:var(--shadow-sm);transition:all .2s ease;}
.process-card:hover{border-color:#D5E3F8;box-shadow:var(--shadow-md);transform:translateY(-2px);}
.process-head{display:flex;gap:12px;align-items:flex-start;}
.process-icon{width:42px;height:42px;border-radius:12px;display:grid;place-items:center;flex:0 0 auto;background:var(--primary-soft);color:var(--primary);}
.process-card:nth-child(3n+2) .process-icon{background:var(--teal-soft);color:#0F9488;}
.process-card:nth-child(3n) .process-icon{background:var(--gold-soft);color:#B7790B;}
.process-title{font-size:14.5px;font-weight:800;color:var(--ink);margin:0;line-height:1.4;}
.process-dept{font-size:9.5px;color:var(--muted);margin-top:3px;}
.process-desc{font-size:11.5px;line-height:1.7;color:var(--muted);margin:11px 0 12px;}
.process-meta{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:11px;}
.process-meta span{display:inline-flex;align-items:center;gap:4px;padding:5px 7px;border-radius:6px;background:#F7F9FD;font-size:9px;color:var(--muted);}
details.card-details{border-top:1px dashed #E7EDF6;padding-top:10px;margin-top:2px;}
details.card-details summary{list-style:none;display:flex;align-items:center;justify-content:space-between;cursor:pointer;font-size:10.5px;font-weight:750;color:var(--primary);padding:2px 0;}
details.card-details summary::-webkit-details-marker{display:none;}
details.card-details summary::after{content:"+";font-size:15px;font-weight:400;transition:transform .2s ease;}
details.card-details[open] summary::after{transform:rotate(45deg);}
.detail-block{padding-top:11px;animation:fadeIn .25s ease;}
.detail-label{font-size:9px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--muted-light);margin:9px 0 5px;}
.detail-list{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:5px;}
.detail-list li{font-size:10.5px;line-height:1.65;color:var(--ink-soft);padding-left:14px;position:relative;}
.detail-list li::before{content:"";position:absolute;left:2px;top:7px;width:4px;height:4px;border-radius:50%;background:var(--primary);}
.process-steps{display:flex;flex-direction:column;gap:8px;counter-reset:step;}
.process-step{display:flex;gap:8px;font-size:10.5px;line-height:1.65;color:var(--ink-soft);}
.process-step .step-num{background:#F3F7FF;}
.notice-box{display:flex;gap:7px;align-items:flex-start;padding:9px 11px;border-radius:9px;background:#FFF8E8;border:1px solid #FBEBC7;color:#8A5B0B;font-size:10px;line-height:1.7;margin-top:9px;}

/* ---------- 活动页 ---------- */
.activity-detail-card{background:#fff;border:1px solid var(--border);border-radius:24px;overflow:hidden;box-shadow:var(--shadow-sm);display:grid;grid-template-columns:minmax(0,.9fr) minmax(0,1.1fr);}
.activity-detail-card .activity-cover{width:100%;min-width:0;height:100%;min-height:260px;aspect-ratio:auto;}
.activity-detail-body{padding:25px 27px;display:flex;flex-direction:column;}
.activity-detail-body h3{margin:5px 0 8px;font-size:21px;font-weight:830;letter-spacing:-.02em;line-height:1.35;}
.activity-detail-body .desc{font-size:12px;line-height:1.8;color:var(--muted);margin:0 0 12px;}
.join-form{margin-top:auto;padding-top:14px;border-top:1px dashed #E7EDF6;display:flex;align-items:center;gap:9px;flex-wrap:wrap;}
.join-form button{border:0;cursor:pointer;border-radius:10px;padding:9px 14px;background:linear-gradient(135deg,#1D4ED8,#2563EB);color:#fff;font-family:var(--font);font-size:10.5px;font-weight:700;}
.joined-badge{display:inline-flex;align-items:center;gap:5px;padding:8px 11px;border-radius:9px;background:#ECFDF9;color:#0F9488;font-size:10.5px;font-weight:700;border:1px solid #CFF5EC;}
.join-form a.join-cancel{display:inline-flex;align-items:center;gap:4px;padding:7px 10px;border-radius:9px;border:1px solid var(--border);background:#fff;color:var(--muted)!important;font-size:10px;font-weight:700;text-decoration:none!important;line-height:1.2;transition:color .16s ease,border-color .16s ease,background .16s ease;}
.join-form a.join-cancel:hover{color:var(--rose)!important;border-color:#FBD5DE;background:#FFF5F7;text-decoration:none!important;}

/* ---------- 个人中心 / 成长 ---------- */
.profile-card{
  position:relative;overflow:hidden;padding:25px 27px;border-radius:24px;color:#fff;
  background:radial-gradient(500px 260px at 88% 10%,rgba(94,234,212,.25),transparent 65%),linear-gradient(125deg,#081733,#103275 55%,#0C627A);
  box-shadow:0 20px 50px rgba(15,42,92,.18);
}
.profile-head{display:flex;align-items:center;gap:14px;}
.profile-avatar{width:60px;height:60px;border-radius:18px;display:grid;place-items:center;font-size:24px;font-weight:850;background:linear-gradient(135deg,rgba(255,255,255,.23),rgba(255,255,255,.1));border:1px solid rgba(255,255,255,.3);box-shadow:inset 0 1px 0 rgba(255,255,255,.25);}
.profile-name{font-size:20px;font-weight:830;margin:0;}
.profile-sub{font-size:10.5px;color:rgba(255,255,255,.62);margin-top:4px;}
.profile-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:19px;padding-top:16px;border-top:1px solid rgba(255,255,255,.13);}
.profile-stat strong{display:block;font-size:16px;font-weight:820;line-height:1.1;}
.profile-stat span{display:block;font-size:8.5px;color:rgba(255,255,255,.55);margin-top:4px;}
.course-list{display:flex;flex-direction:column;gap:8px;}
.course-row{display:flex;align-items:center;gap:12px;padding:10px 11px;border-radius:12px;border:1px solid #EEF3FA;background:#FBFCFE;}
.course-row:hover{background:#F7FAFF;border-color:#DFE9F8;}
.course-time{font-size:11px;font-weight:800;color:var(--primary);width:42px;flex:0 0 auto;}
.course-info{min-width:0;flex:1;}
.course-name{font-size:11.5px;font-weight:700;color:var(--ink);}
.course-place{font-size:9px;color:var(--muted);margin-top:3px;}
.course-state{font-size:8px;padding:4px 6px;border-radius:5px;background:#F0F5FF;color:var(--primary);white-space:nowrap;}
.balance-card{padding:19px 20px;border-radius:19px;color:#fff;background:linear-gradient(125deg,#0F1B33,#1D4ED8 85%);box-shadow:0 14px 30px rgba(29,78,216,.2);}
.balance-label{font-size:9.5px;color:rgba(255,255,255,.6);letter-spacing:.06em;}
.balance-value{font-size:29px;font-weight:830;margin:5px 0 2px;letter-spacing:-.02em;}
.balance-value small{font-size:13px;font-weight:600;opacity:.7;}
.balance-bottom{display:flex;justify-content:space-between;align-items:center;margin-top:15px;font-size:8.5px;color:rgba(255,255,255,.55);}
.ring{
  --size:146px;width:var(--size);height:var(--size);border-radius:50%;position:relative;flex:0 0 auto;
  background:conic-gradient(#2563EB calc(var(--value)*1%),#E7EEF9 0);
  display:grid;place-items:center;box-shadow:inset 0 0 0 1px rgba(29,78,216,.05);
}
.ring::before{content:"";position:absolute;inset:12px;border-radius:50%;background:#fff;box-shadow:0 5px 18px rgba(15,27,51,.06);}
.ring-inner{position:relative;z-index:1;text-align:center;}
.ring-inner strong{display:block;font-size:29px;font-weight:850;letter-spacing:-.03em;color:var(--ink);line-height:1;}
.ring-inner strong small{font-size:11px;color:var(--muted);font-weight:700;margin-left:1px;}
.ring-inner span{display:block;font-size:9px;color:var(--muted);margin-top:5px;}
.skill-row{margin-bottom:11px;}
.skill-top{display:flex;justify-content:space-between;font-size:10.5px;color:var(--ink-soft);margin-bottom:5px;}
.skill-top b{font-weight:700;}
.skill-top span{color:var(--muted);font-weight:700;}
.mini-progress{height:6px;border-radius:999px;background:#EEF2F8;overflow:hidden;}
.mini-progress span{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,#1D4ED8,#3B82F6);}
.mini-progress span.teal{background:linear-gradient(90deg,#0D9488,#2DD4BF);}
.mini-progress span.gold{background:linear-gradient(90deg,#D99A16,#F5B942);}
.mini-progress span.violet{background:linear-gradient(90deg,#6D28D9,#A78BFA);}
.mini-progress span.rose{background:linear-gradient(90deg,#BE123C,#FB7185);}
.badge-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;}
.badge-item{padding:13px 9px;border-radius:14px;text-align:center;background:#FBFCFE;border:1px solid #EEF3FA;transition:all .18s ease;}
.badge-item:hover{transform:translateY(-2px);border-color:#DCE7F7;box-shadow:var(--shadow-xs);}
.badge-item.locked{opacity:.46;filter:grayscale(1);}
.badge-medal{width:42px;height:42px;border-radius:13px;margin:0 auto 7px;display:grid;place-items:center;background:var(--primary-soft);color:var(--primary);}
.badge-item:nth-child(2) .badge-medal{background:var(--teal-soft);color:#0F9488;}
.badge-item:nth-child(3) .badge-medal{background:var(--violet-soft);color:var(--violet);}
.badge-item:nth-child(4) .badge-medal{background:var(--rose-soft);color:var(--rose);}
.badge-item:nth-child(5) .badge-medal{background:var(--gold-soft);color:#B7790B;}
.badge-name{font-size:10px;font-weight:750;color:var(--ink);}
.badge-desc{font-size:8px;color:var(--muted);margin-top:3px;line-height:1.4;}
.timeline{position:relative;display:flex;flex-direction:column;gap:17px;padding-left:19px;}
.timeline::before{content:"";position:absolute;left:4px;top:5px;bottom:5px;width:1px;background:linear-gradient(#C7D9F7,#E7EDF6);}
.timeline-item{position:relative;}
.timeline-item::before{content:"";position:absolute;left:-19px;top:4px;width:9px;height:9px;border-radius:50%;background:#fff;border:2px solid var(--primary);box-shadow:0 0 0 3px #EEF4FF;}
.timeline-date{font-size:8.5px;font-weight:800;color:var(--primary);letter-spacing:.04em;}
.timeline-title{font-size:12px;font-weight:750;color:var(--ink);margin-top:4px;line-height:1.5;}
.timeline-desc{font-size:10px;color:var(--muted);line-height:1.65;margin-top:3px;}
.timeline-tag{display:inline-block;margin-top:5px;}
.stat-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;}
.stat-card{position:relative;padding:17px 17px 15px;border-radius:18px;background:#fff;border:1px solid var(--border);box-shadow:var(--shadow-xs);}
.stat-icon{width:33px;height:33px;border-radius:10px;display:grid;place-items:center;background:var(--primary-soft);color:var(--primary);margin-bottom:12px;}
.stat-card.teal .stat-icon{background:var(--teal-soft);color:#0F9488;}
.stat-card.gold .stat-icon{background:var(--gold-soft);color:#B7790B;}
.stat-card.violet .stat-icon{background:var(--violet-soft);color:var(--violet);}
.stat-card.rose .stat-icon{background:var(--rose-soft);color:var(--rose);}
.stat-value{font-size:23px;font-weight:850;color:var(--ink);line-height:1;letter-spacing:-.03em;}
.stat-value small{font-size:10px;color:var(--muted);font-weight:600;margin-left:3px;}
.stat-label{font-size:10px;color:var(--muted);margin-top:5px;}
.stat-foot{font-size:8.5px;color:var(--muted-light);margin-top:7px;}
.empty-state{padding:44px 24px;text-align:center;background:#fff;border:1px dashed #DDE6F2;border-radius:20px;}
.empty-icon{width:60px;height:60px;border-radius:18px;display:grid;place-items:center;margin:0 auto 13px;background:var(--primary-soft);color:var(--primary);}
.empty-state h3{margin:0 0 6px;font-size:15px;font-weight:800;}
.empty-state p{margin:0 0 14px;font-size:11px;color:var(--muted);line-height:1.7;}

/* ---------- 页脚 ---------- */
.site-footer{margin-top:42px;padding:20px 2px 10px;border-top:1px solid var(--border);}
.footer-main{display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;}
.footer-brand{display:flex;align-items:center;gap:9px;}
.footer-brand .brand-logo{width:34px;height:34px;border-radius:10px;box-shadow:0 4px 12px rgba(29,78,216,.16);}
.footer-brand b{display:block;font-size:13px;font-weight:800;line-height:1.2;}
.footer-brand span{display:block;font-size:8.5px;color:var(--muted);margin-top:3px;}
.footer-links{display:flex;align-items:center;gap:9px;flex-wrap:wrap;}
.footer-links a{font-size:10px;color:var(--muted)!important;text-decoration:none;}
.footer-links a:hover{color:var(--primary)!important;}
.footer-links span{width:2px;height:2px;border-radius:50%;background:#CBD5E1;}
.footer-bottom{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-top:14px;font-size:8.5px;color:var(--muted-light);line-height:1.6;}

/* ---------- Streamlit 原生控件适配 ---------- */
.stButton>button{
  width:100%;border-radius:11px;border:1px solid var(--border);background:#fff;color:var(--ink);
  font-family:var(--font);font-size:11px;font-weight:700;min-height:36px;transition:all .18s ease;
}
.stButton>button:hover{border-color:#C9DAF9;color:var(--primary);}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#1D4ED8,#2563EB);color:#fff;border:0;box-shadow:0 8px 18px rgba(29,78,216,.2);}
[data-testid="stCheckbox"] label{font-family:var(--font)!important;}
[data-testid="stCheckbox"] label p{font-size:12px!important;color:var(--ink)!important;font-weight:600!important;}
[data-testid="stCheckbox"] [data-baseweb="checkbox"] div{border-radius:6px;}
[data-baseweb="input"] input, [data-testid="stTextInput"] input{border-radius:11px;font-family:var(--font);font-size:12px;}
[data-testid="stProgress"] > div > div{background:linear-gradient(90deg,#1D4ED8,#14B8A6);}
[data-testid="stExpander"]{border:1px solid var(--border);border-radius:14px;background:#fff;}
[data-testid="stAlert"]{border-radius:14px;}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--border);border-radius:16px;padding:12px 14px;}

/* ---------- 动画 ---------- */
@keyframes fadeUp{from{opacity:0;transform:translateY(14px);}to{opacity:1;transform:translateY(0);}}
@keyframes fadeIn{from{opacity:0;}to{opacity:1;}}
@keyframes floaty{0%,100%{transform:translateY(0);}50%{transform:translateY(-10px);}}
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:.5;}}
@keyframes spin{to{transform:rotate(360deg);}}

/* ---------- 响应式 ---------- */
@media (max-width:1120px){
  .hero{padding:38px 34px;grid-template-columns:minmax(0,1fr) 330px;}
  .hero-orbit{width:350px;height:350px;}
  .hero-orbit.orbit-2{width:260px;height:260px;}
  .hero-orbit.orbit-3{width:410px;height:410px;}
  .feature-grid{grid-template-columns:repeat(2,1fr);}
  .activity-grid{grid-template-columns:repeat(2,1fr);}
  .activity-grid .activity-card:last-child{display:none;}
  .metric-strip{margin-left:20px;margin-right:20px;}
}
@media (max-width:960px){
  .main-nav{display:none;}
  .mobile-nav{
    display:flex;gap:5px;overflow-x:auto;margin:-6px 0 13px;padding:0 2px 4px;
    scrollbar-width:none;
  }
  .mobile-nav::-webkit-scrollbar{display:none;}
  .mobile-nav-link{
    display:inline-flex;align-items:center;gap:4px;padding:7px 10px;border-radius:9px;background:#fff;
    border:1px solid var(--border);color:var(--muted);font-size:10px;font-weight:700;text-decoration:none;white-space:nowrap;
  }
  .mobile-nav-link.active{background:var(--primary);color:#fff;border-color:transparent;}
  .hero{grid-template-columns:1fr;min-height:0;padding:36px 32px 30px;}
  .hero-visual{min-height:270px;margin-top:8px;}
  .hero-mascot{width:260px;}
  .hero-orbit{width:300px;height:300px;}
  .hero-orbit.orbit-2{width:220px;height:220px;}
  .hero-orbit.orbit-3{display:none;}
  .float-card.top{right:8%;}
  .float-card.bottom{left:8%;}
  .metric-strip{margin:-20px 16px 27px;grid-template-columns:repeat(2,1fr);}
  .metric:nth-child(2){border-right:0;}
  .metric:nth-child(1),.metric:nth-child(2){border-bottom:1px solid #EFF3F9;}
  .lower-grid,.split-2,.process-grid{grid-template-columns:1fr;}
  .activity-detail-card{grid-template-columns:1fr;}
  .activity-detail-card .activity-cover{min-height:220px;}
  .page-hero-art{display:none;}
  .profile-stats{grid-template-columns:repeat(2,1fr);row-gap:14px;}
  .stat-grid{grid-template-columns:repeat(2,1fr);}
  .growth-stats{display:none;}
}
@media (max-width:760px){
  [data-testid="stAppViewBlockContainer"], [data-testid="stMainBlockContainer"]{padding:1rem 1rem 2rem;}
  .topbar{gap:10px;}
  .brand-text small{display:none;}
  .brand-text strong{font-size:18px;}
  .ai-status{display:none;}
  .user-meta{display:none;}
  .user-chip{padding:3px;}
  /* 五个入口等分排布，避免「我的河大」被横向滚动隐藏 */
  .mobile-nav{overflow-x:visible;gap:4px;}
  .mobile-nav-link{flex:1 1 0;min-width:0;justify-content:center;padding:7px 4px;font-size:9.5px;gap:3px;}
  .hero{padding:28px 22px 25px;border-radius:24px;}
  .hero h1{font-size:32px;margin:14px 0 10px;}
  .hero-desc{font-size:12.5px;line-height:1.8;}
  .ai-form{max-width:none;padding:6px;margin-top:19px;}
  .ai-form button{padding:11px 12px;font-size:11px;}
  .ai-form button span{display:none;}
  .suggest-chip{font-size:10px;padding:6px 9px;}
  .hero-trust{display:none;}
  .hero-visual{min-height:235px;}
  .hero-mascot{width:220px;}
  .float-card{display:none;}
  .hero-orbit{width:250px;height:250px;}
  .hero-orbit.orbit-2{width:190px;height:190px;}
  .metric-strip{margin:-18px 8px 24px;}
  .metric{padding:12px 14px;gap:9px;}
  .metric-icon{width:32px;height:32px;}
  .metric-value{font-size:16px;}
  .metric-label{font-size:9px;}
  .section-head{align-items:flex-start;}
  .section-title{font-size:21px;}
  .section-sub{font-size:10.5px;}
  .section-link{font-size:10px;padding:6px 8px;}
  .feature-grid{grid-template-columns:1fr 1fr;gap:10px;}
  .feature-card{min-height:178px;padding:16px 14px 13px;border-radius:17px;}
  .feature-icon{width:38px;height:38px;border-radius:11px;margin-bottom:11px;}
  .feature-title{font-size:14px;}
  .feature-desc{font-size:10.5px;line-height:1.65;margin:5px 0 10px;}
  .feature-tag{font-size:8px;}
  .growth-banner{padding:14px 15px;gap:10px;flex-wrap:wrap;}
  .growth-copy b{font-size:12.5px;}
  .growth-copy span{font-size:9px;}
  .growth-cta{display:none;}
  .activity-grid{grid-template-columns:1fr;}
  .activity-grid .activity-card:last-child{display:flex;}
  .panel{padding:17px 16px;border-radius:19px;}
  .service-grid{grid-template-columns:1fr 1fr;}
  .page-hero{padding:26px 21px;min-height:160px;border-radius:23px;margin-bottom:16px;}
  .page-hero h1{font-size:27px;margin:9px 0 6px;}
  .page-hero p{font-size:11.5px;}
  .grid-2,.grid-3,.grid-4{grid-template-columns:1fr;}
  .badge-grid{grid-template-columns:repeat(2,1fr);}
  .activity-detail-body{padding:19px 18px;}
  .activity-detail-body h3{font-size:18px;}
  .chat-shell{padding:15px;}
  .bubble-ai{max-width:100%;padding:14px;}
  .bubble-user{max-width:88%;}
  .chat-avatar{display:none;}
  .page-hero-meta span{font-size:9px;}
  .site-footer{margin-top:28px;}
  .footer-bottom{font-size:8px;}
}
@media (max-width:480px){
  .feature-grid{grid-template-columns:1fr;}
  .metric-strip{grid-template-columns:1fr 1fr;}
  .stat-grid{grid-template-columns:1fr 1fr;}
  .service-grid{grid-template-columns:1fr;}
  .profile-stats{grid-template-columns:1fr 1fr;}
}
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important;scroll-behavior:auto!important;}
}
"""


def inject_theme() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
