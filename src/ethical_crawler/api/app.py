"""FastAPI application initialization and interactive Web UI dashboard."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response

from ethical_crawler.api.theme import (
    DEFAULT_THEME_ID,
    THEMES,
    generate_google_fonts_link,
    generate_root_css,
    get_themes_json,
)
from ethical_crawler.api.v1.router import router as api_v1_router
from ethical_crawler.config import get_settings

from contextlib import asynccontextmanager
from ethical_crawler.scheduler import get_schedule_manager

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager starting background workers."""
    schedule_mgr = get_schedule_manager()
    schedule_mgr.start()
    try:
        yield
    finally:
        schedule_mgr.stop()


app = FastAPI(
    title="Ethical AI-Native Web Crawler",
    description="A production-grade, ethical web crawling service and API implementing the 4 ethical crawling rules.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api")


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "bot_user_agent": settings.user_agent,
        "version": settings.bot_version,
    }


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CRAWL // ETHIC — Autonomous Web Ingestion Node</title>
  __GOOGLE_FONTS__
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
  <script>
    // Immediate early theme application to eliminate FOUC
    (function initEarlyTheme() {
      try {
        const saved = localStorage.getItem('ethic_user_theme');
        if (saved) {
          const t = JSON.parse(saved);
          if (t && t.tokens) {
            const root = document.documentElement;
            for (const [k, v] of Object.entries(t.tokens)) {
              root.style.setProperty(k, v);
            }
          }
          if (t && t.fonts) {
            if (t.fonts.heading) document.documentElement.style.setProperty('--ds-font-heading', t.fonts.heading);
            if (t.fonts.sans) document.documentElement.style.setProperty('--ds-font-sans', t.fonts.sans);
            if (t.fonts.mono) document.documentElement.style.setProperty('--ds-font-mono', t.fonts.mono);
          }
        }
      } catch (e) {}
    })();
  </script>
  <style>
    __ROOT_THEME_CSS__
    html {
      background-color: var(--ds-bg);
    }
    body.app-shell {
      font-family: var(--ds-font-sans, 'Plus Jakarta Sans', system-ui, sans-serif);
      color: var(--ds-on-surface);
      background-color: var(--ds-bg);
      background-image: none;
    }
    h1, h2, h3, h4, .glow-heading {
      font-family: var(--ds-font-heading, 'Space Grotesk', system-ui, sans-serif);
      color: var(--ds-on-surface);
    }
    code, pre, .font-mono, .status-pill, .data-table th, .ethic-label {
      font-family: var(--ds-font-mono, 'Space Mono', ui-monospace, monospace);
    }
    * {
      scrollbar-color: var(--ds-outline) var(--ds-surface-container-low);
      scrollbar-width: thin;
    }
    @supports not (scrollbar-color: auto) {
      ::-webkit-scrollbar { width: 6px; height: 6px; }
      ::-webkit-scrollbar-thumb { background: var(--ds-outline); border-radius: 4px; }
      ::-webkit-scrollbar-track { background: var(--ds-surface-container-low); }
    }
    .glass-card {
      background: var(--ds-card-bg, #ffffff);
      color: var(--ds-on-surface);
      border: 1px solid var(--ds-border);
      border-radius: var(--ds-radius, 0.75rem);
      box-shadow: var(--ds-shadow);
    }
    .glass-card-subtle {
      background: var(--ds-surface-container-low);
      color: var(--ds-on-surface);
      border: 1px solid var(--ds-border);
      border-radius: 0.5rem;
    }
    .ethic-panel {
      background: #ffffff;
      border: 1px solid var(--ds-border);
      border-radius: 0.75rem;
      box-shadow: var(--ds-shadow);
    }
    .ethic-label {
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: var(--ds-on-surface-variant);
    }
    .ethic-status-bar {
      background: var(--ds-surface-container-low);
      border: 1px solid var(--ds-border);
      border-radius: 0.75rem;
      padding: 0.65rem 1rem;
      font-size: 11px;
      box-shadow: var(--ds-shadow);
    }
    .ethic-toggle {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.5rem 0.75rem;
      background: var(--ds-surface-container-low);
      border: 1px solid var(--ds-border);
      border-radius: 0.5rem;
      font-size: 12px;
      color: var(--ds-on-surface);
      cursor: pointer;
    }
    .ethic-toggle input { accent-color: var(--ds-primary); }
    .ethic-slider-row { margin-bottom: 1rem; }
    .ethic-slider-row label {
      display: flex;
      justify-content: space-between;
      font-size: 10px;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: var(--ds-on-surface-variant);
      margin-bottom: 0.35rem;
      font-family: 'Space Mono', monospace;
      font-weight: 700;
    }
    .ethic-slider-row input[type="range"] {
      width: 100%;
      accent-color: var(--ds-primary);
      height: 4px;
      background: var(--ds-surface-container-highest);
      border: none;
      box-shadow: none;
    }
    .live-stream {
      font-size: 11px;
      line-height: 1.6;
      max-height: 280px;
      overflow-y: auto;
      color: var(--ds-on-surface-variant);
      font-family: 'Space Mono', monospace;
      background: var(--ds-surface-container-low);
      border-radius: 0.5rem;
      padding: 0.75rem;
    }
    .live-stream .stream-ok { color: var(--ds-secondary); }
    .live-stream .stream-warn { color: var(--ds-tertiary); }
    .live-stream .stream-err { color: var(--ds-error); }
    .live-stream .stream-dim { color: var(--ds-outline); }
    .embedding-panel {
      background: #ffffff;
      border: 1px solid var(--ds-border);
      border-radius: 0.5rem;
      padding: 0.75rem 1rem;
      font-size: 10px;
      letter-spacing: 0.04em;
      box-shadow: var(--ds-shadow);
    }
    .embedding-active {
      animation: embedPulse 2s ease-in-out infinite;
    }
    @keyframes embedPulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.6; }
    }
    .stat-tile {
      background: var(--ds-surface-container-low);
      border: 1px solid var(--ds-border);
      border-radius: 0.5rem;
    }
    .glow-heading {
      font-weight: 700;
      letter-spacing: -0.02em;
      color: var(--ds-on-surface);
    }
    .cta-primary {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: var(--ds-primary-container);
      color: var(--ds-on-surface);
      font-family: var(--ds-font-heading);
      font-weight: 700;
      letter-spacing: 0.02em;
      font-size: 13px;
      border: 1px solid var(--ds-on-surface);
      border-radius: 0.5rem;
      box-shadow: 2px 2px 0 var(--ds-on-surface);
      transition: transform 0.12s ease, box-shadow 0.12s ease, filter 0.12s ease;
    }
    .cta-primary:hover {
      filter: brightness(1.05);
      transform: translate(-1px, -1px);
      box-shadow: 3px 3px 0 var(--ds-on-surface);
    }
    .hud-tab-active {
      background: var(--ds-primary-container);
      color: var(--ds-on-surface);
      font-family: var(--ds-font-heading);
      font-weight: 700;
      border: 1px solid var(--ds-on-surface);
      border-radius: 0.5rem;
      box-shadow: 2px 2px 0 var(--ds-on-surface);
    }
    .hud-tab-history {
      background: var(--ds-primary-container);
      color: var(--ds-on-surface);
      font-family: var(--ds-font-heading);
      font-weight: 700;
      border: 1px solid var(--ds-on-surface);
      border-radius: 0.5rem;
      box-shadow: 2px 2px 0 var(--ds-on-surface);
    }
    .chip-export {
      display: inline-flex;
      align-items: center;
      padding: 0.2rem 0.55rem;
      border-radius: 0.25rem;
      font-size: 10px;
      font-weight: 600;
      color: var(--ds-secondary);
      background: rgba(0, 103, 127, 0.08);
      border: 1px solid rgba(0, 103, 127, 0.2);
    }
    .chip-export:hover { background: rgba(0, 103, 127, 0.14); }
    .btn-ghost {
      background: #ffffff;
      border: 1px solid var(--ds-border);
      color: var(--ds-on-surface-variant);
      font-weight: 600;
      font-size: 11px;
      border-radius: 0.5rem;
    }
    .btn-ghost:hover {
      border-color: var(--ds-outline);
      color: var(--ds-on-surface);
      background: var(--ds-surface-container-low);
    }
    .btn-icon {
      width: 1.85rem;
      height: 1.85rem;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 0.375rem;
      color: var(--ds-on-surface-variant);
      background: #ffffff;
      border: 1px solid var(--ds-border);
    }
    .btn-icon:hover { color: var(--ds-primary); border-color: var(--ds-outline); }
    .status-pill {
      display: inline-flex;
      min-width: 2.4rem;
      justify-content: center;
      padding: 0.15rem 0.4rem;
      border-radius: 0.25rem;
      font-size: 10px;
      font-weight: 600;
      border: 1px solid var(--ds-border);
    }
    .status-pill.ok { background: rgba(0, 103, 127, 0.1); color: var(--ds-secondary); border-color: rgba(0, 103, 127, 0.25); }
    .status-pill.bad { background: var(--ds-error-container); color: var(--ds-error); }
    .data-table { min-width: 760px; }
    .data-table th {
      white-space: nowrap;
      font-size: 10px;
      letter-spacing: 0.06em;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--ds-on-surface-variant);
      background: var(--ds-surface-container-low);
      border-bottom: 1px solid var(--ds-border);
    }
    .data-table td { vertical-align: middle; color: var(--ds-on-surface); }
    .export-menu-panel { min-width: 8.5rem; }
    .status-dot-active {
      background: var(--ds-secondary);
      box-shadow: 0 0 0 2px rgba(0, 103, 127, 0.2);
    }
    .glass-card .text-white, .glass-card .text-slate-50, .glass-card .text-slate-100,
    .glass-card .text-slate-200 { color: var(--ds-on-surface) !important; }
    .glass-card .text-slate-300, .glass-card .text-slate-400, .glass-card .text-slate-500 {
      color: var(--ds-on-surface-variant) !important;
    }
    .glass-card .text-teal-300, .glass-card .text-teal-400 { color: var(--ds-secondary) !important; }
    .glass-card .text-violet-300, .glass-card .text-violet-400, .glass-card .text-purple-300,
    .glass-card .text-purple-400 { color: var(--ds-primary) !important; }
    .glass-card .border-slate-700, .glass-card .border-slate-800,
    .glass-card .border-slate-700\\/60, .glass-card .border-slate-800\\/80 {
      border-color: var(--ds-border) !important;
    }
    input:not([type="checkbox"]):not([type="radio"]):not([type="hidden"]):not([type="range"]),
    select, textarea {
      background: #ffffff !important;
      border: 1px solid var(--ds-border) !important;
      border-radius: 0.5rem !important;
      color: var(--ds-on-surface) !important;
      box-shadow: none !important;
      font-family: var(--ds-font-sans) !important;
      font-size: 13px !important;
    }
    .modal-overlay {
      transition: opacity 0.22s ease-out, visibility 0.22s ease-out;
    }
    .modal-overlay.hidden {
      opacity: 0;
      visibility: hidden;
      pointer-events: none;
    }
    .modal-overlay:not(.hidden) {
      opacity: 1;
      visibility: visible;
      pointer-events: auto;
    }
    .modal-card {
      transition: transform 0.24s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.22s ease-out;
    }
    .modal-overlay.hidden .modal-card {
      transform: scale(0.96) translateY(8px);
      opacity: 0;
    }
    .modal-overlay:not(.hidden) .modal-card {
      transform: scale(1) translateY(0);
      opacity: 1;
    }
    @media (prefers-reduced-motion: reduce) {
      .modal-overlay, .modal-card, * {
        transition-duration: 0.05s !important;
        animation-duration: 0.05s !important;
        transform: none !important;
      }
    }
    @keyframes floatIcon {
      0%, 100% { transform: translateY(0px); }
      50% { transform: translateY(-4px); }
    }
    .animate-float {
      animation: floatIcon 3.5s infinite ease-in-out;
    }
    @keyframes shimmerMove {
      0% { transform: translateX(-100%); }
      100% { transform: translateX(250%); }
    }
    .animate-shimmer {
      animation: shimmerMove 2s infinite linear;
    }
    @keyframes pulseSoft {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.6; transform: scale(1.08); }
    }
    .animate-pulse-soft {
      animation: pulseSoft 2.5s infinite ease-in-out;
    }
    @keyframes pulse-ring {
      0% { box-shadow: 0 0 0 0 rgba(83, 102, 0, 0.35); }
      70% { box-shadow: 0 0 0 8px rgba(83, 102, 0, 0); }
      100% { box-shadow: 0 0 0 0 rgba(83, 102, 0, 0); }
    }
    button:focus-visible, a:focus-visible, summary:focus-visible {
      outline: 2px solid var(--ds-primary);
      outline-offset: 2px;
    }
    input:not([type="checkbox"]):not([type="radio"]):not([type="hidden"]):not([type="range"]):focus,
    select:focus, textarea:focus {
      outline: none;
      border-color: var(--ds-primary) !important;
      box-shadow: 0 0 0 3px rgba(83, 102, 0, 0.12) !important;
    }
    .skip-link {
      position: absolute;
      left: 1rem;
      top: -4rem;
      z-index: 10000;
      padding: 0.5rem 0.9rem;
      border-radius: 0.5rem;
      background: var(--ds-primary-container);
      color: var(--ds-on-surface);
      border: 1px solid var(--ds-on-surface);
      font-family: 'Space Grotesk', sans-serif;
      font-size: 0.8125rem;
      font-weight: 700;
    }
    .skip-link:focus {
      top: 0.75rem;
      outline: 2px solid var(--ds-primary);
      outline-offset: 2px;
    }
    .sr-only {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }
    input[type="checkbox"]:focus-visible,
    input[type="radio"]:focus-visible {
      outline: 2px solid var(--ds-primary);
      outline-offset: 2px;
    }
    .text-ds-accent { color: var(--ds-primary); }
    .text-ds-muted { color: var(--ds-on-surface-variant); }
    .text-ds-success { color: var(--ds-secondary); }
    .text-ds-success { color: var(--ds-secondary); }
    .text-ds-lime { color: var(--ds-on-primary-container); }
    .bg-ds-lime { background: var(--ds-primary-container); }
    .border-ds { border-color: var(--ds-border); }
    .domain-card {
      background: #ffffff;
      border: 1px solid var(--ds-border);
      border-radius: 0.75rem;
      overflow: hidden;
      box-shadow: var(--ds-shadow);
    }
    .domain-card-icon {
      background: var(--ds-surface-container-low);
      border: 1px solid var(--ds-border);
      color: var(--ds-secondary);
    }
    .history-row:hover { background: var(--ds-surface-container-low) !important; }
    .history-table-wrap tbody tr:nth-child(even) { background: #fafafa; }
    .rev-badge {
      display: inline-flex;
      padding: 0.125rem 0.5rem;
      border-radius: 0.375rem;
      font-size: 11px;
      font-family: 'Space Mono', monospace;
      background: rgba(0, 103, 127, 0.08);
      color: var(--ds-secondary);
      border: 1px solid rgba(0, 103, 127, 0.2);
    }
    .rev-badge-v1 {
      background: var(--ds-surface-container-low);
      color: var(--ds-on-surface-variant);
      border: 1px solid var(--ds-border);
    }
    .ai-badge {
      display: inline-flex;
      padding: 0.125rem 0.375rem;
      border-radius: 0.25rem;
      font-size: 9px;
      font-weight: 600;
      background: rgba(83, 102, 0, 0.1);
      color: var(--ds-primary);
      border: 1px solid rgba(83, 102, 0, 0.2);
    }
    .view-toggle-active {
      background: var(--ds-primary-container);
      color: var(--ds-on-surface);
      font-weight: 600;
      border: 1px solid var(--ds-on-surface);
      box-shadow: 1px 1px 0 var(--ds-on-surface);
    }
    .view-toggle-inactive {
      color: var(--ds-on-surface-variant);
    }
    .view-toggle-inactive:hover { color: var(--ds-on-surface); background: var(--ds-surface-container-low); }
    .kpi-value { color: var(--ds-on-surface); font-family: 'Space Mono', monospace; }
    .kpi-label { color: var(--ds-on-surface-variant); font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600; }
    .kpi-icon {
      background: var(--ds-surface-container-low);
      border: 1px solid var(--ds-border);
      color: var(--ds-secondary);
    }
    .rule-tint-teal,
    .glass-card.rule-tint-teal { background: #eef6f0; border: 1px solid var(--ds-border); }
    .rule-tint-cyan,
    .glass-card.rule-tint-cyan { background: #eef8fa; border: 1px solid var(--ds-border); }
    .rule-tint-olive,
    .glass-card.rule-tint-olive { background: #f4f6ee; border: 1px solid var(--ds-border); }
    .rule-tint-rose,
    .glass-card.rule-tint-rose { background: #faf0f4; border: 1px solid var(--ds-border); }
    .rule-icon-teal { background: rgba(0, 103, 127, 0.1); border: 1px solid rgba(0, 103, 127, 0.25); color: var(--ds-secondary); }
    .rule-icon-cyan { background: rgba(0, 210, 255, 0.12); border: 1px solid rgba(0, 103, 127, 0.2); color: var(--ds-secondary); }
    .rule-icon-olive { background: rgba(83, 102, 0, 0.1); border: 1px solid rgba(83, 102, 0, 0.25); color: var(--ds-primary); }
    .rule-icon-rose { background: rgba(189, 0, 66, 0.08); border: 1px solid rgba(189, 0, 66, 0.2); color: var(--ds-tertiary); }
    .app-header {
      background: var(--ds-bg);
      border-bottom: 1px solid var(--ds-border);
    }
    .bg-ds-surface-low { background: var(--ds-surface-container-low); }
    .preset-chip {
      padding: 0.25rem 0.625rem;
      font-size: 11px;
      border-radius: 0.375rem;
      border: 1px solid var(--ds-border);
      background: #fff;
      color: var(--ds-on-surface);
      transition: background 0.12s ease;
    }
    .preset-chip:hover { background: var(--ds-surface-container-low); }
    .chroma-stat-docs { color: var(--ds-secondary); }
    .chroma-stat-domains { color: var(--ds-primary); }
    .chroma-stat-space { color: var(--ds-secondary); }
    .modal-overlay-bg { background: rgba(28, 27, 27, 0.45); }
    .modal-table thead { background: var(--ds-surface-container-low); }
    .modal-table th {
      font-size: 10px;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: var(--ds-on-surface-variant);
      font-family: 'Space Mono', monospace;
      font-weight: 700;
      padding: 0.75rem;
    }
    .modal-table td {
      padding: 0.75rem;
      color: var(--ds-on-surface);
      vertical-align: middle;
    }
    .modal-table .doc-id {
      font-family: 'Space Mono', monospace;
      font-size: 11px;
      color: var(--ds-on-surface-variant);
      word-break: break-all;
    }
    .footer-bar {
      border-top: 1px solid var(--ds-border);
      color: var(--ds-on-surface-variant);
    }
    .dossier-modal-card {
      background: #ffffff;
      border: 1px solid var(--ds-border);
      color: var(--ds-on-surface);
    }
    .dossier-domain-chip {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.35rem 0.65rem;
      background: #ffffff;
      border: 1px solid var(--ds-border);
      border-radius: 0.5rem;
      font-size: 11px;
      color: var(--ds-on-surface);
      cursor: pointer;
    }
    .dossier-domain-chip:hover { background: var(--ds-surface-container-low); }
    .dossier-domain-chip input { accent-color: var(--ds-primary); }
    .dossier-domain-chip .domain-name {
      font-family: 'Space Mono', monospace;
      color: var(--ds-on-surface);
    }
    .preview-modal-fullscreen {
      position: fixed !important;
      inset: 0.75rem !important;
      width: calc(100vw - 1.5rem) !important;
      max-width: none !important;
      height: calc(100vh - 1.5rem) !important;
      max-height: none !important;
      border-radius: 1rem !important;
      z-index: 60 !important;
    }
    .preview-tab {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.4rem 0.8rem;
      border-radius: 0.5rem;
      border: 1px solid var(--ds-border);
      background: #ffffff;
      color: var(--ds-on-surface-variant);
      font-size: 11px;
      font-weight: 600;
      white-space: nowrap;
      transition: all 0.15s ease;
      cursor: pointer;
    }
    .preview-tab:hover {
      background: var(--ds-surface-container-low);
      color: var(--ds-on-surface);
      border-color: var(--ds-outline);
    }
    .preview-tab-on {
      background: var(--ds-primary-container) !important;
      color: var(--ds-on-surface) !important;
      border-color: var(--ds-on-surface) !important;
      box-shadow: 1px 1px 0 var(--ds-on-surface);
    }
    .preview-reading {
      color: var(--ds-on-surface);
      font-size: 14px;
      line-height: 1.75;
    }
    .preview-reading h1, .preview-reading h2, .preview-reading h3, .preview-reading h4 {
      font-family: 'Space Grotesk', sans-serif;
      line-height: 1.3;
    }
    .preview-reading h1 {
      font-size: 1.5rem;
      font-weight: 700;
      margin: 1.35rem 0 0.6rem;
      padding-bottom: 0.4rem;
      border-bottom: 2px solid var(--ds-border);
      color: var(--ds-on-surface);
    }
    .preview-reading h2 {
      font-size: 1.25rem;
      font-weight: 700;
      margin: 1.15rem 0 0.45rem;
      color: var(--ds-primary);
    }
    .preview-reading h3 {
      font-size: 1.1rem;
      font-weight: 600;
      margin: 0.95rem 0 0.35rem;
      color: var(--ds-secondary);
    }
    .preview-reading h4 {
      font-size: 0.95rem;
      font-weight: 600;
      margin: 0.8rem 0 0.3rem;
      color: var(--ds-on-surface);
    }
    .preview-reading p {
      margin: 0.6rem 0;
      color: var(--ds-on-surface);
    }
    .preview-reading ul {
      margin: 0.5rem 0 0.75rem 1.35rem;
      list-style: disc;
    }
    .preview-reading ol {
      margin: 0.5rem 0 0.75rem 1.35rem;
      list-style: decimal;
    }
    .preview-reading li {
      margin: 0.3rem 0;
      color: var(--ds-on-surface);
    }
    .preview-reading a, .preview-link {
      color: var(--ds-secondary);
      text-decoration: underline;
      text-underline-offset: 2px;
      font-weight: 500;
      transition: color 0.12s ease;
    }
    .preview-reading a:hover, .preview-link:hover {
      color: var(--ds-primary);
    }
    .preview-reading strong {
      font-weight: 700;
      color: var(--ds-on-surface);
    }
    .preview-reading blockquote {
      border-left: 3px solid var(--ds-primary);
      padding: 0.5rem 0.9rem;
      margin: 0.85rem 0;
      background: var(--ds-surface-container-low);
      border-radius: 0 0.5rem 0.5rem 0;
      color: var(--ds-on-surface-variant);
      font-style: italic;
    }
    .preview-reading hr {
      margin: 1.25rem 0;
      border: 0;
      border-top: 1px solid var(--ds-border);
    }
    .preview-inline-code {
      background: var(--ds-surface-container-low);
      color: var(--ds-secondary);
      padding: 0.15rem 0.35rem;
      border-radius: 0.25rem;
      font-family: 'Space Mono', monospace;
      font-size: 0.82em;
      border: 1px solid var(--ds-border);
    }
    .preview-code-block {
      margin: 0.9rem 0;
      border-radius: 0.75rem;
      overflow: hidden;
      border: 1px solid #1e293b;
      background: #020617;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    }
    .preview-code-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.45rem 0.85rem;
      background: #0f172a;
      border-bottom: 1px solid #1e293b;
      font-family: 'Space Mono', monospace;
      font-size: 11px;
      color: #94a3b8;
    }
    .preview-code-pre {
      padding: 0.9rem 1.1rem;
      margin: 0;
      overflow-x: auto;
      color: #f1f5f9;
      font-family: 'Space Mono', monospace;
      font-size: 12px;
      line-height: 1.65;
    }
    .preview-md-table {
      width: 100%;
      border-collapse: collapse;
      margin: 0.9rem 0;
      font-size: 12px;
      background: #ffffff;
      border: 1px solid var(--ds-border);
      border-radius: 0.5rem;
      overflow: hidden;
    }
    .preview-md-table th {
      background: var(--ds-surface-container-low);
      color: var(--ds-on-surface);
      padding: 0.55rem 0.85rem;
      font-weight: 700;
      font-family: 'Space Mono', monospace;
      text-align: left;
      border-bottom: 2px solid var(--ds-border);
    }
    .preview-md-table td {
      padding: 0.5rem 0.85rem;
      border-bottom: 1px solid var(--ds-border);
      color: var(--ds-on-surface);
    }
    .preview-md-table tr:last-child td {
      border-bottom: none;
    }
    .preview-md-table tr:hover td {
      background: var(--ds-surface-container-low);
    }
    .ask-answer p { margin: 0 0 0.55rem; }
    .ask-answer ol { margin: 0.25rem 0 0.6rem 1.15rem; list-style: decimal; }
    .ask-answer li { margin: 0.35rem 0; }
    .ask-answer strong { font-weight: 700; }
    .dossier-markdown-view {
      background: var(--ds-surface-container-low);
      border: 1px solid var(--ds-border);
      color: var(--ds-on-surface);
      font-family: 'Space Mono', ui-monospace, monospace;
      font-size: 12px;
      line-height: 1.65;
      white-space: pre-wrap;
    }
  </style>
</head>
<body class="app-shell min-h-screen font-sans selection:bg-[#d4ff00] selection:text-[#1c1b1b]">
  <a href="#mainContent" class="skip-link">Skip to main content</a>
  <!-- Toast Notification Stack Container -->
  <div id="toastContainer" class="fixed top-5 right-5 z-[9999] flex flex-col gap-2.5 pointer-events-none max-w-sm w-full" role="region" aria-label="Notifications" aria-live="polite"></div>

  <div class="max-w-7xl mx-auto px-4 py-8">
    <!-- Header -->
    <header class="app-header mb-6 pb-4 relative">
      <div class="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <h1 class="text-2xl sm:text-3xl font-extrabold glow-heading tracking-tight">
            CRAWL <span class="text-ds-accent">//</span> ETHIC
          </h1>
          <p class="text-ds-muted text-xs sm:text-sm mt-1 font-mono tracking-wide">
            Autonomous Web Ingestion Node
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <span id="engineVersionBadge" class="px-2.5 py-1 text-[10px] font-mono font-semibold uppercase tracking-wider text-ds-accent border border-ds rounded bg-ds-surface-low">ETHIC ENGINE V1.4</span>
          <button type="button" id="headerThemeBtn" onclick="openThemeStudioModal()" aria-haspopup="dialog" aria-expanded="false" aria-controls="themeStudioModal"
                  class="px-3 py-1.5 text-ds-accent border border-ds rounded text-[10px] font-mono font-semibold flex items-center gap-1.5 hover:bg-ds-surface-low bg-ds-surface-low transition-all">
            <i class="fa-solid fa-palette text-[10px] text-purple-600" aria-hidden="true"></i>
            <span>THEME & DESIGN</span>
            <span id="activeThemePill" class="px-1.5 py-0.5 rounded text-[9px] bg-white border border-ds text-slate-700 font-mono">Light HUD</span>
          </button>
          <button type="button" id="headerSchedulesBtn" onclick="openSchedulesModal()" aria-haspopup="dialog" aria-expanded="false" aria-controls="schedulesModal"
                  class="px-3 py-1.5 text-ds-accent border border-ds rounded text-[10px] font-mono font-semibold flex items-center gap-1.5 hover:bg-ds-surface-low bg-ds-surface-low transition-all">
            <i class="fa-solid fa-clock text-[10px] text-blue-600" aria-hidden="true"></i>
            <span>MONITORS</span>
            <span id="headerSchedulesCount" class="px-1.5 py-0.5 rounded text-[9px] bg-white border border-ds text-slate-700 font-mono">0</span>
          </button>
          <button type="button" id="headerBenchmarkBtn" onclick="openCompetitorModal()" aria-haspopup="dialog" aria-expanded="false" aria-controls="competitorModal"
                  class="px-3 py-1.5 text-ds-accent border border-ds rounded text-[10px] font-mono font-semibold flex items-center gap-1.5 hover:bg-ds-surface-low bg-ds-surface-low transition-all">
            <i class="fa-solid fa-chart-simple text-[10px] text-amber-600" aria-hidden="true"></i>
            <span>BENCHMARK</span>
          </button>
          <button type="button" id="headerBlueprintBtn" onclick="openBlueprintModal()" aria-haspopup="dialog" aria-expanded="false" aria-controls="blueprintModal"
                  class="px-3 py-1.5 text-ds-accent border border-ds rounded text-[10px] font-mono font-semibold flex items-center gap-1.5 hover:bg-ds-surface-low bg-ds-surface-low transition-all">
            <i class="fa-solid fa-camera-retro text-[10px] text-teal-600" aria-hidden="true"></i>
            <span>BLUEPRINT</span>
          </button>
          <button type="button" id="headerStoreBadge" onclick="openChromaStoreModal()" aria-haspopup="dialog" aria-expanded="false" aria-controls="chromaStoreModal"
                  class="px-3 py-1.5 text-ds-accent border border-ds rounded text-[10px] font-mono font-semibold flex items-center gap-2 hover:bg-ds-surface-low bg-ds-surface-low">
            <span class="w-1.5 h-1.5 rounded-full status-dot-active" aria-hidden="true"></span>
            <i class="fa-solid fa-database text-[10px]" aria-hidden="true"></i>
            <span>CHROMA ACTIVE</span>
            <span id="headerStoreCount" class="text-ds-muted">0</span>
            <span class="sr-only">Open vector store inspector</span>
          </button>
          <a href="/docs" target="_blank" rel="noopener noreferrer" class="px-3 py-1.5 text-ds-muted text-[10px] font-mono border border-ds rounded hover:text-ds-accent hover:border-[#757a60] flex items-center gap-1.5">
            <i class="fa-solid fa-code text-[9px]" aria-hidden="true"></i> API
          </a>
        </div>
      </div>
    </header>

    <main id="mainContent">

    <!-- Ethical Rules Banner (compact) -->
    <div class="hidden lg:grid grid-cols-4 gap-3 mb-6">
      <!-- Rule 1 -->
      <div class="glass-card rule-tint-teal p-4 rounded-xl relative overflow-hidden group hover:-translate-y-0.5 hover:shadow-xl transition-all duration-200 min-w-[260px] snap-start shrink-0 lg:min-w-0 lg:shrink">
        <div class="flex items-start gap-3">
          <div class="w-8 h-8 rounded-lg rule-icon-teal flex items-center justify-center shrink-0">
            <i class="fa-solid fa-robot text-sm"></i>
          </div>
          <div>
            <div class="text-ds-success font-bold text-xs uppercase tracking-wider mb-1">Rule 1: Robots.txt</div>
            <div class="text-xs text-ds-muted leading-snug">Auto-validates Allow/Disallow directives before crawling.</div>
          </div>
        </div>
      </div>

      <!-- Rule 2 -->
      <div class="glass-card rule-tint-cyan p-4 rounded-xl relative overflow-hidden group hover:-translate-y-0.5 hover:shadow-xl transition-all duration-200 min-w-[260px] snap-start shrink-0 lg:min-w-0 lg:shrink">
        <div class="flex items-start gap-3">
          <div class="w-8 h-8 rounded-lg rule-icon-cyan flex items-center justify-center shrink-0">
            <i class="fa-solid fa-stopwatch text-sm"></i>
          </div>
          <div>
            <div class="text-ds-success font-bold text-xs uppercase tracking-wider mb-1">Rule 2: Politeness</div>
            <div class="text-xs text-ds-muted leading-snug">Enforces rate limit pauses & dynamic 429 backoff.</div>
          </div>
        </div>
      </div>

      <!-- Rule 3 -->
      <div class="glass-card rule-tint-olive p-4 rounded-xl relative overflow-hidden group hover:-translate-y-0.5 hover:shadow-xl transition-all duration-200 min-w-[260px] snap-start shrink-0 lg:min-w-0 lg:shrink">
        <div class="flex items-start gap-3">
          <div class="w-8 h-8 rounded-lg rule-icon-olive flex items-center justify-center shrink-0">
            <i class="fa-solid fa-id-badge text-sm"></i>
          </div>
          <div>
            <div class="text-ds-accent font-bold text-xs uppercase tracking-wider mb-1">Rule 3: Bot Identity</div>
            <div class="text-xs text-ds-muted leading-snug">Transparent User-Agent with contact email & version.</div>
          </div>
        </div>
      </div>

      <!-- Rule 4 -->
      <div class="glass-card rule-tint-rose p-4 rounded-xl relative overflow-hidden group hover:-translate-y-0.5 hover:shadow-xl transition-all duration-200 min-w-[260px] snap-start shrink-0 lg:min-w-0 lg:shrink">
        <div class="flex items-start gap-3">
          <div class="w-8 h-8 rounded-lg rule-icon-rose flex items-center justify-center shrink-0">
            <i class="fa-solid fa-sitemap text-sm"></i>
          </div>
          <div>
            <div class="text-[#bd0042] font-bold text-xs uppercase tracking-wider mb-1">Rule 4: Sitemaps</div>
            <div class="text-xs text-ds-muted leading-snug">Recursive sitemap XML & Gzip auto-discovery engine.</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="flex flex-wrap items-center gap-1 mb-5 p-1 rounded-lg border border-[#1c1b1b] bg-white w-fit shadow-[2px_2px_0_#1c1b1b]" role="tablist" aria-label="Dashboard sections">
      <button type="button" id="tabCrawlBtn" role="tab" aria-selected="true" aria-controls="crawlingSection" onclick="switchMode('crawl')" class="hud-tab-active px-4 py-1.5 text-xs font-mono flex items-center gap-2">
        <i class="fa-solid fa-network-wired" aria-hidden="true"></i> INGEST
      </button>
      <button type="button" id="tabScrapeBtn" role="tab" aria-selected="false" aria-controls="crawlingSection" onclick="switchMode('scrape')" class="px-4 py-1.5 rounded text-xs font-mono text-ds-muted hover:text-ds-accent transition-all flex items-center gap-2">
        <i class="fa-solid fa-magnifying-glass" aria-hidden="true"></i> SCRAPE
      </button>
      <button type="button" id="tabHistoryBtn" role="tab" aria-selected="false" aria-controls="historySection" onclick="switchMode('history')" class="px-4 py-1.5 rounded text-xs font-mono text-ds-muted hover:text-ds-accent transition-all flex items-center gap-2">
        <i class="fa-solid fa-brain" aria-hidden="true"></i> KNOWLEDGE
        <span id="tabCountBadge" class="text-ds-accent text-[10px] px-1.5 font-mono">0</span>
      </button>
    </div>

    <!-- CRAWLING & SCRAPING SECTION -->
    <div id="crawlingSection" role="tabpanel" aria-labelledby="tabCrawlBtn" class="space-y-4">

      <!-- Split View Status Bar -->
      <div id="splitStatusBar" class="ethic-status-bar flex flex-wrap items-center justify-between gap-3 font-mono">
        <div class="flex items-center gap-3 text-ds-muted">
          <span class="ethic-label">Split View Control</span>
          <span class="text-ds-accent">|</span>
          <span class="ethic-label text-ds-accent">Live Status</span>
        </div>
        <div class="flex flex-wrap items-center gap-4 text-[10px]">
          <span id="guardrailsStatus" class="px-2 py-0.5 rounded bg-[#00d2ff] border border-[#1c1b1b] text-[#1c1b1b] font-bold text-[10px] uppercase"><i class="fa-solid fa-shield-halved mr-1"></i>Guardrails Active</span>
          <span id="ethicsStatus" class="text-ds-muted">Ethics Check: <span class="text-ds-accent">Robots.txt OK</span></span>
          <span id="engineQueueStatus" class="text-ds-muted">Engine: <span id="engineQueueLabel">Ethic — Queue: 0/0</span></span>
        </div>
      </div>

      <!-- 3-Column Ingest Grid -->
      <div id="ingestSplitGrid" class="grid grid-cols-1 xl:grid-cols-3 gap-4">

      <!-- LEFT: Ingest Config -->
      <div class="ethic-panel p-4" id="ingestPanel">
        <!-- Crawler Mode Form -->
        <div id="crawlerForm">
          <div class="ethic-label mb-3">Choose Mode / Vector Ingest Playbook</div>

          <div class="mb-4">
            <select id="playbookSelect" onchange="applyCrawlPreset(this.value); updatePlaybookDesc(this.value)" class="w-full text-xs mb-2">
              <option value="rag_ingest" selected>Doc Knowledge Base</option>
              <option value="smoke_test">Quick Smoke Test</option>
              <option value="competitor_intel">Competitor Intel</option>
              <option value="ecommerce_catalog">E-Commerce Catalog</option>
              <option value="dynamic_spa">Dynamic SPA / React</option>
              <option value="live_growth_audit">Live Growth Audit</option>
              <option value="polite_stealth">Polite Stealth</option>
            </select>
            <p id="playbookDesc" class="text-[10px] text-ds-muted leading-relaxed font-mono">Optimized for API docs, technical references, code syntax preservation. Sitemap discovery, semantic boilerplate strip, Chroma vector ingest.</p>
            <div id="crawlPresetIndicator" class="hidden text-[10px] text-ds-accent font-mono flex items-center gap-1 mt-2">
              <i class="fa-solid fa-circle-check"></i> <span id="crawlPresetIndicatorText"></span>
            </div>
          </div>

          <div class="mb-4">
            <label class="ethic-label block mb-1.5">Target URL</label>
            <input id="targetUrl" type="url" placeholder="https://stripe.com/docs" value="https://example.com" class="w-full px-3 py-2">
          </div>

          <div class="pt-2 space-y-2.5">
            <button id="btnCrawl" onclick="startCrawl()" class="cta-primary w-full py-2.5 flex items-center justify-center gap-2">
              <i class="fa-solid fa-play text-[10px]"></i> INITIATE CRAWL
            </button>
            <div class="grid grid-cols-2 gap-2">
              <button type="button" onclick="checkRobots()" class="btn-ghost py-1.5 rounded flex items-center justify-center gap-1">
                <i class="fa-solid fa-shield-halved text-[10px]"></i> Robots
              </button>
              <button type="button" onclick="inspectSitemap()" class="btn-ghost py-1.5 rounded flex items-center justify-center gap-1">
                <i class="fa-solid fa-diagram-project text-[10px]"></i> Sitemap
              </button>
            </div>
          </div>

          <div id="crawlCustomPresetsContainer" class="hidden"><div id="crawlCustomPresetsList"></div></div>
          <input id="maxPages" type="hidden" value="35">
          <input id="maxDepth" type="hidden" value="3">
          <input id="delay" type="hidden" value="1.0">
          <select id="strategy" class="sr-only" onchange="updateEngineDesc(this.value)">
            <option value="auto">Auto</option>
            <option value="http" selected>HTTP only</option>
            <option value="browser">Headless browser</option>
          </select>
          <p id="engineHint" class="sr-only">Fast HTTP engine</p>
          <input id="respectRobots" type="checkbox" checked class="sr-only">
          <input id="useSitemap" type="checkbox" checked class="sr-only">
          <input id="crawlUseCache" type="checkbox" class="sr-only">
          <input id="crawlEnableAi" type="checkbox" onchange="toggleCrawlAiInputs()" class="sr-only">

          <details class="mt-4 text-[10px]">
            <summary class="ethic-label cursor-pointer hover:text-ds-accent">Advanced / RPA / AI</summary>
            <div class="mt-3 space-y-3">
              <div id="crawlAiConfigSection" class="hidden space-y-3 p-3 rounded-xl border border-ds bg-[#fafafa]">
                <div>
                  <label class="ethic-label block mb-1">AI Schema Template</label>
                  <select id="crawlAiSchema" class="w-full px-3 py-1.5 text-xs">
                    <option value="company_profile">🏢 Company & Product Intelligence (What they do, Offerings, Market Purpose)</option>
                    <option value="article">Article / Blog Post (Title, Summary, Key Points)</option>
                    <option value="product">Product / Pricing / Services (Name, Price, Features)</option>
                    <option value="faq">FAQ / Q&A (Question & Answer Pairs)</option>
                    <option value="custom">Custom Prompt Instructions</option>
                  </select>
                </div>
                <div>
                  <label class="ethic-label block mb-1">NVIDIA NIM Model</label>
                  <select id="crawlAiModel" class="w-full px-3 py-1.5 text-xs">
                    <option value="deepseek-ai/deepseek-v4.1-flash" selected>🚀 DeepSeek-v4.1 Flash (Ultra-Fast 2.5s Reasoning)</option>
                    <option value="nvidia/nemotron-3.5-lightning-30b-a3b">⚡ Nemotron 3.5 Lightning (Fast 30B MoE)</option>
                    <option value="moonshotai/kimi-k3">🧠 Moonshot Kimi-k3 (2.8T MoE Deep Reasoning)</option>
                    <option value="z-ai/glm-5.3-flash">🎨 GLM-5.3 Flash (320B Multimodal)</option>
                    <option value="meta/llama-3.2-11b-vision-instruct">⚖️ Llama 3.2 11B Vision</option>
                    <option value="nvidia/nemotron-parse-2.0">👁️ Nemotron Parse 2.0 (Document & Table)</option>
                  </select>
                </div>
                <div>
                  <label class="ethic-label block mb-1">Custom Prompt Instructions (Optional)</label>
                  <textarea id="crawlAiPrompt" rows="2" placeholder="e.g. Extract pricing plans, studio features, and highlights..."
                            class="w-full px-3 py-1.5 text-xs"></textarea>
                </div>
              </div>
            </div>

            <!-- RPA Automation Playbook (Expandable) -->
            <details id="crawlRpaDetails" class="group border border-ds rounded-xl p-3 text-xs bg-[#fafafa]">
              <summary class="flex items-center justify-between cursor-pointer font-medium text-[#1c1b1b] gap-2">
                <span class="flex items-center gap-2 min-w-0">
                  <i class="fa-solid fa-robot text-ds-muted"></i>
                  <span class="truncate">RPA playbook</span>
                  <span id="crawlRpaCountBadge" class="chip-export shrink-0">Auto-modals on</span>
                </span>
                <i class="fa-solid fa-chevron-down text-ds-muted group-open:rotate-180 transition-transform shrink-0"></i>
              </summary>

              <div class="mt-3 pt-3 border-t border-ds space-y-3">
                <div class="space-y-1.5">
                  <label class="text-[11px] font-bold text-ds-muted uppercase tracking-wider block">Pre-Built Automation Recipes:</label>
                  <div class="flex flex-col gap-1.5 text-[#1c1b1b]">
                    <label class="flex items-center gap-2 cursor-pointer hover:text-ds-primary">
                      <input type="checkbox" id="crawlRpaDismissCookies" checked class="rounded border-ds text-purple-600 focus:ring-0">
                      <span>🛡️ Auto-Dismiss Cookie & Modal Banners (OneTrust, Cookiebot, Popups)</span>
                    </label>
                    <label class="flex items-center gap-2 cursor-pointer hover:text-ds-primary">
                      <input type="checkbox" id="crawlRpaExpandAccordions" onchange="toggleRpaPreset('crawl', 'expand_accordions', this.checked)" class="rounded border-ds text-purple-600 focus:ring-0">
                      <span>📂 Auto-Expand Collapsed Accordions & FAQ disclosures</span>
                    </label>
                    <label class="flex items-center gap-2 cursor-pointer hover:text-ds-primary">
                      <input type="checkbox" id="crawlRpaToggleAnnual" onchange="toggleRpaPreset('crawl', 'toggle_annual_pricing', this.checked)" class="rounded border-ds text-purple-600 focus:ring-0">
                      <span>💳 Toggle SaaS Annual Pricing discounts</span>
                    </label>
                  </div>
                </div>

                <!-- AI Natural Language RPA Copilot -->
                <div class="bg-purple-50/60 p-2.5 rounded-lg border border-purple-200 space-y-2">
                  <div class="flex items-center justify-between">
                    <span class="text-[11px] font-bold text-purple-900 flex items-center gap-1.5">
                      <i class="fa-solid fa-wand-magic-sparkles text-purple-600"></i> AI RPA Step Generator
                    </span>
                    <span class="text-[11px] text-purple-700 font-mono">DeepSeek V4.1 Flash</span>
                  </div>
                  <div class="flex gap-1.5">
                    <input id="crawlRpaAiPrompt" type="text" placeholder="e.g. Click 'Specs' tab, scroll down 500px, wait 1s"
                           class="flex-1 bg-white border border-purple-200 rounded px-2 py-1 text-[11px] text-[#1c1b1b] focus:outline-none focus:border-purple-500">
                    <button type="button" onclick="generateAiRpaSteps('crawl')" class="px-2.5 py-1 bg-purple-600 hover:bg-purple-500 text-white rounded text-[11px] font-semibold transition flex items-center gap-1 shadow">
                      <i class="fa-solid fa-bolt"></i> Generate
                    </button>
                  </div>
                </div>

                <!-- Active Step Playbook List -->
                <div class="space-y-1.5">
                  <div class="flex items-center justify-between">
                    <span class="text-[11px] font-bold text-ds-muted uppercase tracking-wider">Active Steps Sequence:</span>
                    <button type="button" onclick="showAddCustomRpaStep('crawl')" class="text-[11px] text-purple-700 hover:text-purple-900 font-semibold flex items-center gap-1">
                      <i class="fa-solid fa-plus"></i> Add Custom Step
                    </button>
                  </div>
                  <div id="crawlRpaStepsList" class="space-y-1 max-h-36 overflow-y-auto pr-1">
                    <div class="text-[11px] text-ds-muted italic p-2 bg-white rounded border border-dashed border-ds text-center">
                      No custom steps added. Enable recipes above or generate with AI.
                    </div>
                  </div>
                </div>
              </div>
            </details>
          </details>
        </div>

        <!-- Scraper Mode Form -->
        <div id="scraperForm" class="hidden">
          <div class="flex items-center justify-between mb-4 border-b border-ds pb-3">
            <h2 class="text-lg font-bold text-[#1c1b1b] flex items-center gap-2">
              <i class="fa-solid fa-filter text-ds-success text-sm"></i> Single Page Scraper
            </h2>
            <span class="chip-export">Single Page</span>
          </div>

          <div class="mb-4 p-3 rounded-xl border border-ds bg-[#f6f3f2] space-y-2">
            <div class="ethic-label flex items-center gap-1.5">
              <i class="fa-solid fa-wand-magic-sparkles"></i> Scraper Quick Presets
            </div>
            <div class="flex flex-wrap gap-1.5">
              <button type="button" onclick="applyScrapePreset('instant_markdown')" class="preset-chip">⚡ Instant Markdown</button>
              <button type="button" onclick="applyScrapePreset('company_profile')" class="preset-chip">🏢 Company Profile</button>
              <button type="button" onclick="applyScrapePreset('product_details')" class="preset-chip">🛍️ Product Details</button>
              <button type="button" onclick="applyScrapePreset('clean_article')" class="preset-chip">📰 Clean Article</button>
              <button type="button" onclick="applyScrapePreset('dynamic_spa')" class="preset-chip">🖥️ Dynamic JS / SPA</button>
            </div>
            <div id="scrapePresetIndicator" class="hidden text-[11px] text-ds-accent font-mono flex items-center gap-1 pt-1">
              <i class="fa-solid fa-circle-check"></i> <span id="scrapePresetIndicatorText"></span>
            </div>
          </div>

          <div class="space-y-4">
            <div>
              <label class="ethic-label block mb-1.5">Target Page URL</label>
              <div class="flex gap-2">
                <input id="scrapeUrl" type="url" placeholder="https://example.com" value="https://example.com" class="w-full px-3 py-2 text-sm">
                <button type="button" onclick="openElementPicker(document.getElementById('scrapeUrl').value, 'scraper')" class="btn-secondary text-xs px-3 py-2 flex items-center gap-1.5 whitespace-nowrap shrink-0" title="Visually inspect and pick elements">
                  <i class="fa-solid fa-crosshairs text-purple-600"></i> Pick Element
                </button>
              </div>
            </div>

            <div>
              <label class="ethic-label block mb-1.5">Engine Strategy</label>
              <select id="scrapeStrategy" class="w-full min-w-0 px-3 py-2 text-sm">
                <option value="auto">Auto</option>
                <option value="http">HTTP only</option>
                <option value="browser">Headless browser</option>
              </select>
            </div>

            <div class="pt-2 border-t border-ds space-y-2">
              <label class="ethic-toggle cursor-pointer"><span>Respect robots.txt (Rule 1)</span><input id="scrapeRespectRobots" type="checkbox" checked></label>
              <label class="ethic-toggle cursor-pointer"><span>Use ChromaDB cache</span><input id="scrapeUseCache" type="checkbox" checked></label>
              <label class="ethic-toggle cursor-pointer"><span>Extract AI structured data</span><input id="enableAiExtraction" type="checkbox" onchange="toggleAiInputs()"></label>
            </div>

            <div id="aiConfigSection" class="hidden space-y-3 p-3 rounded-xl border border-ds bg-[#fafafa]">
              <div>
                <label class="ethic-label block mb-1">Schema Template</label>
                <select id="aiSchema" class="w-full px-3 py-1.5 text-xs">
                  <option value="company_profile">🏢 Company & Product Intelligence (What they do, Offerings, Market Purpose)</option>
                  <option value="article">Article / Blog Post (Title, Summary, Key Points)</option>
                  <option value="product">E-Commerce Product (Name, Price, Features)</option>
                  <option value="faq">FAQ / Q&A (Question & Answer Pairs)</option>
                  <option value="custom">Custom Prompt Instructions</option>
                </select>
              </div>
              <div>
                <label class="ethic-label block mb-1">NVIDIA NIM Model</label>
                <select id="scrapeAiModel" class="w-full px-3 py-1.5 text-xs">
                  <option value="deepseek-ai/deepseek-v4.1-flash" selected>🚀 DeepSeek-v4.1 Flash (Ultra-Fast 2.5s Reasoning)</option>
                  <option value="nvidia/nemotron-3.5-lightning-30b-a3b">⚡ Nemotron 3.5 Lightning (Fast 30B MoE)</option>
                  <option value="moonshotai/kimi-k3">🧠 Moonshot Kimi-k3 (2.8T MoE Deep Reasoning)</option>
                  <option value="z-ai/glm-5.3-flash">🎨 GLM-5.3 Flash (320B Multimodal)</option>
                  <option value="meta/llama-3.2-11b-vision-instruct">⚖️ Llama 3.2 11B Vision</option>
                  <option value="nvidia/nemotron-parse-2.0">👁️ Nemotron Parse 2.0 (Document & Table)</option>
                </select>
              </div>
              <div>
                <label class="ethic-label block mb-1">Custom Prompt (Optional)</label>
                <textarea id="aiPrompt" rows="2" placeholder="e.g. Extract main topics, pricing tiers, and contact email..."
                          class="w-full px-3 py-1.5 text-xs"></textarea>
              </div>
            </div>
            <details id="scrapeRpaDetails" class="group border border-ds rounded-xl p-3 text-xs bg-[#fafafa]">
              <summary class="flex items-center justify-between cursor-pointer font-medium text-[#1c1b1b] gap-2">
                <span class="flex items-center gap-2 min-w-0">
                  <i class="fa-solid fa-robot text-ds-muted"></i>
                  <span class="truncate">RPA playbook</span>
                  <span id="scrapeRpaCountBadge" class="chip-export shrink-0">Auto-modals on</span>
                </span>
                <i class="fa-solid fa-chevron-down text-ds-muted group-open:rotate-180 transition-transform shrink-0"></i>
              </summary>

              <div class="mt-3 pt-3 border-t border-ds space-y-3">
                <div class="space-y-1.5">
                  <label class="text-[11px] font-bold text-ds-muted uppercase tracking-wider block">Pre-Built Automation Recipes:</label>
                  <div class="flex flex-col gap-1.5 text-[#1c1b1b]">
                    <label class="flex items-center gap-2 cursor-pointer hover:text-ds-primary">
                      <input type="checkbox" id="scrapeRpaDismissCookies" checked class="rounded border-ds text-purple-600 focus:ring-0">
                      <span>🛡️ Auto-Dismiss Cookie & Modal Banners (OneTrust, Cookiebot, Popups)</span>
                    </label>
                    <label class="flex items-center gap-2 cursor-pointer hover:text-ds-primary">
                      <input type="checkbox" id="scrapeRpaExpandAccordions" checked class="rounded border-ds text-purple-600 focus:ring-0">
                      <span>📂 Auto-Expand Collapsed Accordions & FAQ disclosures</span>
                    </label>
                    <label class="flex items-center gap-2 cursor-pointer hover:text-ds-primary">
                      <input type="checkbox" id="scrapeRpaPricingAnnual" class="rounded border-ds text-purple-600 focus:ring-0">
                      <span>🏷️ Toggle SaaS Annual Pricing/discounts</span>
                    </label>
                  </div>
                </div>

                <!-- AI Copilot Natural Language RPA Step Generator -->
                <div class="p-2.5 bg-purple-50/60 border border-purple-200 rounded-lg space-y-2">
                  <div class="flex items-center justify-between text-[11px] text-purple-900 font-semibold">
                    <span class="flex items-center gap-1.5"><i class="fa-solid fa-wand-magic-sparkles text-purple-600"></i> AI RPA Step Generator</span>
                    <span class="text-[11px] text-purple-700 font-mono">DeepSeek V4.1 Flash</span>
                  </div>
                  <div class="flex gap-1.5">
                    <input id="scrapeRpaAiPrompt" type="text" placeholder="e.g. Click Specs tab, scroll down 500px, wait for .reviews"
                           class="flex-1 bg-white border border-purple-200 rounded px-2.5 py-1 text-[11px] text-[#1c1b1b] focus:outline-none focus:border-purple-500"
                           onkeydown="if(event.key==='Enter') generateRpaFromPrompt('scrape')">
                    <button type="button" onclick="generateRpaFromPrompt('scrape')" class="px-2.5 py-1 bg-purple-600 hover:bg-purple-500 text-white font-bold text-[11px] rounded transition flex items-center gap-1 shadow">
                      <i class="fa-solid fa-bolt text-[11px]"></i> Generate
                    </button>
                  </div>
                </div>

                <!-- Custom Step Builder List -->
                <div>
                  <div class="flex items-center justify-between mb-1">
                    <span class="text-[11px] font-bold text-ds-muted uppercase tracking-wider">Active Steps Sequence:</span>
                    <button type="button" onclick="showAddCustomRpaStep('scrape')" class="text-[11px] text-purple-700 hover:text-purple-900 font-semibold flex items-center gap-1">
                      <i class="fa-solid fa-plus"></i> Add Custom Step
                    </button>
                  </div>
                  <div id="scrapeRpaStepsList" class="space-y-1 max-h-36 overflow-y-auto pr-1">
                    <div class="text-[11px] text-ds-muted italic p-2 bg-white rounded border border-dashed border-ds text-center">
                      No custom steps added. Enable recipes above or generate with AI.
                    </div>
                  </div>
                </div>
              </div>
            </details>

            <div class="flex items-center justify-between p-2.5 rounded-xl border border-ds bg-[#fafafa] text-xs">
              <label class="flex items-center gap-2 cursor-pointer font-medium text-[#1c1b1b]">
                <input type="checkbox" id="scrapeCaptureScreenshot" class="rounded border-ds text-purple-600 focus:ring-0">
                <span>🖼️ Capture Full-Page Screenshot (Playwright)</span>
              </label>
              <span class="text-[10px] text-ds-muted font-mono">Archived to disk</span>
            </div>

            <div class="pt-2">
              <button id="btnScrape" onclick="startScrape()" class="cta-primary w-full py-2.5 flex items-center justify-center gap-2">
                <i class="fa-solid fa-bolt text-xs"></i> SCRAPE WEB PAGE
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- CENTER: Precision Guardrails -->
      <div class="ethic-panel p-4" id="guardrailsPanel">
        <div class="ethic-label mb-3">Precision Guardrails</div>
        <div class="space-y-2 mb-4">
          <label class="ethic-toggle"><span>Respect robots.txt</span><input type="checkbox" id="guardRespectRobots" checked onchange="syncGuardrail('respectRobots', this.checked)"></label>
          <label class="ethic-toggle"><span>Allow JS Rendering</span><input type="checkbox" id="guardJsRender" onchange="syncJsRender(this.checked)"></label>
          <label class="ethic-toggle"><span>Force Sitemap XML</span><input type="checkbox" id="guardSitemap" checked onchange="syncGuardrail('useSitemap', this.checked)"></label>
          <label class="ethic-toggle"><span>Semantic Boilerplate Strip</span><input type="checkbox" id="guardSemantic" checked disabled title="Always enabled"></label>
        </div>
        <div class="ethic-slider-row">
          <label><span>Request Delay</span><span id="delaySliderVal" class="text-ds-accent">1.0s</span></label>
          <input type="range" id="delaySlider" min="0.5" max="10" step="0.5" value="1.0" oninput="syncSlider('delay', this.value)">
        </div>
        <div class="ethic-slider-row">
          <label><span>Crawl Depth</span><span id="depthSliderVal" class="text-ds-accent">3</span></label>
          <input type="range" id="depthSlider" min="0" max="5" step="1" value="3" oninput="syncSlider('maxDepth', this.value)">
        </div>
        <div class="ethic-slider-row">
          <label><span>Page Limit</span><span id="pagesSliderVal" class="text-ds-accent">35</span></label>
          <input type="range" id="pagesSlider" min="1" max="100" step="1" value="35" oninput="syncSlider('maxPages', this.value)">
        </div>
        <label class="ethic-toggle mt-2"><span>ChromaDB cache</span><input type="checkbox" id="guardCache" onchange="syncGuardrail('crawlUseCache', this.checked)"></label>
        <label class="ethic-toggle"><span>AI structured extract</span><input type="checkbox" id="guardAi" onchange="document.getElementById('crawlEnableAi').checked=this.checked; toggleCrawlAiInputs()"></label>
      </div>

      <!-- RIGHT: Live Crawl Stream -->
      <div class="ethic-panel p-4 relative min-h-[360px] flex flex-col" id="liveStreamPanel">
        <div class="ethic-label mb-2 flex items-center justify-between">
          <span>Live Crawl Stream</span>
          <span id="streamPulse" class="hidden w-1.5 h-1.5 rounded-full bg-ds-lime status-dot-active"></span>
        </div>
        <div id="liveCrawlStream" class="live-stream flex-1 font-mono" role="log" aria-live="polite">
          <div class="stream-dim">&gt; awaiting ingestion target...</div>
          <div class="stream-dim">&gt; chroma vector store ready</div>
          <div class="stream-dim">&gt; guardrails armed — robots.txt compliance on</div>
        </div>
        <div id="embeddingPanel" class="embedding-panel mt-3 hidden">
          <div class="ethic-label text-ds-accent mb-1">Embedding // Chroma Vector</div>
          <div class="flex items-baseline justify-between gap-2">
            <span id="embeddingChunkCount" class="text-lg font-bold text-ds-accent">0</span>
            <span class="text-ds-muted">CHUNKS CREATED</span>
          </div>
          <div id="embeddingStatus" class="text-ds-accent mt-1 embedding-active">EMBEDDING ACTIVE</div>
          <div id="embeddingMeta" class="text-ds-muted mt-1 text-[9px]">all-MiniLM-L6-v2 · 1000 char chunks · 10% overlap</div>
        </div>
      </div>

      </div><!-- end ingestSplitGrid -->

      <div class="space-y-4">
        <!-- Status Banner -->
        <div id="statusCard" class="glass-card p-4 relative overflow-hidden">
          <div id="statusShimmerBar" class="hidden absolute top-0 left-0 right-0 h-0.5 bg-ds-lime overflow-hidden">
            <div class="w-1/2 h-full opacity-60 bg-ds-lime animate-shimmer"></div>
          </div>
          <div class="flex flex-wrap items-center justify-between gap-3 font-mono text-xs">
            <div class="flex items-center gap-3">
              <div id="statusIndicator" class="w-2 h-2 rounded-full bg-[#00677f] shrink-0 transition-all"></div>
              <span id="statusText" class="text-ds-muted" role="status" aria-live="polite">Ready to ingest.</span>
            </div>
            <div class="flex items-center gap-2.5">
              <div id="statusTimerBadge" class="hidden items-center gap-2 px-2 py-1 rounded border border-ds text-[10px] text-ds-muted">
                <span>Started: <span id="statusStartTime">--:--:--</span></span>
                <span class="text-ds-muted">|</span>
                <span>Elapsed: <span id="statusElapsedTime" class="text-ds-accent">00:00</span></span>
              </div>
              <span id="counterBadge" class="text-[10px] px-2 py-1 rounded border border-ds text-ds-muted">0 pages</span>
            </div>
          </div>
        </div>

        <!-- Export Toolbar (Visible when results available) -->
        <div id="exportToolbar" class="hidden glass-card p-4 flex flex-wrap items-center justify-between gap-3">
          <div class="flex items-center gap-2 text-ds-accent text-sm font-bold">
            <i class="fa-solid fa-file-export"></i> Export Crawled Content:
          </div>
          <div class="flex flex-wrap gap-2">
            <button onclick="exportData('pdf')" class="px-3 py-1.5 bg-white hover:bg-[#f6f3f2] text-xs font-semibold text-ds-muted rounded-lg transition-all flex items-center gap-1.5 border border-ds active:scale-[0.98]">
              <span class="w-1.5 h-1.5 rounded-full bg-red-400"></span> PDF
            </button>
            <button onclick="exportData('md')" class="px-3 py-1.5 bg-white hover:bg-[#f6f3f2] text-xs font-semibold text-ds-muted rounded-lg transition-all flex items-center gap-1.5 border border-ds active:scale-[0.98]">
              <span class="w-1.5 h-1.5 rounded-full bg-indigo-400"></span> Markdown
            </button>
            <button onclick="exportData('txt')" class="px-3 py-1.5 bg-white hover:bg-[#f6f3f2] text-xs font-semibold text-ds-muted rounded-lg transition-all flex items-center gap-1.5 border border-ds active:scale-[0.98]">
              <span class="w-1.5 h-1.5 rounded-full bg-slate-400"></span> Plain Text
            </button>
            <button onclick="exportData('json')" class="px-3 py-1.5 bg-white hover:bg-[#f6f3f2] text-xs font-semibold text-ds-muted rounded-lg transition-all flex items-center gap-1.5 border border-ds active:scale-[0.98]">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> JSON
            </button>
            <button onclick="exportData('csv')" class="px-3 py-1.5 bg-white hover:bg-[#f6f3f2] text-xs font-semibold text-ds-muted rounded-lg transition-all flex items-center gap-1.5 border border-ds active:scale-[0.98]">
              <span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> CSV
            </button>
          </div>
        </div>

        <!-- Results Table -->
        <div class="glass-card p-4">
          <h3 class="ethic-label mb-3 flex items-center justify-between">
            <span>Ingested Pages</span>
            <span id="resultsCount" class="text-ds-muted font-mono font-normal normal-case"></span>
          </h3>
          <div class="overflow-x-auto max-h-96 rounded border border-ds">
            <table class="w-full text-left text-xs data-table">
              <thead class="sticky top-0">
                <tr>
                  <th class="p-3 w-16">Status</th>
                  <th class="p-3">Title / URL</th>
                  <th class="p-3 w-24 whitespace-nowrap">Size</th>
                  <th class="p-3 w-28 whitespace-nowrap">Engine</th>
                  <th class="p-3 w-20 whitespace-nowrap">Time</th>
                  <th class="p-3 w-32 whitespace-nowrap text-right">Actions</th>
                </tr>
              </thead>
              <tbody id="resultsTableBody" class="divide-y divide-[#e5e2e1]">
                <tr>
                  <td colspan="6" class="p-8 text-center text-ds-muted font-mono text-[11px]">
                    &gt; enter target URL and initiate crawl to stream pages
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- KNOWLEDGE & HISTORY SECTION (CHROMADB) -->
    <div id="historySection" role="tabpanel" aria-labelledby="tabHistoryBtn" class="hidden space-y-8">
      <!-- Knowledge Header & 4 KPI Glassmorphic Cards -->
      <div class="space-y-4">
        <div class="glass-card p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 relative overflow-hidden">
          <div>
            <h2 class="text-xl font-bold text-[#1c1b1b] flex items-center gap-2.5">
              <i class="fa-solid fa-brain text-ds-accent"></i> ChromaDB Vector Knowledge Base & Market History
            </h2>
            <p class="text-ds-muted text-xs mt-1 max-w-2xl leading-relaxed">
              All scraped and crawled pages are locally embedded with full temporal growth tracking. Browse grouped by domain, query semantically via RAG, or synthesize cross-competitor dossiers with Moonshot AI Kimi-k3.
            </p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <button onclick="openDossierModal()" class="cta-primary px-4 py-2 text-xs flex items-center gap-2">
              <i class="fa-solid fa-wand-magic-sparkles"></i> Generate Website Report
            </button>
            <button onclick="loadHistory()" class="btn-ghost px-3.5 py-2 rounded-lg flex items-center gap-1.5 active:scale-95">
              <i class="fa-solid fa-arrows-rotate"></i> Refresh
            </button>
          </div>
        </div>

        <!-- 4 KPI Metrics Grid -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="glass-card p-4 flex items-center gap-3.5">
            <div class="w-10 h-10 rounded-lg kpi-icon flex items-center justify-center shrink-0">
              <i class="fa-solid fa-globe text-lg"></i>
            </div>
            <div>
              <div class="kpi-label">Tracked Domains</div>
              <div id="kpiDomains" class="text-xl font-bold kpi-value mt-0.5">0</div>
            </div>
          </div>
          <div class="glass-card p-4 flex items-center gap-3.5">
            <div class="w-10 h-10 rounded-lg kpi-icon flex items-center justify-center shrink-0">
              <i class="fa-solid fa-file-lines text-lg"></i>
            </div>
            <div>
              <div class="kpi-label">Stored Pages</div>
              <div id="kpiPages" class="text-xl font-bold kpi-value mt-0.5">0</div>
            </div>
          </div>
          <div class="glass-card p-4 flex items-center gap-3.5">
            <div class="w-10 h-10 rounded-lg kpi-icon flex items-center justify-center shrink-0">
              <i class="fa-solid fa-database text-lg"></i>
            </div>
            <div>
              <div class="kpi-label">Vector Memory Size</div>
              <div id="kpiSize" class="text-xl font-bold kpi-value mt-0.5">0 KB</div>
            </div>
          </div>
          <div class="glass-card p-4 flex items-center gap-3.5">
            <div class="w-10 h-10 rounded-lg kpi-icon flex items-center justify-center shrink-0">
              <i class="fa-solid fa-brain text-lg"></i>
            </div>
            <div>
              <div class="kpi-label">AI Company Profiles</div>
              <div id="kpiAiProfiles" class="text-xl font-bold kpi-value mt-0.5">0</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Grid: Search & Ask AI -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Card 1: Semantic Vector Search -->
        <div class="glass-card p-6 flex flex-col">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-base font-bold text-[#1c1b1b] flex items-center gap-2">
              <i class="fa-solid fa-magnifying-glass text-ds-success"></i> Semantic Vector Search
            </h3>
            <span class="chip-export">Cosine Distance</span>
          </div>
          <p class="text-ds-muted text-xs mb-4 leading-relaxed">
            Search stored pages by natural language meaning, concepts, or intent (e.g. <i>"pricing details"</i> or <i>"how does API work"</i>).
          </p>

          <div class="space-y-3 mb-4">
            <div class="flex gap-2">
              <input id="searchQuery" type="text" placeholder="Search by meaning or concepts..."
                     onkeydown="if(event.key==='Enter') runSemanticSearch()"
                     class="flex-1 px-3 py-2 text-sm">
              <button onclick="runSemanticSearch()" class="cta-primary px-4 py-2 text-xs flex items-center gap-1.5 active:scale-95">
                <i class="fa-solid fa-magnifying-glass"></i> Search
              </button>
            </div>
            <div>
              <input id="searchDomain" type="text" placeholder="Optional domain filter (e.g. example.com)"
                     class="w-full px-3 py-1.5 text-xs">
            </div>
          </div>

          <!-- Search Results List -->
          <div id="searchResultsContainer" class="flex-1 overflow-y-auto max-h-96 space-y-3">
            <div id="searchPlaceholder" class="p-6 text-center text-ds-muted text-xs">
              Enter a search query to explore crawled content semantically.
            </div>
          </div>
        </div>

        <!-- Card 2: Ask AI (RAG Q&A) -->
        <div class="glass-card p-6 flex flex-col">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-base font-bold text-[#1c1b1b] flex items-center gap-2">
              <i class="fa-solid fa-sparkles text-ds-accent"></i> Ask AI about Crawled Sites (RAG)
            </h3>
            <span class="chip-export">NVIDIA NIM / OpenAI</span>
          </div>
          <p class="text-ds-muted text-xs mb-4 leading-relaxed">
            Answers are generated strictly using vector context retrieved from your stored web pages.
          </p>

          <div class="space-y-3 mb-4">
            <div class="flex gap-2">
              <input id="askQuestion" type="text" placeholder="e.g. What are the key features described across the sites?"
                     onkeydown="if(event.key==='Enter') runAskAi()"
                     class="flex-1 px-3 py-2 text-sm">
              <button onclick="runAskAi()" class="cta-primary px-4 py-2 text-xs flex items-center gap-1.5">
                <i class="fa-solid fa-paper-plane"></i> Ask AI
              </button>
            </div>
          </div>

          <!-- AI Response Area -->
          <div id="askResultContainer" class="flex-1 overflow-y-auto max-h-96 p-4 bg-[#f6f3f2] rounded-xl border border-ds text-xs">
            <div id="askPlaceholder" class="p-6 text-center text-ds-muted">
              Ask any question to synthesize answers across your crawled knowledge.
            </div>
            <div id="askLoading" class="hidden p-6 text-center space-y-2.5 bg-white rounded-xl border border-ds">
              <div class="text-ds-accent font-medium">
                <i class="fa-solid fa-spinner fa-spin mr-2"></i> Querying vector database and generating answer with citations...
              </div>
              <div class="inline-flex items-center gap-3 px-3.5 py-1.5 bg-[#f6f3f2] border border-ds rounded-full text-xs font-mono text-ds-muted">
                <span>Started: <span id="askStartTime" class="text-[#1c1b1b]">--:--:--</span></span>
                <span>|</span>
                <span>Elapsed: <span id="askElapsedTime" class="text-ds-accent font-bold">00:00</span></span>
              </div>
            </div>
            <div id="askContent" class="hidden space-y-3">
              <div id="askCacheBadge" class="hidden text-[11px] font-mono text-ds-success"></div>
              <div id="askAnswerText" class="ask-answer text-[#1c1b1b] leading-relaxed text-sm"></div>
              <div class="pt-3 border-t border-ds">
                <div class="ethic-label mb-2">Sources Cited:</div>
                <div id="askSourcesList" class="flex flex-wrap gap-2"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Card 3: Domain Grouping & Stored Pages Archive -->
      <div class="glass-card p-5 space-y-4">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h3 class="text-base font-bold text-[#1c1b1b] flex items-center gap-2">
              <i class="fa-solid fa-folder-tree text-ds-accent"></i> Stored Domain Knowledge & Change Tracking
            </h3>
            <p class="text-ds-muted text-xs mt-0.5">
              Pages grouped by web domain with temporal revisions (v1, v2) and growth deltas. Recrawl live to detect updates, preview contents, or selectively purge data.
            </p>
          </div>
          <div class="flex flex-wrap items-center gap-2.5">
            <input id="filterHistoryInput" type="text" placeholder="Filter by domain, title, or URL…" oninput="filterHistoryTable()"
                   class="rounded-full px-3.5 py-1.5 text-xs w-56">
            <div class="flex items-center bg-[#f6f3f2] border border-ds rounded-full p-0.5 text-xs">
              <button id="btnViewDomain" onclick="switchHistoryView('domain')" class="px-3 py-1 rounded-full view-toggle-active transition flex items-center gap-1.5">
                <i class="fa-solid fa-folder-tree"></i> Domains
              </button>
              <button id="btnViewFlat" onclick="switchHistoryView('flat')" class="px-3 py-1 rounded-full view-toggle-inactive transition flex items-center gap-1.5">
                <i class="fa-solid fa-list-ul"></i> Flat List
              </button>
            </div>
          </div>
        </div>

        <!-- View 1: Collapsible Domain Cards Container (Default) -->
        <div id="historyDomainCardsContainer" class="space-y-4">
          <div class="p-8 text-center text-ds-muted text-xs">
            <i class="fa-solid fa-spinner fa-spin mr-2"></i> Loading domain knowledge archives...
          </div>
        </div>

        <!-- View 2: Flat List Table Container (Hidden by default) -->
        <div id="historyFlatTableContainer" class="hidden overflow-x-auto max-h-[500px] rounded-xl border border-ds history-table-wrap">
          <table class="data-table w-full text-left text-xs text-slate-300">
            <thead class="sticky top-0 z-10">
              <tr>
                <th class="px-3 py-2.5">Status</th>
                <th class="px-3 py-2.5">Title / URL</th>
                <th class="px-3 py-2.5">Domain</th>
                <th class="px-3 py-2.5">Revision</th>
                <th class="px-3 py-2.5">Size</th>
                <th class="px-3 py-2.5">Crawled</th>
                <th class="px-3 py-2.5">Export</th>
                <th class="px-3 py-2.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody id="historyTableBody" class="divide-y divide-slate-700/50">
              <tr>
                <td colspan="8" class="p-6 text-center text-slate-500">
                  <i class="fa-solid fa-spinner fa-spin mr-2"></i> Loading stored crawl history...
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    </main>

    <!-- GLOBAL PREVIEW MODAL -->
    <div id="previewModal" role="dialog" aria-modal="true" aria-labelledby="previewTitle" class="hidden fixed inset-0 z-50 flex items-center justify-center p-4 modal-overlay-bg backdrop-blur-sm" onclick="if(event.target===this) closePreview()">
      <div id="previewModalDialog" class="dossier-modal-card w-full max-w-5xl rounded-2xl shadow-2xl flex flex-col max-h-[92vh] overflow-hidden modal-card transition-all duration-200">
        <!-- MODAL HEADER: TWO-TIER DESIGN -->
        <div class="flex flex-col gap-2.5 px-5 py-3.5 border-b border-ds bg-white">
          <!-- Tier 1: Title, URL, Badges, Fullscreen, Close -->
          <div class="flex items-center justify-between gap-3">
            <div class="flex items-center gap-3 min-w-0">
              <div class="w-9 h-9 rounded-xl bg-ds-surface-low border border-ds flex items-center justify-center text-ds-accent shrink-0">
                <i class="fa-solid fa-file-lines text-base"></i>
              </div>
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <h4 id="previewTitle" class="text-sm sm:text-base font-bold text-[#1c1b1b] truncate font-heading">Page Content</h4>
                  <span id="previewStatusBadge" class="status-pill ok shrink-0 text-[10px]">200 OK</span>
                  <span id="previewEngineBadge" class="hidden sm:inline-flex px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-ds-surface-low text-ds-muted border border-ds shrink-0">FAST</span>
                </div>
                <div class="flex items-center gap-2 mt-0.5">
                  <a id="previewUrl" href="#" target="_blank" rel="noopener noreferrer" class="text-xs text-ds-secondary hover:underline truncate inline-flex items-center gap-1">
                    <span id="previewUrlText" class="truncate">https://...</span>
                    <i class="fa-solid fa-arrow-up-right-from-square text-[10px] shrink-0"></i>
                  </a>
                </div>
              </div>
            </div>
            <div class="flex items-center gap-1.5 shrink-0">
              <button type="button" id="previewFullscreenBtn" onclick="togglePreviewFullscreen()" class="btn-icon" aria-label="Toggle Fullscreen" title="Toggle Fullscreen">
                <i id="previewFullscreenIcon" class="fa-solid fa-expand text-xs"></i>
              </button>
              <button type="button" onclick="closePreview()" class="btn-icon" aria-label="Close modal" title="Close">
                <i class="fa-solid fa-xmark text-sm"></i>
              </button>
            </div>
          </div>
          <!-- Tier 2: Pill Tabs with Icons and Count Badges -->
          <div class="flex items-center gap-1.5 overflow-x-auto whitespace-nowrap pt-0.5">
            <button id="viewMdTab" onclick="setPreviewTab('markdown')" class="preview-tab preview-tab-on">
              <i class="fa-regular fa-file-lines"></i>
              <span>Reader View</span>
            </button>
            <button id="viewAiTab" onclick="setPreviewTab('ai')" class="preview-tab">
              <i class="fa-solid fa-wand-magic-sparkles"></i>
              <span>AI Extraction</span>
            </button>
            <button id="viewScreenshotTab" onclick="setPreviewTab('screenshot')" class="preview-tab">
              <i class="fa-solid fa-image text-purple-600"></i>
              <span>Screenshot & Vision</span>
              <span id="previewScreenshotBadge" class="hidden ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-purple-100 text-purple-800 font-mono font-bold border border-purple-200">IMG</span>
            </button>
            <button id="viewRpaTab" onclick="setPreviewTab('rpa')" class="preview-tab">
              <i class="fa-solid fa-robot"></i>
              <span>RPA Logs</span>
            </button>
            <button id="viewNetworkTab" onclick="setPreviewTab('network')" class="preview-tab">
              <i class="fa-solid fa-network-wired"></i>
              <span>Network</span>
              <span id="previewNetworkCountBadge" class="ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-ds-surface-low text-ds-muted font-mono font-bold border border-ds">0</span>
            </button>
            <button id="viewElementsTab" onclick="setPreviewTab('elements')" class="preview-tab">
              <i class="fa-solid fa-code"></i>
              <span>DOM Elements</span>
              <span id="previewElementsCountBadge" class="ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-ds-surface-low text-ds-muted font-mono font-bold border border-ds">0</span>
            </button>
          </div>
        </div>

        <!-- MODAL BODY -->
        <div class="p-5 overflow-y-auto flex-1 space-y-4 bg-ds-surface-low/30">
          <!-- Markdown / Reader Section -->
          <div id="previewMdSection">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3 text-xs bg-white p-3 rounded-xl border border-ds shadow-sm">
              <div class="flex items-center gap-3 text-ds-muted font-mono text-[11px]" id="previewMdStats">
                <span class="inline-flex items-center gap-1.5 text-ds-primary font-semibold">
                  <i class="fa-regular fa-clock"></i>
                  <span id="previewReadTime">1 min read</span>
                </span>
                <span>•</span>
                <span id="previewWordCount">0 words</span>
                <span>•</span>
                <span id="previewCharCount">0 characters</span>
              </div>
              <div class="flex items-center gap-2">
                <button type="button" id="previewSourceToggle" onclick="togglePreviewSource()" class="btn-ghost px-2.5 py-1.5 rounded text-xs flex items-center gap-1.5">
                  <i id="previewSourceToggleIcon" class="fa-solid fa-code text-[11px]"></i>
                  <span id="previewSourceToggleText">Raw Source</span>
                </button>
                <button type="button" onclick="copyPreviewMarkdown()" class="btn-ghost px-2.5 py-1.5 rounded text-xs flex items-center gap-1.5">
                  <i class="fa-regular fa-copy text-[11px]"></i>
                  <span>Copy Markdown</span>
                </button>
              </div>
            </div>
            <div id="previewReading" class="preview-reading bg-white p-6 rounded-xl border border-ds shadow-sm"></div>
            <pre id="previewContent" class="hidden bg-[#0f172a] p-5 rounded-xl text-xs font-mono text-[#f8fafc] overflow-x-auto whitespace-pre-wrap leading-relaxed border border-slate-700/80 shadow-inner"></pre>
          </div>

          <!-- AI Extraction Section -->
          <div id="previewAiSection" class="hidden space-y-3">
            <!-- If AI structured data already exists -->
            <div id="previewAiDataContainer" class="hidden space-y-3">
              <div class="flex justify-between items-center pb-2 border-b border-ds">
                <span class="text-xs text-ds-accent font-semibold flex items-center gap-1.5">
                  <i class="fa-solid fa-circle-check text-emerald-600"></i> Extracted via NVIDIA NIM
                </span>
                <div class="flex items-center gap-2">
                  <button type="button" onclick="copyPreviewAiJson()" class="btn-ghost px-2.5 py-1 rounded text-xs flex items-center gap-1">
                    <i class="fa-regular fa-copy"></i> Copy JSON
                  </button>
                  <button type="button" onclick="showModalAiTrigger()" class="btn-ghost px-2.5 py-1 rounded text-xs flex items-center gap-1">
                    <i class="fa-solid fa-arrows-rotate"></i> Re-Extract
                  </button>
                </div>
              </div>
              <pre id="previewAiJson" class="bg-[#0f172a] p-4 rounded-xl text-xs font-mono text-[#34d399] overflow-x-auto whitespace-pre-wrap leading-relaxed border border-slate-700/80 shadow-inner"></pre>
            </div>

            <!-- If AI structured data doesn't exist yet or user wants to re-extract -->
            <div id="previewAiTriggerContainer" class="p-5 bg-white rounded-xl border border-ds space-y-4 shadow-sm">
              <div class="flex items-start gap-3">
                <div class="w-9 h-9 rounded-lg bg-ds-surface-low border border-ds flex items-center justify-center text-ds-accent flex-shrink-0 mt-0.5">
                  <i class="fa-solid fa-wand-magic-sparkles"></i>
                </div>
                <div>
                  <h4 class="text-sm font-semibold text-[#1c1b1b]">Extract Structured Data with AI</h4>
                  <p class="text-xs text-ds-muted mt-0.5">
                    This page has not been processed through the AI Extractor yet. Choose a schema below to extract clean JSON with NVIDIA NIM instantly.
                  </p>
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
                <div>
                  <label class="block text-xs font-semibold text-ds-muted mb-1">Target Schema</label>
                  <select id="modalAiSchema" class="w-full">
                    <option value="company_profile">🏢 Company & Product Intelligence (What they do, Offerings, Market Purpose)</option>
                    <option value="article">Article / Blog Post (Title, Summary, Key Points)</option>
                    <option value="product">Product / Pricing / Services (Name, Price, Features)</option>
                    <option value="faq">FAQ / Q&A (Question & Answer Pairs)</option>
                    <option value="custom">Custom Schema / Extraction</option>
                  </select>
                </div>
                <div>
                  <label class="block text-xs font-semibold text-ds-muted mb-1">NVIDIA NIM Model</label>
                  <select id="modalAiModel" class="w-full">
                    <option value="deepseek-ai/deepseek-v4.1-flash" selected>🚀 DeepSeek V4.1 Flash (Ultra-Fast 15s - Recommended)</option>
                    <option value="meta/llama-3.2-11b-vision-instruct">⚖️ Llama 3.2 11B Vision (Balanced Fallback)</option>
                    <option value="nvidia/nemotron-3.5-lightning-30b-a3b">⚡ Nemotron 3.5 Lightning (Ultra-Fast MoE)</option>
                    <option value="z-ai/glm-5.3-flash">🎨 GLM-5.3 Flash (320B Multimodal Reasoning)</option>
                    <option value="moonshotai/kimi-k3">🧠 Moonshot Kimi-k3 (2.8T MoE Deep Reasoning)</option>
                    <option value="nvidia/nemotron-parse-2.0">👁️ Nemotron Parse 2.0 (Visual Document & Table)</option>
                  </select>
                </div>
                <div>
                  <label class="block text-xs font-semibold text-ds-muted mb-1">Custom Prompt Instructions (Optional)</label>
                  <input id="modalAiPrompt" type="text" placeholder="e.g. Extract pricing plans, studio features, stats"
                         class="w-full">
                </div>
              </div>

              <div class="pt-2 flex flex-wrap items-center justify-between gap-2">
                <div class="flex items-center gap-3">
                  <span class="text-[11px] text-ds-muted">Uses NVIDIA NIM API with automated ChromaDB caching</span>
                  <div id="modalAiTimerBadge" class="hidden items-center gap-2 px-2.5 py-1 rounded-full bg-ds-surface-low border border-ds text-[11px] font-mono text-ds-accent shadow-xs">
                    <span><i class="fa-regular fa-clock mr-1 text-ds-muted"></i>Started: <span id="modalAiStartTime" class="text-[#1c1b1b] font-medium">--:--:--</span></span>
                    <span class="text-ds-outline">|</span>
                    <span><i class="fa-solid fa-stopwatch mr-1 text-ds-primary"></i>Elapsed: <span id="modalAiElapsedTime" class="font-bold text-ds-primary">00:00</span></span>
                  </div>
                </div>
                <button id="btnModalExtractAi" onclick="runModalAiExtraction()" class="cta-primary px-4 py-2 text-xs flex items-center gap-1.5">
                  <i class="fa-solid fa-bolt"></i> <span>⚡ Extract with AI Now</span>
                </button>
              </div>

              <div id="modalAiError" class="hidden p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700"></div>
            </div>
          </div>

          <!-- RPA Execution Logs Section -->
          <div id="previewRpaSection" class="hidden space-y-3">
            <div class="flex justify-between items-center pb-2 border-b border-ds">
              <span class="text-xs text-purple-700 font-semibold flex items-center gap-1.5">
                <i class="fa-solid fa-robot"></i> Browser Automation Execution Trace
              </span>
              <span id="previewRpaCountBadge" class="text-[11px] font-mono text-ds-muted">0 actions logged</span>
            </div>
            <div id="previewRpaLogsList" class="bg-white p-4 rounded-xl text-xs font-mono text-[#1c1b1b] space-y-2 border border-ds max-h-96 overflow-y-auto shadow-sm">
              <div class="text-ds-muted italic p-3 text-center">No interactive RPA actions logged for this page.</div>
            </div>
          </div>

          <!-- Network APIs Section -->
          <div id="previewNetworkSection" class="hidden space-y-3">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-ds">
              <div class="flex items-center gap-2">
                <span class="text-xs text-ds-secondary font-semibold flex items-center gap-1.5">
                  <i class="fa-solid fa-network-wired"></i> Intercepted Network API Calls
                </span>
                <span id="previewNetworkSummaryBadge" class="text-[11px] font-mono text-ds-muted">0 calls captured</span>
              </div>
              <div class="flex items-center gap-2">
                <input id="networkSearchInput" type="text" oninput="filterPreviewNetwork()" placeholder="Filter by endpoint URL / keyword..."
                       class="w-48 sm:w-64 text-xs">
                <select id="networkStatusFilter" onchange="filterPreviewNetwork()" class="text-xs">
                  <option value="all">All Status</option>
                  <option value="2xx">2xx (OK)</option>
                  <option value="error">4xx / 5xx</option>
                </select>
              </div>
            </div>
            <div id="previewNetworkList" class="space-y-2 max-h-[60vh] overflow-y-auto pr-1">
              <div class="text-ds-muted italic p-6 text-center bg-white rounded-xl border border-ds shadow-sm">
                No background Fetch/XHR API calls recorded for this page.<br>
                <span class="text-[11px] text-ds-muted mt-1 block">(Tip: Use Browser Engine with JavaScript enabled to intercept background API traffic)</span>
              </div>
            </div>
          </div>

          <!-- DOM Elements Section -->
          <div id="previewElementsSection" class="hidden space-y-4">
            <div class="flex items-center justify-between pb-2 border-b border-ds">
              <span class="text-xs text-amber-700 font-semibold flex items-center gap-1.5">
                <i class="fa-solid fa-code"></i> DOM Elements Inspector & Selector Tester
              </span>
              <span id="previewElementsSummaryBadge" class="text-[11px] font-mono text-ds-muted">0 elements</span>
            </div>

            <!-- Live Selector Tester Box -->
            <div class="p-4 bg-white rounded-xl border border-ds space-y-3 shadow-sm">
              <div class="flex items-center justify-between">
                <label class="text-xs font-semibold text-[#1c1b1b] flex items-center gap-1.5">
                  <i class="fa-solid fa-crosshairs text-amber-600"></i> Test Live CSS Selector Against Page DOM
                </label>
                <span class="text-[11px] text-ds-muted">Instant validation & attributes preview</span>
              </div>
              <div class="flex gap-2">
                <input id="elementSelectorInput" type="text" placeholder="e.g. button.pricing-tier, input[name='search'], h2, table, .navbar-brand"
                       class="flex-1 font-mono text-xs">
                <button type="button" onclick="runPreviewElementCheck()" class="px-4 py-2 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700 text-white font-semibold text-xs rounded-lg transition flex items-center gap-1.5 shadow">
                  <i class="fa-solid fa-magnifying-glass"></i> Check Element
                </button>
              </div>
              <div id="elementCheckResult" class="hidden text-xs space-y-2"></div>
            </div>

            <!-- Elements Inventory Categorized Tabs -->
            <div class="space-y-2">
              <div class="flex items-center gap-2 border-b border-ds text-xs">
                <button id="elemCatBtnButtons" onclick="setElementCategory('buttons')" class="px-3 py-1.5 border-b-2 border-amber-600 text-amber-700 font-semibold flex items-center gap-1.5">
                  <i class="fa-solid fa-hand-pointer"></i> Buttons (<span id="elemCountButtons">0</span>)
                </button>
                <button id="elemCatBtnInputs" onclick="setElementCategory('inputs')" class="px-3 py-1.5 border-b-2 border-transparent text-ds-muted hover:text-[#1c1b1b] font-semibold flex items-center gap-1.5">
                  <i class="fa-regular fa-keyboard"></i> Forms & Inputs (<span id="elemCountInputs">0</span>)
                </button>
                <button id="elemCatBtnTables" onclick="setElementCategory('tables')" class="px-3 py-1.5 border-b-2 border-transparent text-ds-muted hover:text-[#1c1b1b] font-semibold flex items-center gap-1.5">
                  <i class="fa-solid fa-table"></i> Tables (<span id="elemCountTables">0</span>)
                </button>
                <button id="elemCatBtnHeadings" onclick="setElementCategory('headings')" class="px-3 py-1.5 border-b-2 border-transparent text-ds-muted hover:text-[#1c1b1b] font-semibold flex items-center gap-1.5">
                  <i class="fa-solid fa-heading"></i> Headings (<span id="elemCountHeadings">0</span>)
                </button>
              </div>

              <!-- Category Lists -->
              <div id="elemCatListButtons" class="space-y-1.5 max-h-72 overflow-y-auto"></div>
              <div id="elemCatListInputs" class="hidden space-y-1.5 max-h-72 overflow-y-auto"></div>
              <div id="elemCatListTables" class="hidden space-y-1.5 max-h-72 overflow-y-auto"></div>
              <div id="elemCatListHeadings" class="hidden space-y-1.5 max-h-72 overflow-y-auto"></div>
            </div>
          </div>

          <!-- Screenshot & Vision Section -->
          <div id="previewScreenshotSection" class="hidden space-y-4">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 bg-white rounded-xl border border-ds shadow-xs">
              <div>
                <h5 class="text-xs font-bold text-slate-900 font-mono flex items-center gap-2">
                  <i class="fa-solid fa-camera text-purple-600"></i> Full-Page Screenshot Archive & Vision AI
                </h5>
                <p class="text-[11px] text-ds-muted mt-0.5">High-fidelity Chromium viewport snapshot captured during crawl.</p>
              </div>
              <div class="flex items-center gap-2">
                <button type="button" id="openFullScreenshotBtn" onclick="openScreenshotInNewTab()" class="btn-ghost px-3 py-1.5 text-xs flex items-center gap-1.5 text-slate-700">
                  <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i> Open Full Image
                </button>
              </div>
            </div>

            <!-- Vision Extraction Control Box -->
            <div class="p-4 rounded-xl border border-purple-200 bg-purple-50/50 space-y-3">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span class="w-2 h-2 rounded-full bg-purple-600"></span>
                  <span class="text-xs font-bold text-purple-900 font-mono">Vision AI Multimodal Extraction</span>
                </div>
                <span class="text-[10px] text-purple-700 font-mono">Llama 3.2 11B Vision / NIM</span>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-12 gap-2">
                <div class="sm:col-span-8">
                  <select id="visionTaskSelect" class="w-full px-3 py-2 text-xs border border-purple-200 rounded-lg bg-white">
                    <option value="chart_to_table">Transcribe Charts & Graphs to Markdown Tables</option>
                    <option value="visual_pricing_matrix">Extract Visual Pricing Tiers & Feature Matrix</option>
                    <option value="visual_summary">Executive Visual Hierarchy & Layout Summary</option>
                  </select>
                </div>
                <div class="sm:col-span-4">
                  <button type="button" id="runVisionBtn" onclick="runPreviewVisionExtract()" class="w-full py-2 px-3 bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs rounded-lg transition flex items-center justify-center gap-1.5 shadow-xs">
                    <i class="fa-solid fa-wand-magic-sparkles text-[10px]"></i> Extract with Vision AI
                  </button>
                </div>
              </div>
              <div id="visionResultCard" class="hidden p-3 bg-white rounded-lg border border-purple-200 text-xs font-mono whitespace-pre-wrap max-h-60 overflow-y-auto"></div>
            </div>

            <!-- Screenshot Display Frame -->
            <div id="screenshotFrameWrap" class="rounded-xl border border-ds overflow-hidden bg-slate-900 shadow-md text-center">
              <div id="screenshotEmptyNotice" class="p-12 text-slate-400 text-xs font-mono">
                <i class="fa-solid fa-image text-3xl mb-2 block opacity-40"></i>
                No screenshot was captured for this page run.<br>
                <span class="text-slate-500 text-[11px]">Enable "Capture Full-Page Screenshot" in the Scraper or run with Browser strategy to archive visual snapshots.</span>
              </div>
              <img id="screenshotImg" src="" alt="Full-Page Page Screenshot" class="hidden w-full h-auto max-h-[600px] object-top object-contain mx-auto">
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- WEBSITE INTELLIGENCE DOSSIER MODAL -->
    <div id="dossierModal" role="dialog" aria-modal="true" aria-labelledby="dossierTitle" class="hidden fixed inset-0 z-50 flex items-center justify-center p-4 modal-overlay-bg backdrop-blur-sm">
      <div class="dossier-modal-card w-full max-w-4xl rounded-2xl shadow-2xl flex flex-col max-h-[92vh] overflow-hidden modal-card">
        <div class="flex justify-between items-start gap-3 px-5 py-4 border-b border-ds">
          <div class="flex items-start gap-3 min-w-0">
            <div class="w-10 h-10 rounded-xl bg-ds-surface-low border border-ds flex items-center justify-center text-ds-success shrink-0">
              <i class="fa-solid fa-file-lines text-lg"></i>
            </div>
            <div class="min-w-0">
              <h3 id="dossierTitle" class="text-base font-bold text-[#1c1b1b]">Website Intelligence Report</h3>
              <p id="dossierSubtitle" class="text-ds-muted text-xs mt-0.5">Generate a structured report from your crawled pages in ChromaDB.</p>
            </div>
          </div>
          <button onclick="closeDossierModal()" class="btn-icon shrink-0" aria-label="Close">
            <i class="fa-solid fa-xmark text-sm"></i>
          </button>
        </div>

        <div class="p-5 overflow-y-auto flex-1 space-y-4 text-xs">
          <div class="p-4 rounded-xl border border-ds bg-[#fafafa] space-y-4">
            <div>
              <label class="ethic-label block mb-1.5" for="dossierReportType">What do you want in this dossier?</label>
              <select id="dossierReportType" onchange="syncDossierTypeUI()" class="w-full px-3 py-2 text-sm font-medium">
                <option value="complete_site_report" selected>Complete website report — full picture of the site</option>
                <option value="highlights_best">Best things on this site — strengths & standout content</option>
                <option value="market_research">Market research brief — category, audience & positioning</option>
                <option value="technical_audit">Content & structure audit — IA, clarity & gaps</option>
                <option value="competitive_matrix">Competitive comparison — multi-domain matrix</option>
              </select>
              <p id="dossierTypeHint" class="text-ds-muted text-[11px] mt-1.5 leading-snug"></p>
            </div>

            <div>
              <label class="ethic-label block mb-1.5">Target domain(s)</label>
              <div id="dossierDomainCheckboxes" class="flex flex-wrap gap-2 max-h-36 overflow-y-auto p-2 rounded-lg border border-ds bg-white">
                <span class="text-ds-muted text-xs italic">Loading tracked domains...</span>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="ethic-label block mb-1.5" for="dossierAiModel">Synthesis model</label>
                <select id="dossierAiModel" class="w-full px-3 py-2 text-xs">
                  <option value="deepseek-ai/deepseek-v4.1-flash" selected>DeepSeek V4.1 Flash (recommended)</option>
                  <option value="meta/llama-3.2-11b-vision-instruct">Llama 3.2 11B Vision</option>
                  <option value="nvidia/nemotron-3.5-lightning-30b-a3b">Nemotron 3.5 Lightning</option>
                  <option value="z-ai/glm-5.3-flash">GLM-5.3 Flash</option>
                  <option value="moonshotai/kimi-k3">Moonshot Kimi-k3</option>
                  <option value="nvidia/nemotron-parse-2.0">Nemotron Parse 2.0</option>
                </select>
              </div>
              <div>
                <label class="ethic-label block mb-1.5" for="dossierCustomFocus">Extra focus (optional)</label>
                <input id="dossierCustomFocus" type="text" placeholder="e.g. pricing, enterprise features, onboarding"
                       class="w-full px-3 py-2 text-xs">
              </div>
            </div>

            <div class="flex flex-wrap items-center justify-between gap-3 pt-1">
              <span id="dossierSelectedCount" class="text-ds-muted text-xs font-mono">0 domain(s) selected</span>
              <button id="btnGenerateDossier" onclick="runDossierGeneration()" class="cta-primary px-5 py-2.5 text-xs flex items-center gap-2">
                <i class="fa-solid fa-brain"></i> <span id="btnGenerateDossierLabel">Generate report</span>
              </button>
            </div>
          </div>

          <div id="dossierError" class="hidden p-3 bg-[#ffdad6] border border-[#ba1a1a]/30 rounded-xl text-[#ba1a1a] text-xs"></div>

          <div id="dossierLoading" class="hidden p-8 text-center space-y-3 rounded-xl border border-ds bg-ds-surface-low">
            <div class="inline-block w-8 h-8 border-2 border-ds-accent border-t-transparent rounded-full animate-spin"></div>
            <div class="text-ds-accent font-semibold text-sm">Synthesizing report from crawled knowledge…</div>
            <p class="text-ds-muted text-xs max-w-md mx-auto">Using <span id="dossierModelDisplay" class="font-mono text-ds-success font-bold">DeepSeek V4.1 Flash</span></p>
            <div class="inline-flex items-center gap-3 px-3.5 py-1.5 bg-white border border-ds rounded-full text-xs font-mono text-ds-muted">
              <span>Started: <span id="dossierStartTime" class="text-[#1c1b1b]">--:--:--</span></span>
              <span>|</span>
              <span>Elapsed: <span id="dossierElapsedTime" class="text-ds-accent font-bold">00:00</span></span>
            </div>
          </div>

          <div id="dossierResultArea" class="hidden space-y-3">
            <div class="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl border border-ds bg-white">
              <div class="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2 min-w-0">
                <span class="text-ds-success font-bold text-xs flex items-center gap-1.5"><i class="fa-solid fa-circle-check"></i> Report ready</span>
                <span id="dossierMetadataBadge" class="text-ds-muted text-[11px] font-mono truncate"></span>
              </div>
              <div class="flex items-center gap-2 flex-wrap">
                <button onclick="copyDossierMarkdown()" class="btn-ghost px-3 py-1.5 rounded-lg text-xs inline-flex items-center gap-1.5">
                  <i class="fa-regular fa-copy"></i> Copy MD
                </button>
                <button onclick="exportDossier('md')" class="btn-ghost px-3 py-1.5 rounded-lg text-xs inline-flex items-center gap-1.5">
                  <i class="fa-solid fa-file-lines"></i> Export MD
                </button>
                <button onclick="exportDossier('pdf')" class="btn-ghost px-3 py-1.5 rounded-lg text-xs inline-flex items-center gap-1.5">
                  <i class="fa-solid fa-file-pdf"></i> Export PDF
                </button>
              </div>
            </div>
            <div class="p-5 rounded-xl max-h-[480px] overflow-y-auto dossier-markdown-view">
              <pre id="dossierMarkdownContent" class="whitespace-pre-wrap m-0 bg-transparent border-0 p-0 text-inherit font-inherit text-xs"></pre>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- SAFE CONFIRM DELETION MODAL -->
    <div id="deleteConfirmModal" role="dialog" aria-modal="true" aria-labelledby="deleteModalTitle" class="hidden fixed inset-0 z-50 flex items-center justify-center modal-overlay-bg backdrop-blur-sm p-4 modal-overlay" onclick="if(event.target===this) closeDeleteConfirmModal()">
      <div class="bg-white border border-ds w-full max-w-md rounded-2xl shadow-2xl overflow-hidden p-6 space-y-4 modal-card">
        <div class="flex items-center gap-3.5">
          <div class="w-11 h-11 rounded-xl bg-red-50 border border-red-200 text-red-600 flex items-center justify-center text-lg shrink-0">
            <i class="fa-solid fa-triangle-exclamation"></i>
          </div>
          <div>
            <h4 id="deleteModalTitle" class="text-sm font-bold text-[#1c1b1b]">Confirm Selective Deletion</h4>
            <p class="text-xs text-ds-muted mt-0.5">Database preservation safe removal</p>
          </div>
        </div>

        <div class="text-xs text-[#1c1b1b] leading-relaxed">
          Are you sure you want to delete <span id="deleteTargetName" class="font-mono font-bold text-red-700 bg-red-50 px-1.5 py-0.5 rounded border border-red-200"></span>?
          <div class="mt-3 p-3 bg-red-50/70 border border-red-200/80 rounded-xl text-red-900 text-xs flex items-start gap-2.5">
            <i class="fa-solid fa-shield-halved text-red-500 mt-0.5 text-xs shrink-0"></i>
            <p id="deleteTargetWarning" class="text-[11px] leading-snug">This will selectively purge this document from the local ChromaDB vector store. Other domains and history remain untouched.</p>
          </div>
        </div>

        <div class="flex justify-end items-center gap-2 pt-3 border-t border-ds">
          <button onclick="closeDeleteConfirmModal()" class="btn-ghost px-4 py-2 text-xs font-semibold rounded-lg border border-ds hover:bg-ds-surface-low text-[#1c1b1b] transition-all active:scale-95">
            Cancel
          </button>
          <button id="btnExecuteDelete" onclick="executeDeletion()" class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 active:scale-95 shadow-sm">
            <i class="fa-solid fa-trash-can"></i> Delete Permanently
          </button>
        </div>
      </div>
    </div>

    <!-- Add Custom RPA Step Modal -->
    <div id="customRpaStepModal" role="dialog" aria-modal="true" aria-labelledby="rpaModalTitle" class="hidden fixed inset-0 z-50 flex items-center justify-center modal-overlay-bg backdrop-blur-sm p-4 modal-overlay" onclick="if(event.target===this) closeCustomRpaStepModal()">
      <div class="bg-white border border-ds w-full max-w-md rounded-2xl p-6 shadow-2xl space-y-4 text-xs modal-card">
        <div class="flex justify-between items-center border-b border-ds pb-3">
          <h4 id="rpaModalTitle" class="text-sm font-bold text-[#1c1b1b] flex items-center gap-2">
            <i class="fa-solid fa-robot text-purple-600"></i> Add Interactive RPA Step
          </h4>
          <button onclick="closeCustomRpaStepModal()" class="btn-icon" aria-label="Close modal">
            <i class="fa-solid fa-xmark text-sm"></i>
          </button>
        </div>
        <div class="space-y-3.5">
          <div>
            <label class="ethic-label block mb-1">Action Type</label>
            <select id="rpaStepAction" class="w-full px-3 py-2 text-xs rounded-lg border border-ds bg-white text-[#1c1b1b]">
              <option value="click">🖱️ Click Element</option>
              <option value="fill">✍️ Fill Input / Textarea</option>
              <option value="select">📋 Select Dropdown Option</option>
              <option value="wait_for">⏳ Wait for Element (Visible)</option>
              <option value="press_key">⌨️ Press Key (Enter, Escape, Tab)</option>
              <option value="hover">👆 Hover Over Element</option>
              <option value="scroll">📜 Scroll Page (pixels or 'bottom')</option>
              <option value="sleep">💤 Pause / Settle (ms)</option>
            </select>
          </div>
          <div>
            <div class="flex justify-between items-center mb-1">
              <label class="ethic-label">Selector (CSS or Text)</label>
              <button type="button" onclick="openElementPickerFromRpa()" class="text-[11px] text-purple-600 hover:text-purple-700 font-semibold flex items-center gap-1 hover:underline">
                <i class="fa-solid fa-crosshairs"></i> Visual Picker
              </button>
            </div>
            <input id="rpaStepSelector" type="text" placeholder="e.g. button:has-text('Annual'), #submit-btn, .tab-specs" class="w-full px-3 py-2 text-xs rounded-lg border border-ds bg-white text-[#1c1b1b] font-mono">
          </div>
          <div>
            <label class="ethic-label block mb-1">Value / Text / Key (Optional)</label>
            <input id="rpaStepValue" type="text" placeholder="e.g. text to fill, option value, key name, or scroll px" class="w-full px-3 py-2 text-xs rounded-lg border border-ds bg-white text-[#1c1b1b]">
          </div>
          <div class="flex items-center justify-between pt-1">
            <label class="flex items-center gap-2 cursor-pointer text-[#1c1b1b] select-none text-xs">
              <input type="checkbox" id="rpaStepOptional" checked class="rounded border-ds text-purple-600 focus:ring-0">
              <span>Optional step (don't fail crawl if not found)</span>
            </label>
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-3 border-t border-ds">
          <button onclick="closeCustomRpaStepModal()" class="btn-ghost px-4 py-2 text-xs font-semibold rounded-lg border border-ds hover:bg-ds-surface-low text-[#1c1b1b] transition-all active:scale-95">Cancel</button>
          <button onclick="commitCustomRpaStep()" class="cta-primary px-4 py-2 text-xs font-bold rounded-lg transition-all active:scale-95">Add Step</button>
        </div>
      </div>
    </div>

    <!-- CHROMADB STORE INSPECTOR -->
    <div id="chromaStoreModal" role="dialog" aria-modal="true" aria-labelledby="chromaStoreTitle" class="hidden fixed inset-0 z-50 flex items-center justify-center modal-overlay-bg backdrop-blur-sm p-4 modal-overlay" onclick="if(event.target===this) closeChromaStoreModal()">
      <div class="glass-card w-full max-w-5xl flex flex-col max-h-[92vh] overflow-hidden modal-card">
        <div class="flex justify-between items-start gap-4 px-5 py-4 border-b border-ds">
          <div>
            <h2 id="chromaStoreTitle" tabindex="-1" class="text-base font-bold text-[#1c1b1b] flex items-center gap-2 outline-none">
              <i class="fa-solid fa-database text-ds-accent" aria-hidden="true"></i>
              ChromaDB Vector Store
            </h2>
            <p id="chromaStoreMeta" class="text-ds-muted text-xs mt-1 font-mono">Loading collection…</p>
          </div>
          <button type="button" onclick="closeChromaStoreModal()" class="btn-icon w-11 h-11 min-w-[44px] min-h-[44px] shrink-0" aria-label="Close">
            <i class="fa-solid fa-xmark" aria-hidden="true"></i>
          </button>
        </div>

        <div class="px-5 py-4 border-b border-ds grid grid-cols-2 md:grid-cols-4 gap-3">
          <div class="stat-tile rounded-lg p-3">
            <div class="kpi-label">Documents</div>
            <div id="chromaStatDocs" class="text-xl font-bold font-mono chroma-stat-docs mt-1">—</div>
          </div>
          <div class="stat-tile rounded-lg p-3">
            <div class="kpi-label">Domains</div>
            <div id="chromaStatDomains" class="text-xl font-bold font-mono chroma-stat-domains mt-1">—</div>
          </div>
          <div class="stat-tile rounded-lg p-3">
            <div class="kpi-label">Distance</div>
            <div id="chromaStatSpace" class="text-xl font-bold font-mono chroma-stat-space mt-1">cosine</div>
          </div>
          <div class="stat-tile rounded-lg p-3">
            <div class="kpi-label">Collection</div>
            <div id="chromaStatCollection" class="text-sm font-bold font-mono text-[#1c1b1b] mt-1 truncate">crawled_knowledge</div>
          </div>
        </div>

        <div class="px-5 pt-3 flex flex-wrap items-center justify-between gap-2">
          <div class="flex gap-1 p-1 rounded-full bg-[#f6f3f2] border border-ds" role="tablist" aria-label="Store inspector views">
            <button type="button" id="chromaTabData" role="tab" aria-selected="true" onclick="setChromaStoreTab('data')" class="px-3 py-1.5 rounded-full text-xs font-semibold view-toggle-active">Stored data</button>
            <button type="button" id="chromaTabMap" role="tab" aria-selected="false" onclick="setChromaStoreTab('map')" class="px-3 py-1.5 rounded-full text-xs font-semibold view-toggle-inactive">Field mappings</button>
          </div>
          <label class="sr-only" for="chromaStoreFilter">Filter stored documents</label>
          <input id="chromaStoreFilter" type="search" oninput="renderChromaStoreData()" placeholder="Filter by domain, title, URL, or document ID"
                 class="rounded-lg px-3 py-1.5 text-xs w-full sm:w-72">
        </div>

        <div class="p-5 overflow-y-auto flex-1">
          <div id="chromaStoreDataPanel"></div>
          <div id="chromaStoreMapPanel" class="hidden overflow-x-auto rounded-xl border border-ds history-table-wrap">
            <table class="modal-table w-full text-left text-xs">
              <thead class="sticky top-0 modal-table">
                <tr>
                  <th>Field</th>
                  <th>Source</th>
                  <th>Role</th>
                </tr>
              </thead>
              <tbody id="chromaStoreMapBody" class="divide-y divide-[#e5e2e1]"></tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- THEME & DESIGN STUDIO MODAL -->
    <div id="themeStudioModal" role="dialog" aria-modal="true" aria-labelledby="themeStudioTitle" class="hidden fixed inset-0 z-50 flex items-center justify-center modal-overlay-bg backdrop-blur-sm p-4 modal-overlay" onclick="if(event.target===this) closeThemeStudioModal()">
      <div class="modal-card bg-white border border-ds rounded-2xl shadow-2xl max-w-4xl w-full max-h-[92vh] flex flex-col overflow-hidden text-[#1c1b1b]">
        <!-- Modal Header -->
        <div class="p-5 border-b border-ds flex items-center justify-between bg-ds-surface-low">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 border border-purple-200 flex items-center justify-center text-lg shadow-xs">
              <i class="fa-solid fa-palette"></i>
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h2 id="themeStudioTitle" class="text-base font-bold font-mono text-[#1c1b1b]">THEME & DESIGN STUDIO</h2>
                <span id="studioActiveBadge" class="px-2 py-0.5 text-[10px] font-mono font-bold rounded-full bg-purple-100 text-purple-800 border border-purple-200">Ethic Neo</span>
              </div>
              <p class="text-xs text-ds-muted mt-0.5">Centralized Design System & Appearance Engine · Instant Live Preview · 1-Click Replace</p>
            </div>
          </div>
          <button type="button" onclick="closeThemeStudioModal()" class="w-8 h-8 rounded-lg border border-ds flex items-center justify-center text-ds-muted hover:text-[#1c1b1b] hover:bg-white transition" aria-label="Close Studio">
            <i class="fa-solid fa-xmark text-sm"></i>
          </button>
        </div>

        <!-- Studio Navigation Tabs -->
        <div class="px-5 pt-3 pb-2 border-b border-ds flex items-center gap-2 bg-white text-xs font-semibold overflow-x-auto">
          <button type="button" id="studioTabPresetsBtn" onclick="switchStudioTab('presets')" class="px-3 py-1.5 rounded-lg bg-ds-surface-low text-ds-primary border border-ds flex items-center gap-1.5 transition">
            <i class="fa-solid fa-swatchbook"></i> Curated Presets
          </button>
          <button type="button" id="studioTabColorsBtn" onclick="switchStudioTab('colors')" class="px-3 py-1.5 rounded-lg text-ds-muted hover:text-[#1c1b1b] flex items-center gap-1.5 transition">
            <i class="fa-solid fa-eye-dropper"></i> Color Palette & Tokens
          </button>
          <button type="button" id="studioTabTypographyBtn" onclick="switchStudioTab('typography')" class="px-3 py-1.5 rounded-lg text-ds-muted hover:text-[#1c1b1b] flex items-center gap-1.5 transition">
            <i class="fa-solid fa-font"></i> Typography & Fonts
          </button>
          <button type="button" id="studioTabSandboxBtn" onclick="switchStudioTab('sandbox')" class="px-3 py-1.5 rounded-lg text-ds-muted hover:text-[#1c1b1b] flex items-center gap-1.5 transition">
            <i class="fa-solid fa-cube"></i> Live Component Sandbox
          </button>
        </div>

        <!-- Modal Body (Scrollable) -->
        <div class="p-6 overflow-y-auto space-y-6 flex-1 bg-[#fafafa]">
          
          <!-- TAB 1: CURATED PRESETS -->
          <div id="studioTabPresets" class="space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-xs font-bold font-mono uppercase tracking-wider text-[#1c1b1b]">Curated Design Presets</h3>
                <p class="text-xs text-ds-muted">Click any preset card to switch the entire application theme in real time.</p>
              </div>
              <button type="button" onclick="resetThemeToDefault()" class="btn-ghost px-3 py-1 text-[11px] flex items-center gap-1.5 text-slate-700">
                <i class="fa-solid fa-arrow-rotate-left text-[10px]"></i> Reset to Default
              </button>
            </div>
            <div id="themePresetsGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <!-- Dynamically populated by JS from THEME_REGISTRY -->
            </div>
          </div>

          <!-- TAB 2: PALETTE & TOKENS -->
          <div id="studioTabColors" class="hidden space-y-4">
            <div>
              <h3 class="text-xs font-bold font-mono uppercase tracking-wider text-[#1c1b1b]">Custom Color Palette & Tokens</h3>
              <p class="text-xs text-ds-muted">Adjust any token color. Updates apply immediately to both the live application and preview sandbox.</p>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" id="colorTokensGrid">
              <!-- Dynamically populated by JS -->
            </div>
          </div>

          <!-- TAB 3: TYPOGRAPHY -->
          <div id="studioTabTypography" class="hidden space-y-4">
            <div>
              <h3 class="text-xs font-bold font-mono uppercase tracking-wider text-[#1c1b1b]">Typography & Font Pairings</h3>
              <p class="text-xs text-ds-muted">Curated font pairings optimized for readability, hierarchy, and code aesthetics.</p>
            </div>
            <div id="fontPairingsList" class="space-y-3">
              <!-- Dynamically populated by JS -->
            </div>
          </div>

          <!-- TAB 4: COMPONENT SANDBOX -->
          <div id="studioTabSandbox" class="hidden space-y-5">
            <div>
              <h3 class="text-xs font-bold font-mono uppercase tracking-wider text-[#1c1b1b]">Interactive Live Component Sandbox</h3>
              <p class="text-xs text-ds-muted">Test how buttons, form controls, cards, and status pills look under the active theme configuration.</p>
            </div>
            <div class="p-6 bg-white border border-ds rounded-xl space-y-6 shadow-xs">
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div class="p-4 rounded-xl border border-ds bg-ds-surface-low space-y-2">
                  <div class="text-[10px] font-mono font-bold text-ds-muted uppercase">Primary Button</div>
                  <button type="button" class="cta-primary px-4 py-2 w-full text-xs">Execute Ingestion</button>
                </div>
                <div class="p-4 rounded-xl border border-ds bg-ds-surface-low space-y-2">
                  <div class="text-[10px] font-mono font-bold text-ds-muted uppercase">Ghost Button</div>
                  <button type="button" class="btn-ghost px-4 py-2 w-full text-xs text-center block">Inspect Payload</button>
                </div>
                <div class="p-4 rounded-xl border border-ds bg-ds-surface-low space-y-2">
                  <div class="text-[10px] font-mono font-bold text-ds-muted uppercase">Status Badges</div>
                  <div class="flex items-center gap-2 pt-1">
                    <span class="status-pill ok">ACTIVE</span>
                    <span class="status-pill bad">OFFLINE</span>
                    <span class="chip-export"><i class="fa-solid fa-file-pdf mr-1"></i>PDF</span>
                  </div>
                </div>
              </div>
              <div class="space-y-2">
                <label class="ethic-label">Sample Input Field</label>
                <input type="text" class="w-full px-3 py-2 border rounded-lg text-xs" value="https://example.com/api/v1/news" readonly>
              </div>
              <div class="p-4 rounded-xl border border-ds bg-white space-y-2 shadow-xs">
                <div class="flex items-center justify-between">
                  <h4 class="font-bold text-sm">Sample Card Container</h4>
                  <span class="text-[10px] font-mono text-ds-muted">CARD PREVIEW</span>
                </div>
                <p class="text-xs text-ds-muted">This card dynamically adapts to your card background, border, font pairings, and shadow tokens.</p>
              </div>
            </div>
          </div>

        </div>

        <!-- Modal Footer & 1-Click Replace Actions -->
        <div class="p-4 border-t border-ds bg-white flex flex-wrap items-center justify-between gap-3">
          <div class="flex flex-wrap items-center gap-2">
            <button type="button" onclick="copyCssVariables()" class="px-3 py-2 text-xs font-semibold rounded-lg border border-ds hover:bg-ds-surface-low text-slate-800 flex items-center gap-1.5 transition">
              <i class="fa-solid fa-copy text-ds-primary"></i> Copy CSS :root
            </button>
            <button type="button" onclick="copyThemeJson()" class="px-3 py-2 text-xs font-semibold rounded-lg border border-ds hover:bg-ds-surface-low text-slate-800 flex items-center gap-1.5 transition">
              <i class="fa-solid fa-code text-purple-600"></i> Copy Theme JSON
            </button>
            <button type="button" onclick="downloadThemeJson()" class="px-3 py-2 text-xs font-semibold rounded-lg border border-ds hover:bg-ds-surface-low text-slate-800 flex items-center gap-1.5 transition">
              <i class="fa-solid fa-download text-teal-600"></i> Export JSON
            </button>
            <button type="button" onclick="promptImportThemeJson()" class="px-3 py-2 text-xs font-semibold rounded-lg border border-ds hover:bg-ds-surface-low text-slate-800 flex items-center gap-1.5 transition">
              <i class="fa-solid fa-upload text-blue-600"></i> Import JSON
            </button>
          </div>
          <div class="flex items-center gap-2">
            <button type="button" onclick="closeThemeStudioModal()" class="btn-ghost px-4 py-2 text-xs text-slate-700">Done</button>
          </div>
        </div>
      </div>
    </div>

    <!-- SCHEDULES & AUTONOMOUS MONITORS MODAL -->
    <div id="schedulesModal" role="dialog" aria-modal="true" aria-labelledby="schedulesModalTitle" class="hidden fixed inset-0 z-50 flex items-center justify-center modal-overlay-bg backdrop-blur-sm p-4 modal-overlay" onclick="if(event.target===this) closeSchedulesModal()">
      <div class="modal-card bg-white border border-ds rounded-2xl shadow-2xl max-w-4xl w-full max-h-[92vh] flex flex-col overflow-hidden text-[#1c1b1b]">
        <!-- Header -->
        <div class="p-5 border-b border-ds flex items-center justify-between bg-ds-surface-low">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 border border-blue-200 flex items-center justify-center text-lg shadow-xs">
              <i class="fa-solid fa-clock"></i>
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h2 id="schedulesModalTitle" class="text-base font-bold font-mono text-[#1c1b1b]">AUTONOMOUS SCHEDULES & MONITORS</h2>
                <span id="schedulesActiveBadge" class="px-2 py-0.5 text-[10px] font-mono font-bold rounded-full bg-blue-100 text-blue-800 border border-blue-200">24/7 Engine</span>
              </div>
              <p class="text-xs text-ds-muted mt-0.5">Continuous Monitoring · Semantic Content Diffing · Webhook Alerts</p>
            </div>
          </div>
          <button type="button" onclick="closeSchedulesModal()" class="w-8 h-8 rounded-lg border border-ds flex items-center justify-center text-ds-muted hover:text-[#1c1b1b] hover:bg-white transition" aria-label="Close Monitors">
            <i class="fa-solid fa-xmark text-sm"></i>
          </button>
        </div>

        <!-- Add Monitor Quick Bar -->
        <div class="p-4 bg-white border-b border-ds">
          <form id="createScheduleForm" onsubmit="handleCreateSchedule(event)" class="space-y-3">
            <div class="grid grid-cols-1 md:grid-cols-12 gap-2.5 items-end">
              <div class="md:col-span-5 space-y-1">
                <label class="ethic-label">Target URL to Monitor</label>
                <input type="url" id="schedUrlInput" required placeholder="https://example.com/pricing" class="w-full px-3 py-1.5 text-xs border rounded-lg">
              </div>
              <div class="md:col-span-3 space-y-1">
                <label class="ethic-label">Monitor Name</label>
                <input type="text" id="schedNameInput" placeholder="e.g. Pricing Monitor" class="w-full px-3 py-1.5 text-xs border rounded-lg">
              </div>
              <div class="md:col-span-2 space-y-1">
                <label class="ethic-label">Interval</label>
                <select id="schedIntervalInput" class="w-full px-2 py-1.5 text-xs border rounded-lg">
                  <option value="10m">Every 10 min</option>
                  <option value="30m">Every 30 min</option>
                  <option value="1h" selected>Hourly (1h)</option>
                  <option value="6h">Every 6 hrs</option>
                  <option value="12h">Every 12 hrs</option>
                  <option value="24h">Daily (24h)</option>
                  <option value="7d">Weekly (7d)</option>
                </select>
              </div>
              <div class="md:col-span-2">
                <button type="submit" id="createScheduleBtn" class="cta-primary w-full py-2 text-xs flex items-center justify-center gap-1.5">
                  <i class="fa-solid fa-plus text-[10px]"></i> Add Monitor
                </button>
              </div>
            </div>
            <!-- Optional Advanced Drawer -->
            <details class="text-[11px] text-ds-muted">
              <summary class="cursor-pointer hover:text-slate-800 font-mono text-[10px] uppercase font-bold text-ds-accent">
                <i class="fa-solid fa-gear mr-1"></i> Advanced Options (Webhook, Engine Strategy)
              </summary>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                <div class="space-y-1">
                  <label class="ethic-label">Outbound Webhook URL (Slack, Discord, Zapier)</label>
                  <input type="url" id="schedWebhookInput" placeholder="https://hooks.slack.com/services/..." class="w-full px-3 py-1.5 text-xs border rounded-lg">
                </div>
                <div class="space-y-1">
                  <label class="ethic-label">Engine Strategy</label>
                  <select id="schedStrategyInput" class="w-full px-2 py-1.5 text-xs border rounded-lg">
                    <option value="auto" selected>Auto-Escalate (Light HTTP + Browser SPA)</option>
                    <option value="browser">Headless Browser (Playwright)</option>
                    <option value="http">Fast Async HTTP</option>
                  </select>
                </div>
              </div>
            </details>
          </form>
        </div>

        <!-- Body / Monitors Table -->
        <div class="p-5 overflow-y-auto flex-1 bg-[#fafafa] space-y-3">
          <div class="flex items-center justify-between">
            <h3 class="text-xs font-mono font-bold uppercase tracking-wider text-[#1c1b1b]">Active Monitors (<span id="schedulesTableCount">0</span>)</h3>
            <button type="button" onclick="loadSchedulesTable()" class="btn-ghost px-2.5 py-1 text-[11px] flex items-center gap-1 text-slate-700">
              <i class="fa-solid fa-rotate text-[10px]"></i> Refresh
            </button>
          </div>
          <div id="schedulesTableWrap" class="rounded-xl border border-ds overflow-x-auto bg-white shadow-xs">
            <table class="modal-table w-full text-left text-xs">
              <thead class="sticky top-0 modal-table">
                <tr>
                  <th>Target & Name</th>
                  <th>Frequency</th>
                  <th>Last Checked</th>
                  <th>Next Run</th>
                  <th>Status & Diff</th>
                  <th class="text-right">Actions</th>
                </tr>
              </thead>
              <tbody id="schedulesTableBody" class="divide-y divide-[#e5e2e1]">
                <tr>
                  <td colspan="6" class="p-4 text-center text-xs text-ds-muted">Loading monitors...</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Footer -->
        <div class="p-4 border-t border-ds bg-white flex items-center justify-between">
          <div class="text-[11px] text-ds-muted flex items-center gap-2">
            <span class="w-2 h-2 rounded-full status-dot-active"></span>
            <span>Scheduler running in background (15s tick loop)</span>
          </div>
          <button type="button" onclick="closeSchedulesModal()" class="btn-ghost px-4 py-2 text-xs text-slate-700">Close</button>
        </div>
      </div>
    </div>

    <!-- CONTENT DIFF MODAL -->
    <div id="diffModal" role="dialog" aria-modal="true" aria-labelledby="diffModalTitle" class="hidden fixed inset-0 z-50 flex items-center justify-center modal-overlay-bg backdrop-blur-sm p-4 modal-overlay" onclick="if(event.target===this) closeDiffModal()">
      <div class="modal-card bg-white border border-ds rounded-2xl shadow-2xl max-w-4xl w-full max-h-[92vh] flex flex-col overflow-hidden text-[#1c1b1b]">
        <!-- Header -->
        <div class="p-5 border-b border-ds flex items-center justify-between bg-ds-surface-low">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 border border-purple-200 flex items-center justify-center text-lg shadow-xs">
              <i class="fa-solid fa-code-compare"></i>
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h2 id="diffModalTitle" class="text-base font-bold font-mono text-[#1c1b1b]">CONTENT DIFF INSPECTOR</h2>
                <span id="diffSimilarityBadge" class="px-2 py-0.5 text-[10px] font-mono font-bold rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">100% Match</span>
              </div>
              <p id="diffSubtitle" class="text-xs text-ds-muted mt-0.5 font-mono">Comparing latest crawl vs historical baseline</p>
            </div>
          </div>
          <button type="button" onclick="closeDiffModal()" class="w-8 h-8 rounded-lg border border-ds flex items-center justify-center text-ds-muted hover:text-[#1c1b1b] hover:bg-white transition" aria-label="Close Diff">
            <i class="fa-solid fa-xmark text-sm"></i>
          </button>
        </div>

        <!-- Metric Badges Bar -->
        <div class="p-3 bg-white border-b border-ds flex flex-wrap items-center justify-between gap-3 text-xs">
          <div class="flex items-center gap-3">
            <span class="inline-flex items-center gap-1 font-mono font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-md">
              <i class="fa-solid fa-plus text-[10px]"></i> <span id="diffAddedCount">0</span> additions
            </span>
            <span class="inline-flex items-center gap-1 font-mono font-bold text-rose-700 bg-rose-50 border border-rose-200 px-2.5 py-1 rounded-md">
              <i class="fa-solid fa-minus text-[10px]"></i> <span id="diffRemovedCount">0</span> deletions
            </span>
          </div>
          <div id="diffSummaryText" class="text-xs font-semibold text-slate-700">No content changes detected.</div>
        </div>

        <!-- Diff Viewer Body -->
        <div class="p-4 overflow-y-auto flex-1 bg-[#0f172a] text-[#f8fafc] font-mono text-xs">
          <div id="diffHtmlContainer" class="space-y-0.5">
            <!-- Populated with color-coded diff lines -->
          </div>
        </div>

        <!-- Footer -->
        <div class="p-4 border-t border-ds bg-white flex items-center justify-end">
          <button type="button" onclick="closeDiffModal()" class="btn-ghost px-4 py-2 text-xs text-slate-700">Done</button>
        </div>
      </div>
    </div>

    <!-- INTERACTIVE POINT-AND-CLICK ELEMENT PICKER MODAL -->
    <div id="elementPickerModal" role="dialog" aria-modal="true" aria-labelledby="pickerModalTitle" class="hidden fixed inset-0 z-50 flex items-center justify-center modal-overlay-bg backdrop-blur-sm p-4 modal-overlay" onclick="if(event.target===this) closeElementPicker()">
      <div class="glass-card w-full max-w-6xl flex flex-col h-[90vh] overflow-hidden modal-card">
        <!-- Header -->
        <div class="flex items-center justify-between px-5 py-3 border-b border-ds bg-white/95">
          <div class="flex items-center gap-3">
            <span class="w-8 h-8 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center text-sm font-bold">
              <i class="fa-solid fa-crosshairs"></i>
            </span>
            <div>
              <h2 id="pickerModalTitle" class="text-sm font-bold text-[#1c1b1b]">Visual Element Picker</h2>
              <p id="pickerTargetUrlText" class="text-xs text-ds-muted font-mono truncate max-w-md">Hover and click any element to generate CSS selector</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button type="button" onclick="refreshPickerIframe()" class="btn-ghost px-2.5 py-1.5 text-xs text-slate-700 flex items-center gap-1" title="Reload iframe">
              <i class="fa-solid fa-rotate-right"></i> Reload
            </button>
            <button type="button" onclick="closeElementPicker()" class="btn-icon" aria-label="Close">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>
        </div>

        <!-- Toolbar / Selected details -->
        <div class="px-5 py-2.5 border-b border-ds bg-slate-50 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div class="flex items-center gap-2 flex-1 min-w-[280px]">
            <span class="font-semibold text-slate-600 shrink-0">Selector:</span>
            <input id="pickerSelectorInput" type="text" readonly placeholder="Click an element in the preview below..." class="w-full px-3 py-1.5 font-mono text-xs rounded border border-ds bg-white text-slate-900 select-all font-semibold">
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <span id="pickerTagBadge" class="hidden px-2 py-0.5 rounded bg-slate-200 text-slate-700 font-mono text-[11px] font-bold">TAG</span>
            <span id="pickerMatchesBadge" class="hidden px-2 py-0.5 rounded bg-purple-100 text-purple-700 font-mono text-[11px] font-semibold">1 match</span>
            <button type="button" onclick="copyPickerSelector()" class="btn-ghost px-2.5 py-1 text-xs border border-ds bg-white flex items-center gap-1">
              <i class="fa-regular fa-copy"></i> Copy
            </button>
            <button type="button" id="pickerApplyBtn" onclick="applyPickerSelector()" class="cta-primary px-3 py-1 text-xs font-semibold rounded flex items-center gap-1">
              <i class="fa-solid fa-check"></i> Use Selector
            </button>
          </div>
        </div>

        <!-- Sandboxed iframe container -->
        <div class="flex-1 bg-slate-200 relative overflow-hidden">
          <div id="pickerLoading" class="absolute inset-0 bg-white/80 backdrop-blur-xs flex flex-col items-center justify-center gap-2 z-10 hidden">
            <i class="fa-solid fa-circle-notch fa-spin text-2xl text-purple-600"></i>
            <span class="text-xs font-medium text-slate-600">Loading and instrumenting page DOM...</span>
          </div>
          <iframe id="pickerSandboxIframe" class="w-full h-full border-0 bg-white" sandbox="allow-scripts allow-same-origin"></iframe>
        </div>
      </div>
    </div>

    <!-- COMPETITIVE BENCHMARK & TECHNOLOGY PROFILER MODAL -->
    <div id="competitorModal" role="dialog" aria-modal="true" aria-labelledby="benchmarkModalTitle" class="hidden fixed inset-0 z-50 flex items-center justify-center modal-overlay-bg backdrop-blur-sm p-4 modal-overlay" onclick="if(event.target===this) closeCompetitorModal()">
      <div class="glass-card w-full max-w-5xl flex flex-col h-[90vh] overflow-hidden modal-card">
        <!-- Header -->
        <div class="flex items-center justify-between px-5 py-4 border-b border-ds bg-white">
          <div class="flex items-center gap-3">
            <span class="w-9 h-9 rounded-lg bg-amber-100 text-amber-800 flex items-center justify-center text-base font-bold">
              <i class="fa-solid fa-chart-simple"></i>
            </span>
            <div>
              <h2 id="benchmarkModalTitle" class="text-base font-bold text-[#1c1b1b]">Competitive Benchmarking & Tech Profiler</h2>
              <p class="text-xs text-ds-muted">Compare 2 to 5 indexed competitor domains side-by-side using ChromaDB knowledge</p>
            </div>
          </div>
          <button type="button" onclick="closeCompetitorModal()" class="btn-icon" aria-label="Close">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>

        <!-- Controls: Domain Selection -->
        <div class="px-5 py-3 border-b border-ds bg-slate-50/80 space-y-3">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <span class="text-xs font-bold text-slate-700">Select Competitor Domains to Compare (2 to 5):</span>
            <div class="flex items-center gap-2">
              <input id="benchmarkFocusInput" type="text" placeholder="Custom Focus (e.g. pricing, AI features, security)" class="px-3 py-1 text-xs rounded border border-ds bg-white w-72">
              <button type="button" id="btnRunBenchmark" onclick="runCompetitorBenchmark()" class="cta-primary px-3 py-1.5 text-xs font-semibold rounded flex items-center gap-1.5 shadow-xs">
                <i class="fa-solid fa-play"></i> Generate Benchmark
              </button>
            </div>
          </div>
          <div id="benchmarkDomainList" class="flex flex-wrap gap-2 max-h-24 overflow-y-auto p-1.5 bg-white border border-ds rounded-lg">
            <span class="text-xs text-slate-400 italic">Loading domains from knowledge base...</span>
          </div>
        </div>

        <!-- Body / Results View -->
        <div class="flex-1 overflow-y-auto p-5 space-y-4 bg-white" id="benchmarkResultsArea">
          <div id="benchmarkEmptyState" class="py-16 text-center text-slate-500 space-y-3">
            <div class="w-12 h-12 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto text-xl">
              <i class="fa-solid fa-scale-balanced"></i>
            </div>
            <p class="text-sm font-medium">Select at least 2 domains above and click "Generate Benchmark"</p>
            <p class="text-xs text-slate-400 max-w-md mx-auto">The engine will cross-examine stored pages, synthesize value propositions, compare pricing models, and fingerprint technology stacks.</p>
          </div>

          <div id="benchmarkLoading" class="py-20 text-center space-y-3 hidden">
            <i class="fa-solid fa-circle-notch fa-spin text-3xl text-amber-600"></i>
            <p class="text-sm font-semibold text-slate-700">Synthesizing multi-domain competitive matrix...</p>
            <p class="text-xs text-slate-400">Analyzing ChromaDB vectors and fingerprinting tech stacks</p>
          </div>

          <div id="benchmarkContent" class="space-y-6 hidden">
            <!-- Action Toolbar for Export -->
            <div class="flex items-center justify-between pb-3 border-b border-ds">
              <div class="flex items-center gap-2">
                <span class="text-xs font-bold text-slate-700">Model Engine:</span>
                <span id="benchmarkModelBadge" class="px-2 py-0.5 rounded bg-slate-100 font-mono text-[11px] text-slate-700 border border-slate-200">heuristic-synthesis</span>
              </div>
              <div class="flex items-center gap-2">
                <button type="button" onclick="exportCompetitorBenchmark('pdf')" class="btn-ghost px-3 py-1.5 text-xs font-semibold rounded border border-ds bg-white hover:bg-slate-50 text-slate-700 flex items-center gap-1.5">
                  <i class="fa-regular fa-file-pdf text-rose-600"></i> Export PDF
                </button>
                <button type="button" onclick="exportCompetitorBenchmark('markdown')" class="btn-ghost px-3 py-1.5 text-xs font-semibold rounded border border-ds bg-white hover:bg-slate-50 text-slate-700 flex items-center gap-1.5">
                  <i class="fa-regular fa-file-code text-blue-600"></i> Export Markdown
                </button>
              </div>
            </div>

            <!-- Side-by-Side Matrix Table Container -->
            <div class="overflow-x-auto rounded-xl border border-ds">
              <div id="benchmarkTableContainer" class="p-2 prose prose-xs max-w-none text-xs">
                <!-- Rendered Markdown Table -->
              </div>
            </div>

            <!-- Full In-Depth Breakdown -->
            <div id="benchmarkReportContainer" class="space-y-4 pt-4 border-t border-ds prose prose-sm max-w-none">
              <!-- Rendered report sections -->
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="px-5 py-3 border-t border-ds bg-slate-50 flex items-center justify-between text-xs text-slate-500">
          <span>Ethical passive fingerprinting & cross-domain analysis</span>
          <button type="button" onclick="closeCompetitorModal()" class="btn-ghost px-4 py-1.5 font-semibold text-slate-700">Close</button>
        </div>
      </div>
    </div>

    <!-- VISUAL PRODUCT BLUEPRINT & REVERSE-ENGINEERING MODAL -->
    <div id="blueprintModal" role="dialog" aria-modal="true" aria-labelledby="blueprintModalTitle" class="hidden fixed inset-0 z-50 flex items-center justify-center modal-overlay-bg backdrop-blur-sm p-4 modal-overlay" onclick="if(event.target===this) closeBlueprintModal()">
      <div class="glass-card w-full max-w-6xl flex flex-col h-[92vh] overflow-hidden modal-card">
        <!-- Header -->
        <div class="flex items-center justify-between px-5 py-3.5 border-b border-ds bg-white">
          <div class="flex items-center gap-3">
            <span class="w-9 h-9 rounded-lg bg-teal-100 text-teal-800 flex items-center justify-center text-base font-bold">
              <i class="fa-solid fa-camera-retro"></i>
            </span>
            <div>
              <h2 id="blueprintModalTitle" class="text-base font-bold text-[#1c1b1b]">Visual Product Blueprint & Reverse-Engineering</h2>
              <p class="text-xs text-ds-muted">Deconstruct multi-page screenshot archives into full-stack specs, diagrams, and API contracts</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button type="button" onclick="closeBlueprintModal()" class="btn-icon" aria-label="Close">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>
        </div>

        <!-- Controls: Domain Selector & Action Bar -->
        <div class="px-5 py-3 border-b border-ds bg-slate-50 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div class="flex items-center gap-2.5 flex-1 min-w-[280px]">
            <span class="font-bold text-slate-700 shrink-0">Target Domain:</span>
            <select id="blueprintDomainSelect" onchange="onBlueprintDomainChange()" class="w-52 px-3 py-1.5 rounded border border-ds bg-white text-slate-900 font-mono text-xs">
              <option value="">Select an indexed domain...</option>
            </select>
            <span class="font-bold text-slate-700 shrink-0">Vision Model:</span>
            <select id="blueprintModelSelect" class="w-64 px-2.5 py-1.5 rounded border border-teal-300 bg-teal-50 text-slate-900 font-medium text-xs focus:ring-1 focus:ring-teal-500">
              <option value="meta/llama-3.2-90b-vision-instruct" selected>🧠 Llama 3.2 90B Vision (Highest Quality)</option>
              <option value="meta/llama-3.2-11b-vision-instruct">⚡ Llama 3.2 11B Vision (Fastest)</option>
              <option value="microsoft/phi-3.5-vision-instruct">📄 Phi-3.5 Vision (Charts/Docs)</option>
              <option value="z-ai/glm-5.3-flash">🔥 GLM 5.3 Flash (Fast + Reasoning)</option>
              <option value="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning">🤖 Nemotron 3 Nano Omni 30B (Reasoning)</option>
            </select>
            <input id="blueprintFocusInput" type="text" placeholder="Custom Focus (e.g. admin workflows, RBAC, billing)" class="flex-1 min-w-[160px] px-3 py-1.5 rounded border border-ds bg-white text-xs">
          </div>
          <div class="flex items-center gap-2">
            <button type="button" onclick="toggleBlueprintUploadSection()" class="btn-ghost px-3 py-1.5 text-xs font-semibold rounded flex items-center gap-1.5 border border-slate-300">
              <i class="fa-solid fa-cloud-arrow-up text-teal-600"></i> Upload Screens
            </button>
            <button type="button" id="btnRunBlueprint" onclick="runGenerateBlueprint()" class="cta-primary px-4 py-1.5 text-xs font-semibold rounded flex items-center gap-1.5 shadow-xs">
              <i class="fa-solid fa-microchip"></i> Deconstruct & Generate Blueprint
            </button>
          </div>
        </div>

        <!-- In-Browser Screenshot & Folder Uploader -->
        <div id="blueprintUploadSection" class="hidden px-5 py-3.5 border-b border-ds bg-teal-50/60 flex flex-col gap-3 text-xs">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="w-6 h-6 rounded bg-teal-600 text-white flex items-center justify-center text-xs font-bold shadow-xs">
                <i class="fa-solid fa-cloud-arrow-up"></i>
              </span>
              <span class="font-bold text-teal-950 text-sm">Upload Screenshots or Screenshot Folder</span>
              <span class="text-slate-500 font-normal text-xs ml-1">Assign images directly to any domain</span>
            </div>
            <button type="button" onclick="toggleBlueprintUploadSection()" class="btn-icon text-slate-400 hover:text-slate-600" aria-label="Close upload drawer">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>

          <!-- Domain Destination Dropdown & Custom Domain Field -->
          <div class="p-3 bg-white rounded-lg border border-teal-200/80 shadow-xs flex flex-wrap items-center justify-between gap-3">
            <div class="flex flex-wrap items-center gap-2.5 flex-1 min-w-[320px]">
              <span class="font-bold text-slate-700 shrink-0 flex items-center gap-1.5">
                <i class="fa-solid fa-globe text-teal-600"></i> Target Domain:
              </span>
              <select id="blueprintUploadDomainSelect" onchange="onBlueprintUploadDomainSelectChange()" class="px-3 py-1.5 rounded border border-ds bg-slate-50 text-slate-900 font-mono text-xs focus:ring-1 focus:ring-teal-500">
                <option value="__NEW__">➕ Create New Domain / Project...</option>
              </select>
              <input id="blueprintUploadDomainInput" type="text" placeholder="Type new domain or app name (e.g. plexis.in, my-app.com)" oninput="document.getElementById('blueprintUploadTargetBadge').textContent=this.value.trim()||'(New Domain)'" class="w-64 px-3 py-1.5 rounded border border-ds bg-white text-xs focus:ring-1 focus:ring-teal-500">
            </div>
            <div class="flex items-center gap-2">
              <span class="text-[11px] text-slate-500">Destination:</span>
              <span id="blueprintUploadTargetBadge" class="font-mono font-bold text-teal-800 bg-teal-100/70 px-2 py-0.5 rounded text-[11px]">(New Domain)</span>
            </div>
          </div>

          <!-- Dual Mode Upload Controls: Individual Files OR Entire Folder -->
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div class="flex items-center gap-2">
              <input id="blueprintUploadFileInput" type="file" multiple accept="image/png,image/jpeg,image/webp" onchange="onBlueprintFileSelect(event)" class="hidden">
              <input id="blueprintUploadFolderInput" type="file" webkitdirectory directory multiple accept="image/png,image/jpeg,image/webp" onchange="onBlueprintFolderSelect(event)" class="hidden">
              <button type="button" onclick="document.getElementById('blueprintUploadFileInput').click()" class="btn-ghost px-3 py-1.5 text-xs font-semibold rounded flex items-center gap-1.5 border border-slate-300 bg-white hover:bg-slate-50 shadow-xs">
                <i class="fa-solid fa-images text-teal-600"></i> Choose Image Files
              </button>
              <button type="button" onclick="document.getElementById('blueprintUploadFolderInput').click()" class="btn-ghost px-3 py-1.5 text-xs font-semibold rounded flex items-center gap-1.5 border border-slate-300 bg-white hover:bg-slate-50 shadow-xs">
                <i class="fa-solid fa-folder-open text-amber-600"></i> Choose Entire Folder
              </button>
            </div>
            <div class="flex items-center gap-2">
              <span id="blueprintUploadStatus" class="text-xs font-mono text-slate-600"></span>
              <button type="button" id="btnSubmitBlueprintUpload" onclick="submitBlueprintUpload()" class="cta-primary px-4 py-1.5 text-xs font-semibold rounded flex items-center gap-1.5 shadow-xs">
                <i class="fa-solid fa-cloud-arrow-up"></i> Upload & Catalog
              </button>
            </div>
          </div>

          <!-- Drag and Drop Zone supporting both Files & Folders -->
          <div id="blueprintUploadDropzone" ondragover="event.preventDefault(); this.classList.add('border-teal-500', 'bg-teal-100/40');" ondragleave="this.classList.remove('border-teal-500', 'bg-teal-100/40');" ondrop="handleBlueprintDrop(event)" class="border-2 border-dashed border-teal-300 rounded-lg p-4 text-center text-slate-500 hover:border-teal-500 transition cursor-pointer bg-white/70">
            <div class="flex flex-col items-center gap-1">
              <i class="fa-solid fa-folder-arrow-up text-teal-600 text-lg"></i>
              <span class="text-xs font-medium text-slate-700">Drag & drop screenshot files or an entire folder here</span>
              <span class="text-[11px] text-slate-400">Supported: .png, .jpg, .jpeg, .webp (Automatic folder name auto-detection)</span>
            </div>
          </div>
        </div>

        <!-- Scroll-Snap Screenshot Carousel (Modern Web Guidance) -->
        <div class="px-5 py-2.5 border-b border-ds bg-slate-100/70">
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-[11px] font-bold text-slate-600 flex items-center gap-1">
              <i class="fa-solid fa-film text-teal-600"></i> Screenshot Storyboard Scroller
            </span>
            <span id="blueprintScreenCountBadge" class="text-[11px] font-mono text-slate-500">0 screens cataloged</span>
          </div>
          <div id="blueprintScreenshotCarousel" class="flex gap-3 overflow-x-auto pb-2 scroll-smooth" style="scroll-snap-type: x mandatory;">
            <div class="p-4 text-center text-xs text-slate-400 w-full italic">Select a domain above to view its captured screenshot collection.</div>
          </div>
        </div>

        <!-- Accessible Navigation Tabs (role="tablist") -->
        <div class="px-5 border-b border-ds bg-white flex items-center justify-between gap-2 overflow-x-auto">
          <div role="tablist" aria-label="Blueprint Sections" class="flex items-center gap-2 text-xs">
            <button type="button" role="tab" id="tabBtn_storyboard" aria-selected="true" onclick="switchBlueprintTab('storyboard')" class="px-3 py-2.5 font-bold border-b-2 border-teal-600 text-teal-700 flex items-center gap-1.5">
              <i class="fa-solid fa-map"></i> Storyboard & Personas
            </button>
            <button type="button" role="tab" id="tabBtn_diagrams" aria-selected="false" onclick="switchBlueprintTab('diagrams')" class="px-3 py-2.5 font-bold border-b-2 border-transparent text-slate-600 hover:text-slate-900 flex items-center gap-1.5">
              <i class="fa-solid fa-diagram-project"></i> Mermaid Diagrams (Flow & ERD)
            </button>
            <button type="button" role="tab" id="tabBtn_frontend" aria-selected="false" onclick="switchBlueprintTab('frontend')" class="px-3 py-2.5 font-bold border-b-2 border-transparent text-slate-600 hover:text-slate-900 flex items-center gap-1.5">
              <i class="fa-solid fa-palette"></i> Frontend & UI Tokens
            </button>
            <button type="button" role="tab" id="tabBtn_backend" aria-selected="false" onclick="switchBlueprintTab('backend')" class="px-3 py-2.5 font-bold border-b-2 border-transparent text-slate-600 hover:text-slate-900 flex items-center gap-1.5">
              <i class="fa-solid fa-server"></i> Backend APIs & Schemas
            </button>
          </div>
          <div id="blueprintExportActions" class="hidden items-center gap-2 py-1 shrink-0">
            <button type="button" onclick="exportBlueprint('pdf')" class="btn-ghost px-2.5 py-1 text-xs border border-ds rounded bg-white text-slate-700 flex items-center gap-1 hover:bg-slate-50">
              <i class="fa-regular fa-file-pdf text-rose-600"></i> Export PDF
            </button>
            <button type="button" onclick="exportBlueprint('markdown')" class="btn-ghost px-2.5 py-1 text-xs border border-ds rounded bg-white text-slate-700 flex items-center gap-1 hover:bg-slate-50">
              <i class="fa-regular fa-file-code text-blue-600"></i> Export Markdown
            </button>
          </div>
        </div>

        <!-- Tab Body Content -->
        <div class="flex-1 overflow-y-auto p-5 bg-white text-xs" id="blueprintTabContentArea">
          <!-- Empty State -->
          <div id="blueprintEmptyState" class="py-20 text-center text-slate-500 space-y-3">
            <div class="w-14 h-14 rounded-2xl bg-teal-50 text-teal-700 flex items-center justify-center mx-auto text-2xl border border-teal-200">
              <i class="fa-solid fa-compass-drafting"></i>
            </div>
            <h4 class="text-sm font-bold text-slate-800">Visual Product Reverse-Engineering Studio</h4>
            <p class="text-xs text-slate-400 max-w-md mx-auto">Select a domain with captured screenshots and click "Deconstruct & Generate Blueprint" to infer complete full-stack architecture, diagrams, and API contracts.</p>
          </div>

          <!-- Loading State -->
          <div id="blueprintLoading" class="py-24 text-center space-y-3 hidden">
            <i class="fa-solid fa-circle-notch fa-spin text-3xl text-teal-600"></i>
            <p class="text-sm font-semibold text-slate-800">Synthesizing full-stack product blueprint from screenshots...</p>
            <p class="text-xs text-slate-400">Deconstructing view types, mapping screen navigation, building ERD, and generating REST contracts</p>
          </div>

          <!-- Active Tabs View -->
          <div id="blueprintContent" class="hidden space-y-6">
            <!-- 1. Storyboard & Personas Tab -->
            <div id="bpPanel_storyboard" role="tabpanel" class="space-y-5">
              <div class="p-4 rounded-xl border border-ds bg-slate-50/60 space-y-3">
                <h3 class="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <i class="fa-solid fa-book-open text-teal-600"></i> Executive Product Overview
                </h3>
                <div id="bpStoryboardText" class="prose prose-xs max-w-none text-slate-700 leading-relaxed"></div>
              </div>
              <div class="space-y-3">
                <h4 class="text-xs font-bold text-slate-900 uppercase tracking-wider">Features & Capabilities Inventory</h4>
                <div id="bpFeaturesGrid" class="grid grid-cols-1 md:grid-cols-2 gap-2.5"></div>
              </div>
              <div class="space-y-3">
                <h4 class="text-xs font-bold text-slate-900 uppercase tracking-wider">Gherkin Use Case Specifications</h4>
                <div id="bpUseCasesList" class="space-y-3"></div>
              </div>
            </div>

            <!-- 2. Mermaid Diagrams Tab -->
            <div id="bpPanel_diagrams" role="tabpanel" class="hidden space-y-6">
              <div class="space-y-2">
                <div class="flex items-center justify-between">
                  <h4 class="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                    <i class="fa-solid fa-route text-teal-600"></i> Information Architecture & Screen Navigation Flow
                  </h4>
                  <button type="button" onclick="copyBlueprintDiagram('nav')" class="text-[11px] text-teal-700 hover:underline">Copy Mermaid</button>
                </div>
                <div class="p-4 rounded-xl border border-ds bg-slate-50 overflow-x-auto text-center" id="bpNavDiagramContainer"></div>
              </div>
              <div class="space-y-2 pt-4 border-t border-ds">
                <div class="flex items-center justify-between">
                  <h4 class="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                    <i class="fa-solid fa-database text-purple-600"></i> Inferred Database Schema (Entity-Relationship Diagram)
                  </h4>
                  <button type="button" onclick="copyBlueprintDiagram('erd')" class="text-[11px] text-purple-700 hover:underline">Copy Mermaid</button>
                </div>
                <div class="p-4 rounded-xl border border-ds bg-slate-50 overflow-x-auto text-center" id="bpErdDiagramContainer"></div>
              </div>
            </div>

            <!-- 3. Frontend & Design Tokens Tab -->
            <div id="bpPanel_frontend" role="tabpanel" class="hidden space-y-6">
              <div class="space-y-3">
                <h4 class="text-xs font-bold text-slate-900 uppercase tracking-wider">Inferred Atomic Component Hierarchy</h4>
                <div id="bpComponentsList" class="grid grid-cols-1 md:grid-cols-2 gap-3"></div>
              </div>
              <div class="space-y-3 pt-4 border-t border-ds">
                <h4 class="text-xs font-bold text-slate-900 uppercase tracking-wider">Extracted Visual Design Tokens</h4>
                <div id="bpDesignTokensContainer" class="p-4 rounded-xl border border-ds bg-slate-900 text-slate-100 font-mono text-[11px] overflow-x-auto"></div>
              </div>
            </div>

            <!-- 4. Backend APIs Tab -->
            <div id="bpPanel_backend" role="tabpanel" class="hidden space-y-4">
              <div class="flex items-center justify-between">
                <h4 class="text-xs font-bold text-slate-900 uppercase tracking-wider">Inferred REST API Contracts</h4>
                <span class="text-[11px] font-mono text-slate-500">OpenAPI 3.1 compatible</span>
              </div>
              <div id="bpApiEndpointsList" class="space-y-3"></div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="px-5 py-3 border-t border-ds bg-slate-50 flex items-center justify-between text-xs text-slate-500">
          <span>Non-invasive visual reverse-engineering engine</span>
          <button type="button" onclick="closeBlueprintModal()" class="btn-ghost px-4 py-1.5 font-semibold text-slate-700">Close</button>
        </div>
      </div>
    </div>

    <!-- GLOBAL FOOTER -->
    <footer class="mt-14 pt-6 pb-6 footer-bar text-center text-xs space-y-3">
      <div class="flex items-center justify-center gap-2.5">
        <span class="w-2 h-2 rounded-full status-dot-active"></span>
        <span class="font-semibold text-[#1c1b1b]">Ethical AI Web Crawler & Knowledge Engine</span>
        <span class="text-ds-muted">&bull;</span>
        <span class="font-mono text-[11px] text-ds-accent">v0.1.0</span>
      </div>
      <p class="text-ds-muted">Built with ❤️ by Ethical AI Crawler</p>
      <div class="flex flex-wrap items-center justify-center gap-4">
        <a href="/docs" target="_blank" class="text-ds-muted hover:text-ds-accent transition flex items-center gap-1.5">
          <i class="fa-solid fa-book"></i> API Docs
        </a>
        <a href="/redoc" target="_blank" class="text-ds-muted hover:text-ds-accent transition flex items-center gap-1.5">
          <i class="fa-solid fa-code"></i> ReDoc
        </a>
        <a href="/health" target="_blank" class="text-ds-muted hover:text-ds-accent transition flex items-center gap-1.5">
          <i class="fa-solid fa-heart-pulse"></i> Health Check
        </a>
        <span class="text-ds-muted">|</span>
        <span class="text-ds-muted flex items-center gap-1.5">
          <i class="fa-solid fa-shield-halved text-ds-success"></i> 100% Robots.txt Compliant
        </span>
      </div>
    </footer>

  </div>

  <script>
    let activePoll = null;
    let activeJobId = null;
    let currentMode = 'crawl';
    let currentAiData = null;
    let storedHistoryList = [];
    let storedDomainsList = [];
    let activeHistoryView = 'domain';
    let pendingDelete = null;
    let currentDossierData = null;
    let statusTimer = null;
    let dossierTimer = null;
    let modalAiTimer = null;
    let askTimer = null;

    const MODAL_IDS = ['blueprintModal', 'competitorModal', 'elementPickerModal', 'diffModal', 'schedulesModal', 'themeStudioModal', 'chromaStoreModal', 'previewModal', 'dossierModal', 'deleteConfirmModal', 'customRpaStepModal'];

    function syncBodyScrollLock() {
      const anyOpen = MODAL_IDS.some((id) => {
        const el = document.getElementById(id);
        return el && !el.classList.contains('hidden');
      });
      document.body.classList.toggle('overflow-hidden', anyOpen);
    }

    function closeTopModal() {
      const order = ['blueprintModal', 'competitorModal', 'elementPickerModal', 'diffModal', 'schedulesModal', 'themeStudioModal', 'customRpaStepModal', 'deleteConfirmModal', 'chromaStoreModal', 'dossierModal', 'previewModal'];
      for (const id of order) {
        const el = document.getElementById(id);
        if (el && !el.classList.contains('hidden')) {
          if (id === 'blueprintModal') closeBlueprintModal();
          else if (id === 'competitorModal') closeCompetitorModal();
          else if (id === 'elementPickerModal') closeElementPicker();
          else if (id === 'diffModal') closeDiffModal();
          else if (id === 'schedulesModal') closeSchedulesModal();
          else if (id === 'themeStudioModal') closeThemeStudioModal();
          else if (id === 'previewModal') closePreview();
          else if (id === 'dossierModal') closeDossierModal();
          else if (id === 'deleteConfirmModal') closeDeleteConfirmModal();
          else if (id === 'customRpaStepModal') closeCustomRpaStepModal();
          else if (id === 'chromaStoreModal') closeChromaStoreModal();
          return;
        }
      }
    }

    // -------------------------------------------------------------------------
    // THEME & DESIGN SYSTEM STUDIO ENGINE
    // -------------------------------------------------------------------------
    const ETHIC_THEMES = __THEMES_JSON__;
    let activeStudioTab = 'presets';
    let currentActiveThemeId = ETHIC_THEMES.defaultThemeId;

    const KEY_COLOR_TOKENS = [
      { key: '--ds-primary', label: 'Primary Accent', desc: 'Main highlights, branding, active states' },
      { key: '--ds-primary-container', label: 'Primary Container (CTA)', desc: 'Primary buttons and selected tab fill' },
      { key: '--ds-secondary', label: 'Secondary Accent', desc: 'Subtle links, export badges, indicators' },
      { key: '--ds-bg', label: 'Background Canvas', desc: 'App-shell viewport background' },
      { key: '--ds-surface', label: 'Surface Panels', desc: 'Glass cards and component surfaces' },
      { key: '--ds-border', label: 'Borders & Outlines', desc: 'Card borders, dividers, inputs' },
      { key: '--ds-on-surface', label: 'Primary Text', desc: 'Headings, table text, high-contrast labels' },
      { key: '--ds-on-surface-variant', label: 'Muted Text', desc: 'Secondary notes, helper text' },
      { key: '--ds-error', label: 'Error / Destructive', desc: 'Delete buttons, error banners' }
    ];

    function openThemeStudioModal() {
      const modal = document.getElementById('themeStudioModal');
      const btn = document.getElementById('headerThemeBtn');
      modal.classList.remove('hidden');
      if (btn) btn.setAttribute('aria-expanded', 'true');
      syncBodyScrollLock();
      renderThemeStudioUI();
      const title = document.getElementById('themeStudioTitle');
      if (title) title.focus();
    }

    function closeThemeStudioModal() {
      const modal = document.getElementById('themeStudioModal');
      const btn = document.getElementById('headerThemeBtn');
      modal.classList.add('hidden');
      if (btn) {
        btn.setAttribute('aria-expanded', 'false');
        btn.focus();
      }
      syncBodyScrollLock();
    }

    function switchStudioTab(tab) {
      activeStudioTab = tab;
      const tabs = ['presets', 'colors', 'typography', 'sandbox'];
      for (const t of tabs) {
        const btn = document.getElementById(`studioTab${t.charAt(0).toUpperCase() + t.slice(1)}Btn`);
        const pane = document.getElementById(`studioTab${t.charAt(0).toUpperCase() + t.slice(1)}`);
        const isActive = t === tab;
        if (btn) {
          btn.className = isActive
            ? 'px-3 py-1.5 rounded-lg bg-ds-surface-low text-ds-primary border border-ds flex items-center gap-1.5 transition'
            : 'px-3 py-1.5 rounded-lg text-ds-muted hover:text-[#1c1b1b] flex items-center gap-1.5 transition';
        }
        if (pane) {
          pane.classList.toggle('hidden', !isActive);
        }
      }
    }

    function renderThemeStudioUI() {
      try {
        const saved = localStorage.getItem('ethic_user_theme');
        if (saved) {
          const parsed = JSON.parse(saved);
          if (parsed && parsed.id) currentActiveThemeId = parsed.id;
        }
      } catch (e) {}

      renderThemePresets();
      renderColorTokens();
      renderFontPairings();
      updateThemeBadges();
    }

    function updateThemeBadges() {
      const activeObj = ETHIC_THEMES.themes[currentActiveThemeId];
      const displayName = activeObj ? activeObj.name.split(' (')[0] : 'Custom';
      const badge = document.getElementById('studioActiveBadge');
      const pill = document.getElementById('activeThemePill');
      if (badge) badge.innerText = displayName;
      if (pill) pill.innerText = displayName;
    }

    function renderThemePresets() {
      const grid = document.getElementById('themePresetsGrid');
      if (!grid) return;
      const themes = Object.values(ETHIC_THEMES.themes);
      grid.innerHTML = themes.map(th => {
        const isCurrent = th.id === currentActiveThemeId;
        const tokens = th.tokens || {};
        const pColor = tokens['--ds-primary'] || '#536600';
        const pContainer = tokens['--ds-primary-container'] || '#d4ff00';
        const bgColor = tokens['--ds-bg'] || '#fcf8f8';
        const borderColor = tokens['--ds-border'] || '#e5e2e1';

        return `
          <div class="p-4 rounded-xl border ${isCurrent ? 'border-purple-600 ring-2 ring-purple-100 bg-purple-50/20' : 'border-ds bg-white'} flex flex-col justify-between gap-3 shadow-xs hover:border-slate-400 transition cursor-pointer" onclick="applyThemePreset('${escapeHtml(th.id)}')">
            <div class="space-y-1.5">
              <div class="flex items-center justify-between">
                <span class="font-bold text-xs text-[#1c1b1b]">${escapeHtml(th.name)}</span>
                <span class="px-1.5 py-0.5 text-[9px] font-mono uppercase rounded ${th.category === 'dark' ? 'bg-slate-900 text-slate-100' : 'bg-slate-100 text-slate-700'}">${escapeHtml(th.category)}</span>
              </div>
              <p class="text-[11px] text-ds-muted leading-tight">${escapeHtml(th.description)}</p>
            </div>
            <div class="flex items-center justify-between pt-2 border-t border-ds">
              <div class="flex items-center gap-1.5">
                <span class="w-4 h-4 rounded-full border border-black/10 shadow-xs" style="background-color: ${pColor};" title="Primary: ${pColor}"></span>
                <span class="w-4 h-4 rounded-full border border-black/10 shadow-xs" style="background-color: ${pContainer};" title="CTA Fill: ${pContainer}"></span>
                <span class="w-4 h-4 rounded-full border border-black/10 shadow-xs" style="background-color: ${bgColor};" title="Background: ${bgColor}"></span>
                <span class="w-4 h-4 rounded-full border border-black/10 shadow-xs" style="background-color: ${borderColor};" title="Border: ${borderColor}"></span>
              </div>
              ${isCurrent ? '<span class="text-[10px] font-mono font-bold text-purple-700 flex items-center gap-1"><i class="fa-solid fa-check"></i> ACTIVE</span>' : '<button type="button" class="btn-ghost px-2.5 py-1 text-[10px]">Select</button>'}
            </div>
          </div>
        `;
      }).join('');
    }

    function applyThemePreset(themeId) {
      const th = ETHIC_THEMES.themes[themeId];
      if (!th) return;
      currentActiveThemeId = themeId;
      const root = document.documentElement;

      for (const [k, v] of Object.entries(th.tokens || {})) {
        root.style.setProperty(k, v);
      }

      const fp = ETHIC_THEMES.fontPairings[th.font_pairing || 'default'];
      if (fp) {
        root.style.setProperty('--ds-font-heading', fp.heading);
        root.style.setProperty('--ds-font-sans', fp.sans);
        root.style.setProperty('--ds-font-mono', fp.mono);
      }

      try {
        localStorage.setItem('ethic_user_theme', JSON.stringify({
          id: th.id,
          name: th.name,
          tokens: th.tokens,
          fontPairingId: th.font_pairing,
          fonts: fp ? { heading: fp.heading, sans: fp.sans, mono: fp.mono } : null
        }));
      } catch (e) {}

      updateThemeBadges();
      renderThemePresets();
      renderColorTokens();
      renderFontPairings();
      showToast('Applied ' + th.name, 'success');
    }

    function rgbToHex(val) {
      if (!val) return '#ffffff';
      val = val.trim();
      if (val.startsWith('#')) {
        return val.length === 4
          ? '#' + val[1] + val[1] + val[2] + val[2] + val[3] + val[3]
          : val.slice(0, 7);
      }
      const match = val.match(/^rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/i);
      if (match) {
        const r = parseInt(match[1], 10).toString(16).padStart(2, '0');
        const g = parseInt(match[2], 10).toString(16).padStart(2, '0');
        const b = parseInt(match[3], 10).toString(16).padStart(2, '0');
        return '#' + r + g + b;
      }
      return '#888888';
    }

    function renderColorTokens() {
      const grid = document.getElementById('colorTokensGrid');
      if (!grid) return;
      const rootStyle = getComputedStyle(document.documentElement);

      grid.innerHTML = KEY_COLOR_TOKENS.map(item => {
        const currentVal = rootStyle.getPropertyValue(item.key).trim() || '#ffffff';
        const hexVal = rgbToHex(currentVal);
        const safeId = item.key.replace(/[^a-zA-Z0-9]/g, '_');

        return `
          <div class="p-3 bg-white border border-ds rounded-xl space-y-2 shadow-xs">
            <div class="flex items-center justify-between">
              <div>
                <div class="text-xs font-bold text-[#1c1b1b]">${escapeHtml(item.label)}</div>
                <div class="text-[10px] text-ds-muted font-mono">${escapeHtml(item.key)}</div>
              </div>
              <input type="color" id="picker_${safeId}" value="${hexVal}"
                     oninput="onTokenColorInput('${item.key}', this.value, '${safeId}')"
                     class="w-7 h-7 rounded border border-ds cursor-pointer p-0 bg-transparent">
            </div>
            <div class="flex items-center gap-2">
              <input type="text" id="hex_${safeId}" value="${hexVal}"
                     onchange="onTokenHexInput('${item.key}', this.value, '${safeId}')"
                     class="font-mono text-xs px-2 py-1 border border-ds rounded w-full bg-[#fafafa]">
            </div>
            <p class="text-[10px] text-ds-muted">${escapeHtml(item.desc)}</p>
          </div>
        `;
      }).join('');
    }

    function onTokenColorInput(tokenKey, hexVal, safeId) {
      document.documentElement.style.setProperty(tokenKey, hexVal);
      const textInput = document.getElementById('hex_' + safeId);
      if (textInput) textInput.value = hexVal;
      saveCustomThemeState(tokenKey, hexVal);
    }

    function onTokenHexInput(tokenKey, hexVal, safeId) {
      if (!hexVal.startsWith('#')) hexVal = '#' + hexVal;
      document.documentElement.style.setProperty(tokenKey, hexVal);
      const pickerInput = document.getElementById('picker_' + safeId);
      if (pickerInput) pickerInput.value = hexVal;
      saveCustomThemeState(tokenKey, hexVal);
    }

    function saveCustomThemeState(tokenKey, tokenVal) {
      currentActiveThemeId = 'custom';
      updateThemeBadges();
      try {
        let saved = localStorage.getItem('ethic_user_theme');
        let data = saved ? JSON.parse(saved) : { id: 'custom', name: 'Custom Theme', tokens: {} };
        data.id = 'custom';
        data.name = 'Custom Theme';
        if (!data.tokens) data.tokens = {};
        data.tokens[tokenKey] = tokenVal;
        localStorage.setItem('ethic_user_theme', JSON.stringify(data));
      } catch (e) {}
    }

    function renderFontPairings() {
      const container = document.getElementById('fontPairingsList');
      if (!container) return;
      const pairings = Object.entries(ETHIC_THEMES.fontPairings);

      container.innerHTML = pairings.map(([pId, p]) => {
        return `
          <div class="p-3.5 bg-white border border-ds rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
            <div class="space-y-1">
              <div class="font-bold text-xs text-[#1c1b1b]">${escapeHtml(p.name)}</div>
              <div class="flex flex-wrap items-center gap-3 text-[11px] text-ds-muted">
                <span>Headings: <strong class="text-slate-800" style="font-family: ${p.heading};">Sample Heading</strong></span>
                <span>Body: <strong class="text-slate-800" style="font-family: ${p.sans};">Sample Body</strong></span>
                <span>Code: <strong class="text-slate-800 font-mono" style="font-family: ${p.mono};">0x2A // ETHIC</strong></span>
              </div>
            </div>
            <button type="button" onclick="applyFontPairing('${escapeHtml(pId)}')" class="btn-ghost px-3 py-1.5 text-xs text-purple-700 font-semibold hover:border-purple-300 shrink-0">
              Apply Typography
            </button>
          </div>
        `;
      }).join('');
    }

    function applyFontPairing(pairingId) {
      const fp = ETHIC_THEMES.fontPairings[pairingId];
      if (!fp) return;
      const root = document.documentElement;
      root.style.setProperty('--ds-font-heading', fp.heading);
      root.style.setProperty('--ds-font-sans', fp.sans);
      root.style.setProperty('--ds-font-mono', fp.mono);

      try {
        let saved = localStorage.getItem('ethic_user_theme');
        let data = saved ? JSON.parse(saved) : { id: currentActiveThemeId, tokens: {} };
        data.fontPairingId = pairingId;
        data.fonts = { heading: fp.heading, sans: fp.sans, mono: fp.mono };
        localStorage.setItem('ethic_user_theme', JSON.stringify(data));
      } catch (e) {}

      showToast('Typography updated: ' + fp.name, 'success');
    }

    function copyCssVariables() {
      const root = document.documentElement;
      const style = getComputedStyle(root);
      const lines = [':root {'];

      lines.push(`  --ds-font-heading: ${style.getPropertyValue('--ds-font-heading').trim() || "'Space Grotesk', sans-serif"};`);
      lines.push(`  --ds-font-sans: ${style.getPropertyValue('--ds-font-sans').trim() || "'Plus Jakarta Sans', sans-serif"};`);
      lines.push(`  --ds-font-mono: ${style.getPropertyValue('--ds-font-mono').trim() || "'Space Mono', monospace"};`);

      const allTokens = [
        '--ds-bg', '--ds-surface', '--ds-card-bg', '--ds-surface-container',
        '--ds-surface-container-low', '--ds-surface-container-high', '--ds-surface-container-highest',
        '--ds-on-surface', '--ds-on-surface-variant', '--ds-outline',
        '--ds-primary', '--ds-primary-container', '--ds-on-primary-container',
        '--ds-secondary', '--ds-secondary-container', '--ds-tertiary',
        '--ds-error', '--ds-error-container', '--ds-border', '--ds-shadow', '--ds-radius'
      ];

      for (const t of allTokens) {
        const val = style.getPropertyValue(t).trim();
        if (val) lines.push(`  ${t}: ${val};`);
      }
      lines.push('}');
      const cssText = lines.join('\\n');

      navigator.clipboard.writeText(cssText).then(() => {
        showToast('Copied CSS :root variables to clipboard!', 'success');
      }).catch(() => {
        prompt('Copy your CSS :root block:', cssText);
      });
    }

    function copyThemeJson() {
      const root = document.documentElement;
      const style = getComputedStyle(root);
      const tokens = {};

      const allTokens = [
        '--ds-bg', '--ds-surface', '--ds-card-bg', '--ds-surface-container',
        '--ds-surface-container-low', '--ds-surface-container-high', '--ds-surface-container-highest',
        '--ds-on-surface', '--ds-on-surface-variant', '--ds-outline',
        '--ds-primary', '--ds-primary-container', '--ds-on-primary-container',
        '--ds-secondary', '--ds-secondary-container', '--ds-tertiary',
        '--ds-error', '--ds-error-container', '--ds-border', '--ds-shadow', '--ds-radius'
      ];

      for (const t of allTokens) {
        const val = style.getPropertyValue(t).trim();
        if (val) tokens[t] = val;
      }

      const exportObj = {
        id: currentActiveThemeId,
        name: 'Custom Theme',
        category: 'light',
        font_pairing: 'default',
        tokens: tokens
      };

      const jsonStr = JSON.stringify(exportObj, null, 2);
      navigator.clipboard.writeText(jsonStr).then(() => {
        showToast('Copied Theme JSON to clipboard! Ready to paste into theme.py', 'success');
      }).catch(() => {
        prompt('Copy your Theme JSON:', jsonStr);
      });
    }

    function downloadThemeJson() {
      const root = document.documentElement;
      const style = getComputedStyle(root);
      const tokens = {};
      const allTokens = [
        '--ds-bg', '--ds-surface', '--ds-card-bg', '--ds-surface-container',
        '--ds-surface-container-low', '--ds-surface-container-high', '--ds-surface-container-highest',
        '--ds-on-surface', '--ds-on-surface-variant', '--ds-outline',
        '--ds-primary', '--ds-primary-container', '--ds-on-primary-container',
        '--ds-secondary', '--ds-secondary-container', '--ds-tertiary',
        '--ds-error', '--ds-error-container', '--ds-border', '--ds-shadow', '--ds-radius'
      ];

      for (const t of allTokens) {
        const val = style.getPropertyValue(t).trim();
        if (val) tokens[t] = val;
      }

      const exportObj = {
        id: currentActiveThemeId,
        name: 'Custom Theme',
        category: 'light',
        tokens: tokens
      };

      const blob = new Blob([JSON.stringify(exportObj, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'ethic_theme.json';
      a.click();
      URL.revokeObjectURL(url);
      showToast('Downloaded ethic_theme.json', 'success');
    }

    function promptImportThemeJson() {
      const raw = prompt('Paste your Theme JSON (must contain a "tokens" object):');
      if (!raw) return;
      try {
        const parsed = JSON.parse(raw);
        if (!parsed || !parsed.tokens) throw new Error('Invalid theme format. Missing "tokens" dictionary.');
        const root = document.documentElement;
        for (const [k, v] of Object.entries(parsed.tokens)) {
          root.style.setProperty(k, v);
        }
        localStorage.setItem('ethic_user_theme', JSON.stringify(parsed));
        currentActiveThemeId = parsed.id || 'custom';
        updateThemeBadges();
        renderColorTokens();
        renderThemePresets();
        showToast('Theme imported and applied successfully!', 'success');
      } catch (err) {
        alert('Could not import theme: ' + err.message);
      }
    }

    function resetThemeToDefault() {
      try {
        localStorage.removeItem('ethic_user_theme');
      } catch (e) {}
      applyThemePreset(ETHIC_THEMES.defaultThemeId);
      showToast('Reset theme to factory default', 'info');
    }

    function escapeHtml(value) {
      return String(value ?? '').replace(/[&<>"']/g, (ch) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
      }[ch]));
    }

    // -------------------------------------------------------------------------
    // AUTONOMOUS SCHEDULES & DIFF ENGINE
    // -------------------------------------------------------------------------
    let schedulesCache = [];

    function openSchedulesModal() {
      const modal = document.getElementById('schedulesModal');
      const badge = document.getElementById('headerSchedulesBtn');
      modal.classList.remove('hidden');
      if (badge) badge.setAttribute('aria-expanded', 'true');
      syncBodyScrollLock();
      loadSchedulesTable();
    }

    function closeSchedulesModal() {
      const modal = document.getElementById('schedulesModal');
      const badge = document.getElementById('headerSchedulesBtn');
      modal.classList.add('hidden');
      if (badge) {
        badge.setAttribute('aria-expanded', 'false');
        badge.focus();
      }
      syncBodyScrollLock();
    }

    async function updateSchedulesBadgeCount() {
      try {
        const res = await fetch('/api/v1/schedules');
        if (!res.ok) return;
        const data = await res.json();
        const activeCount = data.filter((j) => j.status === 'active').length;
        const badge = document.getElementById('headerSchedulesCount');
        if (badge) badge.innerText = String(activeCount);
      } catch (e) {}
    }

    async function loadSchedulesTable() {
      const tbody = document.getElementById('schedulesTableBody');
      const countEl = document.getElementById('schedulesTableCount');
      if (!tbody) return;

      tbody.innerHTML = '<tr><td colspan="6" class="p-4 text-center text-xs text-ds-muted"><i class="fa-solid fa-spinner fa-spin mr-1"></i> Loading monitors...</td></tr>';

      try {
        const res = await fetch('/api/v1/schedules');
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const jobs = await res.json();
        schedulesCache = jobs;

        if (countEl) countEl.innerText = String(jobs.length);
        updateSchedulesBadgeCount();

        if (!jobs || jobs.length === 0) {
          tbody.innerHTML = '<tr><td colspan="6" class="p-6 text-center text-xs text-ds-muted font-mono">No active monitors configured yet. Add a target URL above to begin 24/7 autonomous monitoring.</td></tr>';
          return;
        }

        let rowsHtml = '';
        for (const job of jobs) {
          const isPaused = job.status === 'paused';
          const isRunning = job.status === 'running';

          let statusBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">Active</span>';
          if (isPaused) {
            statusBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-100 text-amber-800 border border-amber-200">Paused</span>';
          } else if (isRunning) {
            statusBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-100 text-blue-800 border border-blue-200"><i class="fa-solid fa-spinner fa-spin mr-1"></i> Running</span>';
          } else if (job.last_status === 'changed') {
            statusBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-100 text-purple-800 border border-purple-200">⚡ Changed</span>';
          } else if (job.status === 'error') {
            statusBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-100 text-rose-800 border border-rose-200">Error</span>';
          }

          const lastChecked = job.last_run_at ? new Date(job.last_run_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Pending';
          const nextRun = job.next_run_at ? new Date(job.next_run_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Soon';

          let diffBtn = '';
          if (job.last_raw_diff) {
            diffBtn = `<button type="button" onclick="inspectScheduleDiff('${escapeHtml(job.id)}')" class="px-2 py-1 text-[11px] font-mono font-bold rounded border border-purple-300 bg-purple-50 hover:bg-purple-100 text-purple-700 transition" title="Inspect diff"><i class="fa-solid fa-code-compare mr-1"></i>Diff</button>`;
          }

          const toggleAction = isPaused ? 'Resume' : 'Pause';
          const toggleIcon = isPaused ? 'fa-play' : 'fa-pause';

          rowsHtml += `
            <tr class="hover:bg-slate-50/80 transition">
              <td class="p-3">
                <div class="font-bold text-slate-900">${escapeHtml(job.name)}</div>
                <div class="font-mono text-[11px] text-slate-500 truncate max-w-xs" title="${escapeHtml(job.url)}">${escapeHtml(job.url)}</div>
              </td>
              <td class="p-3 font-mono text-[11px] font-semibold text-slate-700">
                ${escapeHtml(job.interval)} <span class="text-slate-400 font-normal">(${escapeHtml(job.strategy)})</span>
              </td>
              <td class="p-3 font-mono text-[11px] text-slate-600">${escapeHtml(lastChecked)}</td>
              <td class="p-3 font-mono text-[11px] text-slate-600">${escapeHtml(nextRun)}</td>
              <td class="p-3">
                <div class="flex items-center gap-1.5">${statusBadge}</div>
                <div class="text-[10px] text-slate-500 mt-1 truncate max-w-[200px]" title="${escapeHtml(job.last_diff_summary || '')}">${escapeHtml(job.last_diff_summary || 'No changes')}</div>
              </td>
              <td class="p-3 text-right">
                <div class="inline-flex items-center gap-1">
                  ${diffBtn}
                  <button type="button" onclick="runScheduleNow('${escapeHtml(job.id)}')" class="px-2 py-1 text-[11px] font-mono rounded border border-ds hover:bg-slate-100 text-slate-700 transition" title="Run now">
                    <i class="fa-solid fa-bolt mr-1 text-amber-600"></i>Run
                  </button>
                  <button type="button" onclick="toggleScheduleActive('${escapeHtml(job.id)}')" class="px-2 py-1 text-[11px] font-mono rounded border border-ds hover:bg-slate-100 text-slate-700 transition" title="${toggleAction}">
                    <i class="fa-solid ${toggleIcon}"></i>
                  </button>
                  <button type="button" onclick="deleteScheduleJob('${escapeHtml(job.id)}')" class="px-2 py-1 text-[11px] font-mono rounded border border-rose-200 hover:bg-rose-50 text-rose-600 transition" title="Delete">
                    <i class="fa-solid fa-trash-can"></i>
                  </button>
                </div>
              </td>
            </tr>
          `;
        }
        tbody.innerHTML = rowsHtml;
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-xs text-rose-600 font-mono">Failed to load monitors: ${escapeHtml(err.message)}</td></tr>`;
      }
    }

    async function handleCreateSchedule(event) {
      event.preventDefault();
      const urlInput = document.getElementById('schedUrlInput');
      const nameInput = document.getElementById('schedNameInput');
      const intervalInput = document.getElementById('schedIntervalInput');
      const webhookInput = document.getElementById('schedWebhookInput');
      const strategyInput = document.getElementById('schedStrategyInput');
      const btn = document.getElementById('createScheduleBtn');

      const url = urlInput ? urlInput.value.trim() : '';
      if (!url) return;

      const payload = {
        url: url,
        name: nameInput && nameInput.value.trim() ? nameInput.value.trim() : null,
        interval: intervalInput ? intervalInput.value : '24h',
        strategy: strategyInput ? strategyInput.value : 'auto',
        webhook_url: webhookInput && webhookInput.value.trim() ? webhookInput.value.trim() : null,
      };

      if (btn) btn.disabled = true;
      try {
        const res = await fetch('/api/v1/schedules', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || 'Failed to create schedule');
        }
        showToast('Autonomous monitor registered successfully!', 'success');
        if (urlInput) urlInput.value = '';
        if (nameInput) nameInput.value = '';
        if (webhookInput) webhookInput.value = '';
        loadSchedulesTable();
      } catch (err) {
        showToast('Error: ' + err.message, 'error');
      } finally {
        if (btn) btn.disabled = false;
      }
    }

    async function runScheduleNow(jobId) {
      showToast('Executing monitor run...', 'info');
      try {
        const res = await fetch(`/api/v1/schedules/${encodeURIComponent(jobId)}/run`, { method: 'POST' });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        showToast('Monitor execution complete: ' + (data.job.last_status || 'done'), 'success');
        loadSchedulesTable();
        if (data.diff && data.diff.has_changed) {
          openDiffModal(data.diff, data.job.name, data.job.url);
        }
      } catch (err) {
        showToast('Run error: ' + err.message, 'error');
      }
    }

    async function toggleScheduleActive(jobId) {
      try {
        const res = await fetch(`/api/v1/schedules/${encodeURIComponent(jobId)}/toggle`, { method: 'POST' });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        loadSchedulesTable();
      } catch (err) {
        showToast('Toggle error: ' + err.message, 'error');
      }
    }

    async function deleteScheduleJob(jobId) {
      if (!confirm('Are you sure you want to delete this monitor?')) return;
      try {
        const res = await fetch(`/api/v1/schedules/${encodeURIComponent(jobId)}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        showToast('Monitor deleted', 'info');
        loadSchedulesTable();
      } catch (err) {
        showToast('Delete error: ' + err.message, 'error');
      }
    }

    function inspectScheduleDiff(jobId) {
      const job = schedulesCache.find((j) => j.id === jobId);
      if (!job) return;

      const diffObj = {
        has_changed: true,
        similarity_ratio: job.last_similarity_ratio || 1.0,
        added_lines_count: 0,
        removed_lines_count: 0,
        summary: job.last_diff_summary || 'Changes recorded',
        html_diff: job.last_raw_diff ? escapeHtml(job.last_raw_diff) : '<div class="text-slate-400 p-4">No raw diff recorded.</div>',
      };
      openDiffModal(diffObj, job.name, job.url);
    }

    function openDiffModal(diff, title, url) {
      const modal = document.getElementById('diffModal');
      if (!modal) return;
      modal.classList.remove('hidden');
      syncBodyScrollLock();

      const subtitle = document.getElementById('diffSubtitle');
      if (subtitle) subtitle.innerText = `${title || 'Target'} (${url || ''})`;

      const simBadge = document.getElementById('diffSimilarityBadge');
      if (simBadge) {
        const pct = Math.round((diff.similarity_ratio || 1.0) * 100);
        simBadge.innerText = `${pct}% Match`;
        simBadge.className = pct < 90 ?
          'px-2 py-0.5 text-[10px] font-mono font-bold rounded-full bg-purple-100 text-purple-800 border border-purple-200' :
          'px-2 py-0.5 text-[10px] font-mono font-bold rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200';
      }

      const addedEl = document.getElementById('diffAddedCount');
      if (addedEl) addedEl.innerText = String(diff.added_lines_count || 0);

      const removedEl = document.getElementById('diffRemovedCount');
      if (removedEl) removedEl.innerText = String(diff.removed_lines_count || 0);

      const summaryEl = document.getElementById('diffSummaryText');
      if (summaryEl) summaryEl.innerText = diff.summary || 'Summary unavailable';

      const container = document.getElementById('diffHtmlContainer');
      if (container) {
        container.innerHTML = diff.html_diff || '<div class="text-slate-400 p-4">No unified diff lines to display.</div>';
      }
    }

    function closeDiffModal() {
      const modal = document.getElementById('diffModal');
      if (modal) modal.classList.add('hidden');
      syncBodyScrollLock();
    }

    // -------------------------------------------------------------------------
    // INTERACTIVE POINT-AND-CLICK ELEMENT PICKER CONTROLLER
    // -------------------------------------------------------------------------
    let currentPickerTarget = 'scraper';
    let currentPickerUrl = '';

    function openElementPicker(url, target) {
      currentPickerTarget = target || 'scraper';
      let resolvedUrl = url;
      if (!resolvedUrl) {
        const scrapeInput = document.getElementById('scrapeUrl');
        resolvedUrl = scrapeInput ? scrapeInput.value.trim() : '';
      }
      if (!resolvedUrl || !resolvedUrl.startsWith('http')) {
        showToast('Please enter a valid HTTP/HTTPS URL first', 'error');
        return;
      }
      currentPickerUrl = resolvedUrl;
      const urlText = document.getElementById('pickerTargetUrlText');
      if (urlText) urlText.textContent = resolvedUrl;

      const selInput = document.getElementById('pickerSelectorInput');
      if (selInput) selInput.value = '';

      const tagBadge = document.getElementById('pickerTagBadge');
      if (tagBadge) tagBadge.classList.add('hidden');

      const matchesBadge = document.getElementById('pickerMatchesBadge');
      if (matchesBadge) matchesBadge.classList.add('hidden');

      const modal = document.getElementById('elementPickerModal');
      if (modal) modal.classList.remove('hidden');
      syncBodyScrollLock();

      loadPickerIframe(resolvedUrl);
    }

    function openElementPickerFromRpa() {
      const targetInput = document.getElementById('targetUrl');
      const scrapeInput = document.getElementById('scrapeUrl');
      const url = (targetInput && targetInput.value.trim()) ? targetInput.value.trim() : (scrapeInput ? scrapeInput.value.trim() : '');
      openElementPicker(url, 'rpa');
    }

    function loadPickerIframe(url) {
      const loader = document.getElementById('pickerLoading');
      const iframe = document.getElementById('pickerSandboxIframe');
      if (loader) loader.classList.remove('hidden');
      if (iframe) {
        iframe.src = '/api/v1/elements/sandbox?url=' + encodeURIComponent(url);
        iframe.onload = () => {
          if (loader) loader.classList.add('hidden');
        };
      }
    }

    function refreshPickerIframe() {
      if (currentPickerUrl) {
        loadPickerIframe(currentPickerUrl);
      }
    }

    function closeElementPicker() {
      const modal = document.getElementById('elementPickerModal');
      if (modal) modal.classList.add('hidden');
      const iframe = document.getElementById('pickerSandboxIframe');
      if (iframe) iframe.src = 'about:blank';
      syncBodyScrollLock();
    }

    function copyPickerSelector() {
      const input = document.getElementById('pickerSelectorInput');
      const val = input ? input.value : '';
      if (!val) {
        showToast('No selector picked yet', 'warning');
        return;
      }
      navigator.clipboard.writeText(val);
      showToast('Selector copied to clipboard: ' + val, 'success');
    }

    function applyPickerSelector() {
      const input = document.getElementById('pickerSelectorInput');
      const val = input ? input.value : '';
      if (!val) {
        showToast('Please select an element first', 'warning');
        return;
      }
      if (currentPickerTarget === 'rpa') {
        const rpaInput = document.getElementById('rpaStepSelector');
        if (rpaInput) rpaInput.value = val;
        showToast('Applied selector to RPA Step: ' + val, 'success');
      } else {
        const customPrompt = document.getElementById('customPrompt');
        if (customPrompt) {
          customPrompt.value = (customPrompt.value ? customPrompt.value + '\\nTarget CSS: ' : 'Target CSS: ') + val;
        }
        navigator.clipboard.writeText(val);
        showToast('Selector copied and set: ' + val, 'success');
      }
      closeElementPicker();
    }

    window.addEventListener('message', (event) => {
      if (event.data && event.data.type === 'ELEMENT_PICKED') {
        const { selector, tagName, innerText, matchCount } = event.data;
        const input = document.getElementById('pickerSelectorInput');
        if (input) input.value = selector || '';

        const tagBadge = document.getElementById('pickerTagBadge');
        if (tagBadge && tagName) {
          tagBadge.textContent = tagName;
          tagBadge.classList.remove('hidden');
        }

        const matchBadge = document.getElementById('pickerMatchesBadge');
        if (matchBadge) {
          matchBadge.textContent = matchCount === 1 ? '1 unique match' : (matchCount + ' matches');
          matchBadge.classList.remove('hidden');
        }
      }
    });

    // -------------------------------------------------------------------------
    // COMPETITIVE BENCHMARKING & TECH PROFILING CONTROLLER
    // -------------------------------------------------------------------------
    let lastBenchmarkDomains = [];

    function openCompetitorModal(preselectedDomain) {
      const modal = document.getElementById('competitorModal');
      const badge = document.getElementById('headerBenchmarkBtn');
      if (modal) modal.classList.remove('hidden');
      if (badge) badge.setAttribute('aria-expanded', 'true');
      syncBodyScrollLock();
      loadBenchmarkDomainCheckboxes(preselectedDomain);
    }

    function closeCompetitorModal() {
      const modal = document.getElementById('competitorModal');
      const badge = document.getElementById('headerBenchmarkBtn');
      if (modal) modal.classList.add('hidden');
      if (badge) {
        badge.setAttribute('aria-expanded', 'false');
        badge.focus();
      }
      syncBodyScrollLock();
    }

    async function loadBenchmarkDomainCheckboxes(preselectedDomain) {
      const container = document.getElementById('benchmarkDomainList');
      if (!container) return;

      try {
        let domains = storedDomainsList;
        if (!domains || domains.length === 0) {
          const res = await fetch('/api/v1/domains');
          if (res.ok) {
            domains = await res.json();
            storedDomainsList = domains;
          }
        }

        if (!domains || domains.length === 0) {
          container.innerHTML = '<span class="text-xs text-slate-400 italic">No indexed domains found in ChromaDB. Crawl at least 2 websites first.</span>';
          return;
        }

        let html = '';
        domains.forEach((d) => {
          const domName = typeof d === 'string' ? d : (d.domain || '');
          if (!domName) return;
          const isChecked = preselectedDomain && preselectedDomain.toLowerCase() === domName.toLowerCase();
          html += `
            <label class="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-50 border border-ds text-xs font-mono cursor-pointer hover:bg-slate-100 select-none">
              <input type="checkbox" name="benchmarkDomain" value="${escapeHtml(domName)}" ${isChecked ? 'checked' : ''} class="rounded text-amber-600 focus:ring-0">
              <span class="text-slate-800 font-semibold">${escapeHtml(domName)}</span>
            </label>
          `;
        });
        container.innerHTML = html;
      } catch (err) {
        container.innerHTML = `<span class="text-xs text-rose-500">Failed loading domains: ${err.message}</span>`;
      }
    }

    async function runCompetitorBenchmark() {
      const checkboxes = document.querySelectorAll('input[name="benchmarkDomain"]:checked');
      const selected = Array.from(checkboxes).map((cb) => cb.value);

      if (selected.length < 2) {
        showToast('Please select at least 2 competitor domains to benchmark.', 'warning');
        return;
      }
      if (selected.length > 5) {
        showToast('Please select no more than 5 domains for side-by-side comparison.', 'warning');
        return;
      }

      lastBenchmarkDomains = selected;
      const focus = (document.getElementById('benchmarkFocusInput').value || '').trim();

      const emptyState = document.getElementById('benchmarkEmptyState');
      const loader = document.getElementById('benchmarkLoading');
      const content = document.getElementById('benchmarkContent');
      const btn = document.getElementById('btnRunBenchmark');

      if (emptyState) emptyState.classList.add('hidden');
      if (content) content.classList.add('hidden');
      if (loader) loader.classList.remove('hidden');
      if (btn) btn.disabled = true;

      try {
        const resp = await fetch('/api/v1/competitors/compare', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            domains: selected,
            custom_focus: focus || null,
          }),
        });

        if (!resp.ok) {
          const err = await resp.json().catch(() => ({ detail: 'HTTP ' + resp.status }));
          throw new Error(err.detail || 'Failed to benchmark competitors');
        }

        const data = await resp.json();

        // Render model badge
        const badge = document.getElementById('benchmarkModelBadge');
        if (badge) badge.textContent = data.model_used || 'heuristic-synthesis';

        // Render table
        const tableContainer = document.getElementById('benchmarkTableContainer');
        if (tableContainer) {
          tableContainer.innerHTML = typeof marked !== 'undefined' ? marked.parse(data.comparison_table_md) : `<pre>${escapeHtml(data.comparison_table_md)}</pre>`;
        }

        // Render full report
        const reportContainer = document.getElementById('benchmarkReportContainer');
        if (reportContainer) {
          reportContainer.innerHTML = typeof marked !== 'undefined' ? marked.parse(data.full_report_md) : `<pre>${escapeHtml(data.full_report_md)}</pre>`;
        }

        if (loader) loader.classList.add('hidden');
        if (content) content.classList.remove('hidden');
        showToast('Competitive benchmark generated successfully!', 'success');
      } catch (err) {
        if (loader) loader.classList.add('hidden');
        if (emptyState) emptyState.classList.remove('hidden');
        showToast('Error: ' + err.message, 'error');
      } finally {
        if (btn) btn.disabled = false;
      }
    }

    async function exportCompetitorBenchmark(fmt) {
      if (!lastBenchmarkDomains || lastBenchmarkDomains.length < 2) {
        showToast('Run a benchmark first before exporting.', 'warning');
        return;
      }

      const focus = (document.getElementById('benchmarkFocusInput').value || '').trim();
      const format = fmt || 'pdf';

      try {
        showToast(`Preparing ${format.toUpperCase()} export...`, 'info');
        const resp = await fetch('/api/v1/competitors/compare/export', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            domains: lastBenchmarkDomains,
            custom_focus: focus || null,
            format: format,
          }),
        });

        if (!resp.ok) throw new Error('Export failed: HTTP ' + resp.status);

        const blob = await resp.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        const ext = format === 'markdown' ? 'md' : 'pdf';
        a.download = `competitor_benchmark_${lastBenchmarkDomains.join('_vs_')}.${ext}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
        showToast(`${format.toUpperCase()} export downloaded!`, 'success');
      } catch (err) {
        showToast('Export failed: ' + err.message, 'error');
      }
    }

    // -------------------------------------------------------------------------
    // VISUAL PRODUCT BLUEPRINT & REVERSE-ENGINEERING CONTROLLER
    // -------------------------------------------------------------------------
    let currentBlueprintResult = null;
    let currentBlueprintDomain = '';
    let blueprintPendingFiles = [];

    function toggleBlueprintUploadSection() {
      const sec = document.getElementById('blueprintUploadSection');
      if (!sec) return;
      sec.classList.toggle('hidden');
      if (!sec.classList.contains('hidden')) {
        populateBlueprintUploadDomainSelect();
      }
    }

    function populateBlueprintUploadDomainSelect() {
      const mainSelect = document.getElementById('blueprintDomainSelect');
      const upSelect = document.getElementById('blueprintUploadDomainSelect');
      const badge = document.getElementById('blueprintUploadTargetBadge');
      if (!upSelect) return;

      const currentVal = (mainSelect && mainSelect.value) ? mainSelect.value : currentBlueprintDomain;
      let opts = '';
      let foundSelected = false;

      if (mainSelect) {
        for (let i = 0; i < mainSelect.options.length; i++) {
          const opt = mainSelect.options[i];
          if (opt.value) {
            const isSel = (opt.value === currentVal);
            if (isSel) foundSelected = true;
            opts += `<option value="${escapeHtml(opt.value)}" ${isSel ? 'selected' : ''}>🌐 ${escapeHtml(opt.text)}</option>`;
          }
        }
      }

      opts += `<option value="__NEW__" ${!foundSelected ? 'selected' : ''}>➕ Create New Domain / Project...</option>`;
      upSelect.innerHTML = opts;
      onBlueprintUploadDomainSelectChange();
    }

    function onBlueprintUploadDomainSelectChange() {
      const upSelect = document.getElementById('blueprintUploadDomainSelect');
      const newInput = document.getElementById('blueprintUploadDomainInput');
      const badge = document.getElementById('blueprintUploadTargetBadge');
      if (!upSelect) return;

      if (upSelect.value === '__NEW__') {
        if (newInput) {
          newInput.classList.remove('hidden');
          newInput.focus();
        }
        if (badge) badge.textContent = (newInput && newInput.value.trim()) ? newInput.value.trim() : '(New Domain)';
      } else {
        if (newInput) newInput.classList.add('hidden');
        if (badge) badge.textContent = upSelect.value;
      }
    }

    function isImageFile(file) {
      return !!file && (
        file.type.startsWith('image/') ||
        /\\.(png|jpe?g|webp)$/i.test(file.name)
      );
    }

    function onBlueprintFileSelect(event) {
      const files = Array.from(event.target.files || []).filter(isImageFile);
      setBlueprintPendingFiles(files);
    }

    function onBlueprintFolderSelect(event) {
      const files = Array.from(event.target.files || []).filter(isImageFile);
      if (files.length > 0 && files[0].webkitRelativePath) {
        const parts = files[0].webkitRelativePath.split('/');
        if (parts.length > 1 && parts[0]) {
          autoSuggestDomainIfNew(parts[0]);
        }
      }
      setBlueprintPendingFiles(files);
    }

    function autoSuggestDomainIfNew(suggested) {
      if (!suggested) return;
      const clean = suggested.replace(/[^a-zA-Z0-9_\\-\\.]/g, '_').toLowerCase();
      const upSelect = document.getElementById('blueprintUploadDomainSelect');
      const newInput = document.getElementById('blueprintUploadDomainInput');
      const badge = document.getElementById('blueprintUploadTargetBadge');

      if (upSelect && upSelect.value === '__NEW__' && newInput) {
        newInput.value = clean;
        if (badge) badge.textContent = clean;
      }
    }

    function getFileFromEntry(fileEntry) {
      return new Promise((resolve) => {
        fileEntry.file(resolve, () => resolve(null));
      });
    }

    async function readDirectoryEntries(dirEntry) {
      const dirReader = dirEntry.createReader();
      const entries = await new Promise((resolve) => {
        dirReader.readEntries(resolve, () => resolve([]));
      });
      const files = [];
      for (const entry of entries) {
        if (entry.isFile) {
          const file = await getFileFromEntry(entry);
          if (file && isImageFile(file)) files.push(file);
        } else if (entry.isDirectory) {
          const subFiles = await readDirectoryEntries(entry);
          files.push(...subFiles);
        }
      }
      return files;
    }

    async function handleBlueprintDrop(event) {
      event.preventDefault();
      const dropzone = document.getElementById('blueprintUploadDropzone');
      if (dropzone) dropzone.classList.remove('border-teal-500', 'bg-teal-100/40');

      const items = event.dataTransfer.items;
      if (!items) {
        const files = Array.from(event.dataTransfer.files || []).filter(isImageFile);
        setBlueprintPendingFiles(files);
        return;
      }

      const collectedFiles = [];
      const entries = [];
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        const entry = item.webkitGetAsEntry ? item.webkitGetAsEntry() : null;
        if (entry) entries.push(entry);
      }

      for (const entry of entries) {
        if (entry.isFile) {
          const file = await getFileFromEntry(entry);
          if (file && isImageFile(file)) collectedFiles.push(file);
        } else if (entry.isDirectory) {
          autoSuggestDomainIfNew(entry.name);
          const dirFiles = await readDirectoryEntries(entry);
          collectedFiles.push(...dirFiles);
        }
      }

      if (collectedFiles.length === 0) {
        const fallback = Array.from(event.dataTransfer.files || []).filter(isImageFile);
        setBlueprintPendingFiles(fallback);
      } else {
        setBlueprintPendingFiles(collectedFiles);
      }
    }

    function setBlueprintPendingFiles(files) {
      blueprintPendingFiles = files;
      const status = document.getElementById('blueprintUploadStatus');
      if (status) {
        if (files.length === 0) {
          status.textContent = 'No image files detected.';
        } else {
          status.textContent = `${files.length} screenshot(s) staged: ` + files.map(f => f.name).slice(0, 3).join(', ') + (files.length > 3 ? '...' : '');
        }
      }
    }

    async function submitBlueprintUpload() {
      const upSelect = document.getElementById('blueprintUploadDomainSelect');
      const newInput = document.getElementById('blueprintUploadDomainInput');
      let targetDomain = '';

      if (upSelect && upSelect.value !== '__NEW__') {
        targetDomain = upSelect.value.trim();
      } else if (newInput) {
        targetDomain = newInput.value.trim();
      }

      if (!targetDomain) {
        showToast('Please select or specify a target domain name', 'warning');
        if (newInput && !newInput.classList.contains('hidden')) newInput.focus();
        return;
      }
      if (!blueprintPendingFiles || blueprintPendingFiles.length === 0) {
        showToast('Please select or drop at least one screenshot image or folder', 'warning');
        return;
      }

      const btn = document.getElementById('btnSubmitBlueprintUpload');
      const status = document.getElementById('blueprintUploadStatus');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Uploading...';
      }
      if (status) status.textContent = `Uploading ${blueprintPendingFiles.length} screenshots to ${targetDomain}...`;

      try {
        const filePayloads = await Promise.all(blueprintPendingFiles.map(file => {
          return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve({ filename: file.name, data_base64: reader.result });
            reader.onerror = reject;
            reader.readAsDataURL(file);
          });
        }));

        const resp = await fetch('/api/v1/blueprint/upload', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ domain: targetDomain, files: filePayloads })
        });

        if (!resp.ok) {
          const errData = await resp.json().catch(() => ({}));
          throw new Error(errData.detail || ('HTTP ' + resp.status));
        }

        const data = await resp.json();
        showToast(`Successfully uploaded ${data.saved_count} screenshots for ${data.domain}!`, 'success');

        blueprintPendingFiles = [];
        if (newInput) newInput.value = '';
        const fileInput = document.getElementById('blueprintUploadFileInput');
        if (fileInput) fileInput.value = '';
        const folderInput = document.getElementById('blueprintUploadFolderInput');
        if (folderInput) folderInput.value = '';
        if (status) status.textContent = '';
        toggleBlueprintUploadSection();

        await loadBlueprintDomains(data.domain);
      } catch (err) {
        showToast('Upload failed: ' + err.message, 'error');
        if (status) status.textContent = 'Upload failed: ' + err.message;
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Upload & Catalog';
        }
      }
    }

    function openBlueprintModal(preselectedDomain) {
      const modal = document.getElementById('blueprintModal');
      const badge = document.getElementById('headerBlueprintBtn');
      if (modal) modal.classList.remove('hidden');
      if (badge) badge.setAttribute('aria-expanded', 'true');
      syncBodyScrollLock();
      loadBlueprintDomains(preselectedDomain);
    }

    function closeBlueprintModal() {
      const modal = document.getElementById('blueprintModal');
      const badge = document.getElementById('headerBlueprintBtn');
      if (modal) modal.classList.add('hidden');
      if (badge) {
        badge.setAttribute('aria-expanded', 'false');
        badge.focus();
      }
      syncBodyScrollLock();
    }

    async function loadBlueprintDomains(preselectedDomain) {
      const select = document.getElementById('blueprintDomainSelect');
      if (!select) return;

      select.innerHTML = '<option value="">Loading domains...</option>';

      try {
        const [bpResp, domResp] = await Promise.all([
          fetch('/api/v1/blueprint/domains').catch(() => null),
          fetch('/api/v1/history/domains').catch(() => null)
        ]);

        const bpDomains = (bpResp && bpResp.ok) ? await bpResp.json() : [];
        const allDomains = (domResp && domResp.ok) ? await domResp.json() : [];

        // Combine unique domain names from both ChromaDB crawled history AND screenshot folders
        const domainMap = new Map();

        allDomains.forEach(d => {
          const name = typeof d === 'string' ? d : (d.domain || '');
          const pages = (d && d.total_pages) ? d.total_pages : 0;
          if (name) {
            domainMap.set(name, { screenshots: 0, pages: pages });
          }
        });

        bpDomains.forEach(item => {
          const name = item.domain || '';
          if (name) {
            const existing = domainMap.get(name) || { screenshots: 0, pages: 0 };
            existing.screenshots = item.screenshot_count || 1;
            domainMap.set(name, existing);
          }
        });

        if (domainMap.size === 0) {
          select.innerHTML = '<option value="">No domains found. Crawl or upload screenshots first.</option>';
          populateBlueprintUploadDomainSelect();
          return;
        }

        let optsHtml = '<option value="">Select an indexed domain...</option>';
        domainMap.forEach((info, name) => {
          let badge = '';
          if (info.screenshots > 0 && info.pages > 0) {
            badge = ` (${info.screenshots} screenshots, ${info.pages} crawled pages)`;
          } else if (info.screenshots > 0) {
            badge = ` (${info.screenshots} screenshots)`;
          } else {
            badge = ` (${info.pages} crawled pages)`;
          }
          const isSel = preselectedDomain && preselectedDomain.toLowerCase() === name.toLowerCase();
          optsHtml += `<option value="${escapeHtml(name)}" ${isSel ? 'selected' : ''}>🌐 ${escapeHtml(name)}${badge}</option>`;
        });
        select.innerHTML = optsHtml;
        populateBlueprintUploadDomainSelect();

        if (preselectedDomain) {
          onBlueprintDomainChange();
        }
      } catch (err) {
        select.innerHTML = `<option value="">Error loading domains: ${err.message}</option>`;
      }
    }

    async function onBlueprintDomainChange() {
      const select = document.getElementById('blueprintDomainSelect');
      const domain = select ? select.value.trim() : '';
      currentBlueprintDomain = domain;
      if (!domain) {
        document.getElementById('blueprintScreenshotCarousel').innerHTML = '<div class="p-4 text-center text-xs text-slate-400 w-full italic">Select a domain above to view its captured screenshot collection.</div>';
        document.getElementById('blueprintScreenCountBadge').textContent = '0 screens cataloged';
        return;
      }
      loadDomainScreenshotCarousel(domain);
    }

    async function loadDomainScreenshotCarousel(domain) {
      const carousel = document.getElementById('blueprintScreenshotCarousel');
      const countBadge = document.getElementById('blueprintScreenCountBadge');
      if (!carousel) return;

      carousel.innerHTML = '<div class="p-3 text-xs text-slate-400 flex items-center gap-2"><i class="fa-solid fa-spinner fa-spin text-teal-600"></i> Loading screenshot collection...</div>';

      try {
        const resp = await fetch(`/api/v1/screenshots?domain=${encodeURIComponent(domain)}`);
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        const data = await resp.json();
        const files = Array.isArray(data) ? data : (data.screenshots || []);

        if (countBadge) countBadge.textContent = `${files.length} screens cataloged`;

        if (files.length === 0) {
          carousel.innerHTML = `
            <div class="p-3 text-xs text-slate-500 flex items-center gap-2">
              <i class="fa-solid fa-circle-info text-amber-500"></i>
              No disk screenshots found for <strong>${escapeHtml(domain)}</strong>. The blueprint engine will use ChromaDB page vectors to synthesize architecture.
            </div>`;
          return;
        }

        let itemsHtml = '';
        files.forEach((item, idx) => {
          const fname = typeof item === 'string' ? item : item.filename;
          const urlPath = (typeof item === 'object' && item.url_path) ? item.url_path : `/api/v1/screenshots/file/${encodeURIComponent(domain)}/${encodeURIComponent(fname)}`;
          const fetchPriority = idx === 0 ? 'high' : 'low';
          itemsHtml += `
            <div class="carousel-item shrink-0 rounded-lg overflow-hidden border border-ds bg-white p-1 hover:border-teal-500 transition shadow-xs select-none" style="scroll-snap-align: start;">
              <img src="${urlPath}" alt="${escapeHtml(fname)}" loading="lazy" fetchpriority="${fetchPriority}" class="aspect-video w-48 rounded object-cover cursor-pointer border border-slate-100 hover:opacity-95 transition" onclick="previewCachedScreenshot('${urlPath}')" title="Click to view full image">
              <div class="text-[10px] font-mono text-slate-700 truncate px-1 pt-1 max-w-[192px]" title="${escapeHtml(fname)}">${escapeHtml(fname)}</div>
            </div>
          `;
        });
        carousel.innerHTML = itemsHtml;
      } catch (err) {
        carousel.innerHTML = `<div class="p-3 text-xs text-rose-500">Failed loading screenshots: ${err.message}</div>`;
      }
    }

    function previewCachedScreenshot(url) {
      window.open(url, '_blank');
    }

    async function runGenerateBlueprint() {
      const select = document.getElementById('blueprintDomainSelect');
      const domain = select ? select.value.trim() : '';

      if (!domain) {
        showToast('Please select a target domain first', 'warning');
        return;
      }

      currentBlueprintDomain = domain;
      const focus = (document.getElementById('blueprintFocusInput').value || '').trim();
      const model = document.getElementById('blueprintModelSelect') ? document.getElementById('blueprintModelSelect').value : null;

      const emptyState = document.getElementById('blueprintEmptyState');
      const loader = document.getElementById('blueprintLoading');
      const content = document.getElementById('blueprintContent');
      const btn = document.getElementById('btnRunBlueprint');
      const exportBar = document.getElementById('blueprintExportActions');

      if (emptyState) emptyState.classList.add('hidden');
      if (content) content.classList.add('hidden');
      if (loader) loader.classList.remove('hidden');
      if (btn) btn.disabled = true;

      try {
        const resp = await fetch('/api/v1/blueprint/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            domain: domain,
            custom_focus: focus || null,
            model: model || null
          })
        });

        if (!resp.ok) {
          const err = await resp.json().catch(() => ({ detail: 'HTTP ' + resp.status }));
          throw new Error(err.detail || 'Failed generating blueprint');
        }

        const data = await resp.json();
        currentBlueprintResult = data;
        renderBlueprintResult(data);

        if (loader) loader.classList.add('hidden');
        if (content) content.classList.remove('hidden');
        if (exportBar) exportBar.classList.remove('hidden');
        showToast('Full-stack product blueprint synthesized successfully!', 'success');
      } catch (err) {
        if (loader) loader.classList.add('hidden');
        if (emptyState) emptyState.classList.remove('hidden');
        showToast('Error: ' + err.message, 'error');
      } finally {
        if (btn) btn.disabled = false;
      }
    }

    function renderBlueprintResult(data) {
      // 1. Storyboard & Overview
      const storyText = document.getElementById('bpStoryboardText');
      if (storyText) {
        storyText.innerHTML = typeof marked !== 'undefined' ? marked.parse(data.storyboard_markdown) : `<pre>${escapeHtml(data.storyboard_markdown)}</pre>`;
      }

      // Features Grid
      const featuresGrid = document.getElementById('bpFeaturesGrid');
      if (featuresGrid) {
        featuresGrid.innerHTML = data.features_list.map(f => `
          <div class="p-2.5 rounded-lg border border-ds bg-slate-50 flex items-start gap-2">
            <i class="fa-solid fa-circle-check text-teal-600 mt-0.5 text-xs"></i>
            <span class="text-xs font-semibold text-slate-800">${escapeHtml(f)}</span>
          </div>
        `).join('');
      }

      // Use cases
      const useCasesList = document.getElementById('bpUseCasesList');
      if (useCasesList) {
        useCasesList.innerHTML = data.use_cases.map(uc => `
          <div class="p-3 rounded-lg border border-ds bg-white shadow-xs space-y-1.5">
            <div class="font-bold text-xs text-slate-900 flex items-center justify-between">
              <span>${escapeHtml(uc.title)}</span>
              <span class="px-2 py-0.5 rounded text-[10px] bg-teal-50 text-teal-800 font-mono border border-teal-200">${escapeHtml(uc.actor)}</span>
            </div>
            <div class="text-[11px] text-slate-500 font-mono"><strong class="text-slate-700">Precondition:</strong> ${escapeHtml(uc.precondition)}</div>
            <div class="text-[11px] text-slate-700 bg-slate-50 p-2 rounded border border-ds leading-relaxed">${escapeHtml(uc.flow)}</div>
            <div class="text-[11px] text-emerald-800 font-medium"><i class="fa-solid fa-flag-checkered mr-1"></i><strong>Outcome:</strong> ${escapeHtml(uc.outcome)}</div>
          </div>
        `).join('');
      }

      // 2. Diagrams
      const navContainer = document.getElementById('bpNavDiagramContainer');
      if (navContainer) {
        navContainer.innerHTML = `<pre class="text-left font-mono text-[11px] p-3 rounded bg-slate-900 text-teal-300 overflow-x-auto whitespace-pre">${escapeHtml(data.navigation_mermaid)}</pre>`;
      }

      const erdContainer = document.getElementById('bpErdDiagramContainer');
      if (erdContainer) {
        erdContainer.innerHTML = `<pre class="text-left font-mono text-[11px] p-3 rounded bg-slate-900 text-purple-300 overflow-x-auto whitespace-pre">${escapeHtml(data.erd_mermaid)}</pre>`;
      }

      // 3. Frontend & Design Tokens
      const compList = document.getElementById('bpComponentsList');
      if (compList) {
        compList.innerHTML = data.frontend_components.map(c => `
          <div class="p-3 rounded-lg border border-ds bg-white space-y-1.5 shadow-xs">
            <div class="flex items-center justify-between">
              <span class="font-bold text-xs text-slate-900 font-mono">${escapeHtml(c.name)}</span>
              <span class="px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase bg-slate-100 text-slate-700">${escapeHtml(c.category)}</span>
            </div>
            <p class="text-[11px] text-slate-600">${escapeHtml(c.description)}</p>
            <div class="text-[10px] font-mono text-slate-500">Props: ${escapeHtml(c.props.join(', '))}</div>
            <div class="text-[10px] font-mono text-teal-700">Children: ${escapeHtml(c.subcomponents.join(', '))}</div>
          </div>
        `).join('');
      }

      const tokensContainer = document.getElementById('bpDesignTokensContainer');
      if (tokensContainer) {
        tokensContainer.innerHTML = `<pre class="whitespace-pre">${escapeHtml(JSON.stringify(data.design_tokens, null, 2))}</pre>`;
      }

      // 4. Backend APIs
      const apiList = document.getElementById('bpApiEndpointsList');
      if (apiList) {
        apiList.innerHTML = data.api_endpoints.map(ep => {
          const methodColors = {
            'GET': 'bg-blue-100 text-blue-800 border-blue-200',
            'POST': 'bg-emerald-100 text-emerald-800 border-emerald-200',
            'PUT': 'bg-amber-100 text-amber-800 border-amber-200',
            'DELETE': 'bg-rose-100 text-rose-800 border-rose-200'
          };
          const badgeClass = methodColors[ep.method] || 'bg-slate-100 text-slate-800';

          return `
            <div class="p-3 rounded-lg border border-ds bg-white space-y-2 shadow-xs">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <div class="flex items-center gap-2 font-mono text-xs font-bold">
                  <span class="px-2 py-0.5 rounded text-[11px] border ${badgeClass}">${ep.method}</span>
                  <span class="text-slate-900">${escapeHtml(ep.path)}</span>
                </div>
                <span class="text-[11px] text-slate-400 font-mono">${escapeHtml(ep.screen_origin)}</span>
              </div>
              <p class="text-[11px] text-slate-600">${escapeHtml(ep.summary)}</p>
              ${ep.request_body ? `
                <div class="text-[10px] font-mono bg-slate-50 p-2 rounded border border-ds">
                  <span class="font-bold text-slate-700">Request Body:</span>
                  <pre class="mt-1 text-slate-800 whitespace-pre">${escapeHtml(JSON.stringify(ep.request_body, null, 2))}</pre>
                </div>
              ` : ''}
              <div class="text-[10px] font-mono bg-slate-50 p-2 rounded border border-ds">
                <span class="font-bold text-slate-700">Response Body:</span>
                <pre class="mt-1 text-slate-800 whitespace-pre">${escapeHtml(JSON.stringify(ep.response_body, null, 2))}</pre>
              </div>
            </div>
          `;
        }).join('');
      }
    }

    function switchBlueprintTab(tabName) {
      const tabs = ['storyboard', 'diagrams', 'frontend', 'backend'];
      tabs.forEach(t => {
        const btn = document.getElementById(`tabBtn_${t}`);
        const panel = document.getElementById(`bpPanel_${t}`);
        if (btn) {
          const isAct = t === tabName;
          btn.setAttribute('aria-selected', isAct ? 'true' : 'false');
          btn.className = isAct ?
            'px-3 py-2.5 font-bold border-b-2 border-teal-600 text-teal-700 flex items-center gap-1.5' :
            'px-3 py-2.5 font-bold border-b-2 border-transparent text-slate-600 hover:text-slate-900 flex items-center gap-1.5';
        }
        if (panel) {
          if (t === tabName) panel.classList.remove('hidden');
          else panel.classList.add('hidden');
        }
      });
    }

    function copyBlueprintDiagram(type) {
      if (!currentBlueprintResult) return;
      const text = type === 'nav' ? currentBlueprintResult.navigation_mermaid : currentBlueprintResult.erd_mermaid;
      navigator.clipboard.writeText(text);
      showToast(`${type.toUpperCase()} Mermaid diagram copied to clipboard!`, 'success');
    }

    async function exportBlueprint(fmt) {
      if (!currentBlueprintDomain) {
        showToast('Generate a blueprint first before exporting', 'warning');
        return;
      }

      const format = fmt || 'pdf';
      const dossierMd = currentBlueprintResult ? currentBlueprintResult.full_markdown_dossier : null;

      // Instant client-side download for Markdown if blueprint is already generated
      if (format === 'markdown' && dossierMd) {
        try {
          const blob = new Blob([dossierMd], { type: 'text/markdown;charset=utf-8' });
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.style.display = 'none';
          a.href = url;
          a.download = `blueprint_${currentBlueprintDomain.replace(/\./g, '_')}.md`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          a.remove();
          showToast('Markdown architecture blueprint downloaded!', 'success');
          return;
        } catch (e) {
          console.warn('Client-side download fallback to server:', e);
        }
      }

      const focus = (document.getElementById('blueprintFocusInput').value || '').trim();
      const model = document.getElementById('blueprintModelSelect') ? document.getElementById('blueprintModelSelect').value : null;

      try {
        showToast(`Preparing ${format.toUpperCase()} architecture blueprint...`, 'info');
        const resp = await fetch('/api/v1/blueprint/export', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            domain: currentBlueprintDomain,
            custom_focus: focus || null,
            model: model || null,
            format: format,
            dossier_markdown: dossierMd || null,
            blueprint_data: currentBlueprintResult || null
          })
        });

        if (!resp.ok) throw new Error('HTTP ' + resp.status);

        const blob = await resp.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        const ext = format === 'markdown' ? 'md' : 'pdf';
        a.download = `blueprint_${currentBlueprintDomain.replace(/\./g, '_')}.${ext}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
        showToast(`${format.toUpperCase()} architecture blueprint downloaded!`, 'success');
      } catch (err) {
        showToast('Export failed: ' + err.message, 'error');
      }
    }

    let chromaStoreCache = null;

    function openChromaStoreModal() {
      const modal = document.getElementById('chromaStoreModal');
      const badge = document.getElementById('headerStoreBadge');
      modal.classList.remove('hidden');
      if (badge) badge.setAttribute('aria-expanded', 'true');
      syncBodyScrollLock();
      loadChromaStoreInspector();
      const title = document.getElementById('chromaStoreTitle');
      if (title) title.focus();
    }

    function closeChromaStoreModal() {
      document.getElementById('chromaStoreModal').classList.add('hidden');
      const badge = document.getElementById('headerStoreBadge');
      if (badge) {
        badge.setAttribute('aria-expanded', 'false');
        badge.focus();
      }
      syncBodyScrollLock();
    }

    function setChromaStoreTab(tab) {
      const dataBtn = document.getElementById('chromaTabData');
      const mapBtn = document.getElementById('chromaTabMap');
      const dataPanel = document.getElementById('chromaStoreDataPanel');
      const mapPanel = document.getElementById('chromaStoreMapPanel');
      const isData = tab === 'data';
      const activeCls = 'px-3 py-1.5 rounded-full text-xs font-semibold view-toggle-active';
      const inactiveCls = 'px-3 py-1.5 rounded-full text-xs font-semibold view-toggle-inactive';
      dataBtn.className = isData ? activeCls : inactiveCls;
      mapBtn.className = !isData ? activeCls : inactiveCls;
      dataBtn.setAttribute('aria-selected', isData ? 'true' : 'false');
      mapBtn.setAttribute('aria-selected', !isData ? 'true' : 'false');
      dataPanel.classList.toggle('hidden', !isData);
      mapPanel.classList.toggle('hidden', isData);
    }

    async function loadChromaStoreInspector() {
      const dataPanel = document.getElementById('chromaStoreDataPanel');
      const mapBody = document.getElementById('chromaStoreMapBody');
      dataPanel.innerHTML = '<p class="text-ds-muted text-xs"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Reading local ChromaDB collection…</p>';
      try {
        const resp = await fetch('/api/v1/history/store?limit=500');
        if (!resp.ok) throw new Error('Could not read vector store');
        chromaStoreCache = await resp.json();
        const count = chromaStoreCache.document_count || 0;
        document.getElementById('chromaStatDocs').innerText = count;
        document.getElementById('chromaStatDomains').innerText = chromaStoreCache.domain_count || 0;
        document.getElementById('chromaStatSpace').innerText = chromaStoreCache.distance_space || 'cosine';
        document.getElementById('chromaStatCollection').innerText = chromaStoreCache.collection || 'crawled_knowledge';
        document.getElementById('chromaStoreMeta').innerText =
          `${chromaStoreCache.engine} · ${chromaStoreCache.persist_dir} · upsert-only`;
        const headerCount = document.getElementById('headerStoreCount');
        if (headerCount) headerCount.innerText = count;

        mapBody.innerHTML = (chromaStoreCache.field_mappings || []).map((row) => `
          <tr class="history-row">
            <td class="font-mono text-ds-accent whitespace-nowrap">${escapeHtml(row.field)}</td>
            <td>${escapeHtml(row.source)}</td>
            <td class="text-ds-muted">${escapeHtml(row.role)}</td>
          </tr>
        `).join('') || '<tr><td class="text-ds-muted p-3" colspan="3">No field mappings available.</td></tr>';
        renderChromaStoreData();
      } catch (err) {
        dataPanel.innerHTML = `<p class="text-red-300 text-xs">${escapeHtml(err.message)}</p>`;
      }
    }

    function renderChromaStoreData() {
      const panel = document.getElementById('chromaStoreDataPanel');
      if (!panel || !chromaStoreCache) return;
      const query = (document.getElementById('chromaStoreFilter').value || '').toLowerCase().trim();
      const docs = (chromaStoreCache.documents || []).filter((doc) => {
        if (!query) return true;
        return [doc.id, doc.url, doc.final_url, doc.domain, doc.title]
          .some((value) => String(value || '').toLowerCase().includes(query));
      });
      const grouped = {};
      docs.forEach((doc) => {
        const domain = doc.domain || 'unknown';
        if (!grouped[domain]) grouped[domain] = [];
        grouped[domain].push(doc);
      });
      const domains = Object.keys(grouped).sort();
      if (domains.length === 0) {
        panel.innerHTML = '<p class="text-ds-muted text-sm">No stored documents match this filter. Crawl or scrape a page to populate ChromaDB.</p>';
        return;
      }
      panel.innerHTML = domains.map((domain) => {
        const rows = grouped[domain].map((doc) => `
          <tr class="history-row">
            <td class="doc-id">${escapeHtml(doc.id)}</td>
            <td>
              <div class="font-medium text-[#1c1b1b]">${escapeHtml(doc.title || 'Untitled')}</div>
              <div class="text-[11px] text-ds-muted font-mono truncate max-w-md">${escapeHtml(doc.final_url || doc.url)}</div>
            </td>
            <td class="font-mono text-ds-muted whitespace-nowrap">${formatBytes(doc.size)}</td>
            <td class="font-mono text-ds-muted">v${escapeHtml(doc.revision_count || 1)}</td>
            <td>${doc.has_ai ? '<span class="ai-badge">AI</span>' : '<span class="text-ds-muted">—</span>'}</td>
            <td class="text-right">
              <button type="button" class="btn-ghost px-2.5 py-1 rounded-lg text-[11px]" onclick="closeChromaStoreModal(); previewCachedPage('${encodeURIComponent(doc.url).replace(/'/g, '%27')}')">Preview</button>
            </td>
          </tr>
        `).join('');
        return `
          <section class="mb-5">
            <h3 class="text-sm font-semibold text-[#1c1b1b] mb-2 flex items-center gap-2">
              <i class="fa-solid fa-globe text-ds-success" aria-hidden="true"></i>
              ${escapeHtml(domain)}
              <span class="text-[11px] font-mono text-ds-muted">${grouped[domain].length} docs</span>
            </h3>
            <div class="overflow-x-auto rounded-xl border border-ds history-table-wrap">
              <table class="modal-table w-full text-left text-xs">
                <thead class="sticky top-0">
                  <tr>
                    <th>Document ID</th>
                    <th>Maps to</th>
                    <th>Size</th>
                    <th>Rev</th>
                    <th>AI</th>
                    <th class="text-right">View</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[#e5e2e1]">${rows}</tbody>
              </table>
            </div>
          </section>
        `;
      }).join('');
    }

    function formatTimerSeconds(sec) {
      const m = Math.floor(sec / 60).toString().padStart(2, '0');
      const s = (sec % 60).toString().padStart(2, '0');
      return `${m}:${s}`;
    }

    function createLiveTimer(startTimeElemId, elapsedTimeElemId) {
      const startObj = new Date();
      const startTimeStr = startObj.toLocaleTimeString();
      const startElem = document.getElementById(startTimeElemId);
      const elapsedElem = document.getElementById(elapsedTimeElemId);
      if (startElem) startElem.innerText = startTimeStr;
      if (elapsedElem) elapsedElem.innerText = '00:00';

      let seconds = 0;
      const intervalId = setInterval(() => {
        seconds++;
        if (elapsedElem) elapsedElem.innerText = formatTimerSeconds(seconds);
      }, 1000);

      return {
        intervalId: intervalId,
        stop: () => {
          clearInterval(intervalId);
          return { startedAt: startTimeStr, totalSeconds: seconds, elapsedFormatted: formatTimerSeconds(seconds) };
        }
      };
    }

    // Global Toast Notification System (Stacked, Animated, Non-blocking)
    function showToast(message, type = 'info') {
      const container = document.getElementById('toastContainer');
      if (!container) return;

      const toast = document.createElement('div');
      toast.className = 'pointer-events-auto flex items-start gap-3 p-3.5 rounded-xl shadow-xl border text-xs leading-relaxed transition-all duration-300 transform translate-x-12 opacity-0 backdrop-blur-md bg-[#1c1b1b] border-black/20 text-white';

      let icon = 'fa-circle-info text-cyan-400';
      if (type === 'success') {
        icon = 'fa-circle-check text-emerald-400';
      } else if (type === 'warning') {
        icon = 'fa-triangle-exclamation text-amber-400';
      } else if (type === 'error') {
        icon = 'fa-circle-xmark text-red-400';
      } else if (type === 'info') {
        icon = 'fa-circle-info text-cyan-400';
      }

      toast.innerHTML = `
        <i class="fa-solid ${icon} mt-0.5 text-sm shrink-0"></i>
        <div class="flex-1 font-medium text-slate-100">${message}</div>
        <button type="button" class="text-slate-400 hover:text-white shrink-0 ml-1 p-0.5 rounded hover:bg-white/10" aria-label="Dismiss toast">
          <i class="fa-solid fa-xmark text-xs"></i>
        </button>
      `;

      toast.querySelector('button').onclick = () => {
        toast.classList.add('translate-x-12', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
      };

      container.appendChild(toast);

      requestAnimationFrame(() => {
        toast.classList.remove('translate-x-12', 'opacity-0');
      });

      setTimeout(() => {
        if (toast.parentElement) {
          toast.classList.add('translate-x-12', 'opacity-0');
          setTimeout(() => toast.remove(), 300);
        }
      }, 3500);
    }

    // RPA Playbook State & Helpers
    let crawlRpaSteps = [];
    let scrapeRpaSteps = [];
    let activeRpaTargetMode = 'crawl';
    let rpaPresetsCache = null;

    async function loadRpaPresets() {
      if (rpaPresetsCache) return rpaPresetsCache;
      try {
        const resp = await fetch('/api/v1/rpa/presets');
        if (resp.ok) {
          rpaPresetsCache = await resp.json();
          return rpaPresetsCache;
        }
      } catch (e) {
        console.error('Failed to load RPA presets', e);
      }
      return {};
    }

    async function toggleRpaPreset(mode, presetKey, isChecked) {
      const presets = await loadRpaPresets();
      const preset = presets[presetKey];
      if (!preset || !preset.steps) return;

      const stepsList = mode === 'crawl' ? crawlRpaSteps : scrapeRpaSteps;
      if (isChecked) {
        preset.steps.forEach(s => {
          const exists = stepsList.some(existing => existing.selector === s.selector && existing.action === s.action);
          if (!exists) stepsList.push({...s});
        });
      } else {
        const presetSelectors = new Set(preset.steps.map(s => s.selector));
        const filtered = stepsList.filter(s => !presetSelectors.has(s.selector));
        if (mode === 'crawl') crawlRpaSteps = filtered;
        else scrapeRpaSteps = filtered;
      }
      renderRpaStepsList(mode);
    }

    function renderRpaStepsList(mode) {
      const container = document.getElementById(mode === 'crawl' ? 'crawlRpaStepsList' : 'scrapeRpaStepsList');
      const badge = document.getElementById(mode === 'crawl' ? 'crawlRpaCountBadge' : 'scrapeRpaCountBadge');
      const steps = mode === 'crawl' ? crawlRpaSteps : scrapeRpaSteps;
      if (!container) return;

      if (badge) {
        const total = steps.length;
        badge.innerText = total > 0 ? `${total} action(s)` : 'Auto-modals on';
      }

      if (steps.length === 0) {
        container.innerHTML = `
          <div class="text-[11px] text-ds-muted italic p-2 bg-white rounded border border-dashed border-ds text-center">
            No custom steps added. Enable recipes above or generate with AI.
          </div>`;
        return;
      }

      let html = '';
      steps.forEach((s, idx) => {
        const actionIcons = {
          'click': '🖱️ click',
          'fill': '✍️ fill',
          'select': '📋 select',
          'wait_for': '⏳ wait',
          'press_key': '⌨️ key',
          'hover': '👆 hover',
          'scroll': '📜 scroll',
          'sleep': '💤 sleep'
        };
        const iconLabel = actionIcons[s.action] || s.action;
        const targetDesc = s.selector || s.value || s.action;
        const optBadge = s.optional ? '<span class="text-[9px] px-1 bg-ds-surface-low text-ds-muted rounded border border-ds">opt</span>' : '';
        html += `
          <div class="flex items-center justify-between gap-2 p-2 bg-white border border-ds rounded-lg text-[11px] shadow-xs">
            <div class="flex items-center gap-1.5 truncate">
              <span class="font-bold text-purple-700 font-mono text-[11px] uppercase">${idx + 1}. ${iconLabel}</span>
              <span class="text-[#1c1b1b] truncate max-w-[160px]" title="${targetDesc}">${targetDesc}</span>
              ${optBadge}
            </div>
            <button type="button" onclick="removeRpaStep('${mode}', ${idx})" class="text-ds-muted hover:text-red-600 p-0.5 transition" title="Remove step">
              <i class="fa-solid fa-xmark text-xs"></i>
            </button>
          </div>
        `;
      });
      container.innerHTML = html;
    }

    function removeRpaStep(mode, idx) {
      if (mode === 'crawl') {
        crawlRpaSteps.splice(idx, 1);
      } else {
        scrapeRpaSteps.splice(idx, 1);
      }
      renderRpaStepsList(mode);
    }

    function showAddCustomRpaStep(mode) {
      activeRpaTargetMode = mode;
      document.getElementById('rpaStepSelector').value = '';
      document.getElementById('rpaStepValue').value = '';
      document.getElementById('rpaStepOptional').checked = true;
      document.getElementById('customRpaStepModal').classList.remove('hidden');
      syncBodyScrollLock();
    }

    function closeCustomRpaStepModal() {
      document.getElementById('customRpaStepModal').classList.add('hidden');
      syncBodyScrollLock();
    }

    function commitCustomRpaStep() {
      const action = document.getElementById('rpaStepAction').value;
      const selector = document.getElementById('rpaStepSelector').value.trim();
      const value = document.getElementById('rpaStepValue').value.trim();
      const optional = document.getElementById('rpaStepOptional').checked;

      const step = {
        action: action,
        selector: selector || null,
        value: value || null,
        optional: optional,
        timeout_ms: 3500,
        wait_after_ms: 300
      };

      if (activeRpaTargetMode === 'crawl') {
        crawlRpaSteps.push(step);
      } else {
        scrapeRpaSteps.push(step);
      }
      renderRpaStepsList(activeRpaTargetMode);
      closeCustomRpaStepModal();
    }

    async function generateAiRpaSteps(mode) {
      const input = document.getElementById(mode === 'crawl' ? 'crawlRpaAiPrompt' : 'scrapeRpaAiPrompt');
      const urlInput = document.getElementById(mode === 'crawl' ? 'targetUrl' : 'scrapeUrl');
      const instruction = input.value.trim();
      if (!instruction) return alert('Please enter an action instruction (e.g. "Click the pricing tab and select annual")');

      const originalPlaceholder = input.placeholder;
      input.disabled = true;
      input.value = 'Thinking & generating RPA steps with DeepSeek...';

      try {
        const resp = await fetch('/api/v1/rpa/generate', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            instruction: instruction,
            url: urlInput ? urlInput.value.trim() : null
          })
        });

        if (!resp.ok) {
          const err = await resp.json();
          throw new Error(err.detail || 'Failed to generate steps');
        }

        const data = await resp.json();
        const steps = data.steps || [];
        if (steps.length === 0) {
          alert('No steps generated for this instruction.');
        } else {
          const targetArray = mode === 'crawl' ? crawlRpaSteps : scrapeRpaSteps;
          steps.forEach(s => targetArray.push(s));
          renderRpaStepsList(mode);
          alert(`Successfully generated ${steps.length} RPA step(s)!`);
        }
      } catch (err) {
        alert('RPA generation error: ' + err.message);
      } finally {
        input.disabled = false;
        input.value = '';
        input.placeholder = originalPlaceholder;
      }
    }

    function switchMode(mode) {
      currentMode = mode;
      const tabCrawl = document.getElementById('tabCrawlBtn');
      const tabScrape = document.getElementById('tabScrapeBtn');
      const tabHistory = document.getElementById('tabHistoryBtn');
      const crawlingSection = document.getElementById('crawlingSection');
      const historySection = document.getElementById('historySection');
      const crawlerForm = document.getElementById('crawlerForm');
      const scraperForm = document.getElementById('scraperForm');

      const inactiveClass = 'px-4 py-1.5 rounded text-xs font-mono text-ds-muted hover:text-ds-accent transition-all flex items-center gap-2';
      const crawlActive = 'hud-tab-active px-4 py-1.5 text-xs font-mono flex items-center gap-2';
      const scrapeActive = 'hud-tab-active px-4 py-1.5 text-xs font-mono flex items-center gap-2';
      const historyActive = 'hud-tab-history px-4 py-1.5 text-xs font-mono flex items-center gap-2';
      const guardrails = document.getElementById('guardrailsPanel');
      const liveStream = document.getElementById('liveStreamPanel');
      const splitGrid = document.getElementById('ingestSplitGrid');
      const splitBar = document.getElementById('splitStatusBar');

      tabCrawl.className = inactiveClass;
      tabScrape.className = inactiveClass;
      tabHistory.className = inactiveClass;
      tabCrawl.setAttribute('role', 'tab');
      tabScrape.setAttribute('role', 'tab');
      tabHistory.setAttribute('role', 'tab');
      tabCrawl.setAttribute('aria-selected', 'false');
      tabScrape.setAttribute('aria-selected', 'false');
      tabHistory.setAttribute('aria-selected', 'false');
      tabCrawl.setAttribute('aria-controls', 'crawlingSection');
      tabScrape.setAttribute('aria-controls', 'crawlingSection');
      tabHistory.setAttribute('aria-controls', 'historySection');

      if (mode === 'crawl') {
        tabCrawl.className = crawlActive;
        tabCrawl.setAttribute('aria-selected', 'true');
        crawlingSection.classList.remove('hidden');
        historySection.classList.add('hidden');
        crawlerForm.classList.remove('hidden');
        scraperForm.classList.add('hidden');
        if (guardrails) guardrails.classList.remove('hidden');
        if (liveStream) liveStream.classList.remove('hidden');
        if (splitGrid) { splitGrid.classList.add('xl:grid-cols-3'); splitGrid.classList.remove('xl:grid-cols-1'); }
        if (splitBar) splitBar.classList.remove('hidden');
      } else if (mode === 'scrape') {
        tabScrape.className = scrapeActive;
        tabScrape.setAttribute('aria-selected', 'true');
        crawlingSection.classList.remove('hidden');
        historySection.classList.add('hidden');
        scraperForm.classList.remove('hidden');
        crawlerForm.classList.add('hidden');
        if (guardrails) guardrails.classList.add('hidden');
        if (liveStream) liveStream.classList.add('hidden');
        if (splitGrid) { splitGrid.classList.remove('xl:grid-cols-3'); splitGrid.classList.add('xl:grid-cols-1'); }
        if (splitBar) splitBar.classList.add('hidden');
      } else if (mode === 'history') {
        tabHistory.className = historyActive;
        tabHistory.setAttribute('aria-selected', 'true');
        crawlingSection.classList.add('hidden');
        historySection.classList.remove('hidden');
        loadHistory();
      }
    }

    const PLAYBOOK_DESCRIPTIONS = {
      rag_ingest: 'Optimized for API docs, technical references, code syntax preservation. Sitemap discovery, semantic boilerplate strip, Chroma vector ingest.',
      smoke_test: 'Fast 3-page smoke test. HTTP engine, minimal depth, ideal for connectivity checks.',
      competitor_intel: 'Company profile extraction with AI. Auto engine, 8 pages, DeepSeek reasoning.',
      ecommerce_catalog: 'Product schema extraction across catalog pages. Nemotron 3.5 Lightning.',
      dynamic_spa: 'Headless Chromium for JavaScript SPAs and React apps. Full DOM rendering.',
      live_growth_audit: 'Cache-off live refresh to track revision deltas and content growth over time.',
      polite_stealth: 'Ultra-polite 4s delay crawl for anti-bot protected sites. Strict robots adherence.',
    };

    let liveStreamSeen = new Set();

    function updatePlaybookDesc(key) {
      const desc = document.getElementById('playbookDesc');
      if (desc && PLAYBOOK_DESCRIPTIONS[key]) desc.innerText = PLAYBOOK_DESCRIPTIONS[key];
      const sel = document.getElementById('playbookSelect');
      if (sel && key) sel.value = key;
    }

    function syncSlider(field, value) {
      const input = document.getElementById(field);
      if (input) input.value = value;
      if (field === 'delay') {
        const v = parseFloat(value).toFixed(1);
        const lbl = document.getElementById('delaySliderVal');
        const rng = document.getElementById('delaySlider');
        if (lbl) lbl.innerText = v + 's';
        if (rng) rng.value = value;
      } else if (field === 'maxDepth') {
        const lbl = document.getElementById('depthSliderVal');
        const rng = document.getElementById('depthSlider');
        if (lbl) lbl.innerText = value;
        if (rng) rng.value = value;
      } else if (field === 'maxPages') {
        const lbl = document.getElementById('pagesSliderVal');
        const rng = document.getElementById('pagesSlider');
        if (lbl) lbl.innerText = value;
        if (rng) rng.value = value;
      }
      updateEngineQueueLabel();
    }

    function syncSlidersFromInputs() {
      syncSlider('delay', document.getElementById('delay').value);
      syncSlider('maxDepth', document.getElementById('maxDepth').value);
      syncSlider('maxPages', document.getElementById('maxPages').value);
    }

    function syncGuardrail(id, checked) {
      const el = document.getElementById(id);
      if (el) el.checked = checked;
      updateEthicsStatus();
    }

    function syncGuardrailsFromInputs() {
      const r = document.getElementById('respectRobots');
      const s = document.getElementById('useSitemap');
      const c = document.getElementById('crawlUseCache');
      const a = document.getElementById('crawlEnableAi');
      const strat = document.getElementById('strategy');
      if (document.getElementById('guardRespectRobots') && r) document.getElementById('guardRespectRobots').checked = r.checked;
      if (document.getElementById('guardSitemap') && s) document.getElementById('guardSitemap').checked = s.checked;
      if (document.getElementById('guardCache') && c) document.getElementById('guardCache').checked = c.checked;
      if (document.getElementById('guardAi') && a) document.getElementById('guardAi').checked = a.checked;
      if (document.getElementById('guardJsRender') && strat) {
        document.getElementById('guardJsRender').checked = strat.value === 'browser' || strat.value === 'auto';
      }
      updateEthicsStatus();
    }

    function syncJsRender(checked) {
      const strat = document.getElementById('strategy');
      if (!strat) return;
      strat.value = checked ? 'auto' : 'http';
      updateEngineDesc(strat.value);
    }

    function appendLiveStream(msg, type = 'ok') {
      const stream = document.getElementById('liveCrawlStream');
      if (!stream) return;
      const line = document.createElement('div');
      line.className = 'stream-' + type;
      line.innerHTML = '&gt; ' + msg;
      stream.appendChild(line);
      while (stream.children.length > 80) stream.removeChild(stream.firstChild);
      stream.scrollTop = stream.scrollHeight;
    }

    function clearLiveStream() {
      const stream = document.getElementById('liveCrawlStream');
      if (stream) {
        stream.innerHTML = '<div class="stream-dim">&gt; stream initialized...</div>';
      }
      liveStreamSeen.clear();
    }

    function estimateChunks(results) {
      if (!results) return 0;
      let total = 0;
      results.forEach(r => {
        const size = r.cleaned_markdown_size || (r.markdown || '').length || 0;
        total += Math.max(1, Math.ceil(size / 900));
      });
      return total;
    }

    function updateEmbeddingPanel(results, state) {
      const panel = document.getElementById('embeddingPanel');
      const count = document.getElementById('embeddingChunkCount');
      const status = document.getElementById('embeddingStatus');
      const pulse = document.getElementById('streamPulse');
      if (!panel) return;
      if (state) {
        panel.classList.remove('hidden');
        if (pulse) pulse.classList.remove('hidden');
        if (count) count.innerText = estimateChunks(results);
        if (status) {
          status.innerText = state === 'running' ? 'EMBEDDING ACTIVE' : 'EMBEDDING COMPLETE';
          status.classList.toggle('embedding-active', state === 'running');
        }
      } else {
        panel.classList.add('hidden');
        if (pulse) pulse.classList.add('hidden');
      }
    }

    function updateEngineQueueLabel(crawled, total) {
      const label = document.getElementById('engineQueueLabel');
      if (!label) return;
      const maxP = parseInt(document.getElementById('maxPages').value) || 0;
      const q = crawled !== undefined ? crawled : 0;
      const t = total !== undefined && total > 0 ? total : maxP;
      label.innerText = 'Ethic — Queue: ' + q + '/' + t + ' pages';
    }

    function updateEthicsStatus(violation) {
      const el = document.getElementById('ethicsStatus');
      if (!el) return;
      const robotsOn = document.getElementById('respectRobots')?.checked;
      if (violation) {
        el.innerHTML = 'Ethics Check: <span class="text-[#ba1a1a]">Violation</span>';
      } else if (robotsOn) {
        el.innerHTML = 'Ethics Check: <span class="text-ds-accent">Robots.txt OK (100% Compliant)</span>';
      } else {
        el.innerHTML = 'Ethics Check: <span class="text-[#bd0042]">Robots bypassed</span>';
      }
    }

    function streamResultsToTerminal(results) {
      if (!results) return;
      results.forEach(r => {
        const key = r.final_url || r.url;
        if (!key || liveStreamSeen.has(key)) return;
        liveStreamSeen.add(key);
        const ok = r.status_code === 200;
        const title = (r.title || key).substring(0, 72);
        const size = ((r.cleaned_markdown_size || 0) / 1024).toFixed(1);
        appendLiveStream(
          ok
            ? '<span class="text-ds-accent">[OK]</span> ' + title + ' <span class="stream-dim">(' + size + ' KB md)</span>'
            : '<span class="text-[#ba1a1a]">[ERR ' + r.status_code + ']</span> ' + key,
          ok ? 'ok' : 'err'
        );
      });
    }

    const CRAWL_PRESETS = {
      smoke_test: {
        name: 'Quick Smoke Test',
        pages: 3,
        depth: 1,
        delay: 1.5,
        strategy: 'http',
        sitemap: false,
        cache: true,
        ai: false,
        summary: '3 pgs • Depth 1 • Fast HTTP • AI Off'
      },
      competitor_intel: {
        name: 'Competitor & Market Intel',
        pages: 8,
        depth: 2,
        delay: 1.5,
        strategy: 'auto',
        sitemap: false,
        cache: true,
        ai: true,
        schema: 'company_profile',
        model: 'deepseek-ai/deepseek-v4.1-flash',
        summary: '8 pgs • Auto Engine • DeepSeek-v4.1 Company Profile'
      },
      rag_ingest: {
        name: 'RAG Knowledge Ingest',
        pages: 35,
        depth: 3,
        delay: 1.0,
        strategy: 'http',
        sitemap: true,
        cache: false,
        ai: false,
        summary: '35 pgs • Sitemap ON • Fast HTTP • Fresh Ingest'
      },
      ecommerce_catalog: {
        name: 'E-Commerce Catalog',
        pages: 20,
        depth: 2,
        delay: 2.0,
        strategy: 'auto',
        sitemap: false,
        cache: true,
        ai: true,
        schema: 'product',
        model: 'nvidia/nemotron-3.5-lightning-30b-a3b',
        summary: '20 pgs • Product Schema • Nemotron 3.5'
      },
      dynamic_spa: {
        name: 'Dynamic SPA / React App',
        pages: 10,
        depth: 2,
        delay: 2.5,
        strategy: 'browser',
        sitemap: false,
        cache: true,
        ai: true,
        schema: 'article',
        model: 'meta/llama-3.2-11b-vision-instruct',
        summary: '10 pgs • Headless Chromium • 2.5s Delay'
      },
      live_growth_audit: {
        name: 'Live Growth Audit',
        pages: 12,
        depth: 2,
        delay: 1.5,
        strategy: 'auto',
        sitemap: false,
        cache: false,
        ai: false,
        summary: '12 pgs • Cache OFF (forces revision & delta tracking)'
      },
      polite_stealth: {
        name: 'Ultra-Polite Research',
        pages: 15,
        depth: 2,
        delay: 4.0,
        strategy: 'auto',
        sitemap: false,
        cache: true,
        ai: false,
        respectRobots: true,
        summary: '15 pgs • 4.0s Delay • Strict Robots'
      }
    };

    const SCRAPE_PRESETS = {
      instant_markdown: {
        name: 'Instant Clean Markdown',
        strategy: 'http',
        cache: true,
        ai: false,
        summary: 'Fast HTTP • Cache ON • AI Off (1ms export)'
      },
      company_profile: {
        name: 'Company Profile & Value Prop',
        strategy: 'auto',
        cache: true,
        ai: true,
        schema: 'company_profile',
        model: 'deepseek-ai/deepseek-v4.1-flash',
        summary: 'Auto Engine • DeepSeek-v4.1 Company Profile'
      },
      product_details: {
        name: 'E-Commerce Product Details',
        strategy: 'auto',
        cache: true,
        ai: true,
        schema: 'product',
        model: 'nvidia/nemotron-3.5-lightning-30b-a3b',
        summary: 'Auto Engine • Nemotron 3.5 Product Specs'
      },
      clean_article: {
        name: 'Clean Article Reading View',
        strategy: 'http',
        cache: true,
        ai: true,
        schema: 'article',
        model: 'z-ai/glm-5.3-flash',
        summary: 'Fast HTTP • GLM-5.3 Flash Article Extract'
      },
      dynamic_spa: {
        name: 'Headless Chromium SPA',
        strategy: 'browser',
        cache: true,
        ai: false,
        summary: 'Chromium Browser • Full DOM Rendering'
      }
    };

    function applyCrawlPreset(key) {
      const p = CRAWL_PRESETS[key];
      if (!p) return;

      if (p.pages !== undefined) document.getElementById('maxPages').value = p.pages;
      if (p.depth !== undefined) document.getElementById('maxDepth').value = p.depth;
      if (p.delay !== undefined) document.getElementById('delay').value = p.delay;
      if (p.strategy !== undefined) {
        document.getElementById('strategy').value = p.strategy;
        updateEngineDesc(p.strategy);
      }
      if (p.sitemap !== undefined) document.getElementById('useSitemap').checked = p.sitemap;
      if (p.cache !== undefined) document.getElementById('crawlUseCache').checked = p.cache;
      if (p.respectRobots !== undefined) document.getElementById('respectRobots').checked = p.respectRobots;

      const aiCheckbox = document.getElementById('crawlEnableAi');
      if (aiCheckbox) {
        aiCheckbox.checked = !!p.ai;
        toggleCrawlAiInputs();
      }
      if (p.schema && document.getElementById('crawlAiSchema')) {
        document.getElementById('crawlAiSchema').value = p.schema;
      }
      if (p.model && document.getElementById('crawlAiModel')) {
        document.getElementById('crawlAiModel').value = p.model;
      }

      syncSlidersFromInputs();
      syncGuardrailsFromInputs();
      updatePlaybookDesc(key);
      showPresetToast('crawl', `Applied: ${p.name} (${p.summary})`);
    }

    function applyScrapePreset(key) {
      const p = SCRAPE_PRESETS[key];
      if (!p) return;

      if (p.strategy !== undefined) document.getElementById('scrapeStrategy').value = p.strategy;
      if (p.cache !== undefined) document.getElementById('scrapeUseCache').checked = p.cache;

      const aiCheckbox = document.getElementById('enableAiExtraction');
      if (aiCheckbox) {
        aiCheckbox.checked = !!p.ai;
        toggleAiInputs();
      }
      if (p.schema && document.getElementById('aiSchema')) {
        document.getElementById('aiSchema').value = p.schema;
      }
      if (p.model && document.getElementById('scrapeAiModel')) {
        document.getElementById('scrapeAiModel').value = p.model;
      }

      showPresetToast('scrape', `Applied: ${p.name} (${p.summary})`);
    }

    function showPresetToast(mode, message) {
      const ind = document.getElementById(mode === 'crawl' ? 'crawlPresetIndicator' : 'scrapePresetIndicator');
      const text = document.getElementById(mode === 'crawl' ? 'crawlPresetIndicatorText' : 'scrapePresetIndicatorText');
      if (ind && text) {
        text.innerText = message;
        ind.classList.remove('hidden');
        setTimeout(() => ind.classList.add('hidden'), 4500);
      }
    }

    function saveCurrentCrawlAsCustomPreset() {
      const name = prompt('Enter a name for this custom preset:', 'My Custom Preset');
      if (!name || !name.trim()) return;

      const preset = {
        id: 'cust_' + Date.now(),
        name: name.trim(),
        pages: parseInt(document.getElementById('maxPages').value) || 10,
        depth: parseInt(document.getElementById('maxDepth').value) || 2,
        delay: parseFloat(document.getElementById('delay').value) || 2.0,
        strategy: document.getElementById('strategy').value,
        sitemap: document.getElementById('useSitemap').checked,
        cache: document.getElementById('crawlUseCache').checked,
        ai: document.getElementById('crawlEnableAi') ? document.getElementById('crawlEnableAi').checked : false,
        schema: document.getElementById('crawlAiSchema') ? document.getElementById('crawlAiSchema').value : 'article',
        model: document.getElementById('crawlAiModel') ? document.getElementById('crawlAiModel').value : 'deepseek-ai/deepseek-v4.1-flash',
      };

      try {
        const saved = JSON.parse(localStorage.getItem('crawler_custom_presets') || '[]');
        saved.push(preset);
        localStorage.setItem('crawler_custom_presets', JSON.stringify(saved));
        loadCustomPresets();
        showPresetToast('crawl', `Saved custom preset "${preset.name}"!`);
      } catch (e) {
        alert('Failed saving custom preset: ' + e.message);
      }
    }

    function loadCustomPresets() {
      const container = document.getElementById('crawlCustomPresetsContainer');
      const list = document.getElementById('crawlCustomPresetsList');
      if (!container || !list) return;

      try {
        const saved = JSON.parse(localStorage.getItem('crawler_custom_presets') || '[]');
        if (saved.length === 0) {
          container.classList.add('hidden');
          return;
        }

        container.classList.remove('hidden');
        let html = '';
        saved.forEach((p, idx) => {
          html += `
            <div class="inline-flex items-center gap-1 bg-slate-800 hover:bg-slate-750 px-2 py-0.5 rounded-md border border-slate-700 text-slate-300">
              <button type="button" onclick="applyCustomCrawlPreset(${idx})" class="hover:text-white transition font-medium">
                ⭐ ${p.name}
              </button>
              <button type="button" onclick="deleteCustomPreset(${idx})" title="Delete preset" class="text-slate-500 hover:text-red-400 text-[11px] ml-1">
                &times;
              </button>
            </div>
          `;
        });
        list.innerHTML = html;
      } catch (e) {
        console.error(e);
      }
    }

    function applyCustomCrawlPreset(idx) {
      try {
        const saved = JSON.parse(localStorage.getItem('crawler_custom_presets') || '[]');
        const p = saved[idx];
        if (!p) return;

        document.getElementById('maxPages').value = p.pages;
        document.getElementById('maxDepth').value = p.depth;
        document.getElementById('delay').value = p.delay;
        document.getElementById('strategy').value = p.strategy;
        updateEngineDesc(p.strategy);
        document.getElementById('useSitemap').checked = p.sitemap;
        document.getElementById('crawlUseCache').checked = p.cache;

        const aiCheckbox = document.getElementById('crawlEnableAi');
        if (aiCheckbox) {
          aiCheckbox.checked = !!p.ai;
          toggleCrawlAiInputs();
        }
        if (p.schema && document.getElementById('crawlAiSchema')) {
          document.getElementById('crawlAiSchema').value = p.schema;
        }
        if (p.model && document.getElementById('crawlAiModel')) {
          document.getElementById('crawlAiModel').value = p.model;
        }

        showPresetToast('crawl', `Applied Custom: ${p.name}`);
      } catch (e) {
        console.error(e);
      }
    }

    function deleteCustomPreset(idx) {
      try {
        const saved = JSON.parse(localStorage.getItem('crawler_custom_presets') || '[]');
        saved.splice(idx, 1);
        localStorage.setItem('crawler_custom_presets', JSON.stringify(saved));
        loadCustomPresets();
      } catch (e) {
        console.error(e);
      }
    }

    function applyPreset(pages, depth, delay, sitemap) {
      document.getElementById('maxPages').value = pages;
      document.getElementById('maxDepth').value = depth;
      document.getElementById('delay').value = delay;
      document.getElementById('useSitemap').checked = sitemap;
    }

    function updateEngineDesc(val) {
      const hint = document.getElementById('engineHint');
      if (!hint) return;
      if (val === 'auto') {
        hint.innerText = 'Smart hybrid: HTTP with JS escalation';
      } else if (val === 'http') {
        hint.innerText = 'Fast async HTTP (for static HTML/blogs/docs)';
      } else if (val === 'browser') {
        hint.innerText = 'Headless Chromium browser (for SPAs/React/Vue)';
      }
    }

    function toggleAiInputs() {
      const enabled = document.getElementById('enableAiExtraction').checked;
      const sec = document.getElementById('aiConfigSection');
      if (enabled) sec.classList.remove('hidden');
      else sec.classList.add('hidden');
    }

    function toggleCrawlAiInputs() {
      const enabled = document.getElementById('crawlEnableAi').checked;
      const sec = document.getElementById('crawlAiConfigSection');
      if (enabled) sec.classList.remove('hidden');
      else sec.classList.add('hidden');
    }

    async function startCrawl() {
      const url = document.getElementById('targetUrl').value.trim();
      if (!url) return alert('Please specify a URL');

      const maxPages = parseInt(document.getElementById('maxPages').value) || 5;
      const maxDepth = parseInt(document.getElementById('maxDepth').value) || 2;
      const delay = parseFloat(document.getElementById('delay').value) || 2.0;
      const strategy = document.getElementById('strategy').value;
      const respectRobots = document.getElementById('respectRobots').checked;
      const useSitemap = document.getElementById('useSitemap').checked;
      const useCache = document.getElementById('crawlUseCache').checked;
      const extractAi = document.getElementById('crawlEnableAi') ? document.getElementById('crawlEnableAi').checked : false;
      const aiSchema = document.getElementById('crawlAiSchema') ? document.getElementById('crawlAiSchema').value : 'article';
      const aiPrompt = document.getElementById('crawlAiPrompt') ? document.getElementById('crawlAiPrompt').value.trim() : '';
      const aiModel = document.getElementById('crawlAiModel') ? document.getElementById('crawlAiModel').value : null;
      const dismissCookies = document.getElementById('crawlRpaDismissCookies') ? document.getElementById('crawlRpaDismissCookies').checked : true;

      if (statusTimer) {
        statusTimer.stop();
        statusTimer = null;
      }
      setStatus('running', 'Initiating crawl job...');
      clearLiveStream();
      appendLiveStream('launching ethical ingest for <span class="text-ds-accent">' + url + '</span>', 'ok');
      appendLiveStream('guardrails: delay=' + delay + 's depth=' + maxDepth + ' limit=' + maxPages, 'dim');
      updateEmbeddingPanel([], 'running');
      const tbody = document.getElementById('resultsTableBody');
      tbody.innerHTML = '<tr><td colspan="6" class="p-4 text-center text-ds-muted font-mono text-[11px]">&gt; crawling...</td></tr>';
      document.getElementById('exportToolbar').classList.add('hidden');

      try {
        const resp = await fetch('/api/v1/crawl', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            url: url,
            max_pages: maxPages,
            max_depth: maxDepth,
            delay: delay,
            strategy: strategy,
            respect_robots: respectRobots,
            use_sitemap: useSitemap,
            use_cache: useCache,
            extract_ai: extractAi,
            ai_schema: aiSchema,
            ai_prompt: aiPrompt || null,
            ai_model: aiModel || null,
            rpa_steps: crawlRpaSteps,
            auto_dismiss_modals: dismissCookies
          })
        });
        const data = await resp.json();
        activeJobId = data.job_id;
        pollJob(data.job_id);
      } catch (err) {
        setStatus('failed', 'Error launching crawl: ' + err);
      }
    }

    function pollJob(jobId) {
      if (activePoll) clearInterval(activePoll);
      activePoll = setInterval(async () => {
        try {
          const resp = await fetch('/api/v1/jobs/' + jobId);
          if (!resp.ok) {
            clearInterval(activePoll);
            return;
          }
          const job = await resp.json();

          const totalLabel = job.pages_discovered > 0 ? ` of ~${job.pages_discovered}` : '';
          document.getElementById('counterBadge').innerText = job.pages_crawled + totalLabel + ' pages';
          const queueTotal = job.pages_discovered > 0 ? job.pages_discovered : parseInt(document.getElementById('maxPages').value);
          updateEngineQueueLabel(job.pages_crawled, queueTotal);

          if (job.status === 'running') {
            const activityText = job.current_activity ? ` — ${job.current_activity}` : '';
            setStatus('running', `Ingesting ${job.pages_crawled}${totalLabel} pages${activityText}`);
            if (job.current_activity && !liveStreamSeen.has('act:' + job.current_activity)) {
              liveStreamSeen.add('act:' + job.current_activity);
              appendLiveStream(job.current_activity, 'dim');
            }
            if (job.results && job.results.length > 0) {
              streamResultsToTerminal(job.results);
              renderResults(job.results);
              updateEmbeddingPanel(job.results, 'running');
            }
          } else if (job.status === 'completed') {
            clearInterval(activePoll);
            setStatus('completed', `Ingest complete: ${job.pages_crawled} pages`);
            streamResultsToTerminal(job.results);
            renderResults(job.results);
            updateEmbeddingPanel(job.results, 'done');
            appendLiveStream('ingest complete — ' + estimateChunks(job.results) + ' vector chunks indexed', 'ok');
            document.getElementById('exportToolbar').classList.remove('hidden');
            loadHistory();
          } else if (job.status === 'failed') {
            clearInterval(activePoll);
            setStatus('failed', 'Crawl failed: ' + (job.errors.join(', ') || 'Unknown error'));
            appendLiveStream('FAILED: ' + (job.errors.join(', ') || 'unknown error'), 'err');
            updateEmbeddingPanel(job.results || [], 'done');
            if (job.results && job.results.length > 0) {
              renderResults(job.results);
            }
          }
        } catch (e) {
          console.error(e);
        }
      }, 1000);
    }

    async function startScrape() {
      const url = document.getElementById('scrapeUrl').value.trim();
      if (!url) return alert('Please enter a target URL');

      const strategy = document.getElementById('scrapeStrategy').value;
      const respectRobots = document.getElementById('scrapeRespectRobots').checked;
      const useCache = document.getElementById('scrapeUseCache').checked;
      const extractAi = document.getElementById('enableAiExtraction').checked;
      const schema = document.getElementById('aiSchema').value;
      const prompt = document.getElementById('aiPrompt').value.trim();
      const aiModel = document.getElementById('scrapeAiModel') ? document.getElementById('scrapeAiModel').value : null;
      const dismissCookies = document.getElementById('scrapeRpaDismissCookies') ? document.getElementById('scrapeRpaDismissCookies').checked : true;

      if (statusTimer) {
        statusTimer.stop();
        statusTimer = null;
      }
      setStatus('running', `Scraping page: ${url}...`);
      const tbody = document.getElementById('resultsTableBody');
      tbody.innerHTML = '<tr><td colspan="6" class="p-4 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Scraping and processing markdown...</td></tr>';
      document.getElementById('exportToolbar').classList.add('hidden');
      currentAiData = null;

      try {
        const resp = await fetch('/api/v1/scrape', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            url: url,
            strategy: strategy,
            respect_robots: respectRobots,
            use_cache: useCache,
            extract_ai: extractAi,
            schema_type: schema,
            prompt: prompt || null,
            model: aiModel || null,
            rpa_steps: scrapeRpaSteps,
            auto_dismiss_modals: dismissCookies,
            capture_screenshot: document.getElementById('scrapeCaptureScreenshot') ? document.getElementById('scrapeCaptureScreenshot').checked : false
          })
        });

        if (!resp.ok) {
          const errData = await resp.json();
          throw new Error(errData.detail || 'Scraping failed');
        }

        const data = await resp.json();
        setStatus('completed', `Successfully scraped: ${data.result.title || url}`);
        document.getElementById('counterBadge').innerText = '1 page';
        if (data.ai_extraction) {
          currentAiData = data.ai_extraction.data;
          data.result.ai_data = data.ai_extraction.data;
        } else {
          currentAiData = null;
        }
        renderResults([data.result]);
        document.getElementById('exportToolbar').classList.remove('hidden');
        loadHistory(); // refresh vector store badge
      } catch (err) {
        setStatus('failed', 'Scrape failed: ' + err.message);
        tbody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-red-400">${err.message}</td></tr>`;
      }
    }

    function setStatus(state, msg) {
      const ind = document.getElementById('statusIndicator');
      const text = document.getElementById('statusText');
      const timerBadge = document.getElementById('statusTimerBadge');
      const shimmer = document.getElementById('statusShimmerBar');
      text.innerText = msg;
      if (shimmer) shimmer.classList.toggle('hidden', state !== 'running');
      if (state === 'running') {
        ind.className = 'w-2 h-2 rounded-full status-dot-active shrink-0 transition-all';
        if (!statusTimer) {
          if (timerBadge) {
            timerBadge.classList.remove('hidden');
            timerBadge.classList.add('flex');
          }
          statusTimer = createLiveTimer('statusStartTime', 'statusElapsedTime');
        }
      } else if (state === 'completed') {
        ind.className = 'w-2 h-2 rounded-full bg-ds-lime shrink-0 transition-all';
        if (statusTimer) {
          statusTimer.stop();
          statusTimer = null;
        }
      } else if (state === 'failed') {
        ind.className = 'w-2 h-2 rounded-full bg-[#ba1a1a] shrink-0 transition-all';
        if (statusTimer) {
          statusTimer.stop();
          statusTimer = null;
        }
      } else {
        ind.className = 'w-2 h-2 rounded-full bg-[#00677f] shrink-0 transition-all';
        if (statusTimer) {
          statusTimer.stop();
          statusTimer = null;
        }
        if (timerBadge) {
          timerBadge.classList.add('hidden');
          timerBadge.classList.remove('flex');
        }
      }
    }

    function renderResults(results) {
      const tbody = document.getElementById('resultsTableBody');
      if (!results || results.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="p-6 text-center text-ds-muted">No pages found.</td></tr>';
        return;
      }

      window.crawledResults = results;
      let html = '';
      results.forEach((r, idx) => {
        const isOk = r.status_code === 200;
        const hasAi = r.ai_data && Object.keys(r.ai_data).length > 0;
        let aiBadge = '';
        if (hasAi) {
          const modelShort = r.ai_model_used ? r.ai_model_used.split('/').pop() : 'AI';
          aiBadge = `<span class="ai-badge ml-1" title="Extracted via ${r.ai_model_used || 'AI'}">${modelShort}</span>`;
        }

        const netCount = (r.network_calls || []).length;
        const netBadge = netCount > 0 ? `<span class="chip-export ml-1" title="${netCount} API call(s)">${netCount} APIs</span>` : '';
        const rpaCount = (r.rpa_logs || []).length;
        const rpaBadge = rpaCount > 0 ? `<span class="chip-export ml-1" title="${rpaCount} RPA step(s)">RPA</span>` : '';

        html += `
          <tr class="history-row cursor-pointer">
            <td class="p-3">${statusPillHtml(r.status_code)}</td>
            <td class="p-3">
              <div class="font-medium text-[#1c1b1b] truncate max-w-md lg:max-w-xl flex items-center flex-wrap gap-1">${r.title || r.url} ${aiBadge} ${netBadge} ${rpaBadge}</div>
              <div class="text-ds-muted text-xs truncate max-w-md lg:max-w-xl font-mono mt-0.5">${r.final_url}</div>
            </td>
            <td class="p-3 font-mono whitespace-nowrap text-ds-muted">${(r.cleaned_markdown_size || 0).toLocaleString()} B</td>
            <td class="p-3 font-mono whitespace-nowrap text-ds-muted">${r.strategy_used}</td>
            <td class="p-3 font-mono whitespace-nowrap text-ds-muted">${(r.elapsed_seconds || 0).toFixed(2)}s</td>
            <td class="p-3 text-right whitespace-nowrap">
              <button onclick="showPreview(${idx})" class="btn-ghost px-3 py-1.5 rounded-lg text-xs inline-flex items-center gap-1.5">
                <i class="fa-regular fa-file-lines"></i> Preview
              </button>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    }

    // ==========================================
    // PREVIEW MODAL & MARKDOWN READER SYSTEM
    // ==========================================

    function escapeHtmlEntities(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    function renderPreviewMarkdown(source) {
      if (!source || typeof source !== 'string' || !source.trim()) {
        return '<p class="text-ds-muted italic p-4 text-center">No markdown content available for this page.</p>';
      }

      let text = source.replace(/\\r\\n/g, '\\n').replace(/\\r/g, '\\n');

      // 1. Isolate code blocks
      const codeBlocks = [];
      text = text.replace(/```([a-zA-Z0-9_+-]*)\\n([\\s\\S]*?)```/g, (match, lang, code) => {
        const placeholder = `%%MD_CODE_BLOCK_${codeBlocks.length}%%`;
        codeBlocks.push({ lang: (lang || 'code').trim(), code: code });
        return placeholder;
      });

      function formatInline(line) {
        if (!line) return '';
        let s = escapeHtmlEntities(line);
        // Inline code
        s = s.replace(/`([^`]+)`/g, '<code class="preview-inline-code">$1</code>');
        // Images
        s = s.replace(/!\\[([^\\]]*)\\]\\((https?:\\/\\/[^\\s\\)]+)\\)/g, '<figure class="my-3"><img src="$2" alt="$1" class="max-w-full rounded-lg border border-ds shadow-sm" loading="lazy"><figcaption class="text-xs text-ds-muted mt-1 text-center">$1</figcaption></figure>');
        // Links
        s = s.replace(/\\[([^\\]]+)\\]\\((https?:\\/\\/[^\\s\\)]+)\\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="preview-link">$1 <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i></a>');
        // Bold
        s = s.replace(/\\*\\*([^*]+)\\*\\*/g, '<strong>$1</strong>');
        s = s.replace(/__([^_]+)__/g, '<strong>$1</strong>');
        // Italic
        s = s.replace(/\\*([^*]+)\\*/g, '<em>$1</em>');
        s = s.replace(/_([^_]+)_/g, '<em>$1</em>');
        // Strikethrough
        s = s.replace(/~~([^~]+)~~/g, '<del class="text-ds-muted">$1</del>');
        return s;
      }

      const lines = text.split('\\n');
      const out = [];
      let inUl = false;
      let inOl = false;
      let inBlockquote = false;
      let inTable = false;
      let blockquoteBuffer = [];

      function closeLists() {
        if (inUl) { out.push('</ul>'); inUl = false; }
        if (inOl) { out.push('</ol>'); inOl = false; }
      }

      function closeBlockquote() {
        if (inBlockquote) {
          out.push(`<blockquote>${blockquoteBuffer.map(formatInline).join('<br>')}</blockquote>`);
          inBlockquote = false;
          blockquoteBuffer = [];
        }
      }

      function closeTable() {
        if (inTable) {
          out.push('</tbody></table></div>');
          inTable = false;
        }
      }

      function closeAll() {
        closeLists();
        closeBlockquote();
        closeTable();
      }

      for (let i = 0; i < lines.length; i++) {
        const raw = lines[i];
        const trimmed = raw.trim();

        // Check code block placeholder
        if (trimmed.startsWith('%%MD_CODE_BLOCK_') && trimmed.endsWith('%%')) {
          closeAll();
          const idx = parseInt(trimmed.replace('%%MD_CODE_BLOCK_', '').replace('%%', ''), 10);
          const cb = codeBlocks[idx];
          if (cb) {
            const escapedCode = escapeHtmlEntities(cb.code);
            const encoded = encodeURIComponent(cb.code);
            out.push(`
              <div class="preview-code-block">
                <div class="preview-code-header">
                  <span class="flex items-center gap-1.5"><i class="fa-solid fa-terminal text-[10px]"></i> ${escapeHtmlEntities(cb.lang || 'code')}</span>
                  <button type="button" onclick="copySnippet(this, decodeURIComponent('${encoded}'))" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-[10px] transition flex items-center gap-1">
                    <i class="fa-regular fa-copy"></i> <span>Copy</span>
                  </button>
                </div>
                <pre class="preview-code-pre"><code>${escapedCode}</code></pre>
              </div>
            `);
          }
          continue;
        }

        // Blank line
        if (!trimmed) {
          closeAll();
          continue;
        }

        // Table row | col | col |
        if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
          closeLists();
          closeBlockquote();
          const cells = trimmed.split('|').slice(1, -1).map(c => c.trim());
          const isDivider = cells.every(c => /^:?-+:?$/.test(c));
          if (isDivider) {
            continue;
          }
          if (!inTable) {
            inTable = true;
            out.push('<div class="overflow-x-auto my-3"><table class="preview-md-table"><thead><tr>');
            cells.forEach(c => out.push(`<th>${formatInline(c)}</th>`));
            out.push('</tr></thead><tbody>');
          } else {
            out.push('<tr>');
            cells.forEach(c => out.push(`<td>${formatInline(c)}</td>`));
            out.push('</tr>');
          }
          continue;
        } else {
          closeTable();
        }

        // Headings
        if (trimmed.startsWith('#')) {
          closeAll();
          if (trimmed.startsWith('#### ')) {
            out.push(`<h4>${formatInline(trimmed.substring(5))}</h4>`);
          } else if (trimmed.startsWith('### ')) {
            out.push(`<h3>${formatInline(trimmed.substring(4))}</h3>`);
          } else if (trimmed.startsWith('## ')) {
            out.push(`<h2>${formatInline(trimmed.substring(3))}</h2>`);
          } else if (trimmed.startsWith('# ')) {
            out.push(`<h1>${formatInline(trimmed.substring(2))}</h1>`);
          } else {
            out.push(`<p>${formatInline(trimmed)}</p>`);
          }
          continue;
        }

        // Horizontal Rule
        if (/^(-{3,}|\\*{3,}|_{3,})$/.test(trimmed)) {
          closeAll();
          out.push('<hr class="my-4 border-ds">');
          continue;
        }

        // Blockquote
        if (trimmed.startsWith('>')) {
          closeLists();
          inBlockquote = true;
          blockquoteBuffer.push(trimmed.replace(/^>\\s?/, ''));
          continue;
        } else {
          closeBlockquote();
        }

        // Unordered list
        const ulMatch = trimmed.match(/^[*\\-]\\s+(.*)$/);
        if (ulMatch) {
          if (inOl) { out.push('</ol>'); inOl = false; }
          if (!inUl) { out.push('<ul>'); inUl = true; }
          out.push(`<li>${formatInline(ulMatch[1])}</li>`);
          continue;
        }

        // Ordered list
        const olMatch = trimmed.match(/^\\d+\\.\\s+(.*)$/);
        if (olMatch) {
          if (inUl) { out.push('</ul>'); inUl = false; }
          if (!inOl) { out.push('<ol>'); inOl = true; }
          out.push(`<li>${formatInline(olMatch[1])}</li>`);
          continue;
        }

        // Paragraph
        closeLists();
        out.push(`<p>${formatInline(trimmed)}</p>`);
      }

      closeAll();
      return out.join('\\n');
    }

    function togglePreviewSource() {
      const reading = document.getElementById('previewReading');
      const pre = document.getElementById('previewContent');
      const toggleText = document.getElementById('previewSourceToggleText');
      const toggleIcon = document.getElementById('previewSourceToggleIcon');
      if (!reading || !pre) return;

      const isReadingVisible = !reading.classList.contains('hidden');
      if (isReadingVisible) {
        reading.classList.add('hidden');
        pre.classList.remove('hidden');
        if (toggleText) toggleText.textContent = 'Reader View';
        if (toggleIcon) toggleIcon.className = 'fa-regular fa-file-lines text-[11px]';
      } else {
        pre.classList.add('hidden');
        reading.classList.remove('hidden');
        if (toggleText) toggleText.textContent = 'Raw Source';
        if (toggleIcon) toggleIcon.className = 'fa-solid fa-code text-[11px]';
      }
    }

    function togglePreviewFullscreen() {
      const modalDialog = document.getElementById('previewModalDialog');
      const icon = document.getElementById('previewFullscreenIcon');
      const btn = document.getElementById('previewFullscreenBtn');
      if (!modalDialog) return;

      const isFullscreen = modalDialog.classList.toggle('preview-modal-fullscreen');
      if (icon) {
        if (isFullscreen) {
          icon.className = 'fa-solid fa-compress text-xs';
          if (btn) btn.setAttribute('title', 'Exit Fullscreen');
        } else {
          icon.className = 'fa-solid fa-expand text-xs';
          if (btn) btn.setAttribute('title', 'Toggle Fullscreen');
        }
      }
    }

    function copySnippet(btn, code) {
      if (!navigator.clipboard) {
        showToast('Clipboard access unavailable', 'warning');
        return;
      }
      navigator.clipboard.writeText(code).then(() => {
        const origHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-check text-emerald-400"></i> <span>Copied!</span>';
        setTimeout(() => { btn.innerHTML = origHtml; }, 2000);
      }).catch(() => {
        showToast('Code snippet copied!');
      });
    }

    let activePreviewIndex = 0;
    function showPreview(idx) {
      activePreviewIndex = idx;
      const r = window.crawledResults ? window.crawledResults[idx] : null;
      if (!r) return;
      const modal = document.getElementById('previewModal');
      document.getElementById('previewTitle').innerText = r.title || r.final_url || 'Page Preview';
      const previewUrl = document.getElementById('previewUrl');
      const previewUrlText = document.getElementById('previewUrlText');
      const targetUrl = r.final_url || r.url || '#';
      if (previewUrl) {
        previewUrl.href = targetUrl;
      }
      if (previewUrlText) {
        previewUrlText.textContent = targetUrl;
      }

      // Metadata chips
      const statusBadge = document.getElementById('previewStatusBadge');
      if (statusBadge) {
        const sc = r.status_code || 200;
        statusBadge.textContent = `${sc} ${sc === 200 ? 'OK' : ''}`.trim();
        statusBadge.className = sc >= 200 && sc < 300 ? 'status-pill ok shrink-0 text-[10px]' : 'status-pill bad shrink-0 text-[10px]';
      }
      const engineBadge = document.getElementById('previewEngineBadge');
      if (engineBadge) {
        engineBadge.textContent = (r.discovery_method || r.strategy_used || 'FAST').toUpperCase();
      }

      // Reading statistics
      const source = r.markdown || '';
      const charCount = source.length;
      const wordCount = source.trim() ? source.trim().split(/\\s+/).length : 0;
      const readMinutes = Math.max(1, Math.ceil(wordCount / 200));

      const readTimeEl = document.getElementById('previewReadTime');
      if (readTimeEl) readTimeEl.textContent = `${readMinutes} min read`;
      const wordCountEl = document.getElementById('previewWordCount');
      if (wordCountEl) wordCountEl.textContent = `${wordCount.toLocaleString()} words`;
      const charCountEl = document.getElementById('previewCharCount');
      if (charCountEl) charCountEl.textContent = `${charCount.toLocaleString()} characters`;

      if (r.ai_data && Object.keys(r.ai_data).length > 0) {
        currentAiData = r.ai_data;
      } else {
        currentAiData = null;
      }

      const netBadge = document.getElementById('previewNetworkCountBadge');
      if (netBadge) netBadge.innerText = (r.network_calls || []).length;
      const elemBadge = document.getElementById('previewElementsCountBadge');
      if (elemBadge) {
        elemBadge.innerText = (r.dom_elements && r.dom_elements.summary) ? r.dom_elements.summary.total_elements : 0;
      }

      setPreviewTab('markdown');
      modal.classList.remove('hidden');
      syncBodyScrollLock();
    }

    function setPreviewTab(tab) {
      const r = window.crawledResults ? window.crawledResults[activePreviewIndex] : null;
      if (!r) return;

      const mdTab = document.getElementById('viewMdTab');
      const aiTab = document.getElementById('viewAiTab');
      const screenshotTab = document.getElementById('viewScreenshotTab');
      const rpaTab = document.getElementById('viewRpaTab');
      const netTab = document.getElementById('viewNetworkTab');
      const elemTab = document.getElementById('viewElementsTab');

      const mdSec = document.getElementById('previewMdSection');
      const aiSec = document.getElementById('previewAiSection');
      const screenshotSec = document.getElementById('previewScreenshotSection');
      const rpaSec = document.getElementById('previewRpaSection');
      const netSec = document.getElementById('previewNetworkSection');
      const elemSec = document.getElementById('previewElementsSection');
      const pre = document.getElementById('previewContent');

      const baseInactive = 'preview-tab';
      if (mdTab) mdTab.className = baseInactive;
      if (aiTab) aiTab.className = baseInactive;
      if (screenshotTab) screenshotTab.className = baseInactive;
      if (rpaTab) rpaTab.className = baseInactive;
      if (netTab) netTab.className = baseInactive;
      if (elemTab) elemTab.className = baseInactive;

      if (mdSec) mdSec.classList.add('hidden');
      if (aiSec) aiSec.classList.add('hidden');
      if (screenshotSec) screenshotSec.classList.add('hidden');
      if (rpaSec) rpaSec.classList.add('hidden');
      if (netSec) netSec.classList.add('hidden');
      if (elemSec) elemSec.classList.add('hidden');

      if (tab === 'markdown') {
        if (mdTab) mdTab.className = 'preview-tab preview-tab-on';
        if (mdSec) mdSec.classList.remove('hidden');
        const reading = document.getElementById('previewReading');
        const source = r.markdown || '(No markdown extracted)';
        if (reading) reading.innerHTML = renderPreviewMarkdown(source);
        if (pre) pre.textContent = source;
        const sourceToggleText = document.getElementById('previewSourceToggleText');
        const sourceToggleIcon = document.getElementById('previewSourceToggleIcon');
        if (sourceToggleText) sourceToggleText.textContent = 'Raw Source';
        if (sourceToggleIcon) sourceToggleIcon.className = 'fa-solid fa-code text-[11px]';
        if (reading) reading.classList.remove('hidden');
        if (pre) pre.classList.add('hidden');
      } else if (tab === 'ai') {
        if (aiTab) aiTab.className = 'preview-tab preview-tab-on';
        if (aiSec) aiSec.classList.remove('hidden');

        const activeAiData = r.ai_data || currentAiData;
        const hasData = activeAiData && Object.keys(activeAiData).length > 0;

        const dataContainer = document.getElementById('previewAiDataContainer');
        const triggerContainer = document.getElementById('previewAiTriggerContainer');
        const jsonPre = document.getElementById('previewAiJson');

        if (hasData) {
          if (dataContainer) dataContainer.classList.remove('hidden');
          if (triggerContainer) triggerContainer.classList.add('hidden');
          if (jsonPre) jsonPre.innerText = JSON.stringify(activeAiData, null, 2);
        } else {
          if (dataContainer) dataContainer.classList.add('hidden');
          if (triggerContainer) triggerContainer.classList.remove('hidden');
        }
      } else if (tab === 'screenshot') {
        if (screenshotTab) screenshotTab.className = 'preview-tab preview-tab-on';
        if (screenshotSec) screenshotSec.classList.remove('hidden');
        renderPreviewScreenshot();
      } else if (tab === 'rpa') {
        if (rpaTab) rpaTab.className = 'preview-tab preview-tab-on';
        if (rpaSec) rpaSec.classList.remove('hidden');

        const logsList = document.getElementById('previewRpaLogsList');
        const countBadge = document.getElementById('previewRpaCountBadge');
        const logs = r.rpa_logs || [];
        if (countBadge) countBadge.innerText = `${logs.length} action(s) logged`;

        if (logsList) {
          if (logs.length === 0) {
            logsList.innerHTML = '<div class="text-ds-muted italic p-3 text-center">No interactive RPA actions logged for this page.</div>';
          } else {
            logsList.innerHTML = logs.map(l => {
              const isSuccess = l.includes('Success');
              const icon = isSuccess ? 'fa-circle-check text-emerald-600' : 'fa-triangle-exclamation text-amber-600';
              return `<div class="flex items-start gap-2 py-1.5 border-b border-ds/70"><i class="fa-solid ${icon} mt-0.5 text-xs"></i><span class="leading-relaxed text-[#1c1b1b]">${l}</span></div>`;
            }).join('');
          }
        }
      } else if (tab === 'network') {
        if (netTab) netTab.className = 'preview-tab preview-tab-on';
        if (netSec) netSec.classList.remove('hidden');
        renderPreviewNetwork();
      } else if (tab === 'elements') {
        if (elemTab) elemTab.className = 'preview-tab preview-tab-on';
        if (elemSec) elemSec.classList.remove('hidden');
        renderPreviewElements();
      }
    }

    function renderPreviewScreenshot() {
      const r = window.crawledResults ? window.crawledResults[activePreviewIndex] : null;
      if (!r) return;

      const img = document.getElementById('screenshotImg');
      const emptyNotice = document.getElementById('screenshotEmptyNotice');
      const openBtn = document.getElementById('openFullScreenshotBtn');
      const badge = document.getElementById('previewScreenshotBadge');

      const url = r.screenshot_url;
      if (url) {
        if (img) {
          img.src = url;
          img.classList.remove('hidden');
        }
        if (emptyNotice) emptyNotice.classList.add('hidden');
        if (openBtn) openBtn.classList.remove('hidden');
        if (badge) badge.classList.remove('hidden');
      } else {
        if (img) {
          img.src = '';
          img.classList.add('hidden');
        }
        if (emptyNotice) emptyNotice.classList.remove('hidden');
        if (openBtn) openBtn.classList.add('hidden');
      }
    }

    function openScreenshotInNewTab() {
      const r = window.crawledResults ? window.crawledResults[activePreviewIndex] : null;
      if (r && r.screenshot_url) {
        window.open(r.screenshot_url, '_blank');
      }
    }

    async function runPreviewVisionExtract() {
      const r = window.crawledResults ? window.crawledResults[activePreviewIndex] : null;
      if (!r) return;

      const taskSelect = document.getElementById('visionTaskSelect');
      const task = taskSelect ? taskSelect.value : 'chart_to_table';
      const resultCard = document.getElementById('visionResultCard');
      const btn = document.getElementById('runVisionBtn');

      if (resultCard) {
        resultCard.classList.remove('hidden');
        resultCard.innerHTML = '<div class="text-purple-600"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Analyzing visual content with Vision LLM...</div>';
      }
      if (btn) btn.disabled = true;

      try {
        const payload = {
          task: task,
          image_url: r.screenshot_url ? window.location.origin + r.screenshot_url : null,
          image_path: r.screenshot_path || null,
        };

        const res = await fetch('/api/v1/vision/extract', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();

        if (data.error) {
          resultCard.innerHTML = `<div class="text-rose-600 font-bold">Error: ${escapeHtml(data.error)}</div>`;
        } else {
          resultCard.innerHTML = `<div class="text-purple-900 font-bold mb-1">Model: ${escapeHtml(data.model_used)}</div><div class="whitespace-pre-wrap">${escapeHtml(data.extracted_text)}</div>`;
        }
      } catch (err) {
        if (resultCard) resultCard.innerHTML = `<div class="text-rose-600 font-bold">Failed to extract: ${escapeHtml(err.message)}</div>`;
      } finally {
        if (btn) btn.disabled = false;
      }
    }

    function renderPreviewNetwork() {
      const r = window.crawledResults ? window.crawledResults[activePreviewIndex] : null;
      if (!r) return;
      const calls = r.network_calls || [];
      const countBadge = document.getElementById('previewNetworkSummaryBadge');
      if (countBadge) countBadge.innerText = `${calls.length} call(s) captured`;
      filterPreviewNetwork();
    }

    function filterPreviewNetwork() {
      const r = window.crawledResults ? window.crawledResults[activePreviewIndex] : null;
      if (!r) return;
      const calls = r.network_calls || [];
      const list = document.getElementById('previewNetworkList');
      if (!list) return;

      const q = (document.getElementById('networkSearchInput')?.value || '').toLowerCase().trim();
      const statusFilter = document.getElementById('networkStatusFilter')?.value || 'all';

      const filtered = calls.filter(c => {
        if (q && !c.url.toLowerCase().includes(q) && !c.method.toLowerCase().includes(q)) return false;
        if (statusFilter === '2xx' && (c.status < 200 || c.status >= 300)) return false;
        if (statusFilter === 'error' && c.status < 400) return false;
        return true;
      });

      if (filtered.length === 0) {
        list.innerHTML = `
          <div class="text-ds-muted italic p-6 text-center bg-white rounded-xl border border-ds shadow-sm">
            ${calls.length === 0 ? 'No background Fetch/XHR API calls recorded for this page.<br><span class="text-[11px] text-ds-muted mt-1 block">(Tip: Use Browser Engine with JavaScript enabled to intercept background API traffic)</span>' : 'No network calls match your filter.'}
          </div>
        `;
        return;
      }

      list.innerHTML = filtered.map((c, i) => {
        const is2xx = c.status >= 200 && c.status < 300;
        const statusClass = is2xx ? 'bg-emerald-50 text-emerald-700 border-emerald-300' : 'bg-red-50 text-red-700 border-red-300';
        const methodColors = {
          GET: 'bg-blue-50 text-blue-700 border-blue-300',
          POST: 'bg-emerald-50 text-emerald-700 border-emerald-300',
          PUT: 'bg-amber-50 text-amber-800 border-amber-300',
          DELETE: 'bg-red-50 text-red-700 border-red-300'
        };
        const methodClass = methodColors[c.method] || 'bg-slate-100 text-slate-700 border-slate-300';
        const jsonStr = c.response_data ? (typeof c.response_data === 'object' ? JSON.stringify(c.response_data, null, 2) : String(c.response_data)) : null;

        return `
          <div class="p-3 bg-white rounded-xl border border-ds space-y-2 hover:border-ds-secondary/40 transition shadow-sm">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
              <div class="flex items-center gap-2 min-w-0 flex-1">
                <span class="px-2 py-0.5 rounded text-[11px] font-bold border font-mono ${methodClass}">${c.method}</span>
                <span class="px-2 py-0.5 rounded text-[11px] font-bold border font-mono ${statusClass}">${c.status}</span>
                <span class="font-mono text-[#1c1b1b] truncate select-all" title="${c.url}">${c.url}</span>
              </div>
              <div class="flex items-center gap-2 flex-shrink-0 text-[11px] text-ds-muted font-mono">
                <span>${c.resource_type || 'xhr'}</span>
                ${jsonStr ? `<button type="button" onclick="copyNetworkJson(${i})" class="btn-ghost px-2 py-1 rounded text-[11px]"><i class="fa-regular fa-copy mr-1"></i> Copy JSON</button>` : ''}
                ${jsonStr ? `<button type="button" onclick="toggleNetworkPayload(${i})" class="btn-ghost px-2 py-1 rounded text-[11px]"><i class="fa-solid fa-code mr-1"></i> Payload</button>` : ''}
              </div>
            </div>
            ${c.request_data ? `<div class="text-[11px] font-mono text-ds-muted bg-ds-surface-low p-2 rounded border border-ds truncate"><span class="text-ds-outline font-semibold">Post Data:</span> ${c.request_data}</div>` : ''}
            ${jsonStr ? `<div id="networkPayload_${i}" class="hidden mt-2"><pre class="bg-[#0f172a] p-3.5 rounded-lg text-[11px] font-mono text-[#38bdf8] max-h-56 overflow-auto whitespace-pre-wrap border border-slate-700/80 shadow-inner">${jsonStr}</pre></div>` : ''}
          </div>
        `;
      }).join('');
    }

    function toggleNetworkPayload(idx) {
      const el = document.getElementById(`networkPayload_${idx}`);
      if (el) el.classList.toggle('hidden');
    }

    function copyNetworkJson(idx) {
      const r = window.crawledResults ? window.crawledResults[activePreviewIndex] : null;
      if (!r || !r.network_calls || !r.network_calls[idx]) return;
      const data = r.network_calls[idx].response_data;
      if (!data) return;
      const str = typeof data === 'object' ? JSON.stringify(data, null, 2) : String(data);
      navigator.clipboard.writeText(str).then(() => showToast('API Response JSON copied!'));
    }

    let currentElementCategory = 'buttons';
    function setElementCategory(cat) {
      currentElementCategory = cat;
      const cats = ['buttons', 'inputs', 'tables', 'headings'];
      cats.forEach(c => {
        const btn = document.getElementById(`elemCatBtn${c.charAt(0).toUpperCase() + c.slice(1)}`);
        const list = document.getElementById(`elemCatList${c.charAt(0).toUpperCase() + c.slice(1)}`);
        if (btn && list) {
          if (c === cat) {
            btn.className = 'px-3 py-1.5 border-b-2 border-amber-600 text-amber-700 font-semibold flex items-center gap-1.5';
            list.classList.remove('hidden');
          } else {
            btn.className = 'px-3 py-1.5 border-b-2 border-transparent text-ds-muted hover:text-[#1c1b1b] font-semibold flex items-center gap-1.5';
            list.classList.add('hidden');
          }
        }
      });
    }

    function renderPreviewElements() {
      const r = window.crawledResults ? window.crawledResults[activePreviewIndex] : null;
      if (!r) return;
      const dom = r.dom_elements || {};
      const summary = dom.summary || {};

      document.getElementById('previewElementsSummaryBadge').innerText = `${summary.total_elements || 0} DOM elements`;
      document.getElementById('elemCountButtons').innerText = summary.buttons || 0;
      document.getElementById('elemCountInputs').innerText = summary.inputs || 0;
      document.getElementById('elemCountTables').innerText = summary.tables || 0;
      document.getElementById('elemCountHeadings').innerText = summary.headings || 0;

      // 1. Render Buttons
      const btnList = document.getElementById('elemCatListButtons');
      const buttons = dom.buttons || [];
      if (btnList) {
        btnList.innerHTML = buttons.length === 0 ? '<div class="text-ds-muted italic p-3 text-center text-xs">No buttons detected.</div>' : buttons.map(b => `
          <div class="flex items-center justify-between p-2.5 bg-white rounded-lg border border-ds text-xs gap-3 shadow-xs">
            <div class="flex items-center gap-2 min-w-0 flex-1">
              <span class="px-1.5 py-0.5 rounded text-[11px] font-mono bg-amber-50 text-amber-800 border border-amber-200">${b.tag}</span>
              <span class="text-[#1c1b1b] font-medium truncate">${b.text}</span>
            </div>
            <div class="flex items-center gap-2 flex-shrink-0 font-mono text-[11px]">
              <span class="text-ds-muted truncate max-w-xs bg-ds-surface-low px-2 py-0.5 rounded border border-ds">${b.selector}</span>
              <button type="button" onclick="copySelectorText('${b.selector.replace(/'/g, "\\'")}')" class="btn-ghost px-2 py-1 rounded text-[11px] transition"><i class="fa-regular fa-copy mr-1"></i> Copy</button>
            </div>
          </div>
        `).join('');
      }

      // 2. Render Inputs
      const inpList = document.getElementById('elemCatListInputs');
      const inputs = dom.inputs || [];
      if (inpList) {
        inpList.innerHTML = inputs.length === 0 ? '<div class="text-ds-muted italic p-3 text-center text-xs">No form inputs detected.</div>' : inputs.map(inp => `
          <div class="flex items-center justify-between p-2.5 bg-white rounded-lg border border-ds text-xs gap-3 shadow-xs">
            <div class="flex items-center gap-2 min-w-0 flex-1">
              <span class="px-1.5 py-0.5 rounded text-[11px] font-mono bg-blue-50 text-blue-800 border border-blue-200">${inp.type || inp.tag}</span>
              <span class="text-[#1c1b1b] truncate">${inp.name ? `name="${inp.name}"` : ''} ${inp.placeholder ? `placeholder="${inp.placeholder}"` : ''}</span>
            </div>
            <div class="flex items-center gap-2 flex-shrink-0 font-mono text-[11px]">
              <span class="text-ds-muted truncate max-w-xs bg-ds-surface-low px-2 py-0.5 rounded border border-ds">${inp.selector}</span>
              <button type="button" onclick="copySelectorText('${inp.selector.replace(/'/g, "\\'")}')" class="btn-ghost px-2 py-1 rounded text-[11px] transition"><i class="fa-regular fa-copy mr-1"></i> Copy</button>
            </div>
          </div>
        `).join('');
      }

      // 3. Render Tables
      const tblList = document.getElementById('elemCatListTables');
      const tables = dom.tables || [];
      if (tblList) {
        tblList.innerHTML = tables.length === 0 ? '<div class="text-ds-muted italic p-3 text-center text-xs">No data tables detected.</div>' : tables.map(tbl => `
          <div class="flex items-center justify-between p-2.5 bg-white rounded-lg border border-ds text-xs gap-3 shadow-xs">
            <div class="flex items-center gap-2 min-w-0 flex-1">
              <span class="px-1.5 py-0.5 rounded text-[11px] font-mono bg-purple-50 text-purple-800 border border-purple-200">${tbl.rows_count} rows</span>
              <span class="text-[#1c1b1b] truncate">${(tbl.headers || []).join(', ') || 'Table'}</span>
            </div>
            <div class="flex items-center gap-2 flex-shrink-0 font-mono text-[11px]">
              <span class="text-ds-muted truncate max-w-xs bg-ds-surface-low px-2 py-0.5 rounded border border-ds">${tbl.selector}</span>
              <button type="button" onclick="copySelectorText('${tbl.selector.replace(/'/g, "\\'")}')" class="btn-ghost px-2 py-1 rounded text-[11px] transition"><i class="fa-regular fa-copy mr-1"></i> Copy</button>
            </div>
          </div>
        `).join('');
      }

      // 4. Render Headings
      const hdList = document.getElementById('elemCatListHeadings');
      const headings = dom.headings || [];
      if (hdList) {
        hdList.innerHTML = headings.length === 0 ? '<div class="text-ds-muted italic p-3 text-center text-xs">No headings detected.</div>' : headings.map(h => `
          <div class="flex items-center justify-between p-2.5 bg-white rounded-lg border border-ds text-xs gap-3 shadow-xs">
            <div class="flex items-center gap-2 min-w-0 flex-1">
              <span class="px-1.5 py-0.5 rounded text-[11px] font-mono bg-teal-50 text-teal-800 border border-teal-200 uppercase">${h.level}</span>
              <span class="text-[#1c1b1b] font-medium truncate">${h.text}</span>
            </div>
            <div class="flex items-center gap-2 flex-shrink-0 font-mono text-[11px]">
              <span class="text-ds-muted truncate max-w-xs bg-ds-surface-low px-2 py-0.5 rounded border border-ds">${h.selector}</span>
              <button type="button" onclick="copySelectorText('${h.selector.replace(/'/g, "\\'")}')" class="btn-ghost px-2 py-1 rounded text-[11px] transition"><i class="fa-regular fa-copy mr-1"></i> Copy</button>
            </div>
          </div>
        `).join('');
      }
    }

    function copySelectorText(sel) {
      navigator.clipboard.writeText(sel).then(() => showToast(`Selector copied: ${sel}`));
    }

    async function runPreviewElementCheck() {
      const r = window.crawledResults ? window.crawledResults[activePreviewIndex] : null;
      if (!r) return;
      const selector = document.getElementById('elementSelectorInput').value.trim();
      const resBox = document.getElementById('elementCheckResult');
      if (!selector) {
        showToast('Please enter a CSS selector to test', 'warning');
        return;
      }

      resBox.classList.remove('hidden');
      resBox.innerHTML = '<div class="text-slate-400 flex items-center gap-2"><i class="fa-solid fa-spinner fa-spin"></i> Checking selector against page DOM...</div>';

      try {
        const resp = await fetch('/api/v1/elements/check', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            selector: selector,
            url: r.final_url || r.url
          })
        });

        const data = await resp.json();
        if (!resp.ok || data.error) {
          resBox.innerHTML = `<div class="p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-xs flex items-center gap-2"><i class="fa-solid fa-circle-xmark text-red-500"></i> <span>${data.error || 'Failed to query selector'}</span></div>`;
          return;
        }

        if (data.match_count === 0) {
          resBox.innerHTML = `
            <div class="p-3 bg-ds-surface-low border border-ds rounded-xl text-ds-muted text-xs flex items-center justify-between">
              <span><i class="fa-solid fa-circle-info mr-1 text-ds-muted"></i> No elements matched selector <code class="font-mono text-ds-accent bg-white px-1.5 py-0.5 rounded border border-ds">${selector}</code>.</span>
            </div>
          `;
          return;
        }

        resBox.innerHTML = `
          <div class="p-3 bg-emerald-50/70 border border-emerald-200 rounded-xl space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-emerald-800 font-semibold flex items-center gap-1.5 text-xs">
                <i class="fa-solid fa-circle-check text-emerald-600"></i> Found ${data.match_count} matching element(s)
              </span>
              <button onclick="copySelectorText('${selector.replace(/'/g, "\\'")}')" class="btn-ghost px-2.5 py-1 text-xs rounded border border-emerald-300 hover:bg-emerald-100/60 text-emerald-900 transition">
                <i class="fa-regular fa-copy mr-1"></i> Copy Selector
              </button>
            </div>
            <div class="space-y-1.5 max-h-48 overflow-y-auto pr-1">
              ${data.matches.map((m, idx) => `
                <div class="p-2.5 bg-white rounded-lg border border-ds font-mono text-[11px] space-y-1 shadow-xs text-[#1c1b1b]">
                  <div class="flex items-center justify-between text-ds-muted">
                    <span class="text-amber-800 font-bold">&lt;${m.tag}${m.id ? ` id="${m.id}"` : ''}${m.classes && m.classes.length ? ` class="${m.classes.join(' ')}"` : ''}&gt;</span>
                    <span class="text-[10px]">Match #${idx + 1}</span>
                  </div>
                  ${m.text ? `<div class="text-[#1c1b1b] truncate"><span class="text-ds-muted">text:</span> "${m.text}"</div>` : ''}
                  ${m.attributes && Object.keys(m.attributes).length ? `<div class="text-ds-muted truncate"><span class="text-ds-outline">attrs:</span> ${JSON.stringify(m.attributes)}</div>` : ''}
                </div>
              `).join('')}
            </div>
          </div>
        `;
      } catch (err) {
        resBox.innerHTML = `<div class="p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-xs flex items-center gap-2"><i class="fa-solid fa-circle-xmark text-red-500"></i> <span>${err.message}</span></div>`;
      }
    }


    function showModalAiTrigger() {
      document.getElementById('previewAiDataContainer').classList.add('hidden');
      document.getElementById('previewAiTriggerContainer').classList.remove('hidden');
    }

    async function runModalAiExtraction() {
      const r = window.crawledResults ? window.crawledResults[activePreviewIndex] : null;
      if (!r) return;

      const btn = document.getElementById('btnModalExtractAi');
      const errBox = document.getElementById('modalAiError');
      errBox.classList.add('hidden');
      errBox.innerText = '';

      const schema = document.getElementById('modalAiSchema').value;
      const prompt = document.getElementById('modalAiPrompt').value.trim();
      const aiModel = document.getElementById('modalAiModel') ? document.getElementById('modalAiModel').value : null;

      const originalBtnHtml = btn.innerHTML;
      btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Extracting...';
      btn.disabled = true;

      if (modalAiTimer) modalAiTimer.stop();
      const timerBadge = document.getElementById('modalAiTimerBadge');
      if (timerBadge) {
        timerBadge.classList.remove('hidden');
        timerBadge.classList.add('inline-flex');
      }
      modalAiTimer = createLiveTimer('modalAiStartTime', 'modalAiElapsedTime');

      try {
        const resp = await fetch('/api/v1/extract', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            url: r.final_url || r.url,
            schema_type: schema,
            prompt: prompt || null,
            model: aiModel || null
          })
        });

        if (!resp.ok) {
          const errData = await resp.json();
          throw new Error(errData.detail || 'Extraction failed');
        }

        const data = await resp.json();
        r.ai_data = data.data;
        currentAiData = data.data;

        // Render result in modal
        const dataContainer = document.getElementById('previewAiDataContainer');
        const triggerContainer = document.getElementById('previewAiTriggerContainer');
        const jsonPre = document.getElementById('previewAiJson');

        dataContainer.classList.remove('hidden');
        triggerContainer.classList.add('hidden');
        jsonPre.innerText = JSON.stringify(data.data, null, 2);

        // Re-render results table to show the AI badge
        if (window.crawledResults) {
          renderResults(window.crawledResults);
        }
        loadHistory(); // refresh vector store badge
      } catch (err) {
        errBox.innerText = 'AI Extraction error: ' + err.message;
        errBox.classList.remove('hidden');
      } finally {
        if (modalAiTimer) {
          modalAiTimer.stop();
          modalAiTimer = null;
        }
        btn.innerHTML = originalBtnHtml;
        btn.disabled = false;
      }
    }

    function copyPreviewMarkdown() {
      const r = window.crawledResults ? window.crawledResults[activePreviewIndex] : null;
      if (!r || !r.markdown) {
        showToast('No markdown to copy', 'warning');
        return;
      }
      navigator.clipboard.writeText(r.markdown).then(() => {
        showToast('Markdown copied to clipboard!');
      }).catch(() => {
        showToast('Failed to copy to clipboard', 'warning');
      });
    }

    function copyPreviewAiJson() {
      const r = window.crawledResults ? window.crawledResults[activePreviewIndex] : null;
      const data = (r && r.ai_data) ? r.ai_data : currentAiData;
      if (!data) {
        showToast('No AI data to copy', 'warning');
        return;
      }
      navigator.clipboard.writeText(JSON.stringify(data, null, 2)).then(() => {
        showToast('AI JSON copied to clipboard!');
      }).catch(() => {
        showToast('Failed to copy to clipboard', 'warning');
      });
    }

    function closePreview() {
      if (modalAiTimer) {
        modalAiTimer.stop();
        modalAiTimer = null;
      }
      const timerBadge = document.getElementById('modalAiTimerBadge');
      if (timerBadge) {
        timerBadge.classList.add('hidden');
        timerBadge.classList.remove('inline-flex');
      }
      const modalDialog = document.getElementById('previewModalDialog');
      if (modalDialog && modalDialog.classList.contains('preview-modal-fullscreen')) {
        modalDialog.classList.remove('preview-modal-fullscreen');
        const icon = document.getElementById('previewFullscreenIcon');
        if (icon) icon.className = 'fa-solid fa-expand text-xs';
        const btn = document.getElementById('previewFullscreenBtn');
        if (btn) btn.setAttribute('title', 'Toggle Fullscreen');
      }
      document.getElementById('previewModal').classList.add('hidden');
      syncBodyScrollLock();
    }

    function exportData(fmt) {
      if (currentMode === 'crawl' && activeJobId) {
        window.open(`/api/v1/jobs/${activeJobId}/export?format=${fmt}`, '_blank');
      } else {
        const url = document.getElementById('scrapeUrl').value.trim();
        const strategy = document.getElementById('scrapeStrategy').value;
        const respectRobots = document.getElementById('scrapeRespectRobots').checked;
        const exportUrl = `/api/v1/scrape/export?url=${encodeURIComponent(url)}&format=${fmt}&strategy=${strategy}&respect_robots=${respectRobots}`;
        window.open(exportUrl, '_blank');
      }
    }

    async function checkRobots() {
      const url = document.getElementById('targetUrl').value.trim();
      setStatus('running', 'Checking robots.txt directives...');
      try {
        const resp = await fetch('/api/v1/robots?url=' + encodeURIComponent(url));
        const data = await resp.json();
        setStatus('completed', `Robots for ${data.domain}: Crawl-Delay=${data.crawl_delay || 'none'}, Sitemaps=${data.sitemaps.length}`);
        updateEthicsStatus();
        appendLiveStream('robots.txt OK for ' + data.domain + ' — crawl-delay=' + (data.crawl_delay || 'default'), 'ok');
        alert(`Robots.txt status: ${data.status_code}\\nCrawl-Delay: ${data.crawl_delay || 'Default'}\\nSitemaps: ${data.sitemaps.join(', ') || 'None declared'}`);
      } catch (err) {
        setStatus('failed', 'Error checking robots: ' + err);
      }
    }

    async function inspectSitemap() {
      const url = document.getElementById('targetUrl').value.trim();
      setStatus('running', 'Inspecting sitemap.xml...');
      try {
        const resp = await fetch('/api/v1/sitemap?url=' + encodeURIComponent(url));
        const data = await resp.json();
        setStatus('completed', `Sitemap: ${data.total_urls} URLs found.`);
        alert(`Sitemap found: ${data.total_urls} URLs.\\nNested sitemaps: ${data.nested_sitemaps.length}`);
      } catch (err) {
        setStatus('failed', 'Error fetching sitemap: ' + err);
      }
    }

    /* --- CHROMADB VECTOR STORE & HISTORY FUNCTIONS --- */

    function switchHistoryView(mode) {
      activeHistoryView = mode;
      const domainBtn = document.getElementById('btnViewDomain');
      const flatBtn = document.getElementById('btnViewFlat');
      const domainContainer = document.getElementById('historyDomainCardsContainer');
      const flatContainer = document.getElementById('historyFlatTableContainer');

      const activeCls = 'px-3 py-1 rounded-full view-toggle-active transition flex items-center gap-1.5';
      const inactiveCls = 'px-3 py-1 rounded-full view-toggle-inactive transition flex items-center gap-1.5';
      if (mode === 'domain') {
        if (domainContainer) domainContainer.classList.remove('hidden');
        if (flatContainer) flatContainer.classList.add('hidden');
        if (domainBtn) domainBtn.className = activeCls;
        if (flatBtn) flatBtn.className = inactiveCls;
      } else {
        if (domainContainer) domainContainer.classList.add('hidden');
        if (flatContainer) flatContainer.classList.remove('hidden');
        if (domainBtn) domainBtn.className = inactiveCls;
        if (flatBtn) flatBtn.className = activeCls;
      }
    }

    function formatBytes(bytes) {
      if (!bytes || bytes <= 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    function closeAllExportMenus() {
      document.querySelectorAll('.export-menu-panel').forEach((p) => p.classList.add('hidden'));
    }

    function toggleExportMenu(event, btn) {
      event.stopPropagation();
      const panel = btn.nextElementSibling;
      const wasOpen = panel && !panel.classList.contains('hidden');
      closeAllExportMenus();
      if (panel && !wasOpen) panel.classList.remove('hidden');
    }

    document.addEventListener('click', closeAllExportMenus);

    function exportMenuHtml(safeUrl) {
      return `<select aria-label="Export format" class="btn-ghost rounded-lg px-2 py-1 text-[11px] font-medium max-w-[6.5rem]"
          onchange="if(this.value){exportHistoryItem('${safeUrl}', this.value); this.selectedIndex=0;}">
          <option value="" selected>Export</option>
          <option value="pdf">PDF</option>
          <option value="md">Markdown</option>
          <option value="txt">Plain text</option>
          <option value="json">JSON</option>
          <option value="csv">CSV</option>
        </select>`;
    }

    function pageRowActionsHtml(safeUrl, safeTitle, includeRecrawl) {
      const recrawl = includeRecrawl
        ? `<button type="button" onclick="recrawlLivePage('${safeUrl}')" title="Recrawl live" class="btn-icon" aria-label="Recrawl"><i class="fa-solid fa-rotate text-[11px]"></i></button>`
        : '';
      return `
        <div class="flex items-center justify-end gap-0.5">
          ${recrawl}
          <button type="button" onclick="previewCachedPage('${safeUrl}')" title="Preview" class="btn-ghost px-2.5 py-1 rounded-lg text-[11px] font-medium">
            Preview
          </button>
          <button type="button" onclick="promptDeletePage('${safeUrl}', '${safeTitle}')" title="Delete page" class="btn-icon hover:text-[#ba1a1a]" aria-label="Delete page">
            <i class="fa-solid fa-trash-can text-[11px]"></i>
          </button>
        </div>`;
    }

    function statusPillHtml(code) {
      const ok = code === 200;
      return `<span class="status-pill ${ok ? 'ok' : 'bad'}">${code ?? '—'}</span>`;
    }

    function revisionBadgeHtml(p) {
      const revCount = p.revision_count || 1;
      const delta = p.growth_delta_bytes || 0;
      const deltaSign = delta >= 0 ? `+${delta} B` : `${delta} B`;
      if (revCount > 1) {
        return `<span class="rev-badge" title="Updated ${revCount} times (Net change: ${deltaSign})">v${revCount} · ${deltaSign}</span>`;
      }
      return `<span class="rev-badge rev-badge-v1">v1</span>`;
    }

    async function loadHistory() {
      const tbody = document.getElementById('historyTableBody');
      const cardsContainer = document.getElementById('historyDomainCardsContainer');
      const tabCount = document.getElementById('tabCountBadge');

      try {
        const [domainsResp, pagesResp] = await Promise.all([
          fetch('/api/v1/history/domains'),
          fetch('/api/v1/history?limit=300')
        ]);
        const domains = await domainsResp.json();
        const pages = await pagesResp.json();

        storedDomainsList = Array.isArray(domains) ? domains : [];
        storedHistoryList = Array.isArray(pages) ? pages : [];

        // KPI calculations
        const totalDomains = storedDomainsList.length;
        const totalPages = storedHistoryList.length;
        const totalSizeBytes = storedHistoryList.reduce((acc, p) => acc + (p.size || 0), 0);
        const totalAiProfiles = storedHistoryList.filter(p => p.has_ai || p.ai_data).length;

        const kpiDomains = document.getElementById('kpiDomains');
        const kpiPages = document.getElementById('kpiPages');
        const kpiSize = document.getElementById('kpiSize');
        const kpiAiProfiles = document.getElementById('kpiAiProfiles');

        if (kpiDomains) kpiDomains.innerText = totalDomains;
        if (kpiPages) kpiPages.innerText = totalPages;
        if (kpiSize) kpiSize.innerText = formatBytes(totalSizeBytes);
        if (kpiAiProfiles) kpiAiProfiles.innerText = totalAiProfiles;
        if (tabCount) {
          tabCount.innerText = totalPages;
          tabCount.classList.toggle('animate-pulse', totalPages > 0);
        }
        const headerCount = document.getElementById('headerStoreCount');
        if (headerCount) headerCount.innerText = totalPages;

        renderDomainCards(storedDomainsList);
        renderHistoryTable(storedHistoryList);
      } catch (err) {
        if (cardsContainer) cardsContainer.innerHTML = `<div class="p-6 text-center text-red-400">Failed loading domain history: ${err.message}</div>`;
        if (tbody) tbody.innerHTML = `<tr><td colspan="8" class="p-6 text-center text-red-400">Failed loading history: ${err.message}</td></tr>`;
      }
    }

    function renderDomainCards(domains) {
      const container = document.getElementById('historyDomainCardsContainer');
      if (!container) return;
      if (!domains || domains.length === 0) {
        container.innerHTML = `
          <div class="p-8 text-center text-ds-muted bg-[#f6f3f2] rounded-xl border border-ds">
            <i class="fa-solid fa-folder-open text-3xl mb-3 text-ds-muted opacity-50"></i>
            <p class="text-sm text-[#1c1b1b]">No domains stored in ChromaDB yet.</p>
            <p class="text-xs text-ds-muted mt-1">Start a crawl or scrape above to populate your domain knowledge base.</p>
          </div>`;
        return;
      }

      let html = '';
      domains.forEach((d, idx) => {
        const isFirst = idx === 0;
        const totalSizeStr = formatBytes(d.total_size);
        const lastCrawledStr = d.newest_crawled_at ? new Date(d.newest_crawled_at).toLocaleDateString() : 'N/A';
        const pages = d.pages || [];

        html += `
          <div class="domain-card" id="domainCard_${idx}">
            <div class="p-4 flex flex-col lg:flex-row lg:items-center justify-between gap-3 bg-[#fafafa]">
              <div class="flex items-center gap-3 cursor-pointer select-none min-w-0" onclick="toggleDomainAccordion(${idx})">
                <div class="w-9 h-9 rounded-lg domain-card-icon flex items-center justify-center shrink-0">
                  <i class="fa-solid fa-globe"></i>
                </div>
                <div class="min-w-0">
                  <div class="flex flex-wrap items-center gap-2">
                    <h4 class="text-sm font-semibold text-[#1c1b1b] truncate">${d.domain}</h4>
                    <span class="text-[11px] font-mono text-ds-muted">${d.total_pages} ${d.total_pages === 1 ? 'page' : 'pages'}</span>
                    <span class="text-[11px] font-mono text-ds-muted">${totalSizeStr}</span>
                    ${d.ai_profile_count > 0 ? `
                      <span class="ai-badge">${d.ai_profile_count} AI</span>
                    ` : ''}
                  </div>
                  <div class="text-[11px] text-ds-muted mt-0.5">Updated ${lastCrawledStr}</div>
                </div>
              </div>
              <div class="flex items-center gap-1.5 shrink-0">
                <button onclick="fillSearchDomain('${d.domain}')" title="Search this domain" class="btn-ghost px-2.5 py-1.5 rounded-lg text-[11px] font-medium">Search</button>
                <button onclick="openDossierModal('${d.domain}')" title="Generate dossier" class="btn-ghost px-2.5 py-1.5 rounded-lg text-[11px] font-medium">Dossier</button>
                <button onclick="openCompetitorModal('${d.domain}')" title="Benchmark against other competitors" class="btn-ghost px-2.5 py-1.5 rounded-lg text-[11px] font-medium text-amber-700 hover:bg-amber-50">Compare</button>
                <button onclick="promptDeleteDomain('${d.domain}', ${d.total_pages})" title="Delete this domain" class="btn-ghost px-2.5 py-1.5 rounded-lg text-[11px] font-medium text-[#ba1a1a] hover:bg-[#ffdad6]">Delete</button>
                <button onclick="toggleDomainAccordion(${idx})" class="btn-icon" id="chevronDomain_${idx}" aria-label="Toggle domain pages">
                  <i class="fa-solid ${isFirst ? 'fa-chevron-up' : 'fa-chevron-down'} text-xs"></i>
                </button>
              </div>
            </div>
            <div id="domainPages_${idx}" class="${isFirst ? '' : 'hidden'} overflow-x-auto border-t border-ds history-table-wrap">
              <table class="data-table w-full text-left text-xs">
                <thead class="sticky top-0 z-10 bg-[#f6f3f2]">
                  <tr>
                    <th class="px-3 py-2.5">Status</th>
                    <th class="px-3 py-2.5">Page</th>
                    <th class="px-3 py-2.5">Revision</th>
                    <th class="px-3 py-2.5">Size</th>
                    <th class="px-3 py-2.5">Crawled</th>
                    <th class="px-3 py-2.5">Export</th>
                    <th class="px-3 py-2.5 text-right pr-4">Actions</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[#e5e2e1]">
        `;

        pages.forEach(p => {
          const targetUrl = p.final_url || p.url;
          const safeUrl = encodeURIComponent(targetUrl);
          const safeTitle = (p.title || 'Untitled').replace(/'/g, "\\'");
          const aiBadge = p.has_ai ? `<span class="ai-badge ml-1.5">AI</span>` : '';

          html += `
            <tr class="history-row">
              <td class="px-3 py-2.5">${statusPillHtml(p.status_code)}</td>
              <td class="px-3 py-2.5 max-w-xs md:max-w-md">
                <div class="font-medium text-[#1c1b1b] truncate" title="${p.title || ''}">${p.title || 'Untitled'}${aiBadge}</div>
                <div class="text-ds-muted text-[11px] font-mono truncate" title="${targetUrl}">${targetUrl}</div>
              </td>
              <td class="px-3 py-2.5 whitespace-nowrap">${revisionBadgeHtml(p)}</td>
              <td class="px-3 py-2.5 font-mono text-ds-muted">${formatBytes(p.size || 0)}</td>
              <td class="px-3 py-2.5 text-ds-muted text-[11px] whitespace-nowrap">${p.crawled_at ? new Date(p.crawled_at).toLocaleDateString() : 'N/A'}</td>
              <td class="px-3 py-2.5">${exportMenuHtml(safeUrl)}</td>
              <td class="px-3 py-2.5 pr-4">${pageRowActionsHtml(safeUrl, safeTitle, true)}</td>
            </tr>
          `;
        });

        html += `
                </tbody>
              </table>
            </div>
          </div>
        `;
      });

      container.innerHTML = html;
    }

    function toggleDomainAccordion(idx) {
      const el = document.getElementById('domainPages_' + idx);
      const chevron = document.getElementById('chevronDomain_' + idx);
      if (!el) return;
      const isHidden = el.classList.contains('hidden');
      if (isHidden) {
        el.classList.remove('hidden');
        if (chevron) chevron.innerHTML = '<i class="fa-solid fa-chevron-up text-xs"></i>';
      } else {
        el.classList.add('hidden');
        if (chevron) chevron.innerHTML = '<i class="fa-solid fa-chevron-down text-xs"></i>';
      }
    }

    function renderHistoryTable(pages) {
      const tbody = document.getElementById('historyTableBody');
      if (!tbody) return;
      if (!pages || pages.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="p-6 text-center text-ds-muted">No pages stored in ChromaDB yet. Start crawling or scraping to populate the vector store!</td></tr>';
        return;
      }

      let html = '';
      pages.forEach(p => {
        const dateStr = p.crawled_at ? new Date(p.crawled_at).toLocaleDateString() : 'N/A';
        const targetUrl = p.final_url || p.url;
        const safeUrl = encodeURIComponent(targetUrl);
        const safeTitle = (p.title || 'Untitled').replace(/'/g, "\\'");

        html += `
          <tr class="history-row">
            <td class="px-3 py-2.5">${statusPillHtml(p.status_code)}</td>
            <td class="px-3 py-2.5">
              <div class="font-medium text-[#1c1b1b] truncate max-w-xs" title="${p.title || ''}">${p.title || 'Untitled'}</div>
              <div class="text-ds-muted text-[11px] truncate max-w-xs font-mono" title="${targetUrl}">${targetUrl}</div>
            </td>
            <td class="px-3 py-2.5 text-ds-muted font-mono text-[11px]">${p.domain || '-'}</td>
            <td class="px-3 py-2.5 whitespace-nowrap">${revisionBadgeHtml(p)}</td>
            <td class="px-3 py-2.5 font-mono text-ds-muted">${formatBytes(p.size || 0)}</td>
            <td class="px-3 py-2.5 text-ds-muted text-[11px] whitespace-nowrap">${dateStr}</td>
            <td class="px-3 py-2.5">${exportMenuHtml(safeUrl)}</td>
            <td class="px-3 py-2.5">${pageRowActionsHtml(safeUrl, safeTitle, false)}</td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    }

    function filterHistoryTable() {
      const q = document.getElementById('filterHistoryInput').value.toLowerCase().trim();
      if (!q) {
        renderDomainCards(storedDomainsList);
        renderHistoryTable(storedHistoryList);
        return;
      }
      const filteredDomains = storedDomainsList.filter(d =>
        d.domain.toLowerCase().includes(q) ||
        (d.pages && d.pages.some(p =>
          (p.title && p.title.toLowerCase().includes(q)) ||
          (p.url && p.url.toLowerCase().includes(q))
        ))
      );
      renderDomainCards(filteredDomains);

      const filteredPages = storedHistoryList.filter(p =>
        (p.title && p.title.toLowerCase().includes(q)) ||
        (p.url && p.url.toLowerCase().includes(q)) ||
        (p.final_url && p.final_url.toLowerCase().includes(q)) ||
        (p.domain && p.domain.toLowerCase().includes(q))
      );
      renderHistoryTable(filteredPages);
    }

    function exportHistoryItem(encodedUrl, fmt) {
      window.open(`/api/v1/history/export?url=${encodedUrl}&format=${fmt}`, '_blank');
    }

    async function previewCachedPage(encodedUrl) {
      try {
        const resp = await fetch(`/api/v1/history/page?url=${encodedUrl}`);
        if (!resp.ok) throw new Error('Page not found in vector store');
        const data = await resp.json();
        if (data.result && data.ai_data) {
          data.result.ai_data = data.ai_data;
        }
        window.crawledResults = [data.result];
        currentAiData = data.ai_data;
        showPreview(0);
      } catch (err) {
        alert('Could not load cached preview: ' + err.message);
      }
    }

    async function recrawlLivePage(encodedUrl) {
      const url = decodeURIComponent(encodedUrl);
      if (!confirm(`Re-crawl ${url} live now to detect updates, content changes, and record revision history?`)) return;

      try {
        const resp = await fetch('/api/v1/history/recrawl', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ url: url })
        });
        if (!resp.ok) {
          const err = await resp.json();
          throw new Error(err.detail || 'Recrawl failed');
        }
        const data = await resp.json();
        alert(`Successfully re-crawled! Revision: v${data.revision_count}, Net Growth: ${data.growth_delta_bytes >= 0 ? '+' : ''}${data.growth_delta_bytes} bytes.`);
        loadHistory();
      } catch (e) {
        alert('Error recrawling page: ' + e.message);
      }
    }

    function promptDeletePage(encodedUrl, title) {
      const url = decodeURIComponent(encodedUrl);
      pendingDelete = { type: 'page', url: url };
      document.getElementById('deleteTargetName').innerText = title || url;
      document.getElementById('deleteTargetWarning').innerText = 'This will selectively purge this individual page from your local ChromaDB vector store.';
      document.getElementById('deleteConfirmModal').classList.remove('hidden');
      syncBodyScrollLock();
    }

    function promptDeleteDomain(domain, count) {
      pendingDelete = { type: 'domain', domain: domain };
      document.getElementById('deleteTargetName').innerText = domain;
      document.getElementById('deleteTargetWarning').innerText = `This will selectively purge all ${count} pages belonging to ${domain} from the local ChromaDB vector store.`;
      document.getElementById('deleteConfirmModal').classList.remove('hidden');
      syncBodyScrollLock();
    }

    function closeDeleteConfirmModal() {
      document.getElementById('deleteConfirmModal').classList.add('hidden');
      pendingDelete = null;
      syncBodyScrollLock();
    }

    async function executeDeletion() {
      if (!pendingDelete) return;
      const btn = document.getElementById('btnExecuteDelete');
      const originalHtml = btn.innerHTML;
      btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Deleting...';
      btn.disabled = true;

      try {
        if (pendingDelete.type === 'page') {
          const resp = await fetch(`/api/v1/history/page?url=${encodeURIComponent(pendingDelete.url)}`, {
            method: 'DELETE'
          });
          if (!resp.ok) throw new Error('Failed to delete page');
        } else if (pendingDelete.type === 'domain') {
          const resp = await fetch(`/api/v1/history/domain?domain=${encodeURIComponent(pendingDelete.domain)}`, {
            method: 'DELETE'
          });
          if (!resp.ok) throw new Error('Failed to delete domain');
        }
        closeDeleteConfirmModal();
        loadHistory();
      } catch (err) {
        alert('Deletion error: ' + err.message);
      } finally {
        btn.innerHTML = originalHtml;
        btn.disabled = false;
      }
    }

    const DOSSIER_TYPE_META = {
      complete_site_report: {
        hint: 'Best for one site: overview, key pages, offerings, trust signals, and takeaways.',
        cta: 'Generate complete report',
      },
      highlights_best: {
        hint: 'Highlights strengths, best pages, and why the site stands out.',
        cta: 'Generate highlights report',
      },
      market_research: {
        hint: 'Category, audience, positioning, and market opportunities from crawl evidence.',
        cta: 'Generate market research',
      },
      technical_audit: {
        hint: 'Information architecture, content clarity, and improvement ideas (from text crawl).',
        cta: 'Generate content audit',
      },
      competitive_matrix: {
        hint: 'Select multiple domains for side-by-side comparison tables.',
        cta: 'Generate competitive matrix',
      },
    };

    function syncDossierTypeUI() {
      const sel = document.getElementById('dossierReportType');
      const key = sel ? sel.value : 'complete_site_report';
      const meta = DOSSIER_TYPE_META[key] || DOSSIER_TYPE_META.complete_site_report;
      const hint = document.getElementById('dossierTypeHint');
      const cta = document.getElementById('btnGenerateDossierLabel');
      if (hint) hint.textContent = meta.hint;
      if (cta) cta.textContent = meta.cta;
    }

    function openDossierModal(preselectedDomain) {
      const container = document.getElementById('dossierDomainCheckboxes');
      if (!container) return;

      if (!storedDomainsList || storedDomainsList.length === 0) {
        container.innerHTML = '<span class="text-ds-muted text-xs italic">No domains stored yet. Crawl at least one website first.</span>';
      } else {
        let html = '';
        const singleDefault = Boolean(preselectedDomain);
        storedDomainsList.forEach((d) => {
          const isChecked = preselectedDomain ? (d.domain === preselectedDomain) : !singleDefault;
          html += `
            <label class="dossier-domain-chip">
              <input type="checkbox" name="dossierDomain" value="${d.domain}" ${isChecked ? 'checked' : ''}
                     onchange="updateDossierSelectedCount()">
              <span class="domain-name">${d.domain}</span>
              <span class="text-[11px] text-ds-muted">(${d.total_pages}p)</span>
            </label>
          `;
        });
        container.innerHTML = html;
      }

      const typeSel = document.getElementById('dossierReportType');
      if (typeSel) {
        typeSel.value = preselectedDomain ? 'complete_site_report' : typeSel.value;
      }
      syncDossierTypeUI();
      updateDossierSelectedCount();
      document.getElementById('dossierResultArea').classList.add('hidden');
      document.getElementById('dossierError').classList.add('hidden');
      document.getElementById('dossierLoading').classList.add('hidden');
      document.getElementById('dossierModal').classList.remove('hidden');
      syncBodyScrollLock();
    }

    function closeDossierModal() {
      if (dossierTimer) {
        dossierTimer.stop();
        dossierTimer = null;
      }
      document.getElementById('dossierModal').classList.add('hidden');
      syncBodyScrollLock();
    }

    function updateDossierSelectedCount() {
      const checked = document.querySelectorAll('input[name="dossierDomain"]:checked');
      const counter = document.getElementById('dossierSelectedCount');
      if (counter) counter.innerText = `${checked.length} domain(s) selected`;
    }

    async function runDossierGeneration() {
      const checked = Array.from(document.querySelectorAll('input[name="dossierDomain"]:checked')).map(cb => cb.value);
      if (checked.length === 0) {
        alert('Please select at least one domain to synthesize.');
        return;
      }

      const model = document.getElementById('dossierAiModel').value;
      const dossierType = document.getElementById('dossierReportType').value;
      const customFocus = document.getElementById('dossierCustomFocus').value.trim();

      const loading = document.getElementById('dossierLoading');
      const errBox = document.getElementById('dossierError');
      const resultArea = document.getElementById('dossierResultArea');
      const mdContent = document.getElementById('dossierMarkdownContent');
      const btn = document.getElementById('btnGenerateDossier');
      const modelDisplay = document.getElementById('dossierModelDisplay');

      if (modelDisplay) modelDisplay.innerText = model;
      loading.classList.remove('hidden');
      errBox.classList.add('hidden');
      resultArea.classList.add('hidden');
      btn.disabled = true;

      if (dossierTimer) dossierTimer.stop();
      dossierTimer = createLiveTimer('dossierStartTime', 'dossierElapsedTime');

      try {
        const resp = await fetch('/api/v1/dossier/generate', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            domains: checked,
            dossier_type: dossierType,
            model: model,
            custom_focus: customFocus || null
          })
        });

        if (!resp.ok) {
          const errData = await resp.json();
          throw new Error(errData.detail || 'Failed to generate dossier');
        }

        const data = await resp.json();
        currentDossierData = data;
        let timing = null;
        if (dossierTimer) {
          timing = dossierTimer.stop();
          dossierTimer = null;
        }
        loading.classList.add('hidden');
        resultArea.classList.remove('hidden');
        mdContent.innerText = data.markdown || 'No content generated.';

        const metaBadge = document.getElementById('dossierMetadataBadge');
        if (metaBadge) {
          const timeText = timing ? ` • ${timing.elapsedFormatted}` : '';
          metaBadge.innerText = `Generated via ${data.model_used}${timeText} • ${checked.length} domains • ${data.competitors_analyzed.length} competitors`;
        }
      } catch (err) {
        if (dossierTimer) {
          dossierTimer.stop();
          dossierTimer = null;
        }
        loading.classList.add('hidden');
        errBox.innerText = 'Dossier synthesis error: ' + err.message;
        errBox.classList.remove('hidden');
      } finally {
        btn.disabled = false;
      }
    }

    async function exportDossier(fmt) {
      const md = currentDossierData && (currentDossierData.markdown || currentDossierData.dossier_markdown);
      if (!md) return alert('Generate a dossier first.');

      const domains = currentDossierData.competitors_analyzed || currentDossierData.domains_analyzed || ['report'];
      const slug = domains.slice(0, 2).join('_').replace(/[^a-zA-Z0-9._-]/g, '_') || 'report';
      const ext = fmt === 'pdf' ? 'pdf' : 'md';

      try {
        const resp = await fetch('/api/v1/dossier/export-content', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            markdown: md,
            export_format: fmt,
            title: 'Website Intelligence Report',
          }),
        });
        if (!resp.ok) {
          let detail = resp.statusText;
          try {
            const errJson = await resp.json();
            detail = errJson.detail || detail;
          } catch (_) { /* ignore */ }
          throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
        }
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `dossier_${slug}.${ext}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      } catch (err) {
        alert('Export failed: ' + err.message);
      }
    }

    function copyDossierMarkdown() {
      if (!currentDossierData || !currentDossierData.markdown) return alert('No dossier content to copy');
      navigator.clipboard.writeText(currentDossierData.markdown).then(() => {
        alert('Dossier Markdown copied to clipboard!');
      });
    }

    function fillSearchDomain(domain) {
      const input = document.getElementById('searchDomain');
      if (input) {
        input.value = domain;
        input.scrollIntoView({ behavior: 'smooth', block: 'center' });
        input.focus();
      }
    }

    async function runSemanticSearch() {
      const q = document.getElementById('searchQuery').value.trim();
      if (!q) return alert('Please enter a search query');
      const domain = document.getElementById('searchDomain').value.trim();
      const container = document.getElementById('searchResultsContainer');

      const searchStart = new Date().toLocaleTimeString();
      container.innerHTML = `<div class="p-6 text-center space-y-1.5 text-ds-success"><div><i class="fa-solid fa-spinner fa-spin mr-2"></i>Searching vector embeddings...</div><div class="text-[11px] font-mono text-ds-muted">Started: ${searchStart}</div></div>`;

      try {
        let url = `/api/v1/search?q=${encodeURIComponent(q)}&limit=10`;
        if (domain) url += `&domain=${encodeURIComponent(domain)}`;
        const resp = await fetch(url);
        const results = await resp.json();

        if (!results || results.length === 0) {
          container.innerHTML = '<div class="p-6 text-center text-ds-muted">No matching pages found for this query in ChromaDB.</div>';
          return;
        }

        let html = '';
        results.forEach(m => {
          const matchPercent = Math.round((m.similarity || 0) * 100);
          const targetUrl = m.final_url || m.url;
          const safeUrl = encodeURIComponent(targetUrl);
          html += `
            <div class="p-4 bg-white rounded-xl border border-ds hover:border-[#757a60] transition shadow-sm">
              <div class="flex items-center justify-between gap-2 mb-1.5">
                <span class="text-xs font-bold text-[#1c1b1b] truncate">${m.title || 'Untitled'}</span>
                <span class="chip-export font-bold">${matchPercent}% Match</span>
              </div>
              <div class="text-[11px] text-ds-muted font-mono mb-2 truncate">${targetUrl}</div>
              <div class="text-xs text-[#1c1b1b] bg-[#f6f3f2] p-2.5 rounded-lg mb-3 leading-relaxed whitespace-pre-wrap border border-ds">${m.snippet}</div>
              <div class="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-ds">
                ${exportMenuHtml(safeUrl)}
                <button onclick="previewCachedPage('${safeUrl}')" class="btn-ghost px-2.5 py-1 rounded-lg text-[11px] font-medium">Preview</button>
              </div>
            </div>
          `;
        });
        container.innerHTML = html;
      } catch (err) {
        container.innerHTML = `<div class="p-6 text-center text-red-400">Search error: ${err.message}</div>`;
      }
    }

    function renderAskAnswer(raw) {
      const text = String(raw || '').replace(/\\r\\n/g, '\\n').trim();
      const lines = text.split('\\n');
      const blocks = [];
      let list = [];
      function flushList() {
        if (!list.length) return;
        blocks.push('<ol>' + list.map(item => '<li>' + item + '</li>').join('') + '</ol>');
        list = [];
      }
      lines.forEach(line => {
        const trimmed = line.trim();
        if (!trimmed) {
          flushList();
          return;
        }
        const numbered = trimmed.match(/^\\d+\\.\\s+(.*)$/);
        const inline = formatAskInline(numbered ? numbered[1] : trimmed);
        if (numbered) list.push(inline);
        else {
          flushList();
          blocks.push('<p>' + inline + '</p>');
        }
      });
      flushList();
      return blocks.join('') || '<p>' + formatAskInline(text) + '</p>';
    }

    function formatAskInline(value) {
      return escapeHtml(value)
        .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
        .replace(/\\[(\\d+)\\]/g, '<sup>[$1]</sup>');
    }

    async function runAskAi() {
      const q = document.getElementById('askQuestion').value.trim();
      if (!q) return alert('Please enter a question');

      const placeholder = document.getElementById('askPlaceholder');
      const loading = document.getElementById('askLoading');
      const content = document.getElementById('askContent');
      const answerText = document.getElementById('askAnswerText');
      const sourcesList = document.getElementById('askSourcesList');

      if (placeholder) placeholder.classList.add('hidden');
      if (content) content.classList.add('hidden');
      if (loading) loading.classList.remove('hidden');

      if (askTimer) askTimer.stop();
      askTimer = createLiveTimer('askStartTime', 'askElapsedTime');

      try {
        const resp = await fetch('/api/v1/ask', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ question: q, context_limit: 3 })
        });
        const data = await resp.json();

        if (askTimer) {
          askTimer.stop();
          askTimer = null;
        }
        if (loading) loading.classList.add('hidden');
        if (content) content.classList.remove('hidden');

        answerText.innerHTML = renderAskAnswer(data.answer || 'No answer generated.');
        const cacheBadge = document.getElementById('askCacheBadge');
        if (cacheBadge) {
          if (data.cached) {
            cacheBadge.textContent = 'Saved answer — matched a previous question, model was not called.';
            cacheBadge.classList.remove('hidden');
          } else {
            cacheBadge.textContent = '';
            cacheBadge.classList.add('hidden');
          }
        }

        if (data.sources && data.sources.length > 0) {
          let sHtml = '';
          data.sources.forEach(s => {
            sHtml += `<a href="${escapeHtml(s.url)}" target="_blank" rel="noopener noreferrer" class="chip-export">${escapeHtml(s.title || s.url)}</a>`;
          });
          sourcesList.innerHTML = sHtml;
        } else {
          sourcesList.innerHTML = '<span class="text-ds-muted text-xs">No direct citations available.</span>';
        }
      } catch (err) {
        if (askTimer) {
          askTimer.stop();
          askTimer = null;
        }
        if (loading) loading.classList.add('hidden');
        if (content) content.classList.remove('hidden');
        answerText.innerText = 'Error calling Ask AI: ' + err.message;
        sourcesList.innerHTML = '';
      }
    }

    // Auto-load history count and custom presets on initial page load
    window.addEventListener('DOMContentLoaded', () => {
      loadHistory();
      loadCustomPresets();
      updateSchedulesBadgeCount();
      applyCrawlPreset('rag_ingest');
      syncSlidersFromInputs();
      syncGuardrailsFromInputs();
      updateEngineQueueLabel(0, document.getElementById('maxPages').value);
      fetch('/health').then(r => r.json()).then(d => {
        const badge = document.getElementById('engineVersionBadge');
        if (badge && d.version) badge.innerText = 'ETHIC ENGINE V' + d.version;
      }).catch(() => {});
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeTopModal();
    });
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
async def dashboard():
    """Embedded interactive Web UI dashboard."""
    return (
        DASHBOARD_HTML
        .replace("__BOT_VERSION__", settings.bot_version)
        .replace("__GOOGLE_FONTS__", generate_google_fonts_link())
        .replace("__ROOT_THEME_CSS__", generate_root_css(DEFAULT_THEME_ID))
        .replace("__THEMES_JSON__", get_themes_json())
    )


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Favicon endpoint returning 204 No Content to keep logs clean."""
    return Response(status_code=204)
