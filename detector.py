import re
from urllib.parse import urlparse


SUSPICIOUS_PATTERNS = {
    "urgency": [
        "urgent", "immediately", "act now", "last chance", "final warning",
        "suspended", "expire", "expires today", "limited time", "now now"
    ],
    "credentials": [
        "verify your account", "confirm your account", "password", "otp",
        "pin", "login", "banking details", "security code", "username"
    ],
    "money": [
        "payment", "pay now", "deposit", "release fee", "clearance fee",
        "processing fee", "transfer funds", "claim now", "refund", "cashout"
    ],
    "impersonation": [
        "bank", "sars", "courier", "customs", "hr department", "recruiter",
        "microsoft", "paypal", "capitec", "fnb", "absa", "nedbank", "standard bank"
    ],
    "job_scam": [
        "job offer", "registration fee", "training fee", "work from home",
        "earn daily", "earn per day", "no experience needed"
    ],
    "prize_scam": [
        "winner", "you have won", "congratulations", "prize", "lottery",
        "claim your reward", "gift"
    ],
    "sa_specific": [
        "sars refund", "parcel release", "clear your parcel", "ewallet reversal",
        "bank verification", "sim swap", "load shedding grant"
    ]
}

SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "is.gd", "ow.ly", "buff.ly", "grabify.link"
}

SAFE_DOMAINS_HINTS = {
    "gov.za", "sars.gov.za", "bank.co.za"
}


def extract_urls(text):
    return re.findall(r'https?://[^\s]+', text)


def count_uppercase_words(text):
    words = re.findall(r'\b[A-Z]{3,}\b', text)
    return len(words)


def count_exclamations(text):
    return text.count("!")


def domain_from_url(url):
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower().replace("www.", "")
    except Exception:
        return ""


def analyze_patterns(text_lower):
    score = 0
    reasons = []

    for category, phrases in SUSPICIOUS_PATTERNS.items():
        for phrase in phrases:
            if phrase in text_lower:
                score += 1
                reasons.append(f"Matched {category.replace('_', ' ')} phrase: '{phrase}'")

    return score, reasons


def analyze_urls(urls):
    score = 0
    reasons = []

    if urls:
        score += len(urls)
        reasons.append("Contains link(s), which increases risk")

    for url in urls:
        domain = domain_from_url(url)

        if domain in SHORTENER_DOMAINS:
            score += 3
            reasons.append(f"Uses shortened or suspicious link: '{domain}'")

        if "@" in url:
            score += 2
            reasons.append("Link contains '@', which can hide the real destination")

        if any(char.isdigit() for char in domain) and "." in domain:
            score += 1
            reasons.append(f"Domain contains unusual numbers: '{domain}'")

        if domain and not any(hint in domain for hint in SAFE_DOMAINS_HINTS):
            if any(keyword in domain for keyword in ["verify", "secure", "login", "claim", "reward"]):
                score += 2
                reasons.append(f"Domain looks suspicious: '{domain}'")

    return score, reasons


def analyze_style(text):
    score = 0
    reasons = []

    uppercase_words = count_uppercase_words(text)
    exclamations = count_exclamations(text)

    if uppercase_words >= 3:
        score += 1
        reasons.append("Uses excessive capitalized words to create pressure")

    if exclamations >= 3:
        score += 1
        reasons.append("Uses excessive exclamation marks to create urgency")

    if re.search(r'\b(?:\+27|27|0)\d{9}\b', text.replace(" ", "")):
        score += 1
        reasons.append("Contains phone-number style contact details often seen in scams")

    return score, reasons


def classify_risk(score):
    if score >= 8:
        return "High Risk 🚨", "Do NOT click links, send money, or share personal information."
    if score >= 4:
        return "Suspicious ⚠️", "Be careful. Verify the sender using an official contact channel."
    return "Likely Safe ✅", "No strong scam indicators were found, but stay cautious."


def analyze_text(text):
    text_lower = text.lower()

    score = 0
    reasons = []

    pattern_score, pattern_reasons = analyze_patterns(text_lower)
    score += pattern_score
    reasons.extend(pattern_reasons)

    urls = extract_urls(text)
    url_score, url_reasons = analyze_urls(urls)
    score += url_score
    reasons.extend(url_reasons)

    style_score, style_reasons = analyze_style(text)
    score += style_score
    reasons.extend(style_reasons)

    # Reduce repeated reasons while preserving order
    unique_reasons = list(dict.fromkeys(reasons))

    risk, advice = classify_risk(score)

    return {
        "risk": risk,
        "score": score,
        "reasons": unique_reasons,
        "advice": advice
    }