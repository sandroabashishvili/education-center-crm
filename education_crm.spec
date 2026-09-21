# Build from a local Windows drive: python -m PyInstaller education_crm.spec
from pathlib import Path
root = Path(SPECPATH)
data = []
for directory in ('templates', 'static'):
    base = root / 'app' / directory
    for file in base.rglob('*'):
        if file.is_file() and 'uploads' not in file.relative_to(base).parts:
            data.append((str(file),str(file.parent.relative_to(root))))
a = Analysis([str(root / 'desktop_entry.py')], pathex=[str(root),str(root / 'app')], binaries=[], datas=data,
             hiddenimports=['app_factory','tools.desktop_smoke'], hookspath=[], hooksconfig={}, runtime_hooks=[],
             excludes=['pytest','unittest','tkinter','PyQt5','PyQt6','PySide2','PySide6'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz,a.scripts,[],exclude_binaries=True,name='EducationCenterCRM',debug=False,bootloader_ignore_signals=False,
          strip=False,upx=False,console=False)
coll = COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='EducationCenterCRM')
