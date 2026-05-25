"""
Merci Handy — Field Sales App (v4 — Pop & Colorful edition 💖)
Géolocalisation GPS + détection magasin via OpenStreetMap (100% gratuit)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import uuid
import requests
import time
import html
from PIL import Image
from streamlit_geolocation import streamlit_geolocation
import cloudinary
import cloudinary.uploader

# =========================================================================
# CONFIGURATION
# =========================================================================

st.set_page_config(
    page_title="Merci Handy — Field",
    page_icon="💖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 🎨 Palette Merci Handy — Pop & Colorful edition
PRIMARY = "#FF6BB8"          # Rose MH vif
PRIMARY_DARK = "#E94BA0"     # Rose MH plus profond (hover)
PRIMARY_SOFT = "#FFD6EC"     # Rose poudré (backgrounds)

# Accents pop (utilisés pour stat cards, états, accents)
ACCENT_YELLOW = "#FFD93D"
ACCENT_MINT = "#6BD9C3"
ACCENT_BLUE = "#74B9FF"
ACCENT_CORAL = "#FF8A65"
ACCENT_PURPLE = "#B084EE"

TEXT_DARK = "#2C2C2A"
TEXT_SOFT = "#6B6B6B"
BG_LIGHT = "#FFFFFF"
BG_SOFT = "#FFF9FB"           # Crème rosé doux pour le fond global
BORDER_SOFT = "#FFE3F0"

DEFAULT_ENSEIGNES = ["Monoprix", "Sephora", "Nocibé", "Marionnaud", "Carrefour", "Pharmacie", "Autre"]
DEFAULT_PROJETS = [
    "Implantation permanente",
    "Animation saisonnière",
    "Lancement nouveauté",
    "Visite mensuelle",
    "Calendrier de l'avent",
    "Autre"
]
DEFAULT_ETATS = [
    "✅ Linéaire OK",
    "⚠️ Problème de facing",
    "❌ Rupture détectée",
    "📍 Mauvais emplacement",
    "🎨 PLV manquante"
]

# Colonnes de la Sheet (avec geoloc)
SHEET_COLUMNS = [
    "ID", "Date", "Heure", "Commercial", "Enseigne", "Magasin",
    "Ville", "Projet", "Etat", "Commentaire", "Photos_URLs",
    "Latitude", "Longitude", "Adresse_complete"
]

DEFAULT_ADMIN_PASSWORD = "mercihandy2026"

# =========================================================================
# STYLE — Pop & Colorful Merci Handy 💖
# =========================================================================

st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&family=Quicksand:wght@400;500;600;700&display=swap" rel="stylesheet">

<style>
    /* ====== GLOBAL ====== */
    .stApp {{
        background:
            radial-gradient(circle at 0% 0%, {PRIMARY_SOFT}55 0%, transparent 35%),
            radial-gradient(circle at 100% 0%, {ACCENT_YELLOW}22 0%, transparent 35%),
            radial-gradient(circle at 100% 100%, {ACCENT_MINT}22 0%, transparent 35%),
            radial-gradient(circle at 0% 100%, {ACCENT_BLUE}22 0%, transparent 35%),
            {BG_SOFT};
        color: {TEXT_DARK};
        font-family: 'Quicksand', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}

    .stApp, .stApp p, .stApp span, .stApp div, .stApp label,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    .stApp li, .stApp strong, .stApp em {{
        color: {TEXT_DARK} !important;
        font-family: 'Quicksand', -apple-system, sans-serif !important;
    }}

    .stApp h1, .stApp h2, .stApp h3 {{
        font-family: 'Fredoka', 'Quicksand', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em;
    }}

    /* ====== INPUTS ====== */
    .stTextInput input, .stTextArea textarea,
    .stSelectbox [data-baseweb="select"] > div,
    .stMultiSelect [data-baseweb="select"] > div,
    div[data-baseweb="input"] input, .stDateInput input {{
        background-color: {BG_LIGHT} !important;
        color: {TEXT_DARK} !important;
        border: 2px solid {BORDER_SOFT} !important;
        border-radius: 14px !important;
        font-family: 'Quicksand', sans-serif !important;
        font-weight: 500 !important;
        transition: border-color 0.2s, box-shadow 0.2s;
    }}
    .stTextInput input:focus, .stTextArea textarea:focus {{
        border-color: {PRIMARY} !important;
        box-shadow: 0 0 0 4px {PRIMARY}22 !important;
    }}

    label, .stTextInput label, .stTextArea label, .stSelectbox label,
    .stMultiSelect label, .stCheckbox label, .stFileUploader label, .stRadio label {{
        color: {TEXT_DARK} !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }}

    .stCheckbox label, .stCheckbox label p, .stCheckbox label span,
    .stCheckbox > label > div, .stCheckbox > label > div *,
    [data-testid="stCheckbox"] label, [data-testid="stCheckbox"] label *,
    [data-testid="stCheckbox"] p {{ color: {TEXT_DARK} !important; }}

    .stRadio label, .stRadio label p,
    [data-testid="stRadio"] label * {{ color: {TEXT_DARK} !important; }}

    .stMarkdown, .stMarkdown * {{ color: {TEXT_DARK} !important; }}

    /* ====== FILE UPLOADER ====== */
    [data-testid="stFileUploader"] {{
        background-color: {BG_LIGHT};
        border-radius: 16px;
        padding: 10px;
    }}
    [data-testid="stFileUploader"] * {{ color: {TEXT_DARK} !important; }}
    [data-testid="stFileUploader"] section {{
        background: linear-gradient(135deg, {PRIMARY_SOFT}55 0%, {ACCENT_YELLOW}22 100%) !important;
        border: 2px dashed {PRIMARY} !important;
        border-radius: 14px !important;
    }}
    [data-testid="stFileUploader"] button {{
        background: {PRIMARY} !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
    }}

    /* ====== HEADER HERO ====== */
    .main-header {{
        background: linear-gradient(120deg, {PRIMARY} 0%, {ACCENT_CORAL} 50%, {ACCENT_YELLOW} 100%);
        padding: 26px 28px;
        border-radius: 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 28px rgba(255, 107, 184, 0.28);
        position: relative;
        overflow: hidden;
    }}
    .main-header::before {{
        content: "";
        position: absolute;
        top: -30px; right: -30px;
        width: 140px; height: 140px;
        background: radial-gradient(circle, #ffffff55 0%, transparent 70%);
        border-radius: 50%;
    }}
    .main-header::after {{
        content: "";
        position: absolute;
        bottom: -40px; left: -30px;
        width: 160px; height: 160px;
        background: radial-gradient(circle, #ffffff33 0%, transparent 70%);
        border-radius: 50%;
    }}
    .main-header h1 {{
        color: white !important;
        margin: 0 !important;
        font-size: 26px !important;
        font-weight: 700 !important;
        font-family: 'Fredoka', sans-serif !important;
        text-shadow: 0 2px 8px rgba(0,0,0,0.12);
        position: relative;
        z-index: 1;
    }}
    .main-header p {{
        color: white !important;
        margin: 6px 0 0 0 !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        opacity: 0.95;
        position: relative;
        z-index: 1;
    }}

    /* ====== STAT CARDS ====== */
    .stat-card {{
        background: {BG_LIGHT};
        border-radius: 20px;
        padding: 18px 12px;
        text-align: center;
        border: 2px solid transparent;
        box-shadow: 0 4px 14px rgba(255, 107, 184, 0.08);
        position: relative;
        overflow: hidden;
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }}
    .stat-card::before {{
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 4px;
        border-radius: 20px 20px 0 0;
    }}
    .stat-card.pink::before {{ background: {PRIMARY}; }}
    .stat-card.yellow::before {{ background: {ACCENT_YELLOW}; }}
    .stat-card.mint::before {{ background: {ACCENT_MINT}; }}
    .stat-card.blue::before {{ background: {ACCENT_BLUE}; }}
    .stat-card.coral::before {{ background: {ACCENT_CORAL}; }}
    .stat-card.purple::before {{ background: {ACCENT_PURPLE}; }}

    .stat-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(255, 107, 184, 0.18);
    }}
    .stat-number {{
        font-size: 32px;
        font-weight: 700;
        font-family: 'Fredoka', sans-serif !important;
        background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT_CORAL} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.1;
    }}
    .stat-label {{
        font-size: 11px;
        color: {TEXT_SOFT} !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-weight: 600;
        margin-top: 4px;
    }}

    /* ====== FORM ====== */
    div[data-testid="stForm"] {{
        background: {BG_LIGHT};
        padding: 24px;
        border-radius: 20px;
        border: 2px solid {BORDER_SOFT};
        box-shadow: 0 4px 14px rgba(255, 107, 184, 0.06);
    }}

    /* ====== BUTTONS ====== */
    .stButton > button, .stFormSubmitButton > button {{
        background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT_CORAL} 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: 700 !important;
        font-family: 'Quicksand', sans-serif !important;
        border-radius: 14px !important;
        padding: 10px 18px !important;
        box-shadow: 0 4px 14px rgba(255, 107, 184, 0.32) !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }}
    .stButton > button:hover, .stFormSubmitButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(255, 107, 184, 0.45) !important;
        background: linear-gradient(135deg, {PRIMARY_DARK} 0%, {ACCENT_CORAL} 100%) !important;
        color: white !important;
    }}
    .stButton > button:active, .stFormSubmitButton > button:active {{
        transform: translateY(0);
    }}

    /* Bouton primary (Nouvelle visite) — encore plus pop */
    .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT_PURPLE} 100%) !important;
        font-size: 16px !important;
        padding: 14px 22px !important;
    }}

    /* ====== VISIT CARDS ====== */
    .visit-card {{
        background: {BG_LIGHT};
        border-radius: 18px;
        padding: 16px 18px;
        margin-bottom: 10px;
        border: 2px solid {BORDER_SOFT};
        box-shadow: 0 2px 8px rgba(255, 107, 184, 0.05);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    .visit-card:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(255, 107, 184, 0.15);
    }}
    .visit-card * {{ color: {TEXT_DARK} !important; }}

    /* ====== TABS ====== */
    .stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
    .stTabs [data-baseweb="tab"] {{
        background: {BG_LIGHT};
        border-radius: 12px 12px 0 0;
        color: {TEXT_DARK} !important;
        font-weight: 600 !important;
        padding: 10px 18px !important;
        border: 2px solid {BORDER_SOFT} !important;
        border-bottom: none !important;
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT_CORAL} 100%) !important;
        color: white !important;
        border-color: transparent !important;
    }}
    .stTabs [aria-selected="true"] * {{ color: white !important; }}

    /* ====== ALERTS ====== */
    .stAlert {{
        border-radius: 14px !important;
        border: 2px solid {BORDER_SOFT} !important;
    }}
    .stAlert, .stAlert * {{ color: {TEXT_DARK} !important; }}
    .stDataFrame {{ background: {BG_LIGHT}; border-radius: 14px; }}

    /* ====== GEOLOC DETECTED CARD ====== */
    .geoloc-detected {{
        background: linear-gradient(135deg, #E8F8E8 0%, {ACCENT_MINT}33 100%);
        border: 2px solid {ACCENT_MINT};
        border-radius: 18px;
        padding: 14px 18px;
        margin: 12px 0;
        box-shadow: 0 2px 10px {ACCENT_MINT}33;
    }}
    .geoloc-detected * {{ color: #1F5230 !important; }}

    /* ====== SECTION DIVIDERS ====== */
    .section-title {{
        font-family: 'Fredoka', sans-serif !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        color: {TEXT_DARK} !important;
        margin: 18px 0 10px 0 !important;
        display: flex;
        align-items: center;
        gap: 8px;
    }}

    /* Sparkle decorative element */
    .sparkle {{
        display: inline-block;
        animation: sparkle 2s ease-in-out infinite;
    }}
    @keyframes sparkle {{
        0%, 100% {{ transform: scale(1) rotate(0deg); opacity: 1; }}
        50% {{ transform: scale(1.15) rotate(15deg); opacity: 0.85; }}
    }}

    /* Scrollbar custom */
    ::-webkit-scrollbar {{ width: 10px; }}
    ::-webkit-scrollbar-track {{ background: {BG_SOFT}; }}
    ::-webkit-scrollbar-thumb {{
        background: linear-gradient(180deg, {PRIMARY} 0%, {ACCENT_CORAL} 100%);
        border-radius: 5px;
    }}

    /* Hide Streamlit branding (optional, clean look) */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    header[data-testid="stHeader"] {{ background: transparent; }}
</style>
""", unsafe_allow_html=True)

