how to build:
1. get pyinstaller
2. run `pyinstaller src/main.py --onefile --noconsole` on root dir
3. open up main.spec: you should see something like
```
a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
```
change `datas=[],` to `datas=[('src/extracted_data.json', '.')],`
4. run `pyinstaller main.spec`

yeah thats all hf
