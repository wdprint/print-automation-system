# PyInstaller 초보자를 위한 상세 가이드

## 1. PyInstaller가 하는 일

PyInstaller는 Python 프로그램을 **Python이 없는 컴퓨터에서도 실행 가능한 EXE 파일**로 만들어줍니다.

### 빌드 과정:
```
Python 코드 → 분석 → 필요한 모든 것 수집 → EXE 파일 생성
```

## 2. build 폴더 vs dist 폴더

### **build 폴더** (무시해도 됨)
- PyInstaller가 작업하는 **임시 공간**
- 분석 결과, 중간 파일들이 저장됨
- **배포할 때는 필요 없음!**

### **dist 폴더** (이것만 사용!)
- **최종 결과물**이 들어있는 폴더
- 여기 있는 EXE 파일이 실제 배포할 파일
- **이 폴더 내용만 사용자에게 전달하면 됨**

## 3. 다른 모듈 포함하기

### 문제: config.py와 settings_gui.py도 필요한데?

기본 명령어로는 메인 파일만 포함됩니다. 다른 파일들을 포함하려면 따로 지정해야 합니다.

### 해결 방법 1: spec 파일 사용 (권장)

```python
# print_automation_complete.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 추가 파일들 지정
added_files = [
    ('settings_gui.py', '.'),      # settings_gui.py를 같은 폴더에
    ('config.py', '.'),            # config.py를 같은 폴더에
    # 아이콘 파일이 있다면
    # ('icon.ico', '.'),
]

a = Analysis(
    ['print_automation.py'],
    pathex=[],
    binaries=[],
    datas=added_files,             # 여기에 추가 파일 지정
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='print_automation',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                 # 콘솔 창 숨김
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

빌드 명령:
```bash
pyinstaller print_automation_complete.spec
```

### 해결 방법 2: 코드에 직접 포함

print_automation.py를 수정하여 settings_gui.py 내용을 직접 포함시킬 수 있습니다. 하지만 파일이 길어져서 관리가 어려워집니다.

## 4. 단계별 빌드 과정

### Step 1: 필요한 패키지 설치
```bash
pip install pyinstaller
pip install PyMuPDF Pillow tkinterdnd2
```

### Step 2: spec 파일 생성
위의 spec 파일을 `print_automation_complete.spec`로 저장

### Step 3: 빌드 실행
```bash
pyinstaller print_automation_complete.spec
```

### Step 4: 결과 확인
```
프로젝트 폴더/
├── build/              # ← 무시 (임시 파일)
├── dist/               # ← 중요! 
│   └── print_automation.exe   # ← 배포할 파일
├── print_automation.py
├── settings_gui.py
└── config.py
```

## 5. 최종 배포 준비

### 배포 폴더 만들기:
```
PrintAutomation_배포판/
├── print_automation.exe     # dist 폴더에서 복사
├── PrintAutomation_v2.exe   # AutoHotkey 컴파일된 파일
├── PrintAutomation.ini      # 설정 파일
└── 사용설명서.txt
```

## 6. 자주 발생하는 문제

### Q: "Failed to execute script" 오류
**A:** 필요한 파일이 포함되지 않았을 때 발생
- spec 파일의 `datas` 부분에 모든 필요 파일 추가
- `hiddenimports`에 누락된 모듈 추가

### Q: 파일 크기가 너무 커요
**A:** PyInstaller는 Python 인터프리터까지 포함하므로 크기가 큽니다
- UPX 압축 사용: `upx=True`
- 불필요한 모듈 제외: `excludes=['불필요한모듈']`

### Q: 바이러스로 오탐지됩니다
**A:** PyInstaller로 만든 EXE는 종종 오탐지됩니다
- Windows Defender 예외 추가 안내 필요
- 코드 서명 인증서 구매 (비용 발생)

## 7. 테스트 방법

1. **다른 폴더에서 테스트**
   - dist 폴더의 EXE를 다른 곳으로 복사
   - 실행해보기

2. **Python 없는 컴퓨터에서 테스트**
   - 가능하면 Python이 설치되지 않은 컴퓨터에서 테스트

3. **필수 파일 확인**
   - settings.json이 자동 생성되는지
   - GUI가 정상적으로 열리는지

## 8. AutoHotkey 컴파일

AutoHotkey 스크립트도 EXE로 만들 수 있습니다:

1. **Ahk2Exe 다운로드**
   - https://www.autohotkey.com/download/ahk2exe.zip

2. **컴파일**
   - Ahk2Exe.exe 실행
   - Source: PrintAutomation_v2.ahk
   - Destination: PrintAutomation_v2.exe
   - Compile 클릭

이제 Python도, AutoHotkey도 없는 사용자가 바로 사용할 수 있습니다!