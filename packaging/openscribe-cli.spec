from pathlib import Path

root = Path(SPEC).resolve().parent.parent

analysis = Analysis(
    [str(root / "src" / "openscribe" / "__main__.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=[(str(root / "src" / "openscribe" / "word_addin"), "openscribe/word_addin")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PySide6", "openscribe.desktop", "anthropic", "google.genai", "mistralai", "openai"],
    noarchive=False,
    optimize=0,
)
archive = PYZ(analysis.pure)

executable = EXE(
    archive,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="openscribe-cli",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
