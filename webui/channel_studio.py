"""
channel_studio.py
=================
Channel & Distribution Studio — modulo Streamlit per MoneyPrinter Turbo.
Funzionalità:
  • Canali multi-piattaforma con apertura e visualizzazione video live
  • Esploratore canale dedicato con riproduzione video/audio e gestione stati
  • Video Library globale con filtri per canale e ricerca
  • Pubblicazione multi-piattaforma con varianti copy intelligenti
  • Google Drive (sincronizzazione reale)
  • Paperclip (Block Buzz) & Hermes Agent AI
"""
from __future__ import annotations

import os
import json
import pathlib
import requests
from typing import Any, Dict, List, Optional

import streamlit as st

from app.services import channel_manager, gdrive_service

# ── Constants
PLATFORM_ICONS: Dict[str, str] = {
    "YouTube Shorts": "▶️",
    "YouTube": "📺",
    "Instagram Reels": "📸",
    "TikTok": "🎵",
    "Facebook Reels": "👥",
}

STATUS_CONFIG: Dict[str, Dict[str, str]] = {
    "draft":     {"label": "🟡 In Revisione", "color": "#f59e0b", "bg": "#f59e0b1a", "border": "#f59e0b44"},
    "approved":  {"label": "🟢 Approvato",    "color": "#10b981", "bg": "#10b9811a", "border": "#10b98144"},
    "published": {"label": "🔵 Pubblicato",   "color": "#3b82f6", "bg": "#3b82f61a", "border": "#3b82f644"},
    "rejected":  {"label": "🔴 Rifiutato",    "color": "#ef4444", "bg": "#ef44441a", "border": "#ef444444"},
}

_PAPERCLIP_BASE = os.environ.get("PAPERCLIP_API_URL", "http://127.0.0.1:3102")
_HERMES_BASE    = os.environ.get("HERMES_BACKEND_URL", "http://127.0.0.1:59433")
_HERMES_KEY     = os.environ.get("API_SERVER_KEY", "")

_WEBUI_DIR  = pathlib.Path(__file__).parent
_PROJ_ROOT  = _WEBUI_DIR.parent
_TOKEN_PATH = _PROJ_ROOT / "app" / "services" / "gdrive_token.json"
_CREDS_PATH = _PROJ_ROOT / "app" / "services" / "gdrive_credentials.json"


def _gdrive_ok() -> bool:
    cfg = gdrive_service.get_gdrive_config()
    return (
        _TOKEN_PATH.exists()
        and cfg.get("connected", False) is True
        and not cfg.get("_mock", False)
    )


def _pp_create_task(title: str, desc: str, tags=None) -> Optional[str]:
    try:
        r = requests.post(f"{_PAPERCLIP_BASE}/api/tasks",
            json={"title": title, "description": desc, "tags": tags or ["moneyprinter"]},
            timeout=4)
        return r.json().get("id") if r.ok else None
    except Exception:
        return None


def _pp_get_tasks(tag="moneyprinter") -> List[Dict]:
    try:
        r = requests.get(f"{_PAPERCLIP_BASE}/api/tasks", params={"tag": tag}, timeout=4)
        return r.json().get("tasks", []) if r.ok else []
    except Exception:
        return []


def _hermes_session(cwd: str, prompt: str = "") -> Optional[str]:
    try:
        h = {"Authorization": f"Bearer {_HERMES_KEY}"} if _HERMES_KEY else {}
        r = requests.post(f"{_HERMES_BASE}/api/sessions",
            json={"cwd": cwd, "initial_message": prompt},
            headers=h, timeout=5)
        return r.json().get("session_id") if r.ok else None
    except Exception:
        return None


def _badge_cls(platform: str) -> str:
    if "YouTube" in platform: return "yt-badge"
    if "Instagram" in platform: return "ig-badge"
    if "TikTok" in platform: return "tt-badge"
    return "fb-badge"