# =========================================================================
# GEOLOC HELPERS
# =========================================================================

def reverse_geocode(lat, lon):
    """Récupère l'adresse complète depuis lat/lon (OpenStreetMap Nominatim)."""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {"lat": lat, "lon": lon, "format": "json", "addressdetails": 1, "accept-language": "fr"}
        headers = {"User-Agent": "MerciHandyFieldApp/1.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "address": data.get("display_name", ""),
                "city": data.get("address", {}).get("city")
                        or data.get("address", {}).get("town")
                        or data.get("address", {}).get("village", ""),
                "postcode": data.get("address", {}).get("postcode", ""),
            }
    except Exception:
        pass
    return None


def find_nearby_shops(lat, lon, radius=150):
    """Trouve les magasins (cosmétique, supermarché, parfumerie) autour via Overpass API."""
    try:
        query = f"""
        [out:json][timeout:10];
        (
          node["shop"~"cosmetics|perfumery|chemist|supermarket|convenience|department_store|beauty"](around:{radius},{lat},{lon});
          way["shop"~"cosmetics|perfumery|chemist|supermarket|convenience|department_store|beauty"](around:{radius},{lat},{lon});
        );
        out center;
        """
        url = "https://overpass-api.de/api/interpreter"
        resp = requests.post(url, data=query, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            shops = []
            for elem in data.get("elements", []):
                tags = elem.get("tags", {})
                name = tags.get("name") or tags.get("brand")
                if not name:
                    continue
                if elem["type"] == "node":
                    elat, elon = elem["lat"], elem["lon"]
                else:
                    elat = elem.get("center", {}).get("lat", lat)
                    elon = elem.get("center", {}).get("lon", lon)
                dist = ((elat - lat) ** 2 + (elon - lon) ** 2) ** 0.5 * 111000
                shops.append({
                    "name": name,
                    "shop_type": tags.get("shop", ""),
                    "address": f"{tags.get('addr:housenumber','')} {tags.get('addr:street','')}".strip(),
                    "lat": elat,
                    "lon": elon,
                    "distance_m": round(dist),
                })
            shops.sort(key=lambda x: x["distance_m"])
            return shops[:10]
    except Exception:
        pass
    return []


def detect_enseigne_from_name(shop_name, enseignes_list):
    """Essaie de matcher le nom du magasin OSM avec une enseigne connue."""
    name_lower = shop_name.lower()
    for enseigne in enseignes_list:
        if enseigne.lower() in name_lower:
            return enseigne
    return None


# =========================================================================
# CONNEXIONS GOOGLE
# =========================================================================

@st.cache_resource
def get_google_clients():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        gc = gspread.authorize(creds)
        drive = build("drive", "v3", credentials=creds)
        return gc, drive
    except Exception as e:
        st.error(f"Erreur de connexion Google : {e}")
        st.stop()


@st.cache_resource
def get_workbook():
    gc, _ = get_google_clients()
    return gc.open_by_key(st.secrets["sheet_id"])


@st.cache_resource
def get_visits_sheet():
    wb = get_workbook()
    sheet = wb.sheet1
    try:
        existing = sheet.row_values(1)
        if not existing:
            sheet.append_row(SHEET_COLUMNS)
        elif len(existing) < len(SHEET_COLUMNS):
            for i, col in enumerate(SHEET_COLUMNS):
                if i >= len(existing):
                    sheet.update_cell(1, i + 1, col)
    except Exception:
        pass
    return sheet


@st.cache_resource
def get_config_sheet(name):
    wb = get_workbook()
    try:
        ws = wb.worksheet(name)
    except gspread.exceptions.WorksheetNotFound:
        ws = wb.add_worksheet(title=name, rows=100, cols=2)
        ws.append_row(["Valeur"])
    return ws


def init_config_if_empty(name, default_values):
    ws = get_config_sheet(name)
    values = ws.col_values(1)
    if len(values) <= 1:
        ws.append_rows([[v] for v in default_values])
    return ws


@st.cache_data(ttl=300)
def load_config_list(name, default_values_tuple):
    default_values = list(default_values_tuple)
    ws = init_config_if_empty(name, default_values)
    values = ws.col_values(1)
    result = [v for v in values[1:] if v.strip()]
    return result if result else default_values


def add_to_config(name, value, default_values):
    ws = get_config_sheet(name)
    ws.append_row([value])
    st.cache_data.clear()


def remove_from_config(name, value, default_values):
    ws = get_config_sheet(name)
    values = ws.col_values(1)
    for i, v in enumerate(values):
        if v == value and i != 0:
            ws.delete_rows(i + 1)
            break
    st.cache_data.clear()


def compress_image(photo_file, max_size_kb=800, max_dimension=1600):
    """Compresse une photo pour upload rapide et fiable."""
    try:
        img = Image.open(io.BytesIO(photo_file.getvalue()))
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        if max(img.size) > max_dimension:
            ratio = max_dimension / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        quality = 85
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        while output.tell() > max_size_kb * 1024 and quality > 50:
            quality -= 10
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=quality, optimize=True)

        output.seek(0)
        return output
    except Exception:
        return io.BytesIO(photo_file.getvalue())


