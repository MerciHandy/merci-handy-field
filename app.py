"""
Merci Handy — Field Sales App (v3)
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
    page_icon="🧴",
    layout="centered",
    initial_sidebar_state="collapsed"
)

PRIMARY = "#EDADE7"
PRIMARY_DARK = "#D88FCE"
TEXT_DARK = "#2C2C2A"
BG_LIGHT = "#FFFFFF"
BG_SOFT = "#FDF5FB"

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
# STYLE
# =========================================================================

st.markdown(f"""
<style>
    .stApp {{ background-color: {BG_SOFT}; color: {TEXT_DARK}; }}
    .stApp, .stApp p, .stApp span, .stApp div, .stApp label,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    .stApp li, .stApp strong, .stApp em {{ color: {TEXT_DARK} !important; }}

    .stTextInput input, .stTextArea textarea,
    .stSelectbox [data-baseweb="select"] > div,
    .stMultiSelect [data-baseweb="select"] > div,
    div[data-baseweb="input"] input, .stDateInput input {{
        background-color: {BG_LIGHT} !important;
        color: {TEXT_DARK} !important;
        border: 1px solid #DDD !important;
    }}

    label, .stTextInput label, .stTextArea label, .stSelectbox label,
    .stMultiSelect label, .stCheckbox label, .stFileUploader label, .stRadio label {{
        color: {TEXT_DARK} !important;
        font-weight: 500 !important;
    }}

    .stCheckbox label, .stCheckbox label p, .stCheckbox label span,
    .stCheckbox > label > div, .stCheckbox > label > div *,
    [data-testid="stCheckbox"] label, [data-testid="stCheckbox"] label *,
    [data-testid="stCheckbox"] p {{ color: {TEXT_DARK} !important; }}

    .stRadio label, .stRadio label p,
    [data-testid="stRadio"] label * {{ color: {TEXT_DARK} !important; }}

    .stMarkdown, .stMarkdown * {{ color: {TEXT_DARK} !important; }}

    [data-testid="stFileUploader"] {{ background-color: {BG_LIGHT}; border-radius: 8px; padding: 8px; }}
    [data-testid="stFileUploader"] * {{ color: {TEXT_DARK} !important; }}
    [data-testid="stFileUploader"] section {{
        background-color: {BG_LIGHT} !important;
        border: 2px dashed #DDD !important;
    }}
    [data-testid="stFileUploader"] button {{ background: {PRIMARY} !important; color: {TEXT_DARK} !important; }}

    .main-header {{
        background: linear-gradient(135deg, {PRIMARY} 0%, {PRIMARY_DARK} 100%);
        padding: 20px 24px; border-radius: 16px; margin-bottom: 20px;
        box-shadow: 0 2px 12px rgba(237, 173, 231, 0.3);
    }}
    .main-header h1 {{ color: {TEXT_DARK} !important; margin: 0 !important; font-size: 22px !important; font-weight: 600 !important; }}
    .main-header p {{ color: {TEXT_DARK} !important; margin: 4px 0 0 0 !important; font-size: 13px !important; opacity: 0.85; }}

    .stat-card {{
        background: {BG_LIGHT}; border-radius: 12px; padding: 16px; text-align: center;
        border: 1px solid #EEE; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }}
    .stat-number {{ font-size: 28px; font-weight: 700; color: {PRIMARY_DARK} !important; }}
    .stat-label {{ font-size: 11px; color: #666 !important; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 500; }}

    div[data-testid="stForm"] {{
        background: {BG_LIGHT}; padding: 20px; border-radius: 12px; border: 1px solid #EEE;
    }}

    .stButton > button, .stFormSubmitButton > button {{
        background: {PRIMARY} !important; color: {TEXT_DARK} !important;
        border: none !important; font-weight: 600 !important; border-radius: 8px !important;
    }}
    .stButton > button:hover, .stFormSubmitButton > button:hover {{
        background: {PRIMARY_DARK} !important; color: {TEXT_DARK} !important;
    }}

    .visit-card {{
        background: {BG_LIGHT}; border-radius: 12px; padding: 14px 16px;
        margin-bottom: 8px; border: 1px solid #EEE;
    }}
    .visit-card * {{ color: {TEXT_DARK} !important; }}

    .stTabs [data-baseweb="tab-list"] {{ gap: 4px; }}
    .stTabs [data-baseweb="tab"] {{
        background: {BG_LIGHT}; border-radius: 8px 8px 0 0; color: {TEXT_DARK} !important;
    }}
    .stTabs [aria-selected="true"] {{ background: {PRIMARY} !important; color: {TEXT_DARK} !important; }}

    .stAlert, .stAlert * {{ color: {TEXT_DARK} !important; }}
    .stDataFrame {{ background: {BG_LIGHT}; }}

    /* Geoloc detected card */
    .geoloc-detected {{
        background: linear-gradient(135deg, #E8F8E8 0%, #D4F0D4 100%);
        border: 2px solid #4CAF50;
        border-radius: 12px;
        padding: 12px 16px;
        margin: 10px 0;
    }}
    .geoloc-detected * {{ color: #2C5530 !important; }}
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
        # Overpass query : cherche shops dans un rayon donné
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
                # Coordonnées
                if elem["type"] == "node":
                    elat, elon = elem["lat"], elem["lon"]
                else:
                    elat = elem.get("center", {}).get("lat", lat)
                    elon = elem.get("center", {}).get("lon", lon)
                # Distance approx
                dist = ((elat - lat) ** 2 + (elon - lon) ** 2) ** 0.5 * 111000  # ~mètres
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
            # Ajoute les colonnes manquantes (geoloc) si Sheet créée avant v3
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
        # Convertir en RGB si nécessaire (HEIC, PNG avec alpha)
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Redimensionner si trop grand
        if max(img.size) > max_dimension:
            ratio = max_dimension / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Compresser progressivement jusqu'à atteindre la taille cible
        quality = 85
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        while output.tell() > max_size_kb * 1024 and quality > 50:
            quality -= 10
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=quality, optimize=True)

        output.seek(0)
        return output
    except Exception as e:
        # Si la compression échoue, on renvoie l'original
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

    # Compression locale avant envoi
    compressed = compress_image(photo_file)

    last_error = None
    for attempt in range(max_retries):
        try:
            compressed.seek(0)
            # Public ID basé sur le filename (sans extension)
            public_id = f"merci-handy-field/{filename.rsplit('.', 1)[0]}"

            result = cloudinary.uploader.upload(
                compressed,
                public_id=public_id,
                resource_type="image",
                folder="merci-handy-field",
                use_filename=True,
                unique_filename=True,
                overwrite=False,
                # Optimisation auto côté Cloudinary
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
    # all_data[0] = header, all_data[1+] = data
    for i, row in enumerate(all_data):
        if i == 0:  # skip header
            continue
        if row and len(row) > 0 and row[0] == visit_id:
            sheet.delete_rows(i + 1)  # 1-indexed in gspread
            st.cache_data.clear()
            return True
    return False


def get_admin_password():
    try:
        return st.secrets.get("admin_password", DEFAULT_ADMIN_PASSWORD)
    except Exception:
        return DEFAULT_ADMIN_PASSWORD


def make_thumbnail_url(url, size=120):
    """Génère une URL de miniature Cloudinary."""
    if not url or "res.cloudinary.com" not in url:
        return url
    if "/upload/" in url:
        return url.replace(
            "/upload/",
            f"/upload/w_{size},h_{size},c_fill,q_auto,f_auto/",
            1
        )
    return url


def render_bar_chart(series, max_items=10):
    """Affiche un graphique en barres rose harmonisé avec le thème."""
    if series.empty:
        st.info("Aucune donnée à afficher.")
        return

    series = series.head(max_items)
    max_val = series.max()

    bars_html = []
    for label, value in series.items():
        width_pct = (value / max_val) * 100 if max_val > 0 else 0
        label_safe = html.escape(str(label))
        bars_html.append(f"""
        <div style="margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                <span style="font-size:13px;color:#2C2C2A;font-weight:500;">{label_safe}</span>
                <span style="font-size:13px;color:#D88FCE;font-weight:600;">{value}</span>
            </div>
            <div style="background:#F5E8F2;border-radius:6px;height:10px;overflow:hidden;">
                <div style="background:linear-gradient(90deg,#EDADE7 0%,#D88FCE 100%);height:100%;width:{width_pct}%;border-radius:6px;transition:width 0.4s;"></div>
            </div>
        </div>
        """)

    html_content = "".join(bars_html)
    st.markdown(
        f'<div style="background:#FFFFFF;padding:16px 20px;border-radius:12px;border:1px solid #EEE;margin-bottom:16px;">{html_content}</div>',
        unsafe_allow_html=True
    )


def render_thumbnails(photos_urls_str, size=120, max_thumbs=4, display_size=72):
    """Génère le HTML d'une rangée de miniatures cliquables. Une seule ligne, pas de retours."""
    if not photos_urls_str:
        return ""
    urls = [u.strip() for u in str(photos_urls_str).split("|") if u.strip()]
    if not urls:
        return ""

    parts = []
    for url in urls[:max_thumbs]:
        thumb_url = make_thumbnail_url(url, size=size)
        full_url = html.escape(url, quote=True)
        thumb_url_safe = html.escape(thumb_url, quote=True)
        parts.append(
            f'<a href="{full_url}" target="_blank" rel="noopener" style="display:inline-block;margin-right:6px;text-decoration:none;">'
            f'<img src="{thumb_url_safe}" style="width:{display_size}px;height:{display_size}px;object-fit:cover;border-radius:8px;border:1px solid #E8D5E5;display:block;" />'
            f'</a>'
        )

    extra = ""
    if len(urls) > max_thumbs:
        extra = f'<span style="font-size:11px;color:#888;margin-left:4px;vertical-align:middle;">+{len(urls) - max_thumbs}</span>'

    # Une seule ligne, sans retours à la ligne (évite les bugs de rendu Streamlit)
    return f'<div style="margin-top:8px;display:flex;align-items:center;flex-wrap:wrap;">{"".join(parts)}{extra}</div>'


# =========================================================================
# ÉCRANS
# =========================================================================

def screen_login():
    st.markdown('<div class="main-header"><h1>🧴 Merci Handy — Field</h1><p>Outil de suivi terrain</p></div>', unsafe_allow_html=True)
    st.write("")
    st.markdown("**Bienvenue !** Indique ton prénom pour commencer.")
    nom = st.text_input("Ton prénom", placeholder="Ex : Léa", label_visibility="collapsed")
    if st.button("Continuer", use_container_width=True):
        if nom.strip():
            st.session_state.commercial = nom.strip()
            st.rerun()
        else:
            st.warning("Indique ton prénom pour continuer.")


def screen_home():
    df = load_visits()
    df_user = df[df["Commercial"] == st.session_state.commercial] if "Commercial" in df.columns else df

    st.markdown(f'<div class="main-header"><h1>Salut {st.session_state.commercial} 👋</h1><p>Mes visites terrain</p></div>', unsafe_allow_html=True)

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
        st.markdown(f'<div class="stat-card"><div class="stat-number">{visits_today}</div><div class="stat-label">Aujourd\'hui</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{visits_month}</div><div class="stat-label">Ce mois</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{visits_total}</div><div class="stat-label">Total</div></div>', unsafe_allow_html=True)

    st.write("")
    if st.button("➕ Nouvelle visite", use_container_width=True, type="primary"):
        st.session_state.screen = "new_visit"
        # Reset geoloc state
        for k in ["geo_lat", "geo_lon", "geo_address", "geo_city", "geo_shops", "geo_selected"]:
            st.session_state.pop(k, None)
        st.rerun()

    st.write("")
    st.markdown("### 📋 Mes 10 dernières visites")

    if df_user.empty:
        st.info("Aucune visite enregistrée pour le moment.")
    else:
        df_user_sorted = df_user.sort_values(by=["Date", "Heure"], ascending=False).head(10)
        for _, row in df_user_sorted.iterrows():
            etat_emoji = row["Etat"].split()[0] if row["Etat"] else "📍"
            magasin_safe = html.escape(str(row.get("Magasin", "")))
            enseigne_safe = html.escape(str(row.get("Enseigne", "")))
            date_safe = html.escape(str(row.get("Date", "")))
            projet_safe = html.escape(str(row.get("Projet", "")))
            thumbs_html = render_thumbnails(row.get("Photos_URLs", ""), size=120, max_thumbs=4)
            st.markdown(f"""
            <div class="visit-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div style="flex:1;">
                        <strong>{magasin_safe}</strong> · <span style="color:#888 !important;">{enseigne_safe}</span><br>
                        <span style="font-size:12px; color:#666 !important;">{date_safe} · {projet_safe}</span>
                        {thumbs_html}
                    </div>
                    <div style="font-size:20px;">{etat_emoji}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

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
    st.markdown('<div class="main-header"><h1>📝 Nouvelle visite</h1><p>Détecte ta position et remplis</p></div>', unsafe_allow_html=True)

    if st.button("← Retour"):
        st.session_state.screen = "home"
        st.rerun()

    enseignes = load_config_list("Enseignes", tuple(DEFAULT_ENSEIGNES))
    projets = load_config_list("Projets", tuple(DEFAULT_PROJETS))
    etats = load_config_list("Etats", tuple(DEFAULT_ETATS))

    # ============= GÉOLOCALISATION =============
    st.markdown("### 📍 Étape 1 — Localise-toi")
    st.caption("Clique sur le bouton 🌐 ci-dessous pour détecter ta position. La première fois, ton navigateur te demandera l'autorisation.")

    location = streamlit_geolocation()

    if location and location.get("latitude") and location["latitude"] != "None":
        lat = float(location["latitude"])
        lon = float(location["longitude"])

        # Stocker en session
        if st.session_state.get("geo_lat") != lat:
            st.session_state.geo_lat = lat
            st.session_state.geo_lon = lon

            # Reverse geocoding
            with st.spinner("Recherche de l'adresse…"):
                geo_info = reverse_geocode(lat, lon)
                if geo_info:
                    st.session_state.geo_address = geo_info["address"]
                    st.session_state.geo_city = geo_info["city"]
                else:
                    st.session_state.geo_address = ""
                    st.session_state.geo_city = ""

            # Recherche des magasins à proximité
            with st.spinner("Recherche des magasins à proximité…"):
                shops = find_nearby_shops(lat, lon, radius=200)
                st.session_state.geo_shops = shops

        # Affichage de la position détectée
        st.markdown(f"""
        <div class="geoloc-detected">
            <strong>📍 Position détectée</strong><br>
            <span style="font-size:13px;">{st.session_state.get("geo_address", "Adresse inconnue")}</span><br>
            <span style="font-size:11px; opacity:0.7;">Lat: {lat:.5f} · Lon: {lon:.5f}</span>
        </div>
        """, unsafe_allow_html=True)

        # Liste des magasins trouvés
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
    st.markdown("### 📝 Étape 2 — Remplis les détails")

    selected_shop = st.session_state.get("geo_selected")
    default_magasin = selected_shop["name"] if selected_shop else ""
    default_ville = st.session_state.get("geo_city", "")

    # Pré-détection enseigne
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

        st.markdown("**Photos** (caméra ou galerie)")
        photos = st.file_uploader(
            "Photos",
            accept_multiple_files=True,
            type=["jpg", "jpeg", "png"],
            label_visibility="collapsed"
        )

        commentaire = st.text_area(
            "Commentaire (facultatif)",
            placeholder="Ex : Demande de réassort, retour buyer, idée d'animation…",
            height=80
        )

        submitted = st.form_submit_button("✅ Enregistrer la visite", use_container_width=True)

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
                st.success(f"✅ Visite enregistrée ! ({len(photo_urls)} photo(s) uploadée(s))")
            st.balloons()
            for k in ["geo_lat", "geo_lon", "geo_address", "geo_city", "geo_shops", "geo_selected"]:
                st.session_state.pop(k, None)
            st.session_state.screen = "home"
            st.rerun()


def screen_history():
    st.markdown(f'<div class="main-header"><h1>📜 Mon historique</h1><p>Toutes mes visites — {st.session_state.commercial}</p></div>', unsafe_allow_html=True)

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

    st.markdown("### 🔎 Filtres")
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
        # Échappement HTML pour éviter que les commentaires cassent l'affichage
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
            commentaire_section = f'<div style="margin-top:6px; font-size:12px; color:#666 !important; font-style:italic;">💬 {commentaire_safe}</div>'

        adresse_section = ""
        if row.get("Adresse_complete"):
            adresse_safe = html.escape(str(row["Adresse_complete"]))
            adresse_section = f'<div style="margin-top:4px; font-size:11px; color:#888 !important;">📍 {adresse_safe}</div>'

        st.markdown(f"""
        <div class="visit-card">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div style="flex:1;">
                    <strong>{magasin_safe}</strong> · <span style="color:#888 !important;">{enseigne_safe} — {ville_safe}</span><br>
                    <span style="font-size:12px; color:#666 !important;">{date_safe} {heure_safe} · {projet_safe}</span>
                    <div style="margin-top:6px; font-size:13px;">{etat_safe}</div>
                    {adresse_section}
                    {commentaire_section}
                    {photos_section}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def screen_dashboard():
    st.markdown('<div class="main-header"><h1>📊 Tableau de bord</h1><p>Vue globale — toutes les visites</p></div>', unsafe_allow_html=True)

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
        st.markdown(f'<div class="stat-card"><div class="stat-number">{total}</div><div class="stat-label">Visites</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{ruptures}</div><div class="stat-label">Ruptures</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{commerciaux}</div><div class="stat-label">Commerciaux</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{enseignes_visited}</div><div class="stat-label">Enseignes</div></div>', unsafe_allow_html=True)

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
                    st.markdown("### 🗺️ Carte des visites")
                    st.map(df_geo[["lat", "lon"]], zoom=5)
            except Exception:
                pass

    # Graphiques personnalisés en rose
    st.markdown("### Visites par enseigne")
    by_enseigne = df["Enseigne"].value_counts()
    render_bar_chart(by_enseigne)

    st.markdown("### Visites par projet")
    by_projet = df["Projet"].value_counts()
    render_bar_chart(by_projet)

    st.markdown("### Filtres")
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
    st.markdown('<div class="main-header"><h1>🔐 Espace admin</h1><p>Accès restreint</p></div>', unsafe_allow_html=True)

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
    st.markdown('<div class="main-header"><h1>⚙️ Admin — Configuration</h1><p>Gère les listes du formulaire</p></div>', unsafe_allow_html=True)

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

    # Filtres
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

    # Si une confirmation de suppression est en cours
    pending_delete = st.session_state.get("pending_delete_visit_id")

    for _, row in df_filtered.iterrows():
        visit_id = row["ID"]
        etat_emoji = row["Etat"].split()[0] if row["Etat"] else "📍"

        # Échappement HTML
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
                commentaire_html = f'<div style="margin-top:4px; font-size:11px; color:#666 !important; font-style:italic;">💬 {commentaire_safe}</div>'

            thumbs_html = render_thumbnails(row.get("Photos_URLs", ""), size=120, max_thumbs=4)

            st.markdown(f"""
            <div class="visit-card" style="padding:10px 14px;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div style="flex:1;">
                        <strong>{magasin_safe}</strong> · <span style="color:#888 !important;">{enseigne_safe} — {ville_safe}</span><br>
                        <span style="font-size:11px; color:#666 !important;">{date_safe} {heure_safe} · 👤 {commercial_safe} · ID: <code>{visit_id_safe}</code></span>
                        <div style="margin-top:4px; font-size:12px;">{etat_emoji} {projet_safe}</div>
                        {commentaire_html}
                        {thumbs_html}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_btn:
            if pending_delete == visit_id:
                # Affiche la confirmation
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
            st.markdown(f"<div class='visit-card' style='padding:10px 14px;'>{item}</div>", unsafe_allow_html=True)
        with col_b:
            if st.button("🗑️", key=f"del_{name}_{item}", help="Supprimer"):
                remove_from_config(name, item, defaults)
                st.success(f"« {item} » supprimé.")
                st.rerun()

    st.write("")
    st.markdown("### ➕ Ajouter une nouvelle valeur")
    with st.form(f"add_{name}", clear_on_submit=True):
        new_value = st.text_input("Nouvelle valeur", key=f"new_{name}")
        submitted = st.form_submit_button("Ajouter", use_container_width=True)
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