def _inject_css() -> None:
    st.markdown("""<style>
.stat-card {
  background: linear-gradient(135deg, #1e293b, #0f172a);
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 16px 12px;
  text-align: center;
}
.stat-card .val {
  font-size: 1.6rem;
  font-weight: 800;
  color: #a5b4fc;
}
.stat-card .lbl {
  font-size: 0.72rem;
  color: #94a3b8;
  margin-top: 4px;
}
.ch-sq-card {
  background: linear-gradient(145deg, #1e293b, #0f172a);
  border: 1px solid #334155;
  border-radius: 16px;
  padding: 18px 16px;
  min-height: 200px;
  transition: all .2s ease-in-out;
  margin-bottom: 8px;
}
.ch-sq-card:hover {
  border-color: #6366f1;
  box-shadow: 0 0 20px rgba(99,102,241,.2);
}
.ch-sq-card-active {
  border: 2px solid #818cf8 !important;
  box-shadow: 0 0 25px rgba(129,140,248,.35) !important;
  background: linear-gradient(145deg, #272744, #121829) !important;
}
.ch-sq-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #f8fafc;
  margin-bottom: 6px;
}
.ch-sq-plat {
  font-size: .72rem;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 20px;
  display: inline-block;
  margin-bottom: 6px;
}
.ch-sq-niche {
  color: #a5b4fc;
  font-size: .82rem;
  font-weight: 500;
  margin-bottom: 4px;
}
.ch-sq-meta {
  font-size: .78rem;
  color: #64748b;
  line-height: 1.5;
}
.ch-sq-stat {
  display: flex;
  gap: 8px;
  font-size: .73rem;
  color: #94a3b8;
  margin-top: 10px;
  flex-wrap: wrap;
}
.ch-sq-stat span {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 20px;
  padding: 2px 8px;
}
.yt-badge { background: #ff000022; color: #ff4444; border: 1px solid #ff444455; }
.ig-badge { background: #e1306c22; color: #e1306c; border: 1px solid #e1306c55; }
.tt-badge { background: #00f2ea22; color: #00c8c0; border: 1px solid #00c8c055; }
.fb-badge { background: #1877f222; color: #4096ff; border: 1px solid #4096ff55; }

.vid-card {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  transition: border-color .2s;
}
.vid-card:hover {
  border-color: #4f46e5;
}
.int-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #312e81;
  border: 1px solid #4f46e5;
  border-radius: 20px;
  padding: 4px 12px;
  font-size: .75rem;
  color: #c7d2fe;
  font-weight: 600;
}
.channel-box-header {
  background: linear-gradient(135deg, #1e1b4b, #172554);
  border: 1px solid #4338ca;
  border-radius: 16px;
  padding: 18px 22px;
  margin: 16px 0 20px 0;
}
</style>""", unsafe_allow_html=True)


def _stat_card(col, val, lbl):
    col.markdown(f'<div class="stat-card"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>',
                 unsafe_allow_html=True)


