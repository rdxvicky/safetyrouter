"""
Crisis resource database and escalation utilities.

Country crisis database with emergency numbers, helplines, and webchat links.
Used by SafetyRouter for two-tier mental health escalation.
"""
import json
import os
import urllib.parse
from datetime import datetime
from typing import Any, Dict, Optional


CRISIS_DB = {
    "US": {
        "emergency": "911",
        "helpline": "988",
        "helpline_name": "988 Suicide & Crisis Lifeline",
        "webchat": "https://988lifeline.org/chat",
        "youth_line": "1-800-448-3000",
    },
    "UK": {
        "emergency": "999",
        "helpline": "116 123",
        "helpline_name": "Samaritans",
        "webchat": "https://www.samaritans.org/how-we-can-help/contact-samaritan/webchat/",
    },
    "CA": {
        "emergency": "911",
        "helpline": "1-833-456-4566",
        "helpline_name": "Crisis Services Canada",
        "webchat": "https://www.crisisservicescanada.ca",
    },
    "AU": {
        "emergency": "000",
        "helpline": "13 11 14",
        "helpline_name": "Lifeline Australia",
        "webchat": "https://www.lifeline.org.au/crisis-chat/",
    },
    "IN": {
        "emergency": "112",
        "helpline": "9152987821",
        "helpline_name": "iCall",
        "webchat": "https://icallhelpline.org",
    },
    "NZ": {
        "emergency": "111",
        "helpline": "1737",
        "helpline_name": "Need to Talk?",
        "webchat": "https://1737.org.nz",
    },
    "DE": {
        "emergency": "112",
        "helpline": "0800 111 0 111",
        "helpline_name": "Telefonseelsorge",
        "webchat": "https://online.telefonseelsorge.de",
    },
    "FR": {
        "emergency": "15",
        "helpline": "3114",
        "helpline_name": "Numéro National de Prévention du Suicide",
        "webchat": "https://www.3114.fr",
    },
    "JP": {
        "emergency": "119",
        "helpline": "0120-783-556",
        "helpline_name": "Inochi no Denwa",
        "webchat": None,
    },
    "BR": {
        "emergency": "192",
        "helpline": "188",
        "helpline_name": "CVV",
        "webchat": "https://cvv.org.br/chat/",
    },
    "MX": {
        "emergency": "911",
        "helpline": "800 290 0024",
        "helpline_name": "SAPTEL",
        "webchat": None,
    },
    "ZA": {
        "emergency": "10111",
        "helpline": "0800 567 567",
        "helpline_name": "SADAG",
        "webchat": "https://www.sadag.org",
    },
    "SG": {
        "emergency": "999",
        "helpline": "1800 221 4444",
        "helpline_name": "Samaritans of Singapore",
        "webchat": "https://www.sos.org.sg",
    },
    "IE": {
        "emergency": "999",
        "helpline": "116 123",
        "helpline_name": "Samaritans Ireland",
        "webchat": "https://www.samaritans.org/ireland/how-we-can-help/contact-samaritan/webchat/",
    },
    "MY": {
        "emergency": "999",
        "helpline": "015-4882 3500",
        "helpline_name": "Befrienders KL",
        "webchat": "https://www.befrienders.org.my",
    },
    "_DEFAULT": {
        "emergency": "Your local emergency number",
        "helpline": "988 (if in US) or local helpline",
        "helpline_name": "Local Crisis Helpline",
        "webchat": "https://www.befrienders.org",
    },
}

# Common country name → ISO-2 code mapping
COUNTRY_NAME_TO_CODE: Dict[str, str] = {
    "united states": "US", "usa": "US", "america": "US",
    "united kingdom": "UK", "britain": "UK", "england": "UK", "gb": "UK",
    "canada": "CA",
    "australia": "AU",
    "india": "IN",
    "new zealand": "NZ",
    "germany": "DE",
    "france": "FR",
    "japan": "JP",
    "brazil": "BR",
    "mexico": "MX",
    "south africa": "ZA",
    "singapore": "SG",
    "ireland": "IE",
    "malaysia": "MY",
}

COUNTRY_CODE_TO_NAME: Dict[str, str] = {
    "US": "United States", "UK": "United Kingdom", "CA": "Canada",
    "AU": "Australia", "IN": "India", "NZ": "New Zealand",
    "DE": "Germany", "FR": "France", "JP": "Japan", "BR": "Brazil",
    "MX": "Mexico", "ZA": "South Africa", "SG": "Singapore",
    "IE": "Ireland", "MY": "Malaysia",
}


def normalize_country_code(country: str) -> str:
    """Convert country name or code to uppercase ISO-2 code."""
    country = country.strip()
    if len(country) == 2:
        return country.upper()
    return COUNTRY_NAME_TO_CODE.get(country.lower(), country.upper()[:2])


def get_crisis_resources(country_code: str) -> dict:
    code = normalize_country_code(country_code)
    return CRISIS_DB.get(code, CRISIS_DB["_DEFAULT"])


def get_emergency_number(country_code: str) -> str:
    return get_crisis_resources(country_code)["emergency"]


def get_helpline(country_code: str) -> dict:
    r = get_crisis_resources(country_code)
    return {
        "number": r["helpline"],
        "name": r["helpline_name"],
        "webchat": r.get("webchat"),
    }


def build_session_transcript(
    text: str,
    mental_health_scores: Dict[str, Any],
    user_name: Optional[str] = None,
    age_range: Optional[str] = None,
    country: str = "US",
) -> str:
    """Save session transcript to ~/.safetyrouter/sessions/<timestamp>.json. Returns path."""
    sessions_dir = os.path.expanduser("~/.safetyrouter/sessions")
    os.makedirs(sessions_dir, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
    path = os.path.join(sessions_dir, f"{ts}.json")

    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_name": user_name,
        "age_range": age_range,
        "country": country,
        "text": text,
        "mental_health_scores": mental_health_scores,
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)

    return path


def build_mailto_link(
    crisis_service: dict,
    transcript_path: str,
    user_name: Optional[str] = None,
) -> str:
    """Build a mailto: URL pre-filled with session summary."""
    name_part = f"Hi,\n\nMy name is {user_name}.\n\n" if user_name else "Hi,\n\n"
    body = (
        f"{name_part}"
        f"I am reaching out because I may need support.\n\n"
        f"Crisis resource I was referred to: {crisis_service.get('helpline_name', 'Local Helpline')} "
        f"({crisis_service.get('helpline', '')})\n\n"
        f"Session transcript saved at: {transcript_path}\n\n"
        f"Please help me.\n"
    )
    params = urllib.parse.urlencode(
        {"subject": "I need support", "body": body},
        quote_via=urllib.parse.quote,
    )
    return f"mailto:?{params}"
