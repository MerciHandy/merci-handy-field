"""
Merci Handy — Field Sales App (v2)
Outil de suivi terrain pour les commerciaux.
Backend : Google Sheets + Google Drive
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

# =========================================================================
# CONFIGURATION
# =========================================================================

st.set_page_config(
    page_title="Merci Handy — Field",
    page_icon="🧴",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Couleurs Merci Handy (rose)
PRIMARY = "#EDADE7"
PRIMARY_DARK = "#D88FCE"
TEXT_DARK = "#2C2C2A"
TEXT_LIGHT = "#FFFFFF"
BG_LIGHT = "#FFFFFF"
BG_SOFT = "#FDF5FB"

# Listes par défaut (utilisées seulement si la config Sheet est vide)
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

# Colonnes de la Sheet "Visites"
SHEET_COLUMNS = [
    "ID", "Date", "Heure", "Commercial", "Enseigne", "Magasin",
    "Ville", "Projet", "Etat", "Commentaire", "Photos_URLs"
]

# Mot de passe admin (par défaut, peut être surchargé via secrets)
DEFAULT_ADMIN_PASSWORD = "mercihandy2026"

# =========================================================================
# STYLE — thème clair lisible
# =========================================================================

st.markdown(f"""
<style>
    /* Force light theme & lisibilité */
    .stApp {{
        background-color: {BG_SOFT};
        color: {TEXT_DARK};
    }}

    /* Tous les inputs : fond blanc, texte foncé */
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox [data-baseweb="select"] > div,
    .stMultiSelect [data-baseweb="select"] > div,
    div[data-baseweb="input"] input,
    .stDateInput input {{
        background-color: {BG_LIGHT} !important;
        color: {TEXT_DARK} !important;
        border: 1px solid #DDD !important;
    }}

    /* Labels lisibles */
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label,
    .stMultiSelect label,
    .stCheckbox label,
    .stFileUploader label,
    .stRadio label,
    label {{
        color: {TEXT_DARK} !important;
        font-weight: 500 !important;
    }}

    /* Checkboxes */
    .stCheckbox > label > div[data-testid="stMarkdownContainer"] p {{
        color: {TEXT_DARK} !important;
    }}

    /* Markdown text */
    .stMarkdown, .stMarkdown p, .stMarkdown li {{
        color: {TEXT_DARK} !important;
    }}

    /* File uploader */
    [data-testid="stFileUploader"] {{
        background-color: {BG_LIGHT};
        border-radius: 8px;
        padding: 8px;
    }}
    [data-testid="stFileUploader"] section {{
        background-color: {BG_LIGHT} !important;
        border: 2px dashed #DDD !important;
    }}

    /* Header stylé */
    .main-header {{
        background: linear-gradient(135deg, {PRIMARY} 0%, {PRIMARY_DARK} 100%);
        color: {TEXT_DARK};
        padding: 20px 24px;
        border-radius: 16px;
        margin-bottom: 20px;
        box-shadow: 0 2px 12px rgba(237, 173, 231, 0.3);
    }}
    .main-header h1 {{
        color: {TEXT_DARK} !important;
        margin: 0 !important;
        font-size: 22px !important;
        font-weight: 600 !important;
    }}
    .main-header p {{
        color: {TEXT_DARK} !important;
        margin: 4px 0 0 0 !important;
        font-size: 13px !important;
        opacity: 0.85;
    }}

    /* Stat cards */
    .stat-card {{
        background: {BG_LIGHT};
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        border: 1px solid #EEE;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }}
    .stat-number {{
        font-size: 28px;
        font-weight: 700;
        color: {PRIMARY_DARK};
    }}
    .stat-label {{
        font-size: 11px;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 500;
    }}

    /* Form */
    div[data-testid="stForm"] {{
        background: {BG_LIGHT};
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #EEE;
    }}

    /* Boutons primaires */
    .stButton > button[kind="primary"],
    .stButton > button {{
        background: {PRIMARY};
        color: {TEXT_DARK};
        border: none;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.2s;
    }}
    .stButton > button:hover {{
        background: {PRIMARY_DARK};
        color: {TEXT_DARK};
        transform: translateY(-1px);
    }}
    .stButton > button[kind="secondary"] {{
        background: {BG_LIGHT};
        color: {TEXT_DARK};
        border: 1px solid #DDD;
    }}

    /* Form submit */
    .stFormSubmitButton > button {{
        background: {PRIMARY} !important;
        color: {TEXT_DARK} !important;
        font-weight: 600 !important;
    }}

    /* Visit cards */
    .visit-card {{
        background: {BG_LIGHT};
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 8px;
        border: 1px solid #EEE;
        color: {TEXT_DARK};
    }}
    .visit-card strong, .visit-card span, .visit-card div {{
        color: {TEXT_DARK} !important;
    }}

    /* Tableaux */
    .stDataFrame {{
        background: {BG_LIGHT};
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background: {BG_LIGHT};
        border-radius: 8px 8px 0 0;
        color: {TEXT_DARK};
    }}
    .stTabs [aria-selected="true"] {{
        background: {PRIMARY} !important;
        color: {TEXT_DARK} !important;
    }}

    /* Alertes */
    .stAlert {{
        background: {BG_LIGHT};
        color: {TEXT_DARK};
    }}
</style>
""", unsafe_allow_html=True)

# =========================================================================
# CONNEXIONS GOOGLE
# =========================================================================

@st.cache_resource
def get_google_clients():
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes
        )
        gc = gspread.authorize(creds)
        drive = build("drive", "v3", credentials=creds)
        return gc, drive
    except Exception as e:
        st.error(f"Erreur de connexion Google : {e}")
        st.info("Vérifie que les secrets sont bien configurés dans Streamlit Cloud (voir README).")
        st.stop()


def get_workbook():
    """Ouvre le classeur Google Sheets complet."""
    gc, _ = get_google_clients()
    sheet_id = st.secrets["sheet_id"]
    return gc.open_by_key(sheet_id)


def get_visits_sheet():
    """Onglet principal des visites."""
    wb = get_workbook()
    sheet = wb.sheet1
    if not sheet.row_values(1):
        sheet.append_row(SHEET_COLUMNS)
    return sheet


def get_or_create_config_sheet(name, default_values):
    """
    Récupère ou crée un onglet de config (Enseignes, Projets, Etats).
    Chaque onglet a une seule colonne 'Valeur'.
    """
    wb = get_workbook()
    try:
        ws = wb.worksheet(name)
    except gspread.exceptions.WorksheetNotFound:
        ws = wb.add_worksheet(title=name, rows=100, cols=2)
        ws.append_row(["Valeur"])
        for v in default_values:
            ws.append_row([v])
    # Si l'onglet est vide, on initialise avec les défauts
    values = ws.col_values(1)
    if len(values) <= 1:
        for v in default_values:
            ws.append_row([v])
    return ws


@st.cache_data(ttl=30)
def load_config_list(name, default_values):
    """Charge la liste de configuration (Enseignes/Projets/Etats)."""
    ws = get_or_create_config_sheet(name, default_values)
    values = ws.col_values(1)
    # Skip header
    return [v for v in values[1:] if v.strip()]


def add_to_config(name, value, default_values):
    """Ajoute une valeur dans une liste de config."""
    ws = get_or_create_config_sheet(name, default_values)
    ws.append_row([value])
    st.cache_data.clear()


def remove_from_config(name, value, default_values):
    """Supprime une valeur d'une liste de config."""
    ws = get_or_create_config_sheet(name, default_values)
    values = ws.col_values(1)
    for i, v in enumerate(values):
        if v == value and i != 0:  # Ne pas supprimer le header
            ws.delete_rows(i + 1)
            break
    st.cache_data.clear()


def upload_photo(photo_file, filename):
    """Upload une photo sur Google Drive."""
    _, drive = get_google_clients()
    folder_id = st.secrets["drive_folder_id"]

    file_metadata = {"name": filename, "parents": [folder_id]}
    media = MediaIoBaseUpload(
        io.BytesIO(photo_file.getvalue()),
        mimetype=photo_file.type or "image/jpeg"
    )
    file = drive.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink"
    ).execute()

    drive.permissions().create(
        fileId=file["id"],
        body={"type": "anyone", "role": "reader"}
    ).execute()

    return file["webViewLink"]


@st.cache_data(ttl=30)
def load_visits():
    """Charge l'historique."""
    sheet = get_visits_sheet()
    data = sheet.get_all_records()
    if not data:
        return pd.DataFrame(columns=SHEET_COLUMNS)
    return pd.DataFrame(data)


def save_visit(visit_data, photo_urls):
    """Enregistre une nouvelle visite."""
    sheet = get_visits_sheet()
    row = [
        visit_data["id"],
        visit_data["date"],
        visit_data["heure"],
        visit_data["commercial"],
        visit_data["enseigne"],
        visit_data["magasin"],
        visit_data["ville"],
        visit_data["projet"],
        ", ".join(visit_data["etat"]),
        visit_data["commentaire"],
        " | ".join(photo_urls)
    ]
    sheet.append_row(row)
    st.cache_data.clear()


def get_admin_password():
    """Récupère le mot de passe admin depuis les secrets, ou défaut."""
    try:
        return st.secrets.get("admin_password", DEFAULT_ADMIN_PASSWORD)
    except Exception:
        return DEFAULT_ADMIN_PASSWORD


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

    # Stats
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
        st.rerun()

    st.write("")
    st.markdown("### 📋 Mes 10 dernières visites")

    if df_user.empty:
        st.info("Aucune visite enregistrée pour le moment.")
    else:
        df_user_sorted = df_user.sort_values(by=["Date", "Heure"], ascending=False).head(10)
        for _, row in df_user_sorted.iterrows():
            etat_emoji = row["Etat"].split()[0] if row["Etat"] else "📍"
            st.markdown(f"""
            <div class="visit-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <strong>{row["Magasin"]}</strong> · <span style="color:#888;">{row["Enseigne"]}</span><br>
                        <span style="font-size:12px; color:#666;">{row["Date"]} · {row["Projet"]}</span>
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
    st.markdown('<div class="main-header"><h1>📝 Nouvelle visite</h1><p>Remplis les champs ci-dessous</p></div>', unsafe_allow_html=True)

    if st.button("← Retour"):
        st.session_state.screen = "home"
        st.rerun()

    enseignes = load_config_list("Enseignes", DEFAULT_ENSEIGNES)
    projets = load_config_list("Projets", DEFAULT_PROJETS)
    etats = load_config_list("Etats", DEFAULT_ETATS)

    with st.form("new_visit_form", clear_on_submit=True):
        enseigne = st.selectbox("Enseigne *", enseignes)
        magasin = st.text_input("Nom du magasin *", placeholder="Ex : Monoprix Haussmann")
        ville = st.text_input("Ville *", placeholder="Paris")
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
                if photos:
                    for i, photo in enumerate(photos):
                        filename = f"{now.strftime('%Y%m%d_%H%M%S')}_{enseigne}_{magasin.replace(' ', '_')}_{i+1}.jpg"
                        url = upload_photo(photo, filename)
                        photo_urls.append(url)

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
                    "commentaire": commentaire.strip()
                }
                save_visit(visit_data, photo_urls)

            st.success(f"✅ Visite enregistrée ! ({len(photo_urls)} photo(s) uploadée(s))")
            st.balloons()
            st.session_state.screen = "home"
            st.rerun()


def screen_history():
    """Historique complet des visites du commercial connecté."""
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

    # Filtres
    st.markdown("### 🔎 Filtres")
    col1, col2 = st.columns(2)
    with col1:
        filter_enseigne = st.multiselect("Enseigne", sorted(df_user["Enseigne"].unique()))
    with col2:
        filter_projet = st.multiselect("Projet", sorted(df_user["Projet"].unique()))

    search = st.text_input("🔍 Rechercher (magasin, ville, commentaire…)", placeholder="Ex : Haussmann")

    # Application filtres
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

    # Affichage en cards détaillées
    for _, row in df_filtered.iterrows():
        etat_emoji = row["Etat"].split()[0] if row["Etat"] else "📍"
        photos_section = ""
        if row.get("Photos_URLs"):
            urls = [u.strip() for u in str(row["Photos_URLs"]).split("|") if u.strip()]
            if urls:
                links = " · ".join([f'<a href="{u}" target="_blank" style="color:{PRIMARY_DARK};">📷 Photo {i+1}</a>' for i, u in enumerate(urls)])
                photos_section = f'<div style="margin-top:8px; font-size:12px;">{links}</div>'

        commentaire_section = ""
        if row.get("Commentaire"):
            commentaire_section = f'<div style="margin-top:6px; font-size:12px; color:#666; font-style:italic;">💬 {row["Commentaire"]}</div>'

        st.markdown(f"""
        <div class="visit-card">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div style="flex:1;">
                    <strong>{row["Magasin"]}</strong> · <span style="color:#888;">{row["Enseigne"]} — {row["Ville"]}</span><br>
                    <span style="font-size:12px; color:#666;">{row["Date"]} {row["Heure"]} · {row["Projet"]}</span>
                    <div style="margin-top:6px; font-size:13px;">{row["Etat"]}</div>
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

    # KPIs
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
    st.markdown("### Visites par enseigne")
    by_enseigne = df["Enseigne"].value_counts()
    st.bar_chart(by_enseigne)

    st.markdown("### Visites par projet")
    by_projet = df["Projet"].value_counts()
    st.bar_chart(by_projet)

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
    """Écran de login admin protégé par mot de passe."""
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
    """Page admin pour gérer les listes."""
    st.markdown('<div class="main-header"><h1>⚙️ Admin — Configuration</h1><p>Gère les listes utilisées dans le formulaire</p></div>', unsafe_allow_html=True)

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

    tab1, tab2, tab3 = st.tabs(["🏪 Enseignes", "🚀 Projets / animations", "📋 États linéaire"])

    with tab1:
        manage_list("Enseignes", DEFAULT_ENSEIGNES)
    with tab2:
        manage_list("Projets", DEFAULT_PROJETS)
    with tab3:
        manage_list("Etats", DEFAULT_ETATS, with_emoji_hint=True)


def manage_list(name, defaults, with_emoji_hint=False):
    """Composant générique pour gérer une liste de config."""
    items = load_config_list(name, defaults)

    st.markdown(f"### {len(items)} valeur(s) actives")

    if with_emoji_hint:
        st.caption("💡 Astuce : tu peux ajouter un emoji au début pour la lisibilité (ex : `🆕 Nouveau lancement été 2026`)")

    # Liste des valeurs avec bouton supprimer
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
