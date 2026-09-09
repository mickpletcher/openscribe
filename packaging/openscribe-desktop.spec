from pathlib import Path

root = Path(SPEC).resolve().parent.parent

analysis = Analysis(
    [str(root / "src" / "openscribe" / "desktop_launcher.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=[(str(root / "src" / "openscribe" / "word_addin"), "openscribe/word_addin")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["anthropic", "google.genai", "mistralai", "openai"],
    noarchive=False,
    optimize=0,
)

# Qt uses the Windows ICU API. A foreign ICU directory on PATH can otherwise be frozen beside the app and shadow it.
analysis.binaries = [
    entry
    for entry in analysis.binaries
    if Path(entry[0]).name.casefold() != "icuuc.dll"
    and not Path(entry[0]).name.casefold().startswith("icudt")
]
archive = PYZ(analysis.pure)

executable = EXE(
    archive,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="OpenScribe",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

bundle = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="OpenScribe",
)
