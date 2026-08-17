"""
UGC (User Generated Content) Video Generation Engine for MoneyPrinterTurbo.
Specialized in creating high-converting viral ad scripts, product reviews, and creator-style videos.
"""

from typing import Dict, List, Optional
from loguru import logger

from app.models.schema import VideoAspect, VideoConcatMode, VideoParams
from app.services import llm

UGC_ANGLES = {
    "problem_solution": {
        "label": "Problem & Solution (Problema / Soluzione Immediata)",
        "hook_style": "Identifica il problema doloroso nei primi 2 secondi e mostra la soluzione magica.",
    },
    "honest_review": {
        "label": "Honest Review (Recensione Sincera / 'Ho provato questo per 30 giorni')",
        "hook_style": "Crea massima fiducia con un tono informale, trasparente e test reale.",
    },
    "dont_buy_hook": {
        "label": "Pattern Interrupt ('Non comprare questo finché...')",
        "hook_style": "Shock hook iniziale che ferma lo scroll con una negazione intrigante.",
    },
    "top_reasons": {
        "label": "Top 3 Reasons ('3 motivi per cui tutti usano...')",
        "hook_style": "Elenco numerato ultra-veloce e dinamico con benefici chiari.",
    },
    "life_hack": {
        "label": "Life Hack / Secret Tool ('Il trucco segreto che nessuno ti dice')",
        "hook_style": "Posiziona il prodotto come un'arma segreta o scorciatoia definitiva.",
    },
}

UGC_SYSTEM_PROMPT = """
# Role: Elite UGC (User Generated Content) Video Creator & Direct Response Copywriter.

## Goal:
Write a viral, authentic, high-converting vertical video script (TikTok / Instagram Reels / YouTube Shorts).

## 5-Phase UGC Conversion Structure:
1. **SCROLL-STOPPING HOOK (0-3s)**: Extreme curiosity or direct pain point. Never start with greetings.
2. **PAIN POINT & AGITATION (3-12s)**: Describe the frustrating struggle in raw, relatable human words.
3. **THE SOLUTION & DEMO (12-30s)**: Introduce the tool/product as the effortless breakthrough. Explain what it does.
4. **SOCIAL PROOF & TRANSFORMATION (30-45s)**: Mention results, ease of use, or community adoption.
5. **URGENT CTA (45-60s)**: Direct, clear command (e.g. "Check the link in bio / comment below to get it now").

## Strict Rules:
- Return ONLY the spoken words for the voiceover.
- NO brackets, NO narrator cues, NO markdown titles, NO timestamps.
- Short, punchy sentences tailored for natural speech rhythm.
- Write in the requested target language (Italian by default).
""".strip()


def generate_ugc_script(
    product_or_subject: str,
    niche: str = "Tech / AI / Productivity",
    pain_point: str = "",
    angle_key: str = "problem_solution",
    language: str = "it-IT",
    custom_instructions: str = "",
) -> Dict[str, any]:
    """
    Generates a high-converting UGC script and visual stock terms.
    """
    angle = UGC_ANGLES.get(angle_key, UGC_ANGLES["problem_solution"])
    
    prompt = f"""
Create a 100% viral UGC video script about: "{product_or_subject}".
Niche/Category: {niche}
Target Pain Point: {pain_point or 'Frustration with slow results and wasted time'}
Angle Style: {angle['label']} - {angle['hook_style']}
Language: {language}

{f"Additional instructions: {custom_instructions}" if custom_instructions else ""}
""".strip()

    try:
        script = llm.generate_script(
            video_subject=f"UGC: {product_or_subject}",
            language=language,
            paragraph_number=3,
            video_script_prompt=prompt,
            custom_system_prompt=UGC_SYSTEM_PROMPT,
        )
    except Exception as e:
        logger.error(f"UGC script generation failed: {e}")
        # High-conversion fallback template
        if "it" in language.lower():
            script = (
                f"Se stai ancora perdendo ore con {niche}, fermati un secondo. "
                f"Tutti stanno parlando di {product_or_subject} per un motivo ben preciso: "
                f"risolve {pain_point or 'ogni complicazione'} in pochi secondi senza alcuno sforzo. "
                f"Non fidarti sulla parola, guarda i risultati e provalo subito dal link!"
            )
        else:
            script = (
                f"If you're still wasting hours struggling with {niche}, stop scrolling. "
                f"Everyone is talking about {product_or_subject} for one simple reason: "
                f"it eliminates {pain_point or 'all the friction'} in seconds with zero hassle. "
                f"Check out the link right now and see the difference for yourself!"
            )

    try:
        terms = llm.generate_terms(
            video_subject=f"{product_or_subject} {niche}",
            video_script=script,
            amount=6,
            match_script_order=True,
        )
    except Exception as e:
        logger.warning(f"UGC terms generation error: {e}")
        terms = ["person using phone", "happy creator", "fast laptop", "digital solution", "success", "click"]

    return {
        "script": script,
        "terms": terms,
        "angle": angle_key,
        "subject": product_or_subject,
    }


def build_ugc_video_params(
    ugc_data: Dict[str, any],
    voice_name: str = "it-IT-DiegoNeural",
    video_source: str = "pexels",
    bgm_volume: float = 0.12,
) -> VideoParams:
    """
    Constructs an optimized VideoParams object tuned specifically for vertical UGC video metrics.
    """
    params = VideoParams(
        video_subject=f"UGC - {ugc_data.get('subject', 'Product Showcase')}",
        video_script=ugc_data.get("script", ""),
        video_terms=ugc_data.get("terms", []),
        video_aspect=VideoAspect.portrait.value,
        video_concat_mode=VideoConcatMode.sequential.value,
        video_clip_duration=3,  # Fast 3s cuts for high retention
        video_clip_speed=1.0,
        match_materials_to_script=True,
        video_source=video_source,
        voice_name=voice_name,
        voice_rate=1.05,  # Slightly faster for high-energy creator feel
        voice_volume=1.0,
        bgm_name="random",
        bgm_volume=bgm_volume,
        subtitle_enabled=True,
        font_name="MicrosoftYaHeiBold.ttc",
        font_size=68,
        text_fore_color="#FFE600",  # High-converting energetic yellow
        stroke_color="#000000",
        stroke_width=2.5,
        subtitle_position="bottom",
        custom_position=72.0,
    )
    return params
