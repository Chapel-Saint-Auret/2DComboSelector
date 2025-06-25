# -*- mode: python ; coding: utf-8 -*-
def collect_data_files(src_folder, dest_folder):
    import os, glob
    file_list = []
    for f in glob.glob(os.path.join(src_folder, '**', '*.*'), recursive=True):
        if os.path.isfile(f):
            file_list.append((f, dest_folder))
    return file_list

icon_files = collect_data_files('src/combo_selector/resources/icons', 'resources/icons')
colormap_files = collect_data_files('src/combo_selector/resources/colormaps', 'resources/colormaps')

datas = icon_files + colormap_files
for src, dst in datas:
    print(f"Will copy {src} -> {dst}")

print("ICON FILES:", icon_files)
print("COLORMAP FILES:", colormap_files)

a = Analysis(
    ['src/combo_selector/main.py'],
    pathex=['src/combo_selector'],
    binaries=[],
    datas = datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='combo_selector',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='combo_selector'
)