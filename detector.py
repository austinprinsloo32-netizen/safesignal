import re
from io import BytesIO
from urllib.parse import urlparse

import os
import requests
from PIL import Image, ImageOps, ImageFilter


WEIGHTS = {
    "weak": 1,
    "medium": 2,
    "strong": 4,
    "critical": 6
}

SUSPICIOUS_PATTERNS = {
    "urgency": [
        "urgent", "immediately", "act now", "last chance", "final warning",
        "suspended", "expire", "expires today", "limited time", "now now",
        "today only", "pay today", "respond immediately", "before it expires"
    ],
    "credentials": [
        "verify your account", "confirm your account", "password", "otp",
        "pin", "login", "banking details", "security code", "username"
    ],
    "money": [
        "payment", "pay now", "deposit", "release fee", "clearance fee",
        "processing fee", "transfer funds", "claim now", "refund", "cashout",
        "registration fee", "application fee", "placement fee", "activation fee",
        "secure your spot", "to secure your spot", "pay today"
    ],
    "impersonation": [
        "bank", "sars", "courier", "customs", "hr department", "recruiter",
        "microsoft", "paypal", "capitec", "fnb", "absa", "nedbank", "standard bank"
    ],
    "job_scam": [
        "job offer", "registration fee", "training fee", "work from home",
        "earn daily", "earn per day", "no experience needed",
        "interview fee", "placement fee", "application fee",
        "approved for the job", "secure your job", "to secure your spot"
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

SUSPICIOUS_URL_KEYWORDS = {
    "verify", "secure", "login", "claim", "reward", "update",
    "bank", "wallet", "confirm", "password", "account", "pay"
}

FREE_EMAIL_PROVIDERS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com", "proton.me"
}

BRAND_DOMAINS = {
    "paypal": ["paypal.com"],
    "microsoft": ["microsoft.com", "outlook.com", "live.com"],
    "sars": ["sars.gov.za"],
    "capitec": ["capitecbank.co.za"],
    "fnb": ["fnb.co.za"],
    "absa": ["absa.co.za"],
    "nedbank": ["nedbank.co.za"],
    "standard bank": ["standardbank.co.za"],
}

INSIGHT_MAP = {
    "urgency": {
        "title": "Urgency Pressure",
        "explanation": "Scammers create panic or time pressure so people act quickly without verifying."
    },
    "credentials": {
        "title": "Credential Harvesting",
        "explanation": "The message appears to be trying to collect passwords, OTPs, PINs, or account access details."
    },
    "money": {
        "title": "Payment Extraction",
        "explanation": "The content pushes for money, fees, refunds, or transfers, which is a common scam goal."
    },
    "impersonation": {
        "title": "Authority Impersonation",
        "explanation": "Scammers often pretend to be trusted institutions or brands to make the message feel legitimate."
    },
    "job_scam": {
        "title": "Job Scam Pattern",
        "explanation": "Fake job offers often promise easy income or request upfront fees for registration, training, or placement."
    },
    "prize_scam": {
        "title": "Prize Bait",
        "explanation": "Messages about winning prizes or rewards are often used to lure people into clicking links or sharing information."
    },
    "sa_specific": {
        "title": "Local Scam Pattern",
        "explanation": "The content matches scam themes commonly seen in South African fraud messages."
    },
    "suspicious_url": {
        "title": "Suspicious Link Structure",
        "explanation": "The URL uses traits often seen in phishing links, such as masking, suspicious keywords, or unusual domain structure."
    },
    "suspicious_sender": {
        "title": "Suspicious Sender Identity",
        "explanation": "The sender information looks inconsistent, manipulative, or unprofessional for a legitimate message."
    }
}


class OCRServiceError(Exception):
    pass


def extract_urls(text):
    pattern = r'(https?://[^\s]+|www\.[^\s]+)'
    return re.findall(pattern, text)


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


def extract_root_domain(domain):
    parts = domain.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return domain


def is_ip_address(domain):
    return bool(re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", domain))


def generate_insights(categories):
    insights = []
    seen = set()

    for category in categories:
        if category in INSIGHT_MAP and category not in seen:
            seen.add(category)
            insights.append({
                "title": INSIGHT_MAP[category]["title"],
                "explanation": INSIGHT_MAP[category]["explanation"]
            })

    return insights


def analyze_patterns(text_lower):
    score = 0
    reasons = []
    categories_found = []

    for category, phrases in SUSPICIOUS_PATTERNS.items():
        for phrase in phrases:
            phrase_lower = phrase.lower()

            # Use stricter matching for short terms like "pin", "otp", "bank"
            if re.search(rf'\b{re.escape(phrase_lower)}\b', text_lower):
                if category in ["urgency", "job_scam", "prize_scam"]:
                    score += WEIGHTS["weak"]
                elif category in ["credentials", "money"]:
                    score += WEIGHTS["strong"]
                elif category in ["impersonation", "sa_specific"]:
                    score += WEIGHTS["critical"]

                reasons.append(f"Matched {category.replace('_', ' ')} phrase: '{phrase}'")
                categories_found.append(category)

    return score, reasons, categories_found


def analyze_urls(urls):
    score = 0
    reasons = []
    categories_found = []

    for url in urls:
        domain = domain_from_url(url)

        if domain in SHORTENER_DOMAINS:
            score += WEIGHTS["strong"]
            reasons.append(f"Uses shortened or suspicious link: '{domain}'")
            categories_found.append("suspicious_url")

        if "@" in url:
            score += WEIGHTS["strong"]
            reasons.append("Link contains '@', which can hide the real destination")
            categories_found.append("suspicious_url")

        if any(char.isdigit() for char in domain) and "." in domain:
            score += WEIGHTS["weak"]
            reasons.append(f"Domain contains unusual numbers: '{domain}'")
            categories_found.append("suspicious_url")

        if domain and not any(hint in domain for hint in SAFE_DOMAINS_HINTS):
            if any(keyword in domain for keyword in ["verify", "secure", "login", "claim", "reward"]):
                score += WEIGHTS["medium"]
                reasons.append(f"Domain looks suspicious: '{domain}'")
                categories_found.append("suspicious_url")

    return score, reasons, categories_found


def analyze_style(text):
    score = 0
    reasons = []
    categories_found = []

    uppercase_words = count_uppercase_words(text)
    exclamations = count_exclamations(text)

    text_lower = text.lower()
    has_urgent_words = any(word in text_lower for word in [
        "urgent", "immediately", "act now", "final warning", "last chance", "suspended"
    ])

    if uppercase_words >= 5 and (exclamations >= 2 or has_urgent_words):
        score += WEIGHTS["weak"]
        reasons.append("Uses many capitalized words with pressure language")
        categories_found.append("urgency")

    if exclamations >= 3:
        score += WEIGHTS["weak"]
        reasons.append("Uses excessive exclamation marks to create urgency")
        categories_found.append("urgency")

    return score, reasons, categories_found


def classify_risk(score):
    if score >= 12:
        return "High Risk 🚨", "This looks like a scam. Do NOT click links, send money, or share personal information."
    elif score >= 6:
        return "Suspicious ⚠️", "Be careful. Verify the sender using an official contact channel before taking action."
    else:
        return "Likely Safe ✅", "No strong scam indicators were found, but stay cautious."


def analyze_text(text):
    text_lower = text.lower()

    base_score = 0
    combo_bonus = 0
    legit_bonus = 0

    reasons = []
    legit_reasons = []
    categories_found = []

    pattern_score, pattern_reasons, pattern_categories = analyze_patterns(text_lower)
    base_score += pattern_score
    reasons.extend(pattern_reasons)
    categories_found.extend(pattern_categories)

    urls = extract_urls(text)
    url_score, url_reasons, url_categories = analyze_urls(urls)
    base_score += url_score
    reasons.extend(url_reasons)
    categories_found.extend(url_categories)

    style_score, style_reasons, style_categories = analyze_style(text)
    base_score += style_score
    reasons.extend(style_reasons)
    categories_found.extend(style_categories)

    has_urgency = "urgency" in categories_found
    has_money = "money" in categories_found
    has_credentials = "credentials" in categories_found
    has_url = len(urls) > 0
    has_job_scam = "job_scam" in categories_found
    has_prize_scam = "prize_scam" in categories_found
    has_impersonation = "impersonation" in categories_found

    if has_urgency and has_money:
        combo_bonus += 3
        reasons.append("Combo: urgency + payment request")

    if has_urgency and has_credentials:
        combo_bonus += 4
        reasons.append("Combo: urgency + credential request")

    if has_url and has_credentials:
        combo_bonus += 4
        reasons.append("Combo: link + credential request")

    if has_job_scam and has_money:
        combo_bonus += 5
        reasons.append("Combo: job-related message + payment request")

    if has_prize_scam and has_money:
        combo_bonus += 5
        reasons.append("Combo: reward/prize language + payment request")

    if has_job_scam and has_urgency:
        combo_bonus += 3
        reasons.append("Combo: urgency + job-related pressure")

    if has_impersonation and has_money:
        combo_bonus += 4
        reasons.append("Combo: impersonation + payment request")

    doc_titles = ["invoice", "medical certificate", "statement", "receipt", "quotation"]

    if any(title in text_lower for title in doc_titles):
        legit_bonus += 3
        legit_reasons.append("Recognized document format")

    if "@" in text:
        legit_bonus += 2
        legit_reasons.append("Email/contact info present")

    address_words = ["street", "road", "avenue", "suite", "private bag", "po box"]
    if any(word in text_lower for word in address_words):
        legit_bonus += 3
        legit_reasons.append("Physical address detected")

    if re.search(r'\b(?:\+27|27|0)\d{9}\b', text.replace(" ", "")):
        legit_bonus += 2
        legit_reasons.append("Phone number present")

    final_score = base_score + combo_bonus - legit_bonus
    final_score = max(0, min(100, final_score))

    unique_reasons = list(dict.fromkeys(reasons))
    insights = generate_insights(categories_found)
    risk, advice = classify_risk(final_score)

    if not unique_reasons:
        unique_reasons = ["No specific warning signals were found."]

    return {
        "risk": risk,
        "score": final_score,
        "reasons": unique_reasons,
        "legit_reasons": legit_reasons,
        "insights": insights,
        "advice": advice,
        "debug": {
            "base_score": base_score,
            "combo_bonus": combo_bonus,
            "legit_bonus": legit_bonus
        }
    }


def analyze_single_url(url):
    if not url or not url.strip():
        return {
            "risk": "Invalid Input",
            "score": 0,
            "reasons": ["No URL was provided."],
            "insights": [],
            "advice": "Paste a full link to analyze it."
        }

    original_url = url.strip()

    if not original_url.startswith(("http://", "https://")):
        original_url = "http://" + original_url

    parsed = urlparse(original_url)
    domain = parsed.netloc.lower().replace("www.", "")
    path = parsed.path.lower()

    if not domain:
        return {
            "risk": "Invalid Input",
            "score": 0,
            "reasons": ["Could not read a valid domain from that URL."],
            "insights": [],
            "advice": "Make sure the link is in a valid format."
        }

    score = 0
    reasons = []
    categories_found = []

    root_domain = extract_root_domain(domain)

    if domain in SHORTENER_DOMAINS or root_domain in SHORTENER_DOMAINS:
        score += WEIGHTS["strong"]
        reasons.append(f"Uses shortened or masked link: '{domain}'")
        categories_found.append("suspicious_url")

    if is_ip_address(domain):
        score += WEIGHTS["critical"]
        reasons.append("Uses an IP address instead of a normal domain")
        categories_found.append("suspicious_url")

    if "@" in original_url:
        score += WEIGHTS["strong"]
        reasons.append("URL contains '@', which can hide the true destination")
        categories_found.append("suspicious_url")

    if "xn--" in domain:
        score += WEIGHTS["critical"]
        reasons.append("Domain contains punycode, which can be used for lookalike scams")
        categories_found.append("suspicious_url")

    if domain.count(".") >= 3:
        score += WEIGHTS["medium"]
        reasons.append("Domain uses many subdomains, which can be suspicious")
        categories_found.append("suspicious_url")

    if any(char.isdigit() for char in domain):
        score += WEIGHTS["weak"]
        reasons.append(f"Domain contains numbers: '{domain}'")
        categories_found.append("suspicious_url")

    if domain.count("-") >= 2:
        score += WEIGHTS["weak"]
        reasons.append("Domain uses many hyphens, which is common in phishing links")
        categories_found.append("suspicious_url")

    combined = f"{domain}{path}"

    suspicious_keywords_found = [
        keyword for keyword in SUSPICIOUS_URL_KEYWORDS
        if keyword in combined
    ]

    for keyword in suspicious_keywords_found:
        score += WEIGHTS["medium"]
        reasons.append(f"URL contains suspicious keyword: '{keyword}'")
        categories_found.append("suspicious_url")

    suspicious_lookalikes = [
        "paypa1", "micr0soft", "capitec-secure", "fnb-verify", "absa-login"
    ]

    if any(fake in domain for fake in suspicious_lookalikes):
        score += WEIGHTS["critical"]
        reasons.append("Domain appears to imitate a trusted brand")
        categories_found.append("suspicious_url")

    high_risk_url_flags = 0

    if any(char.isdigit() for char in domain):
        high_risk_url_flags += 1

    if domain.count("-") >= 2:
        high_risk_url_flags += 1

    if suspicious_keywords_found:
        high_risk_url_flags += 1

    if high_risk_url_flags >= 3:
        score += WEIGHTS["critical"]
        reasons.append("Multiple phishing-style URL traits detected")
        categories_found.append("suspicious_url")

    unique_reasons = list(dict.fromkeys(reasons))
    insights = generate_insights(categories_found)
    risk, advice = classify_risk(score)

    if not unique_reasons:
        unique_reasons = ["No strong structural scam indicators were found in the URL."]

    return {
        "risk": risk,
        "score": score,
        "reasons": unique_reasons,
        "insights": insights,
        "advice": advice,
        "domain": domain
    }


def analyze_email(sender, subject, body):
    sender = (sender or "").strip()
    subject = (subject or "").strip()
    body = (body or "").strip()

    combined_text = f"{subject}\n{body}"
    result = analyze_text(combined_text)

    score = result["score"]
    reasons = list(result["reasons"])
    categories_found = []
    legit_reasons = result.get("legit_reasons", [])

    for insight in result.get("insights", []):
        for key, value in INSIGHT_MAP.items():
            if value["title"] == insight["title"]:
                categories_found.append(key)

    sender_domain = ""

    if sender:
        sender_lower = sender.lower()

        if "@" not in sender_lower:
            score += WEIGHTS["medium"]
            reasons.append("Sender format looks unusual or incomplete")
            categories_found.append("suspicious_sender")
        else:
            sender_domain = sender_lower.split("@")[-1]

            if sender_domain in FREE_EMAIL_PROVIDERS:
                score += WEIGHTS["weak"]
                reasons.append(f"Sender uses a free email provider: '{sender_domain}'")
                categories_found.append("suspicious_sender")

            if any(keyword in sender_domain for keyword in ["secure", "verify", "login", "update", "alert"]):
                score += WEIGHTS["strong"]
                reasons.append(f"Sender domain contains suspicious wording: '{sender_domain}'")
                categories_found.append("suspicious_sender")

            if sender_domain.count("-") >= 2:
                score += WEIGHTS["weak"]
                reasons.append("Sender domain uses many hyphens")
                categories_found.append("suspicious_sender")

            if any(char.isdigit() for char in sender_domain):
                score += WEIGHTS["weak"]
                reasons.append("Sender domain contains numbers")
                categories_found.append("suspicious_sender")

    subject_lower = subject.lower()
    if subject:
        if any(word in subject_lower for word in ["urgent", "verify", "suspended", "winner", "refund", "payment"]):
            score += WEIGHTS["strong"]
            reasons.append("Subject line uses urgent or scam-style wording")
            categories_found.append("urgency")

    combined_lower = combined_text.lower()
    claimed_brands = []

    for brand in BRAND_DOMAINS:
        if brand in combined_lower:
            claimed_brands.append(brand)

    if sender_domain and claimed_brands:
        for brand in claimed_brands:
            allowed_domains = BRAND_DOMAINS[brand]

            if not any(sender_domain.endswith(valid_domain) for valid_domain in allowed_domains):
                score += WEIGHTS["strong"]
                reasons.append(f"Sender domain does not match claimed brand: '{brand}'")
                categories_found.append("suspicious_sender")

                if sender_domain in FREE_EMAIL_PROVIDERS:
                    score += WEIGHTS["critical"]
                    reasons.append(f"Claims to be '{brand}' but uses a free email provider")
                    categories_found.append("suspicious_sender")

    has_urgency = "urgency" in categories_found
    has_sender_issue = "suspicious_sender" in categories_found
    has_credentials = any(
        phrase in combined_lower
        for phrase in ["password", "otp", "pin", "login", "verify your account", "security code"]
    )

    if has_sender_issue and has_urgency:
        score += WEIGHTS["strong"]
        reasons.append("Combo: suspicious sender + urgency")
        categories_found.append("suspicious_sender")

    if has_sender_issue and has_credentials:
        score += WEIGHTS["critical"]
        reasons.append("Combo: suspicious sender + credential request")
        categories_found.append("suspicious_sender")

    unique_reasons = list(dict.fromkeys(reasons))
    insights = generate_insights(categories_found)
    risk, advice = classify_risk(score)

    if not unique_reasons:
        unique_reasons = ["No strong scam indicators were found in the email."]

    return {
        "risk": risk,
        "score": score,
        "reasons": unique_reasons,
        "legit_reasons": legit_reasons,
        "insights": insights,
        "advice": advice,
        "sender": sender,
        "subject": subject
    }


def preprocess_image_for_ocr(image_bytes):
    image = Image.open(BytesIO(image_bytes)).convert("L")
    image = ImageOps.autocontrast(image)
    image = image.filter(ImageFilter.SHARPEN)

    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output


def extract_text_from_image(image_file):
    api_key = os.getenv("OCR_SPACE_API_KEY")

    if not api_key:
        raise OCRServiceError("OCR_SPACE_API_KEY is missing.")

    image_bytes = image_file.read()
    processed_image = preprocess_image_for_ocr(image_bytes)

    try:
        response = requests.post(
            "https://api.ocr.space/parse/image",
            files={"file": ("screenshot.png", processed_image, "image/png")},
            data={
                "language": "eng",
                "isOverlayRequired": False,
                "OCREngine": 2,
                "scale": True
            },
            headers={"apikey": api_key},
            timeout=30
        )
    except requests.RequestException as e:
        raise OCRServiceError(f"OCR request failed: {e}")

    if response.status_code != 200:
        raise OCRServiceError(f"OCR API returned status code {response.status_code}")

    try:
        result = response.json()
    except ValueError:
        raise OCRServiceError("OCR API returned invalid JSON.")

    if result.get("IsErroredOnProcessing"):
        error_message = result.get("ErrorMessage") or result.get("ErrorDetails") or "Unknown OCR error"
        raise OCRServiceError(str(error_message))

    parsed_results = result.get("ParsedResults", [])
    if not parsed_results:
        return ""

    extracted_text = "\n".join(
        item.get("ParsedText", "")
        for item in parsed_results
        if item.get("ParsedText")
    ).strip()

    return extracted_text


def estimate_ocr_confidence(text):
    if not text:
        return 0.0

    text = text.strip()

    length_score = min(len(text) / 200, 1.0)

    weird_chars = len(re.findall(r'[^a-zA-Z0-9\s.,!?@:/%()\-]', text))
    weird_ratio = weird_chars / max(len(text), 1)

    confidence = length_score * (1 - weird_ratio)
    confidence = max(0.0, min(confidence, 1.0))

    return round(confidence, 2)


def analyze_image_file(image_file):
    try:
        extracted_text = extract_text_from_image(image_file)
    except OCRServiceError as e:
        return {
            "risk": "OCR Error",
            "score": 0,
            "reasons": [f"OCR failed: {str(e)}"],
            "insights": [],
            "advice": "Please try again in a moment or use a clearer screenshot.",
            "extracted_text": "",
            "ocr_confidence": 0.0,
            "ocr_quality": "Failed"
        }

    if not extracted_text:
        return {
            "risk": "No Text Found",
            "score": 0,
            "reasons": ["No readable text could be extracted from the image."],
            "insights": [],
            "advice": "Try a clearer screenshot with larger text and better contrast.",
            "extracted_text": "",
            "ocr_confidence": 0.0,
            "ocr_quality": "Low"
        }

    result = analyze_text(extracted_text)

    ocr_confidence = estimate_ocr_confidence(extracted_text)

    if ocr_confidence >= 0.75:
        ocr_quality = "High"
    elif ocr_confidence >= 0.45:
        ocr_quality = "Medium"
    else:
        ocr_quality = "Low"

    extracted_urls = extract_urls(extracted_text)

    phone_pattern = r'(?:\+27|27|0)(?:[\s\-]?\d){8,10}'
    raw_phones = re.findall(phone_pattern, extracted_text)

    extracted_phones = []
    seen_phones = set()

    for phone in raw_phones:
        cleaned = re.sub(r'\D', '', phone)

        if len(cleaned) != 10:
            continue

        if cleaned.startswith((
            "060", "061", "062", "063", "064", "065", "066", "067", "068",
            "071", "072", "073", "074", "076", "078", "079",
            "081", "082", "083", "084",
            "011", "021", "031", "041", "051", "086"
        )):
            if cleaned not in seen_phones:
                seen_phones.add(cleaned)
                extracted_phones.append(cleaned)

    result["extracted_text"] = extracted_text
    result["ocr_confidence"] = ocr_confidence
    result["ocr_quality"] = ocr_quality
    result["extracted_urls"] = extracted_urls
    result["extracted_phones"] = extracted_phones

    return result