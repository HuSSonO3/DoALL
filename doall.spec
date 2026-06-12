# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('text.tcss', '.'),
        # ── Tab modules (tcss files included) ──
        ('tabs/base_converter', 'tabs/base_converter'),
        ('tabs/budget', 'tabs/budget'),
        ('tabs/changelog', 'tabs/changelog'),
        ('tabs/cheats', 'tabs/cheats'),
        ('tabs/clock', 'tabs/clock'),
        ('tabs/color_picker', 'tabs/color_picker'),
        ('tabs/countdown', 'tabs/countdown'),
        ('tabs/csv_viewer', 'tabs/csv_viewer'),
        ('tabs/games', 'tabs/games'),
        ('tabs/gitignore_builder', 'tabs/gitignore_builder'),
        ('tabs/habits', 'tabs/habits'),
        ('tabs/job_tracker', 'tabs/job_tracker'),
        ('tabs/json_tool', 'tabs/json_tool'),
        ('tabs/lorem', 'tabs/lorem'),
        ('tabs/money', 'tabs/money'),
        ('tabs/music', 'tabs/music'),
        ('tabs/noting', 'tabs/noting'),
        ('tabs/port_checker', 'tabs/port_checker'),
        ('tabs/qr_extractor', 'tabs/qr_extractor'),
        ('tabs/random_picker', 'tabs/random_picker'),
        ('tabs/recipes', 'tabs/recipes'),
        ('tabs/regex_tester', 'tabs/regex_tester'),
        ('tabs/subnet_calc', 'tabs/subnet_calc'),
        ('tabs/timezones', 'tabs/timezones'),
        ('tabs/todos', 'tabs/todos'),
        ('tabs/typing_test', 'tabs/typing_test'),
        ('tabs/unit_converter', 'tabs/unit_converter'),
        ('tabs/word_counter', 'tabs/word_counter'),
        # ── File-holder data dirs ──
        ('file_holders', 'file_holders'),
    ] + collect_data_files('tree_sitter') + collect_data_files('tree_sitter_markdown')
      + collect_data_files('mf2py')
      + collect_data_files('extruct')
      + collect_data_files('recipe_scrapers'),
    hiddenimports=[
        'tzdata',
    ] + collect_submodules('textual')
      + collect_submodules('tree_sitter')
      + collect_submodules('tree_sitter_markdown')
      + collect_submodules('tree_sitter_python')
      + collect_submodules('tree_sitter_json')
      + collect_submodules('tree_sitter_bash')
      + collect_submodules('tree_sitter_css')
      + collect_submodules('tree_sitter_html')
      + collect_submodules('tree_sitter_xml')
      + collect_submodules('tree_sitter_yaml')
      + collect_submodules('tree_sitter_sql')
      + collect_submodules('tree_sitter_toml')
      + collect_submodules('tree_sitter_regex')
      + collect_submodules('tree_sitter_java')
      + collect_submodules('tree_sitter_javascript')
      + collect_submodules('tree_sitter_go')
      + collect_submodules('tree_sitter_rust')
      + collect_submodules('qrcode')
      + collect_submodules('PIL')
      + collect_submodules('recipe_scrapers')
      + collect_submodules('extruct')
      + collect_submodules('mf2py'),
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
