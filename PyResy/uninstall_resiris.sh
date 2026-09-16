#!/usr/bin/env bash
#
# Resiris uninstaller for Linux.
# Removes everything install_resiris.sh installed (XDG-aware).

set -euo pipefail

DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
MIME_DIR="$DATA_HOME/mime/packages"
ICONS_DIR="$DATA_HOME/icons/hicolor/scalable/mimetypes"
BASH_COMPLETION_DIR="$DATA_HOME/bash-completion/completions"
ZSH_COMPLETION_DIR="$DATA_HOME/zsh/site-functions"

echo "Removing Resiris..."

if [[ -L "$BIN_DIR/resiris" || -f "$BIN_DIR/resiris" ]]; then
    rm -f "$BIN_DIR/resiris"
    echo "Removed: $BIN_DIR/resiris"
else
    echo "Terminal command not installed."
fi

rm -f "$BASH_COMPLETION_DIR/resiris" "$ZSH_COMPLETION_DIR/_resiris"
rm -f "$MIME_DIR/resy.xml" "$ICONS_DIR/application-x-resy.svg"
rm -f "$DATA_HOME/applications/resiris.desktop"

if command -v update-mime-database >/dev/null 2>&1; then
    update-mime-database "$DATA_HOME/mime" >/dev/null 2>&1 || true
fi

# Remove the Resiris VS Code extension if a VS Code-compatible CLI is available.
CODE_CMD=""
for cmd in code code-insiders code-oss codium; do
    if command -v "$cmd" >/dev/null 2>&1; then
        CODE_CMD="$(command -v "$cmd")"
        break
    fi
done

if [[ -n "$CODE_CMD" ]]; then
    "$CODE_CMD" --uninstall-extension resiris.resiris-language-support >/dev/null 2>&1 || true
    echo "Removed Resiris VS Code extension."
fi

echo "Removed Resiris Linux file integration."
echo "Your project files and .resy programs were NOT deleted."