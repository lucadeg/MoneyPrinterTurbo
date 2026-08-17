"""
channel_manager.py
==================
Gestione canali multi-piattaforma (YouTube, Instagram, TikTok) e catalogo video.
Ogni canale ha una piattaforma target + strategia di contenuto per evitare duplicati.
I video vengono registrati automaticamente come "bozza" dopo la generazione.
"""

import os
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
try:
    from loguru import logger
except ImportError:
    import logging as logger

STORAGE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage"
)
CATALOG_FILE = os.path.join(STORAGE_DIR, "channels_catalog.json")

PLATFORMS = ["YouTube Shorts", "Instagram Reels", "TikTok", "YouTube", "Facebook Reels"]

PLATFORM_STRATEGIES = {
    "YouTube Shorts": {
        "aspect": "9:16",
        "max_duration_s": 60,
        "style_note": "Hook nei primi 3s, voiceover didattico, CTA finale 'Seguici per altre scoperte'",
        "hashtag_style": "3-5 hashtag di nicchia (#spazio #curiosità)",
        "content_angle": "educativo-virale con apertura a loop",
    },
    "Instagram Reels": {
        "aspect": "9:16",
        "max_duration_s": 90,
        "style_note": "Apertura visivamente d'impatto, testo overlay in italiano, musica in evidenza",
        "hashtag_style": "15-20 hashtag misti (#reels #viral #italia)",
        "content_angle": "estetico e aspirazionale, focus sull'emozione",
    },
    "TikTok": {
        "aspect": "9:16",
        "max_duration_s": 60,
        "style_note": "Trend sounds, transizioni rapide, stile POV o 'lo sapevi che?'",
        "hashtag_style": "5-8 hashtag trending (#fyp #viral #curiosità)",
        "content_angle": "intrattenimento breve, tono informale e diretto",
    },
    "YouTube": {
        "aspect": "16:9",
        "max_duration_s": 600,
        "style_note": "Intro+outro, capitoli, thumbnail ottimizzata, keyword nel titolo",
        "hashtag_style": "2-3 hashtag nel titolo",
        "content_angle": "approfondito e autorevole, tutorial o analisi",
    },
    "Facebook Reels": {
        "aspect": "9:16",
        "max_duration_s": 60,
        "style_note": "Testo visibile senza audio (60% visualizzazioni senza audio), CTA a condividere",
        "hashtag_style": "2-3 hashtag",
        "content_angle": "informativo con sottotitoli grandi e leggibili",
    },
}

DEFAULT_CHANNELS = [
    {
        "id": "ch_yt_faceless",
        "name": "🚀 Misteri Cosmici IT",
        "platform": "YouTube Shorts",
        "niche": "Spazio & Misteri Scientifici",
        "content_strategy": "educativo-virale con apertura a loop",
        "target_account": "mrvinxsrl@gmail.com",
        "platform_account": "youtube.com/@MisteriCosmiciIT",
        "created_at": "2026-08-15 12:00:00",
        "total_videos": 0,
        "total_views": 0,
        "active": True,
    },
    {
        "id": "ch_ig_reels",
        "name": "✨ Dark Psychology Italia",
        "platform": "Instagram Reels",
        "niche": "Psicologia & Mindset",
        "content_strategy": "estetico e aspirazionale, focus sull'emozione",
        "target_account": "mrvinxsrl@gmail.com",
        "platform_account": "@dark.psychology.it",
        "created_at": "2026-08-15 12:00:00",
        "total_videos": 0,
        "total_views": 0,
        "active": True,
    },
    {
        "id": "ch_tt_viral",
        "name": "🎯 Lo Sapevi Che?",
        "platform": "TikTok",
        "niche": "Curiosità & Fatti Incredibili",
        "content_strategy": "intrattenimento breve, tono informale e diretto",
        "target_account": "mrvinxsrl@gmail.com",
        "platform_account": "@losapevichemd",
        "created_at": "2026-08-15 12:00:00",
        "total_videos": 0,
        "total_views": 0,
        "active": True,
    },
    {
        "id": "ch_ugc_ads",
        "name": "📱 UGC High-Converting Ads",
        "platform": "TikTok",
        "niche": "E-Commerce & Tech SaaS",
        "content_strategy": "intrattenimento breve, tono informale e diretto",
        "target_account": "mrvinxsrl@gmail.com",
        "platform_account": "@ugc.ads.it",
        "created_at": "2026-08-15 12:00:00",
        "total_videos": 0,
        "total_views": 0,
        "active": True,
    },
]


