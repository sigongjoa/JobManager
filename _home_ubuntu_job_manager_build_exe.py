import sys
import os
from PyInstaller.__main__ import run

# 현재 디렉토리 설정
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# PyInstaller 옵션 설정
options = [
    '--name=JobManager',
    '--onefile',
    '--windowed',
    '--add-data=static:static',
    '--add-data=uploads:uploads',
    '--hidden-import=uvicorn.logging',
    '--hidden-import=uvicorn.lifespan',
    '--hidden-import=uvicorn.protocols',
    '--hidden-import=uvicorn.protocols.http',
    '--hidden-import=uvicorn.protocols.http.auto',
    '--hidden-import=uvicorn.protocols.websockets',
    '--hidden-import=uvicorn.protocols.websockets.auto',
    'main.py'
]

# PyInstaller 실행
run(options)
