# 💖 Merci Handy — Field Sales App

Outil de suivi terrain pour les commerciaux Merci Handy. Géolocalisation auto, détection du magasin via OpenStreetMap, photos compressées et hébergées sur Cloudinary, données centralisées dans Google Sheets.

**Stack :** Streamlit + Google Sheets + Cloudinary + OpenStreetMap · **Coût : 0€**

---

## ⚡ Workflow de mise à jour (1 commande)

Quand tu modifies l'app en local :

```bash
./push.sh "Description de ce que tu as changé"
```

Le script fait `git add . → commit → push origin main`. Streamlit Cloud redéploie automatiquement en ~30 secondes.

Si tu n'as pas de message à donner, lance juste `./push.sh` et il génère un message auto avec la date.

---

## 🚀 Déploiement initial — checklist (≈ 35 min)

> À faire **une seule fois** au tout début. Ensuite tu n'auras plus qu'à pusher tes modifs avec `./push.sh`.

### Étape 1 — Google Sheet + Service Account (15 min)

1. Crée une **Google Sheet** vide nommée **"Visites terrain"**. Copie l'ID (la chaîne entre `/d/` et `/edit` dans l'URL).
2. Va sur [Google Cloud Console](https://console.cloud.google.com) → nouveau projet `merci-handy-field`.
3. Active **Google Sheets API** et **Google Drive API** (barre de recherche).
4. **IAM → Comptes de service → Créer** : `field-app-bot`.
5. Onglet **Clés → Ajouter une clé → JSON** → télécharge le fichier.
6. Partage ta Google Sheet avec l'email du compte de service (rôle **Éditeur**).

### Étape 2 — Cloudinary (3 min)

1. Va sur [cloudinary.com](https://cloudinary.com) → crée un compte gratuit (10 Go + 25k transformations/mois).
2. Sur le Dashboard, récupère : `Cloud name`, `API Key`, `API Secret`.

### Étape 3 — Push le code sur GitHub (5 min)

Le repo est déjà configuré sur `https://github.com/MerciHandy/merci-handy-field`. Premier push :

```bash
cd "/Users/louismarty/Documents/Claude/Projects/FIELD TOOL"
git add .
git commit -m "Initial commit"
git push -u origin main
```

> **⚠️ NE PUSH JAMAIS** le fichier JSON du service account ni `secrets.toml`. Le `.gitignore` les exclut déjà — vérifie quand même avec `git status` avant le premier push.

### Étape 4 — Déployer sur Streamlit Community Cloud (5 min)

1. Va sur [share.streamlit.io](https://share.streamlit.io) → connecte-toi avec GitHub.
2. **New app** → sélectionne `MerciHandy/merci-handy-field` → branche `main` → fichier `app.py` → **Deploy**.
3. **Settings → Secrets** → colle ce template (remplace les valeurs) :

```toml
sheet_id = "ID_DE_TA_GOOGLE_SHEET"
admin_password = "mercihandy2026"  # optionnel — change-le !

[gcp_service_account]
type = "service_account"
project_id = "merci-handy-field"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "field-app-bot@merci-handy-field.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"

[cloudinary]
cloud_name = "ton_cloud_name"
api_key = "123456789012345"
api_secret = "abcDEF..."
```

> **Comment remplir `[gcp_service_account]`** : ouvre le fichier `.json` téléchargé à l'étape 1.5 — chaque champ correspond. Recopie tel quel. Pour `private_key`, garde les `\n` tels quels et entoure de guillemets droits `"..."`.

4. **Save** → l'app redémarre. Tu verras l'écran de connexion. 🎉

### Étape 5 — Distribuer aux commerciaux (3 min)

1. Récupère l'URL Streamlit (ex : `merci-handy-field.streamlit.app`).
2. Envoie-la à l'équipe avec ce mode d'emploi :

> **Hello !**
> Voici notre nouvel outil terrain : **[URL]**
> Ouvre le lien sur ton téléphone et ajoute-le à ton écran d'accueil :
> - **iPhone** : icône partage → "Sur l'écran d'accueil"
> - **Android** : menu ⋮ → "Ajouter à l'écran d'accueil"
> À chaque visite : tu ouvres, tu localises, tu remplis (60 sec), 2-3 photos, tu valides. 💖

---

## 🎨 Personnalisation rapide

| Ce que tu veux changer | Où dans `app.py` |
|---|---|
| Palette de couleurs | Bloc `# 🎨 Palette Merci Handy` (lignes ~30) |
| Liste des enseignes | Variable `DEFAULT_ENSEIGNES` |
| Liste des projets | Variable `DEFAULT_PROJETS` |
| États du linéaire | Variable `DEFAULT_ETATS` |
| Header / Logo | Recherche `main-header` dans les fonctions `screen_*()` |

Après modification : `./push.sh "Changement couleur principale"` → Streamlit redéploie en 30 sec.

---

## 🧪 Tester en local (optionnel)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

> Pour tester en local, crée un fichier `.streamlit/secrets.toml` avec le même contenu que sur Streamlit Cloud. Ce fichier est dans le `.gitignore`, il ne sera **jamais** pushé.

---

## ⚠️ Limites à connaître

- **Streamlit Community Cloud** : gratuit mais "s'endort" après quelques minutes d'inactivité — premier accès du jour ~10-15 sec.
- **Stockage photos (Cloudinary gratuit)** : 25 Go + 25k transformations/mois. Avec compression à ~200 Ko/photo, ça fait **~125 000 photos**. Très large.
- **Mode hors-ligne** : pas natif. Si pas de réseau, prendre photos avec l'appareil photo classique et remplir le formulaire au café après.

---

## 🆕 Nouveautés v4 — Pop & Colorful

- 💖 Nouvelle palette pop : rose vif + jaune + mint + bleu + corail
- 🔤 Police custom (Fredoka pour les titres, Quicksand pour le corps)
- 🌈 Gradients multicolores sur les headers
- ✨ Boutons arrondis avec shadows
- 🎨 Stat cards colorées avec liseré coloré
- 📊 Graphiques de dashboard multicolores
- ⚡ Animations subtiles (hover, sparkle)

---

## 🔮 Évolutions possibles

- Authentification par code PIN par commercial
- Dashboard Looker Studio connecté à la Sheet
- Notifications email automatiques en cas de rupture (Apps Script)
- Mode hors-ligne avec sync au retour
- Reconnaissance auto de facing (à ce stade, passer sur Sidely)

---

**Fait avec 💖 pour Merci Handy.**