def render_video_item(vid: Dict[str, Any], chnm: Dict[str, str], chs_all: List[Dict[str, Any]], gdrive_connected: bool, prefix: str = "main") -> None:
    """Renders a single video card with inline player, status editor, drive sync, and actions."""
    vid_id = vid["id"]
    sc = STATUS_CONFIG.get(vid.get("status", "draft"), STATUS_CONFIG["draft"])
    vch = chnm.get(vid.get("channel_id", ""), "—")
    fp = vid.get("file_path", "")
    fe = os.path.exists(fp) if fp else False
    smb = vid.get("size_mb", "?")
    is_mp4 = fp.endswith(".mp4") if fp else False
    is_audio = fp.endswith((".mp3", ".wav")) if fp else False

    st.markdown(f"""<div class="vid-card">
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
        <span style="font-size:1.8rem;">{'🎬' if is_mp4 else ('🎵' if is_audio else '📄')}</span>
        <div style="flex:1;min-width:200px;">
          <div style="font-size:1rem;font-weight:700;color:#f8fafc;">{vid.get("title", "Video")}</div>
          <div style="font-size:.76rem;color:#94a3b8;margin-top:2px;">
            📡 <b>{vch}</b> · 📦 {smb} MB · 🕒 {vid.get("created_at", "?")} · 🏷️ <code>{vid.get("file_name", "file")}</code>
          </div>
        </div>
        <span style="background:{sc['bg']};color:{sc['color']};border:1px solid {sc['border']};padding:4px 14px;border-radius:20px;font-size:.75rem;font-weight:700;">
          {sc['label']}
        </span>
      </div>
    </div>""", unsafe_allow_html=True)

    # Media Playback
    if fe:
        if is_mp4:
            st.video(fp)
        elif is_audio:
            st.caption("🎵 Audio renderizzato (video in preparazione):")
            st.audio(fp)
    else:
        st.warning("⚠️ File multimediale non trovato sul percorso locale specificato.")

    # Details & Controls
    with st.expander(f"⚙️ Gestione, Script & Azioni — {vid.get('title','')[:40]}", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            ck = {c["name"]: c["id"] for c in chs_all}
            cnm = chnm.get(vid.get("channel_id", ""), "")
            cl = list(ck.keys())
            def_idx = cl.index(cnm) if cnm in cl else 0
            nca = st.selectbox("📡 Assegna a Canale", cl, index=def_idx, key=f"{prefix}_ch_{vid_id}")
            if st.button("💾 Salva Canale", key=f"{prefix}_sv_{vid_id}", use_container_width=True):
                channel_manager.assign_video_channel(vid_id, ck[nca])
                st.success(f"Assegnato a '{nca}'!")
                st.rerun()

        with c2:
            so = ["draft", "approved", "published", "rejected"]
            labels_map = {"draft": "🟡 In Revisione", "approved": "🟢 Approvato", "published": "🔵 Pubblicato", "rejected": "🔴 Rifiutato"}
            cur_st = vid.get("status", "draft")
            ns = st.selectbox("🏷️ Stato Video", so, format_func=lambda x: labels_map.get(x, x),
                              index=so.index(cur_st) if cur_st in so else 0, key=f"{prefix}_st_{vid_id}")
            nt = st.text_input("📝 Note Revisione", vid.get("review_note", ""), key=f"{prefix}_nt_{vid_id}")
            if st.button("✅ Aggiorna Stato", key=f"{prefix}_as_{vid_id}", use_container_width=True):
                channel_manager.update_video_status(vid_id, ns, nt)
                if ns == "approved":
                    _pp_create_task(f"Pubblica: {vid.get('title','Video')}", "Video approvato — pronto per pubblicazione.", ["moneyprinter", "publish"])
                st.success("Stato aggiornato!")
                st.rerun()

        with c3:
            if fe and is_mp4:
                with open(fp, "rb") as vf:
                    st.download_button("⬇️ Scarica MP4", vf, file_name=vid.get("file_name", "video.mp4"),
                                       mime="video/mp4", use_container_width=True, key=f"{prefix}_dl_{vid_id}")
            elif fe and is_audio:
                with open(fp, "rb") as vf:
                    st.download_button("⬇️ Scarica Audio", vf, file_name=vid.get("file_name", "audio.mp3"),
                                       mime="audio/mp3", use_container_width=True, key=f"{prefix}_dla_{vid_id}")

            gl = "✅ Sincronizzato su Drive" if vid.get("gdrive_synced") else "☁️ Salva su Drive"
            if st.button(gl, key=f"{prefix}_gd_{vid_id}", use_container_width=True):
                if not gdrive_connected:
                    st.error("❌ Drive non connesso → Configura nel tab 'Google Drive'")
                elif fe:
                    co = next((c for c in chs_all if c["id"] == vid.get("channel_id")), {})
                    res = gdrive_service.upload_video_to_gdrive(fp, vid["title"], co.get("name", "Generale"))
                    channel_manager.update_video_gdrive(vid_id, res)
                    st.success(f"✅ Drive: {res.get('link','')}" if res.get("success") else f"❌ {res.get('error')}")
                    st.rerun()

            if st.button("🗑️ Elimina Video", key=f"{prefix}_dv_{vid_id}", use_container_width=True):
                channel_manager.delete_video(vid_id)
                st.success("Video eliminato dal catalogo.")
                st.rerun()

        if vid.get("script"):
            st.markdown("**📄 Script Vocale / Testo Generato:**")
            st.text_area("Script", vid["script"], height=90, disabled=True, key=f"{prefix}_sc_{vid_id}", label_visibility="collapsed")


def render() -> None:
    """Entry point — chiamato da Main.py."""
    _inject_css()

    # Scan storage once per session or on manual refresh
    if not st.session_state.get("_studio_storage_scanned", False):
        channel_manager.scan_storage_for_new_videos()
        st.session_state["_studio_storage_scanned"] = True

    stats = channel_manager.get_catalog_stats()
    gdrive_connected = _gdrive_ok()
    gdrive_cfg = gdrive_service.get_gdrive_config()

    # Header
    gc = "#10b981" if gdrive_connected else "#f59e0b"
    gt = "🟢 Drive connesso" if gdrive_connected else "🟡 Drive da configurare"
    st.markdown(f"""<div style="background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);
      border-radius:16px;padding:22px 28px;margin-bottom:18px;
      display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
      <div>
        <div style="font-size:1.6rem;font-weight:800;color:#fff;margin-bottom:4px;">
          📡 Channel &amp; Distribution Studio
        </div>
        <div style="color:rgba(255,255,255,.7);font-size:.88rem;">
          Gestione canali · Video Library per canale · Multi-Piattaforma · Hermes &amp; Paperclip
        </div>
      </div>
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
        <span style="background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.2);
          border-radius:20px;padding:5px 14px;color:{gc};font-size:.78rem;font-weight:600;">
          ☁️ {gdrive_cfg.get("account","mrvinxsrl@gmail.com")} · {gt}
        </span>
        <span class="int-pill">🤖 Hermes Agent</span>
        <span class="int-pill">📎 Paperclip</span>
      </div>
    </div>""", unsafe_allow_html=True)

    # Stats Summary
    by_st = stats["by_status"]
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    _stat_card(c1, stats["total_channels"],   "Canali Totali")
    _stat_card(c2, stats["active_channels"],  "Canali Attivi")
    _stat_card(c3, stats["total_videos"],     "Video Totali")
    _stat_card(c4, by_st.get("draft", 0),     "🟡 In Revisione")
    _stat_card(c5, by_st.get("approved", 0),  "🟢 Approvati")
    _stat_card(c6, by_st.get("published", 0), "🔵 Pubblicati")
    st.markdown("<br>", unsafe_allow_html=True)

    # Navigation Tabs
    tab_ch, tab_lib, tab_pub, tab_gd, tab_int = st.tabs([
        "📡 I Tuoi Canali & Video", "🎬 Video Library Globale", "🚀 Pubblicazione Multi-Piattaforma", "☁️ Google Drive", "🔗 Integrazioni"
    ])

    # Preload channels
    channels = channel_manager.get_channels()
    chs_all = channels
    chnm = {c["id"]: c["name"] for c in chs_all}
    selected_ch_id = st.session_state.get("_selected_channel_id", channels[0]["id"] if channels else None)

    # ═════════════════════════════════════════════════════════════════════════
    # TAB 1 — CANALI & VIDEO SPECIFICI
    # ═════════════════════════════════════════════════════════════════════════
    with tab_ch:
        if not channels:
            st.info("📭 Nessun canale configurato. Aggiungine uno qui sotto!")
        else:
            st.markdown("### 📡 Seleziona o Apri un Canale per Visualizzarne i Video")

            # Quick Selector Pills
            st.markdown("**Filtro Rapido Canale:**")
            pills = st.columns(len(channels) + 1)
            with pills[0]:
                is_all = (selected_ch_id is None or selected_ch_id == "all")
                if st.button("🌐 Tutti i Canali", key="pill_all", type="primary" if is_all else "secondary", use_container_width=True):
                    st.session_state["_selected_channel_id"] = "all"
                    st.rerun()

            for idx, ch in enumerate(channels):
                with pills[idx + 1]:
                    is_active = (selected_ch_id == ch["id"])
                    v_count = len(channel_manager.get_videos(channel_id=ch["id"]))
                    icon = PLATFORM_ICONS.get(ch["platform"], "📱")
                    short_name = ch["name"].replace("🚀 ", "").replace("✨ ", "").replace("🎯 ", "").replace("📱 ", "")[:14]
                    if st.button(f"{icon} {short_name} ({v_count})", key=f"pill_{ch['id']}", type="primary" if is_active else "secondary", use_container_width=True):
                        st.session_state["_selected_channel_id"] = ch["id"]
                        st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)

            # 3-Column Channel Grid
            COLS = 3
            for rs in range(0, len(channels), COLS):
                row = channels[rs:rs+COLS]
                gcols = st.columns(COLS)
                for ci, ch in enumerate(row):
                    with gcols[ci]:
                        active = ch.get("active", True)
                        icon = PLATFORM_ICONS.get(ch["platform"], "📱")
                        badge = _badge_cls(ch["platform"])
                        ch_videos = channel_manager.get_videos(channel_id=ch["id"])
                        tv = len(ch_videos)
                        dv = len([v for v in ch_videos if v.get("status") == "draft"])
                        pv = len([v for v in ch_videos if v.get("status") == "published"])
                        is_sel = (selected_ch_id == ch["id"])

                        card_cls = "ch-sq-card ch-sq-card-active" if is_sel else "ch-sq-card"

                        st.markdown(f"""<div class="{card_cls}">
                          <div class="ch-sq-title">{"🟢" if active else "⏸️"} {ch["name"]}</div>
                          <span class="ch-sq-plat {badge}">{icon} {ch["platform"]}</span>
                          <div class="ch-sq-niche">🎯 <b>Nicchia:</b> {ch["niche"]}</div>
                          <div class="ch-sq-meta">🔗 <b>Account:</b> {ch.get("platform_account","—")}</div>
                          <div class="ch-sq-stat">
                            <span>📹 <b>{tv}</b> Video</span>
                            <span>🟡 <b>{dv}</b> Bozze</span>
                            <span>🔵 <b>{pv}</b> Pubblicati</span>
                          </div>
                        </div>""", unsafe_allow_html=True)

                        # Primary Open Channel Action
                        btn_label = f"📂 APRI VIDEO ({tv})" if not is_sel else f"✅ CANALE APERTO ({tv})"
                        if st.button(btn_label, key=f"open_ch_{ch['id']}", type="primary" if is_sel else "secondary", use_container_width=True):
                            st.session_state["_selected_channel_id"] = ch["id"]
                            st.rerun()

                        # Secondary controls row
                        b1, b2 = st.columns([1, 1])
                        with b1:
                            if st.button("⏸️ Pausa" if active else "▶️ Attiva", key=f"tog_{ch['id']}", use_container_width=True):
                                channel_manager.toggle_channel_active(ch["id"])
                                st.rerun()
                        with b2:
                            if st.button("🗑️ Elimina", key=f"del_{ch['id']}", use_container_width=True):
                                channel_manager.delete_channel(ch["id"])
                                if selected_ch_id == ch["id"]:
                                    st.session_state["_selected_channel_id"] = None
                                st.rerun()

                        # In-card expander for direct video preview
                        with st.expander(f"👁️ Anteprima Rapida Video ({tv})", expanded=False):
                            if not ch_videos:
                                st.caption("Nessun video associato.")
                            else:
                                for v in ch_videos:
                                    st.markdown(f"• **{v.get('title','Video')}** ({v.get('status','draft')})")
                                    v_fp = v.get("file_path", "")
                                    if v_fp and os.path.exists(v_fp) and v_fp.endswith(".mp4"):
                                        st.video(v_fp)

            # ═════════════════════════════════════════════════════════════════
            # DEDICATED CHANNEL VIDEO WORKSPACE (Below Cards)
            # ═════════════════════════════════════════════════════════════════
            st.markdown("---")
            active_channel_obj = next((c for c in channels if c["id"] == selected_ch_id), None) if (selected_ch_id and selected_ch_id != "all") else None

            if active_channel_obj:
                ch_name = active_channel_obj["name"]
                ch_plat = active_channel_obj["platform"]
                ch_icon = PLATFORM_ICONS.get(ch_plat, "📱")
                ch_strat = channel_manager.PLATFORM_STRATEGIES.get(ch_plat, {})
                channel_videos = channel_manager.get_videos(channel_id=active_channel_obj["id"])

                st.markdown(f"""<div class="channel-box-header">
                  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">
                    <div>
                      <div style="font-size:1.35rem;font-weight:800;color:#f8fafc;">
                        {ch_icon} {ch_name} — Spazio Video &amp; Distribuzione
                      </div>
                      <div style="font-size:.85rem;color:#c7d2fe;margin-top:4px;">
                        🎯 <b>Nicchia:</b> {active_channel_obj['niche']} · 🔗 <b>Account:</b> {active_channel_obj.get('platform_account','—')} · 📐 <b>Formato:</b> {ch_strat.get('aspect','9:16')}
                      </div>
                    </div>
                    <div style="background:#1e1b4b;border:1px solid #6366f1;border-radius:12px;padding:8px 16px;text-align:right;">
                      <div style="font-size:1.1rem;font-weight:800;color:#38bdf8;">{len(channel_videos)} VIDEO</div>
                      <div style="font-size:.72rem;color:#94a3b8;">Catalogo canale</div>
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)

                w1, w2 = st.columns([3, 1])
                with w1:
                    st.markdown(f"#### 🎬 Video Associati a **{ch_name}** ({len(channel_videos)})")
                with w2:
                    if st.button("❌ Mostra Tutti i Canali", key="reset_ch_view", use_container_width=True):
                        st.session_state["_selected_channel_id"] = "all"
                        st.rerun()

                if not channel_videos:
                    st.info(f"📭 Nessun video attualmente associato al canale **{ch_name}**.")
                    all_existing_videos = channel_manager.get_videos()
                    if all_existing_videos:
                        with st.expander("➕ Assegna un video esistente dallo storage a questo canale", expanded=True):
                            v_opts = {f"{v.get('title','Video')} (da {chnm.get(v.get('channel_id',''),'altro')})": v["id"] for v in all_existing_videos}
                            sel_v_label = st.selectbox("Seleziona video da collegare:", list(v_opts.keys()), key=f"bind_v_{active_channel_obj['id']}")
                            if st.button(f"🔗 Collega Video a {ch_name}", key=f"do_bind_{active_channel_obj['id']}", type="primary"):
                                channel_manager.assign_video_channel(v_opts[sel_v_label], active_channel_obj["id"])
                                st.success(f"Video collegato con successo a {ch_name}!")
                                st.rerun()
                else:
                    for vid in channel_videos:
                        render_video_item(vid, chnm, chs_all, gdrive_connected, prefix=f"ch_{active_channel_obj['id']}")

            else:
                # Viewing All Channels Videos
                all_vids = channel_manager.get_videos()
                st.markdown(f"#### 🎬 Tutti i Video di Tutti i Canali ({len(all_vids)})")
                if not all_vids:
                    st.info("Nessun video trovato in storage. Crea o genera un nuovo video!")
                else:
                    for vid in all_vids:
                        render_video_item(vid, chnm, chs_all, gdrive_connected, prefix="all_view")

        # Add Channel Expander
        st.markdown("---")
        with st.expander("➕ Aggiungi Nuovo Canale"):
            with st.form("add_ch_form", clear_on_submit=True):
                a1, a2 = st.columns(2)
                with a1:
                    nm = st.text_input("Nome Canale (es. 🚀 Tech AI Trends)")
                    pl = st.selectbox("Piattaforma Target", channel_manager.PLATFORMS)
                with a2:
                    ni = st.text_input("Nicchia Contenuto (es. Scienza & Spazio, Psicologia, Tech)")
                    ac = st.text_input("Account Social / URL (es. @tech.ai.it)")
                if pl:
                    s = channel_manager.PLATFORM_STRATEGIES.get(pl, {})
                    st.info(f"**Strategia {pl}**: {s.get('style_note','—')}\n\n**Formato**: {s.get('aspect','9:16')} · **Hashtag**: {s.get('hashtag_style','—')}")
                if st.form_submit_button("✅ Crea e Attiva Canale") and nm:
                    new_ch = channel_manager.add_channel(name=nm, platform=pl, niche=ni, platform_account=ac)
                    st.session_state["_selected_channel_id"] = new_ch["id"]
                    st.success(f"Canale '{nm}' creato con successo!")
                    st.rerun()

    # ═════════════════════════════════════════════════════════════════════════
    # TAB 2 — VIDEO LIBRARY GLOBALE
    # ═════════════════════════════════════════════════════════════════════════
    with tab_lib:
        st.markdown("### 🎬 Video Library Globale & Filtri Avanzati")
        ch_opt = {"Tutti i canali": "all"} | {c["name"]: c["id"] for c in chs_all}

        # Match dropdown index to currently selected channel if any
        def_label = "Tutti i canali"
        if selected_ch_id and selected_ch_id != "all":
            for n, cid in ch_opt.items():
                if cid == selected_ch_id:
                    def_label = n
                    break

        lc1, lc2, lc3, lc4 = st.columns([3, 2, 3, 1])
        with lc1:
            sel_chn = st.selectbox("Filtra per Canale", list(ch_opt.keys()),
                                   index=list(ch_opt.keys()).index(def_label), key="lib_ch_select")
            sel_ch_id = ch_opt[sel_chn]
        with lc2:
            sel_st = st.selectbox("Filtra per Stato",
                                  ["Tutti", "🟡 In Revisione", "🟢 Approvato", "🔵 Pubblicato", "🔴 Rifiutato"],
                                  key="lib_st_select")
            sm = {"Tutti": "all", "🟡 In Revisione": "draft", "🟢 Approvato": "approved", "🔵 Pubblicato": "published", "🔴 Rifiutato": "rejected"}
            sel_st_v = sm[sel_st]
        with lc3:
            search_query = st.text_input("🔍 Cerca nel titolo o script", "", key="lib_search")
        with lc4:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            if st.button("🔄 Ricarica", use_container_width=True, key="ref_lib_btn"):
                channel_manager.scan_storage_for_new_videos()
                st.rerun()

        lib_vids = channel_manager.get_videos(channel_id=sel_ch_id, status=sel_st_v)
        if search_query.strip():
            sq = search_query.strip().lower()
            lib_vids = [v for v in lib_vids if sq in v.get("title", "").lower() or sq in v.get("script", "").lower()]

        if not lib_vids:
            st.info("📂 Nessun video trovato per i criteri selezionati.")
        else:
            st.caption(f"Trovati **{len(lib_vids)}** video corrispondenti.")
            for vid in lib_vids:
                render_video_item(vid, chnm, chs_all, gdrive_connected, prefix="global_lib")

    # ═════════════════════════════════════════════════════════════════════════
    # TAB 3 — PUBBLICAZIONE MULTI-PIATTAFORMA
    # ═════════════════════════════════════════════════════════════════════════
    with tab_pub:
        st.markdown("### 🚀 Pubblicazione Multi-Piattaforma con Varianti AI")
        pub_vids = channel_manager.get_videos(status="approved") + channel_manager.get_videos(status="draft")
        if not pub_vids:
            st.info("Nessun video disponibile per la pubblicazione. Genera o approva un video!")
        else:
            vm = {f"{v['title']} ({chnm.get(v.get('channel_id',''),'—')})": v["id"] for v in pub_vids}
            st_title = st.selectbox("📹 Seleziona Video da Pubblicare", list(vm.keys()), key="pub_v_select")
            sv_id = vm[st_title]
            sv = channel_manager.get_video(sv_id)
            act_chs = channel_manager.get_channels(active_only=True)

            if sv:
                fp = sv.get("file_path", "")
                fe = os.path.exists(fp) if fp else False
                p1, p2 = st.columns([1, 2])
                with p1:
                    if fe and fp.endswith(".mp4"):
                        st.video(fp)
                    elif fe and fp.endswith((".mp3", ".wav")):
                        st.audio(fp)
                    else:
                        st.warning("File non trovato")
                with p2:
                    scc = STATUS_CONFIG.get(sv.get("status", "draft"), {})
                    st.markdown(f"**Titolo:** {sv.get('title','—')}")
                    st.markdown(f"**Stato:** {scc.get('label','?')} · **Dim:** {sv.get('size_mb','?')} MB")
                    st.markdown(f"**Creato il:** {sv.get('created_at','?')}")
                    st.markdown(f"**Canale Assegnato:** {chnm.get(sv.get('channel_id',''),'—')}")

                st.markdown("---")
                st.markdown("#### 🎯 Varianti Personalizzate per Ogni Piattaforma Attiva")
                st.caption("Ogni canale riceve copy, hashtag e formattazione ottimizzati per massimizzare la retention.")

                for ch in act_chs:
                    var = channel_manager.get_platform_variations(sv, ch)
                    icon = PLATFORM_ICONS.get(ch["platform"], "📱")
                    pubs = sv.get("publications", {})
                    already = ch["platform"] in pubs

                    with st.expander(f"{icon} {ch['name']} — {ch['platform']}" + (" ✅ (Pubblicato)" if already else " ⏳ (Pronto)"),
                                     expanded=not already):
                        if already:
                            pd = pubs[ch["platform"]]
                            st.success(f"✅ Pubblicato il {pd.get('published_at','?')}")
                            if pd.get("url"):
                                st.markdown(f"[🔗 Apri Link Post]({pd['url']})")
                        else:
                            strat = channel_manager.PLATFORM_STRATEGIES.get(ch["platform"], {})
                            st.caption(f"📐 {strat.get('aspect','9:16')} · ⏱ {strat.get('max_duration_s',60)}s · 🎯 {strat.get('content_angle','—')}")
                            cp1, cp2 = st.columns(2)
                            with cp1:
                                pt = st.text_input("📌 Titolo Ottimizzato", var.get("title", sv.get("title", "")), key=f"pt_{ch['id']}_{sv_id}")
                                ph = st.text_input("# Hashtag Suggeriti", var.get("hashtags", ""), key=f"ph_{ch['id']}_{sv_id}")
                            with cp2:
                                pd2 = st.text_area("📝 Descrizione / Caption", var.get("description", ""), height=90, key=f"pd_{ch['id']}_{sv_id}")

                            bb1, bb2 = st.columns(2)
                            with bb1:
                                if st.button(f"📤 Segna Pubblicato su {ch['platform']}", key=f"pub_{ch['id']}_{sv_id}", type="primary", use_container_width=True):
                                    channel_manager.update_video_publish_info(sv_id, ch["platform"], {
                                        "title": pt, "description": pd2, "hashtags": ph, "channel": ch["name"], "url": ""
                                    })
                                    channel_manager.update_video_status(sv_id, "published")
                                    st.success(f"✅ Pubblicazione registrata per {ch['name']}!")
                                    st.rerun()
                            with bb2:
                                if fe and fp.endswith(".mp4"):
                                    with open(fp, "rb") as vf:
                                        st.download_button(f"⬇️ Scarica MP4 per {ch['platform']}", vf,
                                                           file_name=f"{ch['id']}_{sv.get('file_name','video.mp4')}",
                                                           mime="video/mp4", use_container_width=True, key=f"dlp_{ch['id']}_{sv_id}")

    # ═════════════════════════════════════════════════════════════════════════
    # TAB 4 — GOOGLE DRIVE STORAGE
    # ═════════════════════════════════════════════════════════════════════════
    with tab_gd:
        st.markdown("### ☁️ Sincronizzazione Google Drive Cloud")
        if not gdrive_connected:
            st.warning("⚠️ **Google Drive non connesso.**\n\n"
                       "1. Salva il file credenziali come `app/services/gdrive_credentials.json`\n"
                       "2. Clicca **Autentica** per completare l'associazione OAuth reale.")
            if _CREDS_PATH.exists():
                st.info("✅ `gdrive_credentials.json` rilevato. Clicca sul pulsante qui sotto per autenticare:")
                if st.button("🔐 Autentica con Google Drive", type="primary", use_container_width=True):
                    try:
                        res = gdrive_service.authenticate_gdrive()
                        if res.get("success"):
                            st.success("✅ Connessione a Google Drive stabilita con successo!")
                            st.rerun()
                        else:
                            st.error(f"Errore autenticazione: {res.get('error')}")
                    except Exception as e:
                        st.error(f"Eccezione durante l'autenticazione: {e}")
            else:
                cf = st.file_uploader("Carica credentials.json di Google Cloud", type=["json"], key="gdc_uploader")
                if cf:
                    _CREDS_PATH.write_bytes(cf.read())
                    st.success("✅ File credentials.json salvato!")
                    st.rerun()
        else:
            gc2 = gdrive_service.get_gdrive_config()
            umb = gc2.get("storage_quota_used_mb", 0)
            tgb = gc2.get("total_quota_gb", 15)
            up = round(umb / max(tgb * 1024, 1) * 100, 1)

            st.markdown(f"""<div style="background:#1e293b;border:1px solid #334155;border-radius:14px;padding:20px;margin-bottom:16px;">
              <div style="display:flex;align-items:center;gap:14px;margin-bottom:12px;">
                <span style="font-size:2rem;">☁️</span>
                <div>
                  <div style="font-size:1.05rem;font-weight:700;color:#f8fafc;">Google Drive Cloud Storage</div>
                  <div style="font-size:.82rem;color:#94a3b8;">Account collegato: <b>{gc2.get("account","mrvinxsrl@gmail.com")}</b></div>
                </div>
                <div style="margin-left:auto;background:#10b98122;color:#10b981;padding:4px 14px;border-radius:20px;font-size:.78rem;font-weight:700;">● Connesso</div>
              </div>
              <div style="background:#0f172a;border-radius:8px;padding:12px;">
                <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                  <span style="font-size:.8rem;color:#94a3b8;">Spazio Utilizzato</span>
                  <span style="font-size:.8rem;color:#e2e8f0;font-weight:600;">{umb:.1f} MB / {tgb} GB ({up}%)</span>
                </div>
                <div style="background:#1e293b;border-radius:4px;height:8px;overflow:hidden;">
                  <div style="width:{min(up,100)}%;height:100%;background:linear-gradient(90deg,#6366f1,#8b5cf6);"></div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

            dc1, dc2 = st.columns(2)
            with dc1:
                avs = channel_manager.get_videos()
                uns = [v for v in avs if not v.get("gdrive_synced") and os.path.exists(v.get("file_path", ""))]
                st.metric("Video Non Sincronizzati", len(uns))
                if uns and st.button(f"☁️ Sincronizza Tutti ({len(uns)}) su Drive", type="primary", use_container_width=True):
                    cm2 = {c["id"]: c["name"] for c in channel_manager.get_channels()}
                    pr = st.progress(0)
                    syn = 0
                    for i, v in enumerate(uns):
                        res = gdrive_service.upload_video_to_gdrive(v["file_path"], v["title"], cm2.get(v.get("channel_id", ""), "Generale"))
                        channel_manager.update_video_gdrive(v["id"], res)
                        if res.get("success"):
                            syn += 1
                        pr.progress((i + 1) / len(uns))
                    st.success(f"✅ {syn}/{len(uns)} video sincronizzati con successo!")
                    st.rerun()

            with dc2:
                svs = [v for v in channel_manager.get_videos() if v.get("gdrive_synced")]
                st.metric("Video su Google Drive", len(svs))
                for v in svs[:5]:
                    lk = v.get("gdrive_link", "")
                    lb = v["title"][:40]
                    st.markdown(f"[{lb}...]({lk})" if lk else f"✅ {lb}...")
                if len(svs) > 5:
                    st.caption(f"... e altri {len(svs)-5} video archiviati")

    # ═════════════════════════════════════════════════════════════════════════
    # TAB 5 — INTEGRAZIONI ENTERPRISE
    # ═════════════════════════════════════════════════════════════════════════
    with tab_int:
        st.markdown("### 🔗 Integrazioni Enterprise (Paperclip & Hermes AI)")
        ic1, ic2 = st.columns(2)

        with ic1:
            st.markdown("""<div style="background:linear-gradient(135deg,#1e1b4b,#312e81);
              border:1px solid #4f46e5;border-radius:14px;padding:20px;margin-bottom:16px;">
              <div style="font-size:1.1rem;font-weight:700;color:#c7d2fe;margin-bottom:6px;">📎 Paperclip · Block Buzz</div>
              <div style="font-size:.8rem;color:#818cf8;">Monitoraggio task e pipeline di produzione</div>
            </div>""", unsafe_allow_html=True)
            pp_ok = False
            try:
                r = requests.get(f"{_PAPERCLIP_BASE}/api/health", timeout=0.3)
                pp_ok = r.ok
            except Exception:
                pass

            if pp_ok:
                st.success(f"🟢 Paperclip connesso su {_PAPERCLIP_BASE}")
                tasks = _pp_get_tasks()
                st.markdown(f"**Task Attivi MoneyPrinter:** {len(tasks)}")
                for t in tasks[:5]:
                    st.markdown(f"- `{t.get('status','?')}` · {t.get('title','?')[:50]}")
            else:
                st.info(f"🟡 Paperclip in ascolto su `{_PAPERCLIP_BASE}`.")

        with ic2:
            st.markdown("""<div style="background:linear-gradient(135deg,#0c1445,#1e3a5f);
              border:1px solid #0ea5e9;border-radius:14px;padding:20px;margin-bottom:16px;">
              <div style="font-size:1.1rem;font-weight:700;color:#7dd3fc;margin-bottom:6px;">🤖 Hermes Agent Swarm</div>
              <div style="font-size:.8rem;color:#38bdf8;">Automazione analisi script e trend virali</div>
            </div>""", unsafe_allow_html=True)
            hermes_ok = False
            try:
                hr = requests.get(f"{_HERMES_BASE}/api/health", timeout=0.3)
                hermes_ok = hr.ok
            except Exception:
                pass

            if hermes_ok:
                st.success(f"🟢 Hermes backend connesso su {_HERMES_BASE}")
            else:
                st.info(f"🔵 Hermes backend disponibile su `{_HERMES_BASE}`")
