"""
Merci Handy — Field Sales App
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

# Couleurs Merci Handy
PRIMARY = "#FF6B35"   # orange MH
DARK = "#2C2C2A"
LIGHT_BG = "#FAECE7"

ENSEIGNES = ["Monoprix", "Sephora", "Nocibé", "Marionnaud", "Carrefour", "Pharmacie", "Autre"]
PROJETS = [
    "Implantation permanente",
    "Animation saisonnière",
    "Lancement nouveauté",
    "Visite mensuelle",
    "Calendrier de l'avent",
    "Autre"
]
ETATS = ["✅ Linéaire OK", "⚠️ Problème de facing", "❌ Rupture détectée", "📍 Mauvais emplacement", "🎨 PLV manquante"]

# Colonnes de la Google Sheet (dans l'ordre)
SHEET_COLUMNS = [
    "ID", "Date", "Heure", "Commercial", "Enseigne", "Magasin",
    "Ville", "Projet", "Etat", "Commentaire", "Photos_URLs"
]

# =========================================================================
# STYLE
# =========================================================================

st.markdown(f"""
<style>
    .stApp {{
        background-color: #FAFAF7;
    }}
    .main-header {{
        background: {PRIMARY};
        color: white;
        padding: 16px 20px;
        border-radius: 12px;
        margin-bottom: 20px;
    }}
    .main-header h1 {{
        color: white !important;
        margin: 0 !important;
        font-size: 22px !important;
    }}
    .main-header p {{
        color: rgba(255,255,255,0.9) !important;
        margin: 4px 0 0 0 !important;
        font-size: 13px !important;
    }}
    .stat-card {{
        background: white;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        border: 1px solid #EEE;
    }}
    .stat-number {{
        font-size: 28px;
        font-weight: 600;
        color: {PRIMARY};
    }}
    .stat-label {{
        font-size: 12px;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    div[data-testid="stForm"] {{
        background: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #EEE;
    }}
    .stButton > button {{
        background: {PRIMARY};
        color: white;
        border: none;
        font-weight: 500;
    }}
    .stButton > button:hover {{
        background: #E55A28;
        color: white;
    }}
    .visit-card {{
        background: white;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
        border: 1px solid #EEE;
    }}
</style>
""", unsafe_allow_html=True)

# =========================================================================
# CONNEXIONS GOOGLE
# =========================================================================

@st.cache_resource
def get_google_clients():
    """Connecte à Google Sheets + Google Drive via le compte de service."""
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


def get_sheet():
    """Ouvre la Google Sheet et retourne l'onglet de données."""
    gc, _ = get_google_clients()
    sheet_id = st.secrets["sheet_id"]
    sheet = gc.open_by_key(sheet_id).sheet1
    # Initialise les colonnes si la sheet est vide
    if not sheet.row_values(1):
        sheet.append_row(SHEET_COLUMNS)
    return sheet


def upload_photo(photo_file, filename):
    """Upload une photo sur Google Drive et retourne le lien public."""
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

    # Rendre le fichier accessible via le lien
    drive.permissions().create(
        fileId=file["id"],
        body={"type": "anyone", "role": "reader"}
    ).execute()

    return file["webViewLink"]


@st.cache_data(ttl=60)
def load_visits():
    """Charge l'historique des visites depuis la Sheet."""
    sheet = get_sheet()
    data = sheet.get_all_records()
    if not data:
        return pd.DataFrame(columns=SHEET_COLUMNS)
    return pd.DataFrame(data)


def save_visit(visit_data, photo_urls):
    """Enregistre une nouvelle visite dans la Sheet."""
    sheet = get_sheet()
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


# =========================================================================
# ÉCRANS
# =========================================================================

def screen_login():
    """Écran de connexion : juste le nom du commercial."""
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
    """Écran d'accueil avec stats et bouton nouvelle visite."""
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
    st.markdown("### 📋 Mes dernières visites")

    if df_user.empty:
        st.info("Aucune visite enregistrée pour le moment. Clique sur « Nouvelle visite » pour commencer.")
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
        if st.button("📊 Tableau de bord", use_container_width=True):
            st.session_state.screen = "dashboard"
            st.rerun()
    with col_b:
        if st.button("👋 Changer d'utilisateur", use_container_width=True):
            del st.session_state.commercial
            st.rerun()


def screen_new_visit():
    """Formulaire de saisie d'une nouvelle visite."""
    st.markdown('<div class="main-header"><h1>📝 Nouvelle visite</h1><p>Remplis les champs ci-dessous</p></div>', unsafe_allow_html=True)

    if st.button("← Retour"):
        st.session_state.screen = "home"
        st.rerun()

    with st.form("new_visit_form", clear_on_submit=True):
        enseigne = st.selectbox("Enseigne *", ENSEIGNES)
        magasin = st.text_input("Nom du magasin *", placeholder="Ex : Monoprix Haussmann")
        ville = st.text_input("Ville *", placeholder="Paris")
        projet = st.selectbox("Projet / animation *", PROJETS)

        st.markdown("**État du linéaire** (coche tout ce qui s'applique)")
        etat_selected = []
        for etat in ETATS:
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

                # Upload des photos
                photo_urls = []
                if photos:
                    for i, photo in enumerate(photos):
                        filename = f"{now.strftime('%Y%m%d_%H%M%S')}_{enseigne}_{magasin.replace(' ', '_')}_{i+1}.jpg"
                        url = upload_photo(photo, filename)
                        photo_urls.append(url)

                # Sauvegarde dans la Sheet
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


def screen_dashboard():
    """Dashboard pilotage (vue globale, tous commerciaux)."""
    st.markdown('<div class="main-header"><h1>📊 Tableau de bord</h1><p>Vue globale — toutes les visites</p></div>', unsafe_allow_html=True)

    if st.button("← Retour"):
        st.session_state.screen = "home"
        st.rerun()

    df = load_visits()

    if df.empty:
        st.info("Aucune visite enregistrée pour l'instant.")
        return

    # KPIs globaux
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

    st.markdown("### Filtres")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_enseigne = st.multiselect("Enseigne", df["Enseigne"].unique())
    with col_f2:
        filter_commercial = st.multiselect("Commercial", df["Commercial"].unique())

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

    # Export CSV
    csv = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Exporter en CSV",
        csv,
        f"merci_handy_visites_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv",
        use_container_width=True
    )


# =========================================================================
# ROUTING
# =========================================================================

if "commercial" not in st.session_state:
    screen_login()
else:
    if "screen" not in st.session_state:
        st.session_state.screen = "home"

    if st.session_state.screen == "home":
        screen_home()
    elif st.session_state.screen == "new_visit":
        screen_new_visit()
    elif st.session_state.screen == "dashboard":
        screen_dashboard()
