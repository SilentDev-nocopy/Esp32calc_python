#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BIN="$HOME/.local/bin"
MIME="$HOME/.local/share/mime/packages"
ICONS="$HOME/.local/share/icons/hicolor/scalable/mimetypes"
BASH_COMPLETION="$HOME/.local/share/bash-completion/completions"
ZSH_COMPLETION="$HOME/.local/share/zsh/site-functions"

mkdir -p "$BIN" "$MIME" "$ICONS" "$BASH_COMPLETION" "$ZSH_COMPLETION"

ln -sfn "$ROOT/bin/resiris" "$BIN/resiris"

# Install shell completion for Resiris CLI arguments and .resy files.
if [[ -f "$ROOT/pre_packaging/shell/resiris.bash" ]]; then
    cp "$ROOT/pre_packaging/shell/resiris.bash"         "$BASH_COMPLETION/resiris"
fi

if [[ -f "$ROOT/pre_packaging/shell/_resiris" ]]; then
    cp "$ROOT/pre_packaging/shell/_resiris"         "$ZSH_COMPLETION/_resiris"
fi

if [[ -f "$ROOT/pre_packaging/linux/mime/resy.xml" ]]; then
    cp \
        "$ROOT/pre_packaging/linux/mime/resy.xml" \
        "$MIME/resy.xml"

    if [[ -f "$ROOT/pre_packaging/linux/icons/application-x-resy.svg" ]]; then
        cp \
            "$ROOT/pre_packaging/linux/icons/application-x-resy.svg" \
            "$ICONS/application-x-resy.svg"
    fi

    # Update MIME database
    if command -v update-mime-database >/dev/null 2>&1; then
        update-mime-database \
            "$HOME/.local/share/mime" \
            >/dev/null 2>&1 || true
    fi

fi

CODE_CMD=""

for cmd in code code-insiders codium; do
    if command -v "$cmd" >/dev/null 2>&1; then
        CODE_CMD="$cmd"
        break
    fi
done

CODE_DESKTOP=""

for desktop in \
    code.desktop \
    visual-studio-code.desktop \
    code-insiders.desktop \
    codium.desktop
do
    if [[ -f "$HOME/.local/share/applications/$desktop" ]]; then
        CODE_DESKTOP="$desktop"
        break
    fi

    if [[ -f "/usr/share/applications/$desktop" ]]; then
        CODE_DESKTOP="$desktop"
        break
    fi
done

if command -v xdg-mime >/dev/null 2>&1; then
    if [[ -n "$CODE_DESKTOP" ]]; then
        xdg-mime default \
            "$CODE_DESKTOP" \
            application/x-resy \
            || true

    else
        echo "WARNING: VS Code desktop entry not found."
        echo "         .resy files were not assigned a default editor."
    fi
fi

VSIX="$ROOT/pre_packaging/vscode/build/resiris-seti-file-icons-0.1.0.vsix"

if [[ -n "$CODE_CMD" ]]; then
    # Build the extension package if it does not exist
    if [[ ! -f "$VSIX" && \
          -f "$ROOT/pre_packaging/vscode/build_vsix.py" ]]; then

        if ! /usr/bin/python3 \
            "$ROOT/pre_packaging/vscode/build_vsix.py" \
            >/dev/null 2>&1
        then
            echo
            echo "WARNING: Could not build the VS Code extension."
            echo "         .resy Linux integration was still installed."
            echo
        fi
    fi

    # Install the extension
    if [[ -f "$VSIX" ]]; then
        "$CODE_CMD" \
            --install-extension "$VSIX" \
            --force
    else
        echo
        echo "WARNING: VS Code extension package is not available."
        echo "         .resy Linux integration was still installed."
        echo
    fi
else
    echo
    echo "WARNING: VS Code CLI was not found."
    echo "         .resy Linux integration was still installed."
    echo
fi

echo
echo "Resiris installed."
echo
echo "Run:"
echo "  resiris <file.resy>"
