# 🧴 Merci Handy — Field Sales App

Outil de suivi terrain pour les commerciaux Merci Handy. Permet de photographier les linéaires en magasin, renseigner l'enseigne, le projet et l'état du facing, et alimenter automatiquement un historique structuré dans Google Sheets.

**Stack :** Streamlit + Google Sheets + Google Drive · **Coût : 0€**

---

## 🚀 Déploiement — checklist (≈ 35 minutes)

> Suis les étapes **dans l'ordre**. À la fin tu auras une URL publique du type `merci-handy-field.streamlit.app` que tes commerciaux peuvent ouvrir sur leur téléphone.

### Étape 1 — Préparer la Google Sheet et le dossier Drive (5 min)

1. Va sur [Google Drive](https://drive.google.com) (compte Merci Handy).
2. Crée un dossier **« Merci Handy — Field Sales »**.
3. Dedans, crée :
   - Une **Google Sheet** vide → nomme-la **« Visites terrain »**. ➜ **copie l'ID dans l'URL** (la chaîne entre `/d/` et `/edit` dans l'URL `https://docs.google.com/spreadsheets/d/AAA_ID_ICI_AAA/edit`). Garde ça quelque part.
   - Un **dossier** vide nommé **« Photos terrain »**. ➜ **copie l'ID dans l'URL** (la chaîne après `/folders/` dans l'URL). Garde-le aussi.

### Étape 2 — Créer un compte de service Google (15 min, fait une fois pour toujours)

C'est l'étape la plus technique mais elle est indolore si tu suis ligne par ligne.

1. Va sur [Google Cloud Console](https://console.cloud.google.com).
2. En haut, clique sur le sélecteur de projet → **« Nouveau projet »** → nomme-le `merci-handy-field` → crée.
3. Une fois dans le projet, dans la barre de recherche en haut, tape **« Google Sheets API »** → clique sur le résultat → bouton **« Activer »**.
4. Refais pareil avec **« Google Drive API »** → **« Activer »**.
5. Dans le menu de gauche : **IAM et administration → Comptes de service**.
6. **« Créer un compte de service »** :
   - Nom : `field-app-bot`
   - Description : `Lecture/écriture pour l'app field sales`
   - Clique **Créer et continuer** → ignore les rôles → **OK**.
7. Sur la liste des comptes de service, clique sur celui que tu viens de créer → onglet **« Clés »** → **« Ajouter une clé » → « Créer une clé » → JSON** → télécharge le fichier `.json`. **Garde-le précieusement, on en a besoin à l'étape 4.**
8. **Copie l'adresse email du compte de service** (du type `field-app-bot@merci-handy-field.iam.gserviceaccount.com`).

### Étape 3 — Partager Sheet et Drive avec le compte de service (2 min)

1. Ouvre ta Google Sheet « Visites terrain » → bouton **Partager** → colle l'email du compte de service → rôle **Éditeur** → décoche « Avertir les utilisateurs » → **Envoyer**.
2. Pareil avec le dossier **« Photos terrain »** : Partager → email du compte de service → **Éditeur**.

### Étape 4 — Push le code sur GitHub (5 min)

1. Crée un nouveau repo GitHub (privé recommandé) : `merci-handy-field`.
2. Push les 3 fichiers :
   - `app.py`
   - `requirements.txt`
   - `README.md`

> **⚠️ NE PUSH PAS** le fichier JSON du compte de service. Il va dans les "secrets" Streamlit (étape suivante), pas dans le code.

### Étape 5 — Déployer sur Streamlit Community Cloud (5 min)

1. Va sur [share.streamlit.io](https://share.streamlit.io) → connecte-toi avec GitHub.
2. **« New app »** → sélectionne ton repo `merci-handy-field` → branche `main` → fichier `app.py` → **Deploy**.
3. Avant le premier lancement, va dans **Settings → Secrets**.
4. Colle ce template (remplace les valeurs) :

```toml
sheet_id = "ID_DE_TA_GOOGLE_SHEET"
drive_folder_id = "ID_DE_TON_DOSSIER_DRIVE"

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
```

> **Comment remplir `[gcp_service_account]`** : ouvre le fichier `.json` téléchargé à l'étape 2.7 — chaque champ correspond. Recopie tel quel. **Pour la clé privée**, garde les `\n` tels qu'ils sont dans le JSON, et entoure la valeur de guillemets droits `"..."`.

5. **Save** → l'app redémarre. Si tout est bon, tu verras l'écran de connexion. 🎉

### Étape 6 — Distribuer aux équipes (3 min)

1. Récupère l'URL de ton app (du type `https://merci-handy-field.streamlit.app`).
2. Envoie-la à tes commerciaux avec ce mode d'emploi :

> **Salut !**
> Voici notre nouvel outil terrain : **[URL]**
> Ouvre le lien sur ton téléphone, puis ajoute-le à ton écran d'accueil :
> - **iPhone** : icône partage → « Sur l'écran d'accueil »
> - **Android** : menu ⋮ → « Ajouter à l'écran d'accueil »
> Ça devient une icône comme une vraie app.
> À chaque visite : tu ouvres, tu remplis (60 sec), tu prends 2-3 photos, tu valides.

---

## 🛠️ Personnalisation rapide

| Ce que tu veux changer | Où dans `app.py` |
|---|---|
| Liste des enseignes | Variable `ENSEIGNES` en haut du fichier |
| Liste des projets | Variable `PROJETS` |
| États du linéaire | Variable `ETATS` |
| Couleur principale (orange MH) | Variable `PRIMARY` |
| Logo/header | Fonctions `screen_login()`, `screen_home()`, etc. |

Après modification : `git push` → Streamlit redéploie automatiquement en 30 secondes.

---

## ⚠️ Limites à connaître

- **Streamlit Community Cloud** : gratuit mais "s'endort" après quelques minutes d'inactivité — le premier accès du jour peut prendre 10-15 secondes. Acceptable pour un usage terrain.
- **Stockage Drive** : 15 Go gratuits sur le compte Google. À raison de ~500 Ko par photo compressée, ça fait **~30 000 photos**. Très large.
- **Mode hors-ligne** : pas natif. Si pas de réseau en magasin, le commercial prend ses photos avec son appareil photo classique et remplit le formulaire au café après.

---

## 🔮 Évolutions possibles

- Géolocalisation auto du magasin (Streamlit + JS)
- Dashboard plus visuel via Looker Studio connecté à la Sheet
- Notifications email automatiques en cas de rupture (Apps Script sur la Sheet)
- Authentification par code PIN par commercial
- Reconnaissance auto de facing (à ce stade, passer sur Sidely)

---

**Fait avec ❤️ pour Merci Handy.**
