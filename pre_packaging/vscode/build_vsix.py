#!/usr/bin/env python3
import json, os, shutil, sys, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"build"; STAGING=OUT/"extension"

cands=[
Path("/usr/share/code/resources/app/extensions/theme-seti/icons"),
Path("/usr/lib/code/resources/app/extensions/theme-seti/icons"),
Path("/opt/visual-studio-code/resources/app/extensions/theme-seti/icons"),
Path("/snap/code/current/usr/share/code/resources/app/extensions/theme-seti/icons")]
for cmd in ("code","code-insiders","codium"):
    exe=shutil.which(cmd)
    if exe:
        real=Path(os.path.realpath(exe))
        for parent in [real.parent,*real.parents]:
            cands += [parent/"resources/app/extensions/theme-seti/icons",
                      parent/"share/code/resources/app/extensions/theme-seti/icons"]

seti=None
for p in cands:
    try: p=p.resolve()
    except OSError: continue
    if (p/"vs-seti-icon-theme.json").is_file() and (p/"seti.woff").is_file():
        seti=p; break
if seti is None:
    print("ERROR: VS Code Seti theme not found.",file=sys.stderr); sys.exit(2)

if STAGING.exists(): shutil.rmtree(STAGING)
(STAGING/"icons").mkdir(parents=True); OUT.mkdir(exist_ok=True)
shutil.copy2(ROOT/"package.json",STAGING/"package.json")
shutil.copy2(ROOT/"icons/resy.png",STAGING/"icons/resy.png")
shutil.copy2(seti/"seti.woff",STAGING/"icons/seti.woff")

theme=json.loads((seti/"vs-seti-icon-theme.json").read_text(encoding="utf-8"))
theme.setdefault("iconDefinitions",{})["_resy"]={"iconPath":"./resy.png"}
theme.setdefault("fileExtensions",{})["resy"]="_resy"
for mode in ("light","highContrast"):
    theme.setdefault(mode,{}).setdefault("fileExtensions",{})["resy"]="_resy"
(STAGING/"icons/resiris-seti-icon-theme.json").write_text(json.dumps(theme,indent=2)+"\n",encoding="utf-8")

manifest="\n".join([
'<?xml version="1.0" encoding="utf-8"?>',
'<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">',
'  <Metadata>',
'    <Identity Id="resiris-seti-file-icons" Version="0.1.0" Language="en" Publisher="resiris" />',
'    <DisplayName>Resiris Seti File Icons</DisplayName>',
'    <Description xml:space="preserve">Seti File Icon Theme with a custom RESY icon for .resy files.</Description>',
'    <Categories>Themes</Categories>',
'  </Metadata>',
'  <Installation><InstallationTarget Id="Microsoft.VisualStudio.Code" Version="[1.80.0,2.0.0)" /></Installation>',
'  <Dependencies />',
'  <Assets>',
'    <Asset Type="Microsoft.VisualStudio.Services.VSIXManifest" Path="extension.vsixmanifest" />',
'    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" />',
'  </Assets>',
'</PackageManifest>'
])
vsix=OUT/"resiris-seti-file-icons-0.1.0.vsix"
with zipfile.ZipFile(vsix,"w",zipfile.ZIP_DEFLATED) as z:
    z.writestr("extension.vsixmanifest",manifest)
    for p in [STAGING/"package.json",STAGING/"icons/resy.png",STAGING/"icons/seti.woff",STAGING/"icons/resiris-seti-icon-theme.json"]:
        z.write(p,"extension/"+str(p.relative_to(STAGING)))
print(vsix)
