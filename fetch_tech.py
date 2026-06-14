import json
import os
import re
from datetime import datetime, timezone
from typing import List, Dict
from xml.etree import ElementTree

import requests
from google import genai

RSS_FEEDS = [
    "https://hnrss.org/frontpage",
    "https://www.reddit.com/r/technology/.rss",
]

OUTPUT_FILE = "data.json"
MAX_CANDIDATES = 25
MAX_ITEMS = 10
DEFAULT_CANDIDATES = [
    "IA générative et assistants multimodaux",
    "Nouveautés cloud et infrastructure",
    "Cybersécurité et vulnérabilités critiques",
    "Avancées open source et frameworks web",
    "Tendances mobiles et applications",
    "Robotique et automatisation industrielle",
    "Semi-conducteurs et puces IA",
    "Réalité augmentée et virtuelle",
    "Régulation technologique et conformité",
    "Green IT et sobriété numérique",
]


def fetch_rss_titles(url: str) -> List[str]:
    response = requests.get(url, timeout=20, headers={"User-Agent": "Tech-actu-bot/1.0"})
    response.raise_for_status()

    root = ElementTree.fromstring(response.content)
    titles: List[str] = []

    # RSS 2.0
    for item in root.findall(".//channel/item/title"):
        if item.text:
            titles.append(item.text.strip())

    # Atom fallback
    if not titles:
        for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
            title = entry.find("{http://www.w3.org/2005/Atom}title")
            if title is not None and title.text:
                titles.append(title.text.strip())

    return titles


def clean_json_text(raw_text: str) -> str:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned


def summarize_with_gemini(candidates: List[str]) -> List[Dict[str, str]]:
    api_key = os.environ["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)

    prompt = (
        "Tu es un assistant éditorial tech. "
        "À partir de la liste de titres suivante, sélectionne les 10 sujets les plus importants du moment, "
        "traduis les titres en français si nécessaire, et produis un résumé concis (1-2 phrases) en français. "
        "Retourne STRICTEMENT un JSON valide sous forme de tableau avec exactement cette structure: "
        "[{\"title\": \"...\", \"summary\": \"...\", \"source\": \"...\"}]. "
        "Le champ source doit être 'Hacker News' ou 'Reddit'.\n\n"
        "Titres candidats:\n"
    )

    prompt += "\n".join(f"- {title}" for title in candidates)

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
    )

    raw = response.text or "[]"
    data = json.loads(clean_json_text(raw))

    if not isinstance(data, list):
        raise ValueError("Gemini response is not a list")

    normalized = []
    for item in data[:MAX_ITEMS]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        summary = str(item.get("summary", "")).strip()
        source = str(item.get("source", "")).strip() or "Tech"
        if title and summary:
            normalized.append({"title": title, "summary": summary, "source": source})

    return normalized[:MAX_ITEMS]


def fallback_items(candidates: List[str]) -> List[Dict[str, str]]:
    return [
        {
            "title": title,
            "summary": "Sujet technologique en tendance. Résumé IA indisponible temporairement.",
            "source": "Flux RSS",
        }
        for title in candidates[:MAX_ITEMS]
    ]


def ensure_minimum_items(items: List[Dict[str, str]], candidates: List[str]) -> List[Dict[str, str]]:
    final_items = list(items[:MAX_ITEMS])
    missing = MAX_ITEMS - len(final_items)
    if missing <= 0:
        return final_items

    reserve_titles = [title for title in candidates if title not in {i["title"] for i in final_items}]
    for title in reserve_titles[:missing]:
        final_items.append(
            {
                "title": title,
                "summary": "Actualité technologique à surveiller aujourd'hui.",
                "source": "Flux RSS",
            }
        )

    while len(final_items) < MAX_ITEMS:
        final_items.append(
            {
                "title": f"Veille technologique #{len(final_items) + 1}",
                "summary": "Mise à jour automatique en attente de nouvelles sources.",
                "source": "Tech Actu",
            }
        )

    return final_items


def main() -> None:
    all_candidates: List[str] = []

    for feed in RSS_FEEDS:
        try:
            all_candidates.extend(fetch_rss_titles(feed))
        except Exception as exc:  # noqa: BLE001
            print(f"Erreur RSS ({feed}): {exc}")

    # De-duplication preserving order
    deduped = list(dict.fromkeys(all_candidates))[:MAX_CANDIDATES]

    if not deduped:
        print("Aucun sujet RSS récupéré, utilisation des sujets par défaut.")
        deduped = DEFAULT_CANDIDATES.copy()

    try:
        items = summarize_with_gemini(deduped)
    except Exception as exc:  # noqa: BLE001
        print(f"Erreur Gemini, fallback activé: {exc}")
        items = fallback_items(deduped)
    items = ensure_minimum_items(items, deduped)

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "items": items,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"✅ {OUTPUT_FILE} mis à jour avec {len(items)} entrées")


if __name__ == "__main__":
    main()