# ─────────────────────────────── DATA LAYER ────────────────────────────────

def _load_data() -> Dict[str, Any]:
    os.makedirs(STORAGE_DIR, exist_ok=True)
    if not os.path.exists(CATALOG_FILE):
        initial = {
            "channels": DEFAULT_CHANNELS,
            "videos": [],
            "gdrive_account": "mrvinxsrl@gmail.com",
            "gdrive_connected": True,
            "last_scan_time": 0,
        }
        _save_data(initial)
        return initial
    try:
        with open(CATALOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "channels" not in data or not data["channels"]:
            data["channels"] = DEFAULT_CHANNELS
        if "videos" not in data:
            data["videos"] = []
        return data
    except Exception as e:
        logger.error(f"Failed to read channels catalog: {e}")
        return {"channels": DEFAULT_CHANNELS, "videos": []}


def _save_data(data: Dict[str, Any]):
    os.makedirs(STORAGE_DIR, exist_ok=True)
    try:
        with open(CATALOG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save channels catalog: {e}")


# ─────────────────────────────── CHANNELS ──────────────────────────────────

def get_channels(active_only: bool = False) -> List[Dict[str, Any]]:
    data = _load_data()
    channels = data.get("channels", [])
    if active_only:
        channels = [c for c in channels if c.get("active", True)]
    return channels


def add_channel(
    name: str,
    platform: str = "YouTube Shorts",
    niche: str = "Generale",
    platform_account: str = "",
) -> Dict[str, Any]:
    data = _load_data()
    channel_id = f"ch_{int(time.time())}"
    strategy_info = PLATFORM_STRATEGIES.get(platform, {})
    new_ch = {
        "id": channel_id,
        "name": name.strip(),
        "platform": platform,
        "niche": niche.strip(),
        "content_strategy": strategy_info.get("content_angle", "generale"),
        "platform_account": platform_account.strip(),
        "target_account": "mrvinxsrl@gmail.com",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_videos": 0,
        "total_views": 0,
        "active": True,
    }
    data["channels"].append(new_ch)
    _save_data(data)
    return new_ch


def toggle_channel_active(channel_id: str):
    data = _load_data()
    for ch in data["channels"]:
        if ch["id"] == channel_id:
            ch["active"] = not ch.get("active", True)
    _save_data(data)


def get_channel(channel_id: str) -> Optional[Dict[str, Any]]:
    data = _load_data()
    for ch in data.get("channels", []):
        if ch.get("id") == channel_id:
            return ch
    return None


def delete_channel(channel_id: str):
    data = _load_data()
    data["channels"] = [c for c in data["channels"] if c["id"] != channel_id]
    _save_data(data)


# ─────────────────────────────── VIDEOS ────────────────────────────────────

def get_videos(
    channel_id: Optional[str] = None, status: Optional[str] = None
) -> List[Dict[str, Any]]:
    scan_storage_for_new_videos()
    data = _load_data()
    videos = data.get("videos", [])
    if channel_id and channel_id != "all":
        videos = [v for v in videos if v.get("channel_id") == channel_id]
    if status and status != "all":
        videos = [v for v in videos if v.get("status") == status]
    return sorted(videos, key=lambda x: x.get("created_at", ""), reverse=True)


def get_video(video_id: str) -> Optional[Dict[str, Any]]:
    data = _load_data()
    for v in data.get("videos", []):
        if v["id"] == video_id:
            return v
    return None


def update_video_status(video_id: str, new_status: str, note: str = ""):
    data = _load_data()
    for v in data["videos"]:
        if v["id"] == video_id:
            v["status"] = new_status
            if note:
                v["review_note"] = note
            v["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            break
    _save_data(data)


def assign_video_channel(video_id: str, channel_id: str):
    data = _load_data()
    for v in data["videos"]:
        if v["id"] == video_id:
            v["channel_id"] = channel_id
            v["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            break
    _save_data(data)


def update_video_publish_info(video_id: str, platform: str, pub_data: Dict[str, Any]):
    """Store the publication record for a specific platform."""
    data = _load_data()
    for v in data["videos"]:
        if v["id"] == video_id:
            if "publications" not in v:
                v["publications"] = {}
            v["publications"][platform] = {
                **pub_data,
                "published_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            v["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            break
    _save_data(data)


def update_video_gdrive(video_id: str, gdrive_result: Dict[str, Any]):
    data = _load_data()
    for v in data["videos"]:
        if v["id"] == video_id:
            v["gdrive_synced"] = gdrive_result.get("success", False)
            v["gdrive_link"] = gdrive_result.get("link")
            v["gdrive_file_id"] = gdrive_result.get("file_id")
            v["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            break
    _save_data(data)


def delete_video(video_id: str):
    data = _load_data()
    data["videos"] = [v for v in data["videos"] if v["id"] != video_id]
    _save_data(data)


def get_platform_variations(video: Dict[str, Any], channel: Dict[str, Any]) -> Dict[str, str]:
    """Generate platform-specific title/description/hashtag suggestions for a video."""
    title = video.get("title", "Video Interessante")
    platform = channel.get("platform", "YouTube Shorts")
    strategy = PLATFORM_STRATEGIES.get(platform, {})

    variations: Dict[str, str] = {
        "YouTube Shorts": {
            "title": f"🚀 {title} [SHORTS]",
            "description": f"Scopri {title}! Segui per contenuti esclusivi ogni giorno.\n\n{strategy.get('hashtag_style','')}",
            "hashtags": "#spazio #curiosità #scienzadivulgativa #shorts #viral",
        },
        "Instagram Reels": {
            "title": title,
            "description": f"✨ {title}\n\nSalva questo video per rivederlo! ❤️\n\n#reels #viral #italia #curiosità #scienza #mindblowing #esplora #reel #trending",
            "hashtags": "#reels #viral #italia #curiosità #scienza #mindblowing #esplora",
        },
        "TikTok": {
            "title": f"Lo sapevi che... {title}?",
            "description": f"POV: scopri {title} 🤯 #fyp #viral #curiosità #losapevichemd",
            "hashtags": "#fyp #viral #curiosità #scienzatiktok #trending",
        },
        "YouTube": {
            "title": f"{title} - Documentario Completo",
            "description": f"In questo video esploriamo {title} con prove e testimonianze...\n\nIscriviti al canale per non perderti nulla!",
            "hashtags": "#youtube #documentario",
        },
        "Facebook Reels": {
            "title": f"👁 {title}",
            "description": f"Condividi con un amico che non lo sa ancora! 👇\n\n{title}",
            "hashtags": "#curiosità #viral",
        },
    }.get(platform, {})

    return variations


# ─────────────────────────────── SCANNER ───────────────────────────────────

def scan_storage_for_new_videos() -> int:
    """Scans storage/tasks and local storage for video and audio files, auto-registering drafts."""
    data = _load_data()
    existing_task_ids = {v.get("task_id") for v in data.get("videos", [])}

    tasks_dir = os.path.join(STORAGE_DIR, "tasks")
    channels = data.get("channels", DEFAULT_CHANNELS)
    ch_ids = [c["id"] for c in channels] if channels else ["ch_default"]
    added = 0

    if os.path.exists(tasks_dir):
        for idx, task_folder in enumerate(sorted(os.listdir(tasks_dir))):
            task_path = os.path.join(tasks_dir, task_folder)
            if not os.path.isdir(task_path) or task_folder in existing_task_ids:
                continue

            # Check for mp4 files: final-*.mp4, combined-*.mp4, or any .mp4
            mp4_files = [f for f in os.listdir(task_path) if f.endswith(".mp4")]
            final_files = [f for f in mp4_files if f.startswith("final-")] or [f for f in mp4_files if f.startswith("combined-")] or mp4_files
            audio_files = [f for f in os.listdir(task_path) if f.endswith(".mp3") or f.endswith(".wav")]

            if not final_files and not audio_files and not os.path.exists(os.path.join(task_path, "script.json")):
                continue

            fname = final_files[0] if final_files else (audio_files[0] if audio_files else "script.json")
            full_path = os.path.join(task_path, fname)

            # Read script metadata & build engaging title
            subject = ""
            script_text = ""
            script_path = os.path.join(task_path, "script.json")
            if os.path.exists(script_path):
                try:
                    with open(script_path, "r", encoding="utf-8") as sf:
                        sdata = json.load(sf)
                        script_text = sdata.get("script", "")
                        subject = sdata.get("subject", "")
                except Exception:
                    pass

            if not subject:
                if script_text:
                    first_sentence = script_text.split(".")[0].split("?")[0].split("!")[0].strip()
                    subject = first_sentence[:60] if len(first_sentence) > 10 else f"Video {task_folder[:8]}"
                else:
                    subject = f"Video {task_folder[:8]}"

            # Assign channel cyclically or based on topic keywords
            assigned_ch = ch_ids[idx % len(ch_ids)]
            if "psicologia" in script_text.lower() or "mente" in script_text.lower() or "dark" in script_text.lower():
                assigned_ch = next((c["id"] for c in channels if "psicologia" in c.get("niche", "").lower() or "ig" in c["id"]), assigned_ch)
            elif "spazio" in script_text.lower() or "cosm" in script_text.lower() or "galassi" in script_text.lower():
                assigned_ch = next((c["id"] for c in channels if "spazio" in c.get("niche", "").lower() or "yt" in c["id"]), assigned_ch)
            elif "curiosit" in script_text.lower() or "sapevi" in script_text.lower():
                assigned_ch = next((c["id"] for c in channels if "curiosit" in c.get("niche", "").lower() or "tt" in c["id"]), assigned_ch)

            size_mb = round(os.path.getsize(full_path) / (1024 * 1024), 2) if os.path.exists(full_path) else 0.0
            created_str = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(full_path)) if os.path.exists(full_path) else time.time()
            )

            new_video = {
                "id": f"vid_{task_folder}",
                "task_id": task_folder,
                "title": subject,
                "channel_id": assigned_ch,
                "status": "draft",
                "file_path": full_path,
                "file_name": fname,
                "size_mb": size_mb,
                "script": script_text,
                "created_at": created_str,
                "gdrive_synced": False,
                "gdrive_link": None,
                "gdrive_file_id": None,
                "publications": {},
            }
            data["videos"].append(new_video)
            added += 1

    if added > 0:
        _save_data(data)
        logger.info(f"Auto-registered {added} new video drafts.")

    return added


# ─────────────────────────────── STATS ─────────────────────────────────────

def get_catalog_stats() -> Dict[str, Any]:
    data = _load_data()
    videos = data.get("videos", [])
    channels = data.get("channels", [])
    statuses = {"draft": 0, "approved": 0, "published": 0, "rejected": 0}
    for v in videos:
        s = v.get("status", "draft")
        statuses[s] = statuses.get(s, 0) + 1

    platforms: Dict[str, int] = {}
    for ch in channels:
        p = ch.get("platform", "Unknown")
        platforms[p] = platforms.get(p, 0) + 1

    return {
        "total_channels": len(channels),
        "active_channels": sum(1 for c in channels if c.get("active", True)),
        "total_videos": len(videos),
        "by_status": statuses,
        "by_platform": platforms,
        "gdrive_account": data.get("gdrive_account", "mrvinxsrl@gmail.com"),
        # False unless a real OAuth token file exists
        "gdrive_connected": data.get("gdrive_connected", False),
    }
