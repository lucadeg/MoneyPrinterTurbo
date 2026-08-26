#!/usr/bin/env python3
"""
Sovereign Gemini 3.6 Flash Content Critic & Quality Audit Engine.
Automated multi-metric critical evaluation system for social media scripts,
visual scenes, voiceover pacing, and platform virality.

Evaluates against:
1. HRI (Hook Retention Index) - 0-100
2. MSS (Memorability & Stickiness Score) - 0-100
3. ERI (Emotional Resonance Index) - 0-100
4. AMS (Audio & Musicality Score) - 0-100
5. VQS (Visual Quality & Dynamic Pacing Score) - 0-100
6. NUI (Novelty & Anti-Fatigue Unpredictability Index) - 0-100
7. Platform Algorithmic Alignment (TikTok, Instagram Reels, YouTube Shorts)
8. Critical Diagnosis & Concrete Line-by-Line Fix Directives
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows console UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
STORAGE_DIR = SCRIPT_DIR / "storage"
AUDIT_LOG_DIR = STORAGE_DIR / "viral_intelligence" / "gemini_critique_audits"
AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Multi-Account Key Pool
def get_gemini_key_pool() -> list[str]:
    keys = []
    env_p = Path(r"C:\Users\Deglu\.hermes\.env")
    if env_p.exists():
        for line in env_p.read_text(encoding="utf-8").splitlines():
            if line.startswith("GEMINI_API_KEY="):
                k = line.split("=", 1)[1].strip()
                if k and k not in keys:
                    keys.append(k)
            elif line.startswith("GEMINI_API_KEY_ACCOUNT_B="):
                k = line.split("=", 1)[1].strip()
                if k and k not in keys:
                    keys.append(k)
            elif line.startswith("GOOGLE_API_KEY="):
                k = line.split("=", 1)[1].strip()
                if k and k not in keys:
                    keys.append(k)
    return keys or [os.environ.get("GEMINI_API_KEY", "")]


CRITIC_SYSTEM_PROMPT = """You are the Senior Executive Content Director & Viral Algorithm Auditor for high-performing short-form video (TikTok, Instagram Reels, YouTube Shorts).
Your job is to provide a RUTHLESS, OBJECTIVE, MATHEMATICALLY GROUNDED, and HIGHLY CONSTRUCTIVE audit of video scripts and production plans.

You DO NOT give generic praise. You evaluate content against the proprietary Sovereign Viral Matrix:

### 1. EVALUATION METRICS (Score 0-100 each):
- **HRI (Hook Retention Index, Weight 30%)**: First 3s impact. Does it trigger cognitive tension, curiosity gap, or contrarian pattern interrupt? Will users swipe away (APV < 60%) or stay locked?
- **MSS (Memorability & Stickiness Score, Weight 20%)**: Does it feature unforgettable aphorisms, quote-worthy maxims, life rules, or sticky mnemonic formulas?
- **ERI (Emotional Resonance Index, Weight 15%)**: Conviction, authority, high-stakes curiosity, subtle wit, or gravitas. Does it evoke genuine feeling or feel like generic corporate filler?
- **AMS (Audio & Musicality Cadence, Weight 15%)**: Rhythm of the words, syllable flow, natural breathing pauses, absence of robotic monotonicity, harmony with luxury lounge/satirical BGM.
- **VQS (Visual Quality & Scene Diversity, Weight 10%)**: Avoidance of "PowerPoint Slide Flop". Does the visual plan have dynamic 3-5s scene cuts, high-fashion/cosmic aesthetics, kinetic contrast, and brand dignity?
- **NUI (Novelty & Anti-Fatigue Score, Weight 10%)**: Is the angle unique, unexpected, and contrarian, or is it a generic regurgitation of clichés across 1,000+ catalog videos?

### 2. PLATFORM ALGORITHMIC FIT:
- **TikTok**: High speed, fast hook, loopable ending (Target APV > 88%).
- **Instagram Reels**: High aesthetic dignity, luxury framing, save/share value (Target Shares > 20%).
- **YouTube Shorts**: High retention, algorithmic authority, subscribe trigger (Target Retention > 85%).

