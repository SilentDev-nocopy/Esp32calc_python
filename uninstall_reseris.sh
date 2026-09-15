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

# Remove the current Resiris VS Code extension. Also remove the old file-icon
# extension ID from previous releases so upgrades/uninstalls leave no residue.
for cmd in code code-insiders codium; do
    if command -v "$cmd" >/dev/null 2>&1; then
        "$cmd" --uninstall-extension resiris.resiris-language-support >/dev/null 2>&1 || true
        "$cmd" --uninstall-extension resiris.resiris-seti-file-icons >/dev/null 2>&1 || true
    fi
done

echo "Removed Resiris Linux file integration and VS Code extension."
echo "Your project files and .resy programs were NOT deleted."
