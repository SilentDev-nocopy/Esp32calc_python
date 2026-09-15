#!/usr/bin/env bash
set -euo pipefail

echo "Removing Resiris..."

if [[ -L "$HOME/.local/bin/resiris" || -f "$HOME/.local/bin/resiris" ]]; then
    rm -f "$HOME/.local/bin/resiris"
    echo "Removed: ~/.local/bin/resiris"
else
    echo "Terminal command not installed."
fi

MIME="$HOME/.local/share/mime/packages"
ICONS="$HOME/.local/share/icons/hicolor/scalable/mimetypes"
BASH_COMPLETION="$HOME/.local/share/bash-completion/completions"
ZSH_COMPLETION="$HOME/.local/share/zsh/site-functions"

rm -f "$BASH_COMPLETION/resiris" "$ZSH_COMPLETION/_resiris"

# Remove .resy Linux file-manager integration.
rm -f "$MIME/resy.xml" "$ICONS/application-x-resy.svg"
rm -f "$HOME/.local/share/applications/resiris.desktop"

command -v update-mime-database >/dev/null 2>&1 && \
    update-mime-database "$HOME/.local/share/mime" >/dev/null 2>&1 || true

echo "Removed Resiris Linux file integration."
echo "Your project files and .resy programs were NOT deleted."
