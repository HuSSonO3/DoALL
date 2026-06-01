# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('text.tcss', '.'),
        ('tabs/noting', 'tabs/noting'),
        ('tabs/clock', 'tabs/clock'),
        ('tabs/music', 'tabs/music'),
        ('tabs/games', 'tabs/games'),
        ('tabs/todos', 'tabs/todos'),
        ('tabs/cheats', 'tabs/cheats'),
        ('tabs/timezones', 'tabs/timezones'),
        ('tabs/json_tool', 'tabs/json_tool'),
        ('tabs/color_picker', 'tabs/color_picker'),
        ('tabs/base_converter', 'tabs/base_converter'),
        ('tabs/lorem', 'tabs/lorem'),
        ('file_holders', 'file_holders'),
    ] + collect_data_files('tree_sitter') + collect_data_files('tree_sitter_markdown'),
    hiddenimports=[
        'tzdata',
    ] + collect_submodules('textual') + collect_submodules('tree_sitter') + collect_submodules('tree_sitter_markdown') + collect_submodules('tree_sitter_python') + collect_submodules('tree_sitter_json') + collect_submodules('tree_sitter_bash') + collect_submodules('tree_sitter_css') + collect_submodules('tree_sitter_html') + collect_submodules('tree_sitter_xml') + collect_submodules('tree_sitter_yaml') + collect_submodules('tree_sitter_sql') + collect_submodules('tree_sitter_toml') + collect_submodules('tree_sitter_regex') + collect_submodules('tree_sitter_java') + collect_submodules('tree_sitter_javascript') + collect_submodules('tree_sitter_go') + collect_submodules('tree_sitter_rust'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='doall',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
