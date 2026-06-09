"""QR payload parser — detect and extract data from common QR/barcode formats."""

import io
import re
from urllib.parse import unquote, parse_qs, urlparse

import qrcode
import qrcode.image.svg


# ═══════════════════════════════════════════════════════════════
# QR Generation
# ═══════════════════════════════════════════════════════════════

def generate_qr_ascii(text: str) -> str:
    """Return a scannable QR code as terminal art using Unicode half-blocks."""
    qr = qrcode.QRCode(box_size=1, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    buf = io.StringIO()
    qr.print_ascii(out=buf)
    return buf.getvalue().replace("\xa0", " ")


def generate_qr_svg(text: str) -> str:
    """Return a QR code as an SVG string — proper square modules, scans reliably."""
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue().decode("utf-8")


# ═══════════════════════════════════════════════════════════════
# QR / Barcode Extraction
# ═══════════════════════════════════════════════════════════════

def detect_type(raw: str) -> str:
    """Return a human-readable label for the payload type."""
    s = raw.strip()
    if not s:
        return "Empty"
    if s.upper().startswith("BEGIN:VCARD"):    return "📇 vCard (contact)"
    if s.upper().startswith("MECARD:"):         return "📇 MeCard (contact)"
    if re.match(r"^WIFI:[TS]:", s, re.IGNORECASE): return "📶 WiFi Network"
    if re.match(r"^mailto:", s, re.IGNORECASE): return "📧 Email"
    if re.match(r"^MATMSG:", s, re.IGNORECASE): return "📧 Email (MATMSG)"
    if re.match(r"^(smsto|SMSTO|sms):", s):    return "💬 SMS"
    if re.match(r"^tel:", s, re.IGNORECASE):    return "📞 Phone"
    if re.match(r"^geo:", s, re.IGNORECASE):    return "📍 Geo Location"
    if s.upper().startswith("BEGIN:VEVENT"):    return "📅 Calendar Event"
    if re.match(r"^https?://", s, re.IGNORECASE): return "🌐 URL"
    if "@" in s and "." in s.split("@")[-1]:    return "📧 Email (plain)"
    if re.match(r"^\+?[\d\s\-()]{7,}$", s):    return "📞 Phone (plain)"
    return "📝 Plain Text"


# ── Parsers, each returns list[tuple[str, str]] ──────────────

def _simple(url: str) -> list[tuple[str, str]]:
    p = urlparse(url)
    rows = [("URL", url)]
    if p.scheme:   rows.append(("Scheme", p.scheme))
    if p.netloc:   rows.append(("Host", p.netloc))
    if p.path:     rows.append(("Path", p.path))
    if p.query:
        rows.append(("Query String", p.query))
        for k, v in parse_qs(p.query).items():
            rows.append((f"  param: {k}", ", ".join(v)))
    if p.fragment: rows.append(("Fragment", p.fragment))
    return rows


VCARD_LABELS = {
    "FN": "Full Name", "N": "Name (structured)", "ORG": "Organization",
    "TITLE": "Title", "TEL": "Phone", "EMAIL": "Email",
    "URL": "Website", "ADR": "Address", "NOTE": "Note",
    "BDAY": "Birthday", "NICKNAME": "Nickname", "PHOTO": "Photo",
    "ROLE": "Role", "CATEGORIES": "Categories",
}


def _vcard_label(key: str) -> str:
    key = key.strip().upper()
    base = key.split(";")[0].split(",")[0]
    return VCARD_LABELS.get(base, key)


def _vcard(raw: str) -> list[tuple[str, str]]:
    rows = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.upper() in ("BEGIN:VCARD", "END:VCARD", "VERSION:3.0"):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            rows.append((_vcard_label(key.replace(";", " ")), unquote(val)))
    return rows


def _mecard(raw: str) -> list[tuple[str, str]]:
    body = raw[len("MECARD:"):]
    rows = []
    for part in body.split(";"):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            k, v = part.split(":", 1)
            rows.append((k.upper(), unquote(v)))
    return rows


def _wifi(raw: str) -> list[tuple[str, str]]:
    rows = []
    m = re.search(r"WIFI:([^;]*)", raw, re.IGNORECASE)
    content = raw[m.start():] if m else raw
    pairs = re.findall(r"([TSHP]):([^;]+)", content, re.IGNORECASE)
    labels = {"T": "Auth Type", "S": "SSID", "P": "Password", "H": "Hidden"}
    for k, v in pairs:
        label = labels.get(k.upper(), k.upper())
        val = unquote(v)
        if k.upper() == "T":
            val = {"WPA": "WPA/WPA2", "WEP": "WEP", "nopass": "Open (no password)"}.get(val, val)
        elif k.upper() == "H":
            val = "Yes" if val.lower() == "true" else "No"
        rows.append((label, val))
    return rows


def _email(raw: str) -> list[tuple[str, str]]:
    rows = []
    if raw.lower().startswith("mailto:"):
        addr = raw[len("mailto:"):]
        if "?" in addr:
            addr, qs = addr.split("?", 1)
            rows.append(("To", unquote(addr)))
            for k, v in parse_qs(qs).items():
                rows.append((k.capitalize(), unquote(", ".join(v))))
        else:
            rows.append(("To", unquote(addr)))
    elif raw.upper().startswith("MATMSG:"):
        body = raw[len("MATMSG:"):]
        for part in body.split(";"):
            part = part.strip()
            if ":" in part:
                k, v = part.split(":", 1)
                label = {"TO": "To", "SUB": "Subject", "BODY": "Body"}.get(k.upper().strip(), k.upper().strip())
                rows.append((label, unquote(v)))
    else:
        rows.append(("Address", raw))
    return rows


def _sms(raw: str) -> list[tuple[str, str]]:
    s = raw
    for prefix in ("smsto:", "SMSTO:", "sms:"):
        if s.lower().startswith(prefix.lower()):
            s = s[len(prefix):]
            break
    if ":" in s:
        number, body = s.split(":", 1)
        return [("Number", number), ("Body", unquote(body))]
    return [("Number", s)]


def _tel(raw: str) -> list[tuple[str, str]]:
    return [("Number", raw[len("tel:"):])]


def _geo(raw: str) -> list[tuple[str, str]]:
    s = raw[len("geo:"):]
    parts = s.split(",")
    rows = []
    if len(parts) >= 2:
        rows.append(("Latitude", parts[0].strip()))
        rows.append(("Longitude", parts[1].strip()))
    if len(parts) >= 3:
        rows.append(("Altitude", parts[2].strip()))
    if "?" in s:
        qs = s.split("?", 1)[1]
        for k, v in parse_qs(qs).items():
            rows.append((k.capitalize(), unquote(", ".join(v))))
    return rows


def _calendar(raw: str) -> list[tuple[str, str]]:
    rows = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.upper() in ("BEGIN:VEVENT", "END:VEVENT"):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            rows.append((key.strip(), unquote(val)))
    return rows


def parse_payload(raw: str) -> tuple[str, list[tuple[str, str]]]:
    """Return (type_label, [(field, value), ...])."""
    s = raw.strip()
    if not s:
        return "Empty", []

    upper = s.upper()
    if upper.startswith("BEGIN:VCARD"):           return "📇 vCard", _vcard(s)
    if upper.startswith("MECARD:"):               return "📇 MeCard", _mecard(s)
    if re.match(r"^WIFI:[TS]:", s, re.IGNORECASE): return "📶 WiFi Network", _wifi(s)
    if s.lower().startswith("mailto:"):           return "📧 Email", _email(s)
    if upper.startswith("MATMSG:"):               return "📧 Email (MATMSG)", _email(s)
    if re.match(r"^(smsto|SMSTO|sms):", s):      return "💬 SMS", _sms(s)
    if s.lower().startswith("tel:"):              return "📞 Phone", _tel(s)
    if s.lower().startswith("geo:"):              return "📍 Geo Location", _geo(s)
    if upper.startswith("BEGIN:VEVENT"):          return "📅 Calendar Event", _calendar(s)
    if re.match(r"^https?://", s, re.IGNORECASE): return "🌐 URL", _simple(s)

    return "📝 Plain Text", [("Content", s)]
