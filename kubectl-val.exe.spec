# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['guardctl/cli.py'],
             pathex=['/home/vasily/environment-name/artemm/artem/kubectl-chai'],
             binaries=[],
             datas=[('guardctl/model/kinds', 'guardctl/model/kinds'), ('.tox/.package/lib/python3.7/site-packages/yaspin/data', 'yaspin/data')],
             hiddenimports=['guardctl.model.kinds'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='kubectl-val.exe',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
