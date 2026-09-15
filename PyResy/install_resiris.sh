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

# Verify that the installed CLI points to this exact project copy.
if [[ "$(readlink -f "$BIN/resiris")" != "$(readlink -f "$ROOT/bin/resiris")" ]]; then
    echo "ERROR: Resiris CLI installation points to the wrong executable." >&2
    exit 1
fi

# Install shell completion for Resiris CLI arguments and .resy files.
if [[ -f "$ROOT/pre_packaging/shell/resiris.bash" ]]; then
    cp "$ROOT/pre_packaging/shell/resiris.bash" "$BASH_COMPLETION/resiris"
fi

if [[ -f "$ROOT/pre_packaging/shell/_resiris" ]]; then
    cp "$ROOT/pre_packaging/shell/_resiris" "$ZSH_COMPLETION/_resiris"
fi

# Install Linux MIME integration and the file-manager icon.
if [[ -f "$ROOT/pre_packaging/linux/mime/resy.xml" ]]; then
    cp "$ROOT/pre_packaging/linux/mime/resy.xml" "$MIME/resy.xml"

    if [[ -f "$ROOT/pre_packaging/linux/icons/application-x-resy.svg" ]]; then
        cp "$ROOT/pre_packaging/linux/icons/application-x-resy.svg" "$ICONS/application-x-resy.svg"
    fi

    if command -v update-mime-database >/dev/null 2>&1; then
        update-mime-database "$HOME/.local/share/mime" >/dev/null 2>&1 || true
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
        xdg-mime default "$CODE_DESKTOP" application/x-resy || true
    else
        echo "WARNING: VS Code desktop entry not found."
        echo "         .resy files were not assigned a default editor."
    fi
fi

VSIX="$ROOT/pre_packaging/vscode/build/resiris-language-support-0.2.1.vsix"

# The terminal installer does NOT install the VS Code extension automatically.
# If a VS Code-compatible CLI is available, explicitly ask the user first.
if [[ -n "$CODE_CMD" ]]; then
    echo
    read -r -p "Install Resiris Language Support for VS Code (includes .resy icons)? [y/N] " answer
    echo

    if [[ "$answer" =~ ^[Yy]$ ]]; then
        if [[ ! -f "$VSIX" && -f "$ROOT/pre_packaging/vscode/build_vsix.py" ]]; then
            if ! /usr/bin/python3 "$ROOT/pre_packaging/vscode/build_vsix.py" >/dev/null 2>&1; then
                echo "WARNING: Could not build the VS Code extension."
                echo "         Resiris terminal/Linux integration was still installed."
                VSIX=""
            fi
        fi

        if [[ -n "$VSIX" && -f "$VSIX" ]]; then
            "$CODE_CMD" --install-extension "$VSIX" --force
        else
            echo "WARNING: VS Code extension package is not available."
            echo "         Resiris terminal/Linux integration was still installed."
        fi
    else
        echo "VS Code extension not installed."
        echo "You can install Resiris Language Support from VS Code later."
    fi
else
    echo
    echo "VS Code CLI was not found."
    echo "The Resiris VS Code extension was not installed."
    echo
fi

echo
echo "Resiris installed."
echo
echo "Run:"
echo "  resiris <file.resy>"