### 3. OUTPUT FORMAT:
You MUST respond ONLY with a valid, parseable JSON object matching this schema:
{
  "overall_score": 88,
  "verdict": "VIRAL_BROADCAST_GRADE" | "ACCEPTABLE_NEEDS_POLISH" | "REJECTED_FATAL_FLAWS",
  "metrics": {
    "hri_hook_retention": { "score": 90, "analysis": "..." },
    "mss_memorability_stickiness": { "score": 85, "analysis": "..." },
    "eri_emotional_resonance": { "score": 88, "analysis": "..." },
    "ams_audio_musicality": { "score": 92, "analysis": "..." },
    "vqs_visual_pacing": { "score": 86, "analysis": "..." },
    "nui_novelty_antifatigue": { "score": 87, "analysis": "..." }
  },
  "platform_alignment": {
    "tiktok_apv_projected_pct": 86.5,
    "reels_shareability_projected_pct": 24.0,
    "yt_shorts_retention_projected_pct": 84.0,
    "estimated_rpm_usd": 1.65,
    "projected_views_bracket": "100k - 450k"
  },
  "critical_strengths": [
    "...", "..."
  ],
  "critical_weaknesses": [
    "...", "..."
  ],
  "concrete_actionable_directives": [
    "Rewrite hook to ...",
    "Shorten sentence 3 by removing ...",
    "Ensure scene transition at second 12 focuses on ..."
  ],
  "recommended_refined_script": "...",
  "recommended_refined_hook": "..."
}"""


def call_gemini_36_flash(prompt_payload: str, preferred_model: str = "gemini-3.6-flash") -> dict:
    """Calls Google Gemini 3.6 Flash via direct Generative Language API with automatic key rotation and model fallback."""
    key_pool = get_gemini_key_pool()
    if not key_pool:
        raise ValueError("Nessuna chiave GEMINI_API_KEY trovata in .env!")

    models_to_try = [preferred_model, "gemini-3.7-flash", "gemini-2.5-flash", "gemini-flash-latest", "gemini-3.5-flash"]
    
    last_error = None
    for model in models_to_try:
        for api_key in key_pool:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": f"{CRITIC_SYSTEM_PROMPT}\n\n### CONTENT TO EVALUATE:\n{prompt_payload}"}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json"
                }
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )

            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    raw_text = re.sub(r"^```json\s*", "", raw_text.strip())
                    raw_text = re.sub(r"\s*```$", "", raw_text.strip())
                    res = json.loads(raw_text)
                    res["evaluated_by_model"] = model
                    return res
            except Exception as e:
                last_error = e
                # If rate limited (429) or busy, sleep 1s and try next key/model
                time.sleep(1.0)
                continue

    raise RuntimeError(f"Tutti i tentativi con Gemini Flash sono falliti: {last_error}")


def evaluate_task_content(task_data: dict, channel_niche: str = "executive_fashion") -> dict:
    """
    Runs an exhaustive Gemini 3.6 Flash critical evaluation on a given video task config/script.
    """
    title = task_data.get("title", "")
    hook = task_data.get("hook", "")
    script = task_data.get("script", "")
    category = task_data.get("category", "")
    voice = task_data.get("voice_name", "")
    scenes = task_data.get("scenes", [])

    prompt_payload = f"""
NICHE / CHANNEL: {channel_niche.upper()}
TITLE: {title}
CATEGORY: {category}
HOOK: {hook}
VOICE / AUDIO ARCHETYPE: {voice}
FULL SCRIPT:
{script}

