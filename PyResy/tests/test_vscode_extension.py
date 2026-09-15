import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VSCODE = ROOT / "pre_packaging" / "vscode"
VSIX = VSCODE / "build" / "resiris-language-support-0.2.0.vsix"


def test_extension_manifest_declares_resy_language_and_icon_theme():
    package = json.loads((VSCODE / "package.json").read_text(encoding="utf-8"))

    assert package["name"] == "resiris-language-support"
    assert package["displayName"] == "Resiris Language Support"

    languages = package["contributes"]["languages"]
    resiris = next(item for item in languages if item["id"] == "resiris")
    assert ".resy" in resiris["extensions"]

    grammars = package["contributes"]["grammars"]
    assert any(item["language"] == "resiris" for item in grammars)

    snippets = package["contributes"]["snippets"]
    assert any(item["language"] == "resiris" for item in snippets)

    themes = package["contributes"]["iconThemes"]
    assert any(item["id"] == "resiris-seti" for item in themes)


def test_language_configuration_forces_tabs():
    config = json.loads(
        (VSCODE / "language-configuration.json").read_text(encoding="utf-8")
    )
    defaults = json.loads((VSCODE / "package.json").read_text(encoding="utf-8"))["contributes"]["configurationDefaults"]

    assert config["comments"]["lineComment"] == "##"
    assert defaults["[resiris]"]["editor.insertSpaces"] is False
    assert defaults["[resiris]"]["editor.detectIndentation"] is False
    assert defaults["[resiris]"]["editor.tabSize"] == 4


def test_grammar_contains_current_resiris_keywords_and_lifecycle():
    grammar = json.loads(
        (VSCODE / "syntaxes" / "resiris.tmLanguage.json").read_text(encoding="utf-8")
    )
    text = json.dumps(grammar)

    for word in ("v", "c", "fn", "start", "process", "await", "if", "elif", "else", "mat", "return", "pass"):
        assert word in text

    assert "##.*$" in text
    assert "print_cmd" in text
    assert "RSMath" not in text  # modules are intentionally generic


def test_snippets_use_tab_indentation():
    snippets = json.loads(
        (VSCODE / "snippets" / "resiris.json").read_text(encoding="utf-8")
    )

    assert snippets["Resiris start"]["body"][1].startswith("\t")
    assert snippets["Resiris process"]["body"][1].startswith("\t")
    assert snippets["Resiris function"]["body"][1].startswith("\t")


def test_built_vsix_contains_language_support_files():
    assert VSIX.is_file()

    with zipfile.ZipFile(VSIX) as archive:
        names = set(archive.namelist())

    expected = {
        "extension/package.json",
        "extension/language-configuration.json",
        "extension/syntaxes/resiris.tmLanguage.json",
        "extension/snippets/resiris.json",
        "extension/icons/resiris-seti-icon-theme.json",
        "extension/icons/resy.png",
        "extension/icons/seti.woff",
    }
    assert expected <= names
