#!/bin/bash
# ============================================================================
# 🚀 push.sh — Push tout-en-un pour Merci Handy Field
# Usage :
#   ./push.sh                     → commit avec message auto-généré
#   ./push.sh "ton message ici"   → commit avec ton message custom
# ============================================================================

set -e  # Stop si une commande échoue

# === Couleurs MH ===
PINK='\033[38;5;213m'
YELLOW='\033[38;5;220m'
GREEN='\033[38;5;120m'
RED='\033[38;5;203m'
BLUE='\033[38;5;111m'
GRAY='\033[38;5;245m'
BOLD='\033[1m'
RESET='\033[0m'

# === Bannière ===
echo ""
echo -e "${PINK}${BOLD}╭──────────────────────────────────────────╮${RESET}"
echo -e "${PINK}${BOLD}│  💖 MERCI HANDY — Push to GitHub  💖     │${RESET}"
echo -e "${PINK}${BOLD}╰──────────────────────────────────────────╯${RESET}"
echo ""

# === Se positionner dans le dossier du script ===
cd "$(dirname "$0")"

# === Vérifier qu'on est dans un repo git ===
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Ce dossier n'est pas un repo git !${RESET}"
    echo -e "${GRAY}   Lance d'abord : git init && git remote add origin <url>${RESET}"
    exit 1
fi

# === Vérifier qu'il y a un remote ===
if ! git remote get-url origin > /dev/null 2>&1; then
    echo -e "${RED}❌ Aucun remote 'origin' configuré.${RESET}"
    echo -e "${GRAY}   Lance : git remote add origin https://github.com/MerciHandy/merci-handy-field.git${RESET}"
    exit 1
fi

REMOTE_URL=$(git remote get-url origin)
echo -e "${BLUE}📡 Remote :${RESET} ${GRAY}${REMOTE_URL}${RESET}"

# === Détecter la branche ===
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
echo -e "${BLUE}🌿 Branche :${RESET} ${GRAY}${BRANCH}${RESET}"

# === Vérifier qu'il y a des changements ===
if [ -z "$(git status --porcelain)" ]; then
    echo ""
    echo -e "${YELLOW}✨ Rien à pusher — tout est à jour !${RESET}"
    echo ""
    exit 0
fi

# === Afficher ce qui va être commité ===
echo ""
echo -e "${YELLOW}📝 Changements détectés :${RESET}"
git status --short | sed 's/^/   /'
echo ""

# === Message de commit ===
if [ -n "$1" ]; then
    COMMIT_MSG="$1"
else
    # Auto : date + nb fichiers modifiés
    NB_FILES=$(git status --porcelain | wc -l | tr -d ' ')
    COMMIT_MSG="Mise à jour ($(date '+%d/%m/%Y %H:%M')) — $NB_FILES fichier(s)"
fi

echo -e "${BLUE}💬 Message :${RESET} ${GRAY}${COMMIT_MSG}${RESET}"
echo ""

# === Add + Commit ===
echo -e "${PINK}📦 git add .${RESET}"
git add .

echo -e "${PINK}💾 git commit${RESET}"
git commit -m "$COMMIT_MSG"

# === Push ===
echo ""
echo -e "${PINK}🚀 git push origin ${BRANCH}${RESET}"
echo ""

if git push origin "$BRANCH"; then
    echo ""
    echo -e "${GREEN}${BOLD}✅ Push réussi !${RESET}"
    echo -e "${GRAY}   ${REMOTE_URL%.git}${RESET}"
    echo ""
    echo -e "${YELLOW}💡 Streamlit Cloud va redéployer automatiquement dans ~30 sec.${RESET}"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Push échoué.${RESET}"
    echo -e "${GRAY}   Pistes :${RESET}"
    echo -e "${GRAY}   • Le repo distant a-t-il des commits que tu n'as pas ? → git pull --rebase${RESET}"
    echo -e "${GRAY}   • Premier push ? → git push -u origin ${BRANCH}${RESET}"
    echo -e "${GRAY}   • Auth GitHub ? → vérifie ton token / SSH key${RESET}"
    echo ""
    exit 1
fi