def configure_cloudinary():
    """Configure Cloudinary depuis les secrets."""
    try:
        cloudinary.config(
            cloud_name=st.secrets["cloudinary"]["cloud_name"],
            api_key=st.secrets["cloudinary"]["api_key"],
            api_secret=st.secrets["cloudinary"]["api_secret"],
            secure=True
        )
        return True
    except Exception as e:
        st.error(f"Erreur configuration Cloudinary : {e}")
        return False


def upload_photo(photo_file, filename, max_retries=3):
    """Upload une photo sur Cloudinary avec compression et retry."""
    if not configure_cloudinary():
        raise Exception("Cloudinary non configuré")

    compressed = compress_image(photo_file)

    last_error = None
    for attempt in range(max_retries):
        try:
            compressed.seek(0)
            public_id = f"merci-handy-field/{filename.rsplit('.', 1)[0]}"

            result = cloudinary.uploader.upload(
                compressed,
                public_id=public_id,
                resource_type="image",
                folder="merci-handy-field",
                use_filename=True,
                unique_filename=True,
                overwrite=False,
                quality="auto:good",
                fetch_format="auto",
            )
            return result.get("secure_url", "")
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    raise last_error


@st.cache_data(ttl=60)
def load_visits():
    sheet = get_visits_sheet()
    data = sheet.get_all_records()
    if not data:
        return pd.DataFrame(columns=SHEET_COLUMNS)
    return pd.DataFrame(data)


