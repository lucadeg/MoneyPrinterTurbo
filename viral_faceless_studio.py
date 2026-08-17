"""
MoneyPrinterTurbo - Viral Faceless & UGC Studio
Complete interactive interface and automated pipeline for 100% original video recreation
and high-converting UGC creation using free Google / Edge AI tools.
"""

import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import streamlit as st
from app.config import config
from app.models.schema import VideoParams
from app.services import task as tm
from app.services import webui_task
from app.services.ugc_engine import UGC_ANGLES, build_ugc_video_params, generate_ugc_script
from app.services.viral_faceless_engine import (
    FACELESS_NICHES,
    build_faceless_video_params,
    recreate_viral_faceless_script,
    search_viral_videos_free,
)

st.set_page_config(
    page_title="MoneyPrinterTurbo - Viral Faceless & UGC Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
.main-header {
    font-size: 1.6rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
    background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.metric-badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    background-color: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.3);
}
.viral-card {
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.75rem;
    padding: 1rem;
    margin-bottom: 0.75rem;
    background-color: rgba(255, 255, 255, 0.03);
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="main-header">🎬 MoneyPrinterTurbo — Viral Studio & UGC Studio</div>', unsafe_allow_html=True)
st.caption("Motore integrato per video Faceless (ricerca virale + ricreazione 100% originale) e video UGC ad alta conversione con strumenti gratuiti (Google Gemini, Edge-TTS, Pexels).")

tabs = st.tabs(["🚀 Video Faceless (Viral Discovery & 100% Auto-Recreation)", "📱 Video UGC & Creator Ads", "⚙️ Configurazione Provider Gratuiti"])

# -----------------------------------------------------------------------------
# TAB 1: FACELESS VIRAL STUDIO
# -----------------------------------------------------------------------------
with tabs[0]:
    st.subheader("Ricerca Video con Milioni di Views & Ricreazione Originale")
    
    col_search, col_options = st.columns([0.65, 0.35])
    
    with col_search:
        niche_keys = list(FACELESS_NICHES.keys())
        selected_niche_key = st.selectbox(
            "Seleziona Nicchia Faceless",
            options=niche_keys,
            format_func=lambda k: FACELESS_NICHES[k]["label"],
        )
        custom_search_topic = st.text_input(
            "Argomento Specifico o Query di Ricerca (opzionale)",
            placeholder="es. abitudini oscure dei miliardari, buchi neri nello spazio, trucchi mentali",
        )
        
    with col_options:
        target_lang = st.selectbox("Lingua Video Finale", options=["it-IT", "en-US", "es-ES", "fr-FR", "de-DE"], index=0)
        selected_voice = st.selectbox(
            "Voce Edge-TTS (100% Gratuita)",
            options=[
                "it-IT-DiegoNeural",
                "it-IT-ElsaNeural",
                "it-IT-IsabellaNeural",
                "it-IT-GiuseppeNeural",
                "en-US-ChristopherNeural",
                "en-US-JennyNeural",
                "en-US-GuyNeural",
            ],
            index=0,
        )
        video_stock_source = st.selectbox("Sorgente Video HD", options=["pexels", "pixabay", "local"], index=0)

    if st.button("🔍 Trova Video Virali con Milioni di Views", type="primary", use_container_width=True):
        query_to_search = custom_search_topic.strip() or FACELESS_NICHES[selected_niche_key]["keywords"][0]
        with st.spinner(f"Ricerca trend virali per: '{query_to_search}' in corso…"):
            found_videos = search_viral_videos_free(query_to_search, max_results=4)
            st.session_state["faceless_found_videos"] = found_videos
            st.session_state["faceless_selected_niche"] = selected_niche_key

    if "faceless_found_videos" in st.session_state and st.session_state["faceless_found_videos"]:
        st.write("### 🏆 Video Virali Trovati (Riferimenti di Ispirazione):")
        
        v_cols = st.columns(len(st.session_state["faceless_found_videos"]))
        for idx, vid in enumerate(st.session_state["faceless_found_videos"]):
            with v_cols[idx]:
                with st.container(border=True):
                    st.markdown(f"**{vid['title']}**")
                    st.markdown(f"👁️ `{vid['formatted_views']}` | ⏱️ `{vid['duration']}s`")
                    st.caption(f"Autore: {vid['uploader']}")
                    
                    if st.button(f"✨ Ricrea al 100% Originale", key=f"recreate_{idx}", use_container_width=True):
                        with st.spinner("Decostruzione del gancio e scrittura script 100% originale con Google Gemini / Free AI…"):
                            recreated = recreate_viral_faceless_script(
                                viral_reference=vid,
                                niche_key=st.session_state.get("faceless_selected_niche", "dark_psychology"),
                                target_language=target_lang,
                            )
                            st.session_state["active_faceless_project"] = recreated

    if "active_faceless_project" in st.session_state:
        proj = st.session_state["active_faceless_project"]
        st.divider()
        st.write("### 📝 Script Ricreato al 100% (Zero Plagio, Massimo Gancio di Trattenimento):")
        
        col_script, col_meta = st.columns([0.65, 0.35])
        with col_script:
            edited_script = st.text_area(
                "Testo Voiceover (puoi modificarlo liberamente)",
                value=proj["script"],
                height=160,
                key="faceless_edited_script",
            )
            proj["script"] = edited_script
            
        with col_meta:
            terms_str = st.text_area(
                "Keyword B-Roll per Video HD Stock",
                value=", ".join(proj["terms"]),
                height=80,
                key="faceless_terms_input",
            )
            proj["terms"] = [t.strip() for t in terms_str.split(",") if t.strip()]
            st.info(f"Ispirato a: **{proj['reference_title']}** ({proj['reference_views']})")

        if st.button("🎬 GENERA VIDEO FACELESS COMPLETO (MP4 9:16 + Voce + Sottotitoli + Musica)", type="primary", use_container_width=True):
            with st.spinner("Preparazione pipeline e avvio rendering video…"):
                params = build_faceless_video_params(
                    faceless_data=proj,
                    voice_name=selected_voice,
                    video_source=video_stock_source,
                )
                from uuid import uuid4
                task_id = str(uuid4())
                try:
                    webui_task.submit_generation(
                        task_id=task_id,
                        params=params,
                        capture_logs=True,
                    )
                    st.session_state["current_task_id"] = task_id
                    st.success(f"🚀 Task di generazione avviato con successo! Task ID: `{task_id}`")
                except Exception as e:
                    st.error(f"Errore nell'avvio del rendering: {e}")

# -----------------------------------------------------------------------------
# TAB 2: UGC VIDEO STUDIO
# -----------------------------------------------------------------------------
with tabs[1]:
    st.subheader("Generatore di Video UGC & In-Feed Ads ad Alta Conversione")
    
    col_ugc_in, col_ugc_set = st.columns([0.6, 0.4])
    
    with col_ugc_in:
        ugc_product = st.text_input("Nome Prodotto / App / Servizio", placeholder="es. MindGlow App, Hermes AI, Corso E-commerce")
        ugc_niche = st.text_input("Settore / Target", value="Produttività & Intelligenza Artificiale")
        ugc_pain = st.text_input("Problema Principale Risolto", placeholder="es. perdere 3 ore al giorno a montare video a mano")
        
        selected_angle = st.selectbox(
            "Angolo di Vendita / Hook UGC",
            options=list(UGC_ANGLES.keys()),
            format_func=lambda k: UGC_ANGLES[k]["label"],
        )
        
    with col_ugc_set:
        ugc_lang = st.selectbox("Lingua UGC", options=["it-IT", "en-US", "es-ES", "fr-FR"], index=0, key="ugc_lang")
        ugc_voice = st.selectbox(
            "Voce Narratore / Creator",
            options=[
                "it-IT-DiegoNeural",
                "it-IT-ElsaNeural",
                "it-IT-IsabellaNeural",
                "en-US-JennyNeural",
                "en-US-ChristopherNeural",
            ],
            index=0,
            key="ugc_voice",
        )
        ugc_source = st.selectbox("Materiale Video", options=["pexels", "pixabay", "local"], index=0, key="ugc_source")

    if st.button("⚡ Genera Script UGC a 5 Fasi (Hook, Problema, Demo, Prova, CTA)", type="primary", use_container_width=True):
        if not ugc_product:
            st.warning("Inserisci il nome del prodotto o servizio.")
        else:
            with st.spinner("Scrittura copywriting UGC ad alta conversione…"):
                ugc_res = generate_ugc_script(
                    product_or_subject=ugc_product,
                    niche=ugc_niche,
                    pain_point=ugc_pain,
                    angle_key=selected_angle,
                    language=ugc_lang,
                )
                st.session_state["active_ugc_project"] = ugc_res

    if "active_ugc_project" in st.session_state:
        ugc_p = st.session_state["active_ugc_project"]
        st.divider()
        st.write("### 📱 Anteprima Script UGC & Tag Visivi:")
        
        ugc_script_edit = st.text_area("Script Voiceover UGC", value=ugc_p["script"], height=150, key="ugc_script_edit")
        ugc_p["script"] = ugc_script_edit
        
        if st.button("🔥 GENERA VIDEO UGC FINALE (9:16 + Tagli Rapidi + Sottotitoli Gialli TikTok)", type="primary", use_container_width=True):
            params = build_ugc_video_params(
                ugc_data=ugc_p,
                voice_name=ugc_voice,
                video_source=ugc_source,
            )
            from uuid import uuid4
            task_id = str(uuid4())
            try:
                webui_task.submit_generation(
                    task_id=task_id,
                    params=params,
                    capture_logs=True,
                )
                st.session_state["current_task_id"] = task_id
                st.success(f"🚀 Video UGC in fase di montaggio! Task ID: `{task_id}`")
            except Exception as e:
                st.error(f"Errore: {e}")

# -----------------------------------------------------------------------------
# TAB 3: CONFIGURAZIONE PROVIDER GRATUITI
# -----------------------------------------------------------------------------
with tabs[2]:
    st.subheader("Stato Strumenti & Provider Gratuiti")
    
    st.markdown(
        """
| Servizio | Provider Configurato | Stato & Costo |
| :--- | :--- | :--- |
| **Generazione Testo & Script** | **Google Gemini** (Gemini 2.0 Flash) / Ollama / Pollinations | 🟢 100% Gratuito |
| **Sintesi Vocale (TTS)** | **Microsoft Edge-TTS** (Multilingual Neural Voices) | 🟢 100% Gratuito (Illimitato) |
| **Allineamento & Sottotitoli** | **OpenAI Whisper** + Subtitle Engine | 🟢 Locale / Gratuito |
| **Materiale Video Stock** | **Pexels & Pixabay** (API & HD Scraper) | 🟢 100% Gratuito |
| **Discovery Virale** | **YouTube Shorts Public Search / yt-dlp** | 🟢 100% Gratuito (Senza API Key) |
"""
    )
    
    st.info("Tutti i parametri sono pre-configurati in `c:\\Users\\Deglu\\.hermes\\tools\\moneyprinterturbo\\config.toml`. Se possiedi una chiave Google Gemini API (gratuita su aistudio.google.com), puoi incollarla nel file o usarla direttamente.")

# Task Monitor Widget
if "current_task_id" in st.session_state:
    st.divider()
    active_tid = st.session_state["current_task_id"]
    st.write(f"### 📊 Monitoraggio Task Attivo: `{active_tid}`")
    
    from app.services import state as sm
    task_state = sm.state.get_task(active_tid)
    if task_state:
        progress = task_state.get("progress", 0)
        state_code = task_state.get("state", 0)
        st.progress(progress / 100.0, text=f"Progresso: {progress}% - {task_state.get('state_desc', 'In elaborazione')}")
        
        final_file = task_state.get("final_file")
        if final_file and os.path.exists(final_file):
            st.success("🎉 Video completato con successo!")
            st.video(final_file)