SCENE BREAKDOWN (IF PLANNED):
{json.dumps(scenes, indent=2) if scenes else 'Dynamic 5-scene editorial card progression'}
"""
    print(f"[*] Invio a Gemini 3.6 Flash per valutazione critica ({title})...")
    critique = call_gemini_36_flash(prompt_payload)
    
    # Enrich with metadata
    critique["task_id"] = task_data.get("task_id", f"task_{int(time.time())}")
    critique["evaluated_at"] = datetime.now(timezone.utc).isoformat()
    critique["model_evaluator"] = "google/gemini-3.6-flash"

    # Save report to audit ledger
    audit_file = AUDIT_LOG_DIR / f"{critique['task_id']}_critique.json"
    with open(audit_file, "w", encoding="utf-8") as f:
        json.dump(critique, f, indent=2, ensure_ascii=False)

    return critique


def format_critique_terminal_report(critique: dict) -> str:
    """Formats the critique result into an elegant ASCII report."""
    score = critique.get("overall_score", 0)
    verdict = critique.get("verdict", "N/A")
    m = critique.get("metrics", {})
    p = critique.get("platform_alignment", {})

    color_icon = "🟢" if score >= 85 else ("🟡" if score >= 75 else "🔴")

    lines = [
        f"\n=======================================================",
        f"🤖 GEMINI 3.6 FLASH CRITICAL QUALITY AUDIT REPORT",
        f"=======================================================",
        f"🎯 Task ID: {critique.get('task_id', 'N/A')}",
        f"🏆 OVERALL VIRAL SCORE: {color_icon} {score}/100 [{verdict}]",
        f"-------------------------------------------------------",
        f"📊 METRICHE CHIAVE SOVEREIGN MATRIX:",
        f"  • HRI (Hook Retention Index):     {m.get('hri_hook_retention', {}).get('score', 'N/A')}/100",
        f"  • MSS (Memorability & Stickiness): {m.get('mss_memorability_stickiness', {}).get('score', 'N/A')}/100",
        f"  • ERI (Emotional Resonance):       {m.get('eri_emotional_resonance', {}).get('score', 'N/A')}/100",
        f"  • AMS (Audio & Musical Cadence):   {m.get('ams_audio_musicality', {}).get('score', 'N/A')}/100",
        f"  • VQS (Visual Pacing & Diversity): {m.get('vqs_visual_pacing', {}).get('score', 'N/A')}/100",
        f"  • NUI (Novelty & Anti-Fatigue):    {m.get('nui_novelty_antifatigue', {}).get('score', 'N/A')}/100",
        f"-------------------------------------------------------",
        f"📱 PROIEZIONI ALGORITMICHE:",
        f"  • TikTok APV Stimata:     {p.get('tiktok_apv_projected_pct', 'N/A')}%",
        f"  • Reels Save/Share Rate:  {p.get('reels_shareability_projected_pct', 'N/A')}%",
        f"  • Shorts Retention:       {p.get('yt_shorts_retention_projected_pct', 'N/A')}%",
        f"  • RPM Stimato:            ${p.get('estimated_rpm_usd', 0.0):.2f}",
        f"  • Visualizzazioni Stimate: {p.get('projected_views_bracket', 'N/A')}",
        f"-------------------------------------------------------",
        f"✨ PUNTI DI FORZA:",
    ]
    for s in critique.get("critical_strengths", []):
        lines.append(f"  + {s}")

    lines.append(f"⚠️ CRITICITÀ & PUNTI DEBOLI:")
    for w in critique.get("critical_weaknesses", []):
        lines.append(f"  - {w}")

    lines.append(f"⚡ DIRETTIVE CONCRETE DI MIGLIORAMENTO:")
    for d in critique.get("concrete_actionable_directives", []):
        lines.append(f"  ➜ {d}")

    if critique.get("recommended_refined_hook"):
        lines.append(f"\n💡 HOOK OTTIMIZZATO CONSIGLIATO:\n  “{critique['recommended_refined_hook']}”")

    lines.append(f"=======================================================\n")
    return "\n".join(lines)


# ==============================================================================
# CLI INTERFACE
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Gemini 3.6 Flash Content Critic Engine")
    parser.add_argument("--task-file", "-f", type=str, help="Percorso del file task_config.json")
    parser.add_argument("--script", "-s", type=str, help="Testo dello script da valutare")
    parser.add_argument("--hook", type=str, default="", help="Hook opzionale")
    parser.add_argument("--title", type=str, default="Contenuto Social", help="Titolo opzionale")
    parser.add_argument("--niche", type=str, default="executive_fashion", help="Nicchia (executive_fashion, satire, space_doc)")
    parser.add_argument("--all-channels", action="store_true", help="Valuta tutti i task di tutti i canali")
    args = parser.parse_args()

    if args.all_channels:
        print("[*] Esecuzione Audit Standard Gemini 3.6 Flash su tutti i canali...")
        # 1. Giuly Moser
        giuly_dir = STORAGE_DIR / "giuly_moser" / "tasks"
        if giuly_dir.exists():
            for tf in giuly_dir.iterdir():
                cfg_f = tf / "task_config.json"
                if cfg_f.exists():
                    with open(cfg_f, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                    res = evaluate_task_content(cfg, channel_niche="executive_fashion")
                    print(format_critique_terminal_report(res))
        
        # 2. Orazio
        orazio_dir = STORAGE_DIR / "orazio_shorts" / "tasks"
        if orazio_dir.exists():
            for tf in orazio_dir.iterdir():
                cfg_f = tf / "task_config.json"
                if cfg_f.exists():
                    with open(cfg_f, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                    res = evaluate_task_content(cfg, channel_niche="satire")
                    print(format_critique_terminal_report(res))
        return

    if args.task_file:
        tf_path = Path(args.task_file)
        if not tf_path.exists():
            print(f"[-] File '{args.task_file}' non trovato.")
            return
        with open(tf_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        res = evaluate_task_content(cfg, channel_niche=args.niche)
        print(format_critique_terminal_report(res))
        return

    if args.script:
        task_data = {
            "title": args.title,
            "hook": args.hook or args.script[:80],
            "script": args.script,
            "category": args.niche,
            "voice_name": "en-US-JennyNeural"
        }
        res = evaluate_task_content(task_data, channel_niche=args.niche)
        print(format_critique_terminal_report(res))
        return

    # Default: evaluate giuly_01
    default_giuly_cfg = STORAGE_DIR / "giuly_moser" / "tasks" / "giuly_01_quiet_luxury_vs_logos" / "task_config.json"
    if default_giuly_cfg.exists():
        with open(default_giuly_cfg, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        res = evaluate_task_content(cfg, channel_niche="executive_fashion")
        print(format_critique_terminal_report(res))
    else:
        print("Usa --task-file, --script, o --all-channels per eseguire l'audit.")


if __name__ == "__main__":
    main()