def save_visit(visit_data, photo_urls):
    sheet = get_visits_sheet()
    row = [
        visit_data["id"], visit_data["date"], visit_data["heure"],
        visit_data["commercial"], visit_data["enseigne"], visit_data["magasin"],
        visit_data["ville"], visit_data["projet"], ", ".join(visit_data["etat"]),
        visit_data["commentaire"], " | ".join(photo_urls),
        visit_data.get("latitude", ""), visit_data.get("longitude", ""),
        visit_data.get("adresse", ""),
    ]
    sheet.append_row(row)
    st.cache_data.clear()


def delete_visit_by_id(visit_id):
    """Supprime une visite par son ID dans la Sheet."""
    sheet = get_visits_sheet()
    all_data = sheet.get_all_values()
    for i, row in enumerate(all_data):
        if i == 0:
            continue
        if row and len(row) > 0 and row[0] == visit_id:
            sheet.delete_rows(i + 1)
            st.cache_data.clear()
            return True
    return False


def get_admin_password():
    try:
        return st.secrets.get("admin_password", DEFAULT_ADMIN_PASSWORD)
    except Exception:
        return DEFAULT_ADMIN_PASSWORD


def make_thumbnail_url(url, size=120):
    """Génère une URL de miniature Cloudinary avec rotation auto selon EXIF."""
    if not url or "res.cloudinary.com" not in url:
        return url
    if "/upload/" in url:
        return url.replace(
            "/upload/",
            f"/upload/a_exif,w_{size},h_{size},c_fill,q_auto,f_auto/",
            1
        )
    return url


def make_fullsize_url(url):
    """Génère une URL pleine taille avec rotation auto EXIF (pour le clic)."""
    if not url or "res.cloudinary.com" not in url:
        return url
    if "/upload/" in url:
        return url.replace("/upload/", "/upload/a_exif,q_auto,f_auto/", 1)
    return url


def render_bar_chart(series, max_items=10):
    """Affiche un graphique en barres multicolore harmonisé MH."""
    if series.empty:
        st.info("Aucune donnée à afficher.")
        return

    # Palette tournante pour les barres
    palette = [PRIMARY, ACCENT_CORAL, ACCENT_YELLOW, ACCENT_MINT, ACCENT_BLUE, ACCENT_PURPLE]

    series = series.head(max_items)
    max_val = series.max()

    bars_html = []
    for idx, (label, value) in enumerate(series.items()):
        width_pct = (value / max_val) * 100 if max_val > 0 else 0
        label_safe = html.escape(str(label))
        color = palette[idx % len(palette)]
        bar = (
            f'<div style="margin-bottom:12px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">'
            f'<span style="font-size:13px;color:{TEXT_DARK};font-weight:600;">{label_safe}</span>'
            f'<span style="font-size:14px;color:{color};font-weight:700;">{value}</span>'
            f'</div>'
            f'<div style="background:{BG_SOFT};border-radius:8px;height:12px;overflow:hidden;border:1px solid {BORDER_SOFT};">'
            f'<div style="background:linear-gradient(90deg,{color} 0%,{color}dd 100%);height:100%;width:{width_pct}%;border-radius:8px;box-shadow:0 1px 3px {color}44;"></div>'
            f'</div></div>'
        )
        bars_html.append(bar)

    full = f'<div style="background:{BG_LIGHT};padding:20px 22px;border-radius:18px;border:2px solid {BORDER_SOFT};margin-bottom:16px;box-shadow:0 2px 8px rgba(255,107,184,0.06);">{"".join(bars_html)}</div>'
    st.markdown(full, unsafe_allow_html=True)


def render_thumbnails(photos_urls_str, size=120, max_thumbs=4, display_size=72):
    """Génère le HTML d'une rangée de miniatures cliquables."""
    if not photos_urls_str:
        return ""
    urls = [u.strip() for u in str(photos_urls_str).split("|") if u.strip()]
    if not urls:
        return ""

    parts = []
    for url in urls[:max_thumbs]:
        thumb_url = make_thumbnail_url(url, size=size)
        full_url_rotated = make_fullsize_url(url)
        full_url_safe = html.escape(full_url_rotated, quote=True)
        thumb_url_safe = html.escape(thumb_url, quote=True)
        parts.append(
            f'<a href="{full_url_safe}" target="_blank" rel="noopener" style="display:inline-block;margin-right:8px;text-decoration:none;">'
            f'<img src="{thumb_url_safe}" style="width:{display_size}px;height:{display_size}px;object-fit:cover;border-radius:12px;border:2px solid {BORDER_SOFT};display:block;box-shadow:0 2px 6px rgba(255,107,184,0.15);" />'
            f'</a>'
        )

    extra = ""
    if len(urls) > max_thumbs:
        extra = f'<span style="font-size:12px;color:{PRIMARY};font-weight:600;margin-left:4px;vertical-align:middle;">+{len(urls) - max_thumbs}</span>'

    return f'<div style="margin-top:10px;display:flex;align-items:center;flex-wrap:wrap;">{"".join(parts)}{extra}</div>'


# =========================================================================
# ÉCRANS
# =========================================================================

def screen_login():
    st.markdown(
        '<div class="main-header">'
        '<h1>💖 Merci Handy — Field <span class="sparkle">✨</span></h1>'
        '<p>L\'outil terrain qui sent bon les linéaires propres</p>'
        '</div>',
        unsafe_allow_html=True
    )
    st.write("")
    st.markdown("**Hello toi !** 👋 Dis-moi ton prénom pour commencer.")
    nom = st.text_input("Ton prénom", placeholder="Ex : Léa", label_visibility="collapsed")
    if st.button("Let's go 🚀", use_container_width=True, type="primary"):
        if nom.strip():
            st.session_state.commercial = nom.strip()
            st.rerun()
        else:
            st.warning("Indique ton prénom pour continuer.")


def screen_home():
    df = load_visits()
    df_user = df[df["Commercial"] == st.session_state.commercial] if "Commercial" in df.columns else df

    st.markdown(
        f'<div class="main-header">'
        f'<h1>Salut {html.escape(st.session_state.commercial)} 👋</h1>'
        f'<p>Tes visites terrain en un coup d\'œil</p>'
        f'</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)
    today = datetime.now().strftime("%Y-%m-%d")
    visits_today = len(df_user[df_user["Date"] == today]) if not df_user.empty else 0
    visits_total = len(df_user)
    visits_month = 0
    if not df_user.empty:
        df_user_dates = pd.to_datetime(df_user["Date"], errors="coerce")
        current_month = datetime.now().strftime("%Y-%m")
        visits_month = (df_user_dates.dt.strftime("%Y-%m") == current_month).sum()

    with col1:
        st.markdown(f'<div class="stat-card pink"><div class="stat-number">{visits_today}</div><div class="stat-label">Aujourd\'hui</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="stat-card yellow"><div class="stat-number">{visits_month}</div><div class="stat-label">Ce mois</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="stat-card mint"><div class="stat-number">{visits_total}</div><div class="stat-label">Total</div></div>', unsafe_allow_html=True)

    st.write("")
    if st.button("➕  Nouvelle visite", use_container_width=True, type="primary"):
        st.session_state.screen = "new_visit"
        for k in ["geo_lat", "geo_lon", "geo_address", "geo_city", "geo_shops", "geo_selected"]:
            st.session_state.pop(k, None)
        st.rerun()

    st.write("")
    st.markdown('<div class="section-title">📋 Tes 10 dernières visites</div>', unsafe_allow_html=True)

    if df_user.empty:
        st.info("Aucune visite enregistrée pour le moment. À toi de jouer ! 💪")
    else:
        df_user_sorted = df_user.sort_values(by=["Date", "Heure"], ascending=False).head(10)
        for _, row in df_user_sorted.iterrows():
            etat_emoji = row["Etat"].split()[0] if row["Etat"] else "📍"
            magasin_safe = html.escape(str(row.get("Magasin", "")))
            enseigne_safe = html.escape(str(row.get("Enseigne", "")))
            date_safe = html.escape(str(row.get("Date", "")))
            projet_safe = html.escape(str(row.get("Projet", "")))
            thumbs_html = render_thumbnails(row.get("Photos_URLs", ""), size=120, max_thumbs=4)
            card_html = (
                f'<div class="visit-card">'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
                f'<div style="flex:1;">'
                f'<strong style="font-size:15px;">{magasin_safe}</strong> · <span style="color:{PRIMARY};font-weight:600;">{enseigne_safe}</span><br>'
                f'<span style="font-size:12px;color:{TEXT_SOFT};">{date_safe} · {projet_safe}</span>'
                f'{thumbs_html}'
                f'</div>'
                f'<div style="font-size:24px;">{etat_emoji}</div>'
                f'</div></div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

    st.write("")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📜 Tout l'historique", use_container_width=True):
            st.session_state.screen = "history"
            st.rerun()
    with col_b:
        if st.button("📊 Tableau de bord", use_container_width=True):
            st.session_state.screen = "dashboard"
            st.rerun()

    st.write("")
    col_c, col_d = st.columns(2)
    with col_c:
        if st.button("⚙️ Admin", use_container_width=True):
            st.session_state.screen = "admin_login"
            st.rerun()
    with col_d:
        if st.button("👋 Changer d'utilisateur", use_container_width=True):
            del st.session_state.commercial
            if "screen" in st.session_state:
                del st.session_state.screen
            st.rerun()


def screen_new_visit():
    st.markdown(
        '<div class="main-header">'
        '<h1>📝 Nouvelle visite</h1>'
        '<p>Localise-toi, remplis, photos, c\'est plié ✨</p>'
        '</div>',
        unsafe_allow_html=True
    )

    if st.button("← Retour"):
        st.session_state.screen = "home"
        st.rerun()

    enseignes = load_config_list("Enseignes", tuple(DEFAULT_ENSEIGNES))
    projets = load_config_list("Projets", tuple(DEFAULT_PROJETS))
    etats = load_config_list("Etats", tuple(DEFAULT_ETATS))

    # ============= GÉOLOCALISATION =============
    st.markdown('<div class="section-title">📍 Étape 1 — Localise-toi</div>', unsafe_allow_html=True)
    st.caption("Clique sur l'icône 🌐 ci-dessous pour détecter ta position. La première fois, ton navigateur te demandera l'autorisation.")

    location = streamlit_geolocation()

    if location and location.get("latitude") and location["latitude"] != "None":
        lat = float(location["latitude"])
        lon = float(location["longitude"])

        if st.session_state.get("geo_lat") != lat:
            st.session_state.geo_lat = lat
            st.session_state.geo_lon = lon

            with st.spinner("Recherche de l'adresse…"):
                geo_info = reverse_geocode(lat, lon)
                if geo_info:
                    st.session_state.geo_address = geo_info["address"]
                    st.session_state.geo_city = geo_info["city"]
                else:
                    st.session_state.geo_address = ""
                    st.session_state.geo_city = ""

            with st.spinner("Recherche des magasins à proximité…"):
                shops = find_nearby_shops(lat, lon, radius=200)
                st.session_state.geo_shops = shops

        st.markdown(f"""
        <div class="geoloc-detected">
            <strong>📍 Position détectée</strong><br>
            <span style="font-size:13px;">{html.escape(st.session_state.get("geo_address", "Adresse inconnue"))}</span><br>
            <span style="font-size:11px; opacity:0.7;">Lat: {lat:.5f} · Lon: {lon:.5f}</span>
        </div>
        """, unsafe_allow_html=True)

        shops = st.session_state.get("geo_shops", [])
        if shops:
            st.markdown("**🏪 Magasins détectés à proximité :**")
            shop_options = ["✏️ Saisir manuellement"] + [
                f"{s['name']} ({s['distance_m']}m)" + (f" · {s['shop_type']}" if s['shop_type'] else "")
                for s in shops
            ]
            selected_idx = st.radio(
                "Sélectionne le magasin",
                range(len(shop_options)),
                format_func=lambda i: shop_options[i],
                label_visibility="collapsed",
                key="shop_selector"
            )
            if selected_idx > 0:
                st.session_state.geo_selected = shops[selected_idx - 1]
            else:
                st.session_state.geo_selected = None
        else:
            st.info("Aucun magasin détecté dans un rayon de 200m. Tu peux remplir manuellement.")
            st.session_state.geo_selected = None
    else:
        st.info("👆 Clique sur l'icône GPS ci-dessus pour détecter ta position (optionnel mais recommandé).")

    # ============= FORMULAIRE =============
    st.markdown('<div class="section-title">📝 Étape 2 — Remplis les détails</div>', unsafe_allow_html=True)

    selected_shop = st.session_state.get("geo_selected")
    default_magasin = selected_shop["name"] if selected_shop else ""
    default_ville = st.session_state.get("geo_city", "")

    default_enseigne_idx = 0
    if selected_shop:
        detected_enseigne = detect_enseigne_from_name(selected_shop["name"], enseignes)
        if detected_enseigne and detected_enseigne in enseignes:
            default_enseigne_idx = enseignes.index(detected_enseigne)

    with st.form("new_visit_form", clear_on_submit=True):
        enseigne = st.selectbox("Enseigne *", enseignes, index=default_enseigne_idx)
        magasin = st.text_input("Nom du magasin *", value=default_magasin, placeholder="Ex : Monoprix Haussmann")
        ville = st.text_input("Ville *", value=default_ville, placeholder="Paris")
        projet = st.selectbox("Projet / animation *", projets)

        st.markdown("**État du linéaire** (coche tout ce qui s'applique)")
        etat_selected = []
        for etat in etats:
            if st.checkbox(etat, key=f"etat_{etat}"):
                etat_selected.append(etat)

        st.markdown("**📸 Photos** (caméra ou galerie)")
        photos = st.file_uploader(
            "Photos",
            accept_multiple_files=True,
            type=["jpg", "jpeg", "png"],
            label_visibility="collapsed"
        )

        commentaire = st.text_area(
            "💬 Commentaire (facultatif)",
            placeholder="Ex : Demande de réassort, retour buyer, idée d'animation…",
            height=80
        )

        submitted = st.form_submit_button("✅ Enregistrer la visite", use_container_width=True, type="primary")

        if submitted:
            if not magasin.strip() or not ville.strip():
                st.error("Le nom du magasin et la ville sont obligatoires.")
                return
            if not etat_selected:
                st.error("Sélectionne au moins un état du linéaire.")
                return

            with st.spinner("Enregistrement en cours…"):
                visit_id = str(uuid.uuid4())[:8]
                now = datetime.now()

                photo_urls = []
                photos_failed = 0
                if photos:
                    progress_bar = st.progress(0, text="Upload des photos…")
                    for i, photo in enumerate(photos):
                        try:
                            filename = f"{now.strftime('%Y%m%d_%H%M%S')}_{enseigne}_{magasin.replace(' ', '_')}_{i+1}.jpg"
                            url = upload_photo(photo, filename)
                            photo_urls.append(url)
                        except Exception as e:
                            photos_failed += 1
                            st.warning(f"⚠️ Photo {i+1} non envoyée (sera à reprendre) : {str(e)[:100]}")
                        progress_bar.progress((i + 1) / len(photos), text=f"Upload {i+1}/{len(photos)}")
                    progress_bar.empty()

                visit_data = {
                    "id": visit_id,
                    "date": now.strftime("%Y-%m-%d"),
                    "heure": now.strftime("%H:%M"),
                    "commercial": st.session_state.commercial,
                    "enseigne": enseigne,
                    "magasin": magasin.strip(),
                    "ville": ville.strip(),
                    "projet": projet,
                    "etat": etat_selected,
                    "commentaire": commentaire.strip(),
                    "latitude": st.session_state.get("geo_lat", ""),
                    "longitude": st.session_state.get("geo_lon", ""),
                    "adresse": st.session_state.get("geo_address", ""),
                }
                save_visit(visit_data, photo_urls)

            if photos_failed > 0:
                st.success(f"✅ Visite enregistrée — {len(photo_urls)} photo(s) ok, {photos_failed} échec(s).")
            else:
                st.success(f"💖 Visite enregistrée ! ({len(photo_urls)} photo(s) uploadée(s))")
            st.balloons()
            for k in ["geo_lat", "geo_lon", "geo_address", "geo_city", "geo_shops", "geo_selected"]:
                st.session_state.pop(k, None)
            st.session_state.screen = "home"
            st.rerun()


def screen_history():
    st.markdown(
        f'<div class="main-header">'
        f'<h1>📜 Mon historique</h1>'
        f'<p>Toutes tes visites — {html.escape(st.session_state.commercial)}</p>'
        f'</div>',
        unsafe_allow_html=True
    )

    if st.button("← Retour"):
        st.session_state.screen = "home"
        st.rerun()

    df = load_visits()
    if df.empty or "Commercial" not in df.columns:
        st.info("Aucune visite enregistrée.")
        return

    df_user = df[df["Commercial"] == st.session_state.commercial]
    if df_user.empty:
        st.info("Tu n'as pas encore de visite enregistrée.")
        return

    st.markdown('<div class="section-title">🔎 Filtres</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        filter_enseigne = st.multiselect("Enseigne", sorted(df_user["Enseigne"].unique()))
    with col2:
        filter_projet = st.multiselect("Projet", sorted(df_user["Projet"].unique()))

    search = st.text_input("🔍 Rechercher", placeholder="Magasin, ville, commentaire…")

    df_filtered = df_user.copy()
    if filter_enseigne:
        df_filtered = df_filtered[df_filtered["Enseigne"].isin(filter_enseigne)]
    if filter_projet:
        df_filtered = df_filtered[df_filtered["Projet"].isin(filter_projet)]
    if search:
        s = search.lower()
        mask = (
            df_filtered["Magasin"].str.lower().str.contains(s, na=False) |
            df_filtered["Ville"].str.lower().str.contains(s, na=False) |
            df_filtered["Commentaire"].str.lower().str.contains(s, na=False)
        )
        df_filtered = df_filtered[mask]

    df_filtered = df_filtered.sort_values(by=["Date", "Heure"], ascending=False)
    st.markdown(f"### {len(df_filtered)} visite(s)")

    if df_filtered.empty:
        st.info("Aucune visite ne correspond à ces filtres.")
        return

    for _, row in df_filtered.iterrows():
        magasin_safe = html.escape(str(row.get("Magasin", "")))
        enseigne_safe = html.escape(str(row.get("Enseigne", "")))
        ville_safe = html.escape(str(row.get("Ville", "")))
        projet_safe = html.escape(str(row.get("Projet", "")))
        etat_safe = html.escape(str(row.get("Etat", "")))
        date_safe = html.escape(str(row.get("Date", "")))
        heure_safe = html.escape(str(row.get("Heure", "")))

        photos_section = render_thumbnails(row.get("Photos_URLs", ""), size=120, max_thumbs=6)

        commentaire_section = ""
        if row.get("Commentaire"):
            commentaire_safe = html.escape(str(row["Commentaire"]))
            commentaire_section = f'<div style="margin-top:6px;font-size:12px;color:{TEXT_SOFT};font-style:italic;">💬 {commentaire_safe}</div>'

        adresse_section = ""
        if row.get("Adresse_complete"):
            adresse_safe = html.escape(str(row["Adresse_complete"]))
            adresse_section = f'<div style="margin-top:4px;font-size:11px;color:{TEXT_SOFT};">📍 {adresse_safe}</div>'

        card_html = (
            f'<div class="visit-card">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
            f'<div style="flex:1;">'
            f'<strong style="font-size:15px;">{magasin_safe}</strong> · <span style="color:{PRIMARY};font-weight:600;">{enseigne_safe} — {ville_safe}</span><br>'
            f'<span style="font-size:12px;color:{TEXT_SOFT};">{date_safe} {heure_safe} · {projet_safe}</span>'
            f'<div style="margin-top:6px;font-size:13px;">{etat_safe}</div>'
            f'{adresse_section}'
            f'{commentaire_section}'
            f'{photos_section}'
            f'</div></div></div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)


def screen_dashboard():
    st.markdown(
        '<div class="main-header">'
        '<h1>📊 Tableau de bord</h1>'
        '<p>Vue globale — toutes les visites terrain</p>'
        '</div>',
        unsafe_allow_html=True
    )

    if st.button("← Retour"):
        st.session_state.screen = "home"
        st.rerun()

    df = load_visits()
    if df.empty:
        st.info("Aucune visite enregistrée pour l'instant.")
        return

    col1, col2, col3, col4 = st.columns(4)
    total = len(df)
    ruptures = df["Etat"].str.contains("Rupture", na=False).sum()
    commerciaux = df["Commercial"].nunique()
    enseignes_visited = df["Enseigne"].nunique()

    with col1:
        st.markdown(f'<div class="stat-card pink"><div class="stat-number">{total}</div><div class="stat-label">Visites</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="stat-card coral"><div class="stat-number">{ruptures}</div><div class="stat-label">Ruptures</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="stat-card blue"><div class="stat-number">{commerciaux}</div><div class="stat-label">Commerciaux</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="stat-card mint"><div class="stat-number">{enseignes_visited}</div><div class="stat-label">Enseignes</div></div>', unsafe_allow_html=True)

    st.write("")

    # Carte des visites
    if "Latitude" in df.columns and "Longitude" in df.columns:
        df_geo = df[df["Latitude"].astype(str).str.strip() != ""].copy()
        if not df_geo.empty:
            try:
                df_geo["lat"] = pd.to_numeric(df_geo["Latitude"], errors="coerce")
                df_geo["lon"] = pd.to_numeric(df_geo["Longitude"], errors="coerce")
                df_geo = df_geo.dropna(subset=["lat", "lon"])
                if not df_geo.empty:
                    st.markdown('<div class="section-title">🗺️ Carte des visites</div>', unsafe_allow_html=True)
                    st.map(df_geo[["lat", "lon"]], zoom=5)
            except Exception:
                pass

    # Graphiques personnalisés
    st.markdown('<div class="section-title">🏪 Visites par enseigne</div>', unsafe_allow_html=True)
    by_enseigne = df["Enseigne"].value_counts()
    render_bar_chart(by_enseigne)

    st.markdown('<div class="section-title">🚀 Visites par projet</div>', unsafe_allow_html=True)
    by_projet = df["Projet"].value_counts()
    render_bar_chart(by_projet)

    st.markdown('<div class="section-title">🔎 Filtres</div>', unsafe_allow_html=True)
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_enseigne = st.multiselect("Enseigne", sorted(df["Enseigne"].unique()))
    with col_f2:
        filter_commercial = st.multiselect("Commercial", sorted(df["Commercial"].unique()))

    df_filtered = df.copy()
    if filter_enseigne:
        df_filtered = df_filtered[df_filtered["Enseigne"].isin(filter_enseigne)]
    if filter_commercial:
        df_filtered = df_filtered[df_filtered["Commercial"].isin(filter_commercial)]

    st.markdown(f"### Détail ({len(df_filtered)} visites)")
    st.dataframe(
        df_filtered.sort_values(by=["Date", "Heure"], ascending=False),
        use_container_width=True,
        hide_index=True
    )

    csv = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Exporter en CSV",
        csv,
        f"merci_handy_visites_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv",
        use_container_width=True
    )


def screen_admin_login():
    st.markdown(
        '<div class="main-header">'
        '<h1>🔐 Espace admin</h1>'
        '<p>Accès restreint</p>'
        '</div>',
        unsafe_allow_html=True
    )

    if st.button("← Retour"):
        st.session_state.screen = "home"
        st.rerun()

    st.markdown("Saisis le mot de passe admin pour gérer les listes.")
    pw = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter", use_container_width=True, type="primary"):
        if pw == get_admin_password():
            st.session_state.is_admin = True
            st.session_state.screen = "admin"
            st.rerun()
        else:
            st.error("Mot de passe incorrect.")


def screen_admin():
    st.markdown(
        '<div class="main-header">'
        '<h1>⚙️ Admin — Configuration</h1>'
        '<p>Gère les listes et les visites</p>'
        '</div>',
        unsafe_allow_html=True
    )

    col_back, col_logout = st.columns(2)
    with col_back:
        if st.button("← Retour à l'accueil"):
            st.session_state.screen = "home"
            st.rerun()
    with col_logout:
        if st.button("🔒 Déconnexion admin"):
            st.session_state.is_admin = False
            st.session_state.screen = "home"
            st.rerun()

    st.write("")

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Visites", "🏪 Enseignes", "🚀 Projets / animations", "📋 États linéaire"])

    with tab1:
        manage_visits()
    with tab2:
        manage_list("Enseignes", DEFAULT_ENSEIGNES)
    with tab3:
        manage_list("Projets", DEFAULT_PROJETS)
    with tab4:
        manage_list("Etats", DEFAULT_ETATS, with_emoji_hint=True)


def manage_visits():
    """Gestion admin des visites : liste, filtre, suppression."""
    df = load_visits()
    if df.empty:
        st.info("Aucune visite enregistrée pour le moment.")
        return

    st.markdown(f"### {len(df)} visite(s) au total")
    st.caption("💡 Utilise les filtres ci-dessous pour retrouver les doublons ou visites à supprimer.")

    col1, col2 = st.columns(2)
    with col1:
        filter_commercial = st.multiselect("Commercial", sorted(df["Commercial"].unique()), key="admin_filter_commercial")
    with col2:
        filter_enseigne = st.multiselect("Enseigne", sorted(df["Enseigne"].unique()), key="admin_filter_enseigne")

    search = st.text_input("🔍 Rechercher", placeholder="Magasin, ville, ID, commentaire…", key="admin_search")

    df_filtered = df.copy()
    if filter_commercial:
        df_filtered = df_filtered[df_filtered["Commercial"].isin(filter_commercial)]
    if filter_enseigne:
        df_filtered = df_filtered[df_filtered["Enseigne"].isin(filter_enseigne)]
    if search:
        s = search.lower()
        mask = (
            df_filtered["Magasin"].astype(str).str.lower().str.contains(s, na=False) |
            df_filtered["Ville"].astype(str).str.lower().str.contains(s, na=False) |
            df_filtered["ID"].astype(str).str.lower().str.contains(s, na=False) |
            df_filtered["Commentaire"].astype(str).str.lower().str.contains(s, na=False)
        )
        df_filtered = df_filtered[mask]

    df_filtered = df_filtered.sort_values(by=["Date", "Heure"], ascending=False)

    st.markdown(f"### {len(df_filtered)} résultat(s)")

    if df_filtered.empty:
        st.info("Aucune visite ne correspond à ces filtres.")
        return

    pending_delete = st.session_state.get("pending_delete_visit_id")

    for _, row in df_filtered.iterrows():
        visit_id = row["ID"]
        etat_emoji = row["Etat"].split()[0] if row["Etat"] else "📍"

        magasin_safe = html.escape(str(row.get("Magasin", "")))
        enseigne_safe = html.escape(str(row.get("Enseigne", "")))
        ville_safe = html.escape(str(row.get("Ville", "")))
        date_safe = html.escape(str(row.get("Date", "")))
        heure_safe = html.escape(str(row.get("Heure", "")))
        commercial_safe = html.escape(str(row.get("Commercial", "")))
        projet_safe = html.escape(str(row.get("Projet", "")))
        visit_id_safe = html.escape(str(visit_id))

        col_card, col_btn = st.columns([5, 1])

        with col_card:
            commentaire_html = ""
            if row.get("Commentaire"):
                comment_str = str(row["Commentaire"])
                truncated = comment_str[:80] + ("…" if len(comment_str) > 80 else "")
                commentaire_safe = html.escape(truncated)
                commentaire_html = f'<div style="margin-top:4px;font-size:11px;color:{TEXT_SOFT};font-style:italic;">💬 {commentaire_safe}</div>'

            thumbs_html = render_thumbnails(row.get("Photos_URLs", ""), size=120, max_thumbs=4)

            card_html = (
                f'<div class="visit-card" style="padding:12px 16px;">'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
                f'<div style="flex:1;">'
                f'<strong>{magasin_safe}</strong> · <span style="color:{PRIMARY};font-weight:600;">{enseigne_safe} — {ville_safe}</span><br>'
                f'<span style="font-size:11px;color:{TEXT_SOFT};">{date_safe} {heure_safe} · 👤 {commercial_safe} · ID: <code>{visit_id_safe}</code></span>'
                f'<div style="margin-top:4px;font-size:12px;">{etat_emoji} {projet_safe}</div>'
                f'{commentaire_html}'
                f'{thumbs_html}'
                f'</div></div></div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

        with col_btn:
            if pending_delete == visit_id:
                if st.button("✅", key=f"confirm_{visit_id}", help="Confirmer la suppression"):
                    with st.spinner("Suppression…"):
                        if delete_visit_by_id(visit_id):
                            st.session_state.pop("pending_delete_visit_id", None)
                            st.success("Visite supprimée.")
                            st.rerun()
                        else:
                            st.error("Erreur lors de la suppression.")
                if st.button("✕", key=f"cancel_{visit_id}", help="Annuler"):
                    st.session_state.pop("pending_delete_visit_id", None)
                    st.rerun()
            else:
                if st.button("🗑️", key=f"del_visit_{visit_id}", help="Supprimer cette visite"):
                    st.session_state["pending_delete_visit_id"] = visit_id
                    st.rerun()

    if pending_delete:
        st.warning(f"⚠️ Clique sur ✅ pour confirmer la suppression de la visite `{pending_delete}`, ou ✕ pour annuler.")


def manage_list(name, defaults, with_emoji_hint=False):
    items = load_config_list(name, tuple(defaults))
    st.markdown(f"### {len(items)} valeur(s) actives")

    if with_emoji_hint:
        st.caption("💡 Astuce : tu peux ajouter un emoji au début pour la lisibilité")

    for item in items:
        col_v, col_b = st.columns([5, 1])
        with col_v:
            st.markdown(f"<div class='visit-card' style='padding:12px 16px;'>{html.escape(item)}</div>", unsafe_allow_html=True)
        with col_b:
            if st.button("🗑️", key=f"del_{name}_{item}", help="Supprimer"):
                remove_from_config(name, item, defaults)
                st.success(f"« {item} » supprimé.")
                st.rerun()

    st.write("")
    st.markdown('<div class="section-title">➕ Ajouter une nouvelle valeur</div>', unsafe_allow_html=True)
    with st.form(f"add_{name}", clear_on_submit=True):
        new_value = st.text_input("Nouvelle valeur", key=f"new_{name}")
        submitted = st.form_submit_button("Ajouter", use_container_width=True, type="primary")
        if submitted:
            if new_value.strip():
                if new_value.strip() in items:
                    st.warning("Cette valeur existe déjà.")
                else:
                    add_to_config(name, new_value.strip(), defaults)
                    st.success(f"« {new_value.strip()} » ajouté !")
                    st.rerun()
            else:
                st.warning("Saisis une valeur.")


# =========================================================================
# ROUTING
# =========================================================================

if "commercial" not in st.session_state:
    screen_login()
else:
    if "screen" not in st.session_state:
        st.session_state.screen = "home"

    screen = st.session_state.screen

    if screen == "home":
        screen_home()
    elif screen == "new_visit":
        screen_new_visit()
    elif screen == "history":
        screen_history()
    elif screen == "dashboard":
        screen_dashboard()
    elif screen == "admin_login":
        if st.session_state.get("is_admin"):
            st.session_state.screen = "admin"
            st.rerun()
        else:
            screen_admin_login()
    elif screen == "admin":
        if st.session_state.get("is_admin"):
            screen_admin()
        else:
            st.session_state.screen = "admin_login"
            st.rerun()
