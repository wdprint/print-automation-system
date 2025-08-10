; ============================================
;     PDF 인쇄 의뢰서 자동화 시스템 v2
;     AutoHotkey v2.0 - 프리셋 단축키 버전
; ============================================

#Requires AutoHotkey v2.0
#SingleInstance Force
SendMode("Input")
SetWorkingDir(A_ScriptDir)

; ============================================
;     전역 변수
; ============================================
global ExePath := A_ScriptDir . "\print_automation.exe"
global CurrentPreset := 1
global ShowNotifications := true
global PlaySounds := true
global ProcessRunning := false

; ============================================
;     초기화 및 검증
; ============================================

; EXE 파일 존재 확인
if (!FileExist(ExePath)) {
    MsgBox("print_automation.exe 파일을 찾을 수 없습니다.`n`n경로: " . ExePath, "오류", "Icon!")
    ExitApp()
}

; 시작 알림
ShowNotification("PDF 자동화 시스템이 실행되었습니다`nAlt+H로 도움말을 확인하세요", 3000)

; ============================================
;     메인 단축키 정의
; ============================================

; 프리셋 처리 단축키
!q::ProcessWithPreset(1)  ; Alt+Q - 프리셋 1
!w::ProcessWithPreset(2)  ; Alt+W - 프리셋 2
!e::ProcessWithPreset(3)  ; Alt+E - 프리셋 3
!r::ProcessWithPreset(4)  ; Alt+R - 프리셋 4

; 프로그램 제어 단축키
!s::OpenSettings()         ; Alt+S - 설정 창 열기
!g::OpenGUI()             ; Alt+G - GUI 모드 실행
!h::ShowHelp()            ; Alt+H - 도움말
!+r::ReloadScript()       ; Alt+Shift+R - 스크립트 재시작
!+q::ExitScript()         ; Alt+Shift+Q - 스크립트 종료

; ============================================
;     핵심 처리 함수
; ============================================

/**
 * 선택된 프리셋으로 파일 처리
 * @param {Number} presetNum - 프리셋 번호 (1-4)
 */
ProcessWithPreset(presetNum) {
    global ProcessRunning, CurrentPreset
    
    ; 처리 중 체크
    if (ProcessRunning) {
        ShowNotification("이미 처리 중입니다. 잠시 후 다시 시도하세요.", 2000)
        return
    }
    
    ; 현재 프리셋 업데이트
    CurrentPreset := presetNum
    
    ; 선택된 파일 가져오기
    files := GetSelectedFiles()
    
    if (files = "") {
        ShowNotification("선택된 파일이 없습니다.`n파일을 선택한 후 다시 시도하세요.", 2000)
        return
    }
    
    ; 파일 분류
    classified := ClassifyFiles(files)
    
    ; 의뢰서 필수 체크
    if (classified["orderPdf"] = "") {
        ShowNotification("의뢰서 PDF를 찾을 수 없습니다.`n파일명에 '의뢰서'가 포함된 PDF가 필요합니다.", 3000)
        return
    }
    
    ; 썸네일 또는 QR 체크
    if (classified["printPdfs"].Length = 0 && classified["qrImage"] = "") {
        ShowNotification("썸네일 PDF 또는 QR 이미지가 필요합니다.", 3000)
        return
    }
    
    ; 처리 시작
    ProcessRunning := true
    ShowNotification("프리셋 " . presetNum . "로 처리를 시작합니다...", 1500)
    
    ; EXE 실행
    ExecuteProcess(classified["orderPdf"], classified["printPdfs"], classified["qrImage"], presetNum)
    
    ProcessRunning := false
}

/**
 * 선택된 파일 가져오기
 * @return {String} 선택된 파일 경로들 (줄바꿈으로 구분)
 */
GetSelectedFiles() {
    ; 활성 창 확인
    activeClass := WinGetClass("A")
    
    ; Windows 탐색기 확인
    if (activeClass = "CabinetWClass" || activeClass = "ExploreWClass") {
        try {
            files := ""
            ; COM 객체로 탐색기에서 선택된 파일 가져오기
            for window in ComObject("Shell.Application").Windows {
                if (window.hwnd = WinExist("A")) {
                    for item in window.Document.SelectedItems {
                        files .= item.Path . "`n"
                    }
                    break
                }
            }
            return RTrim(files, "`n")
        } catch {
            ; COM 실패 시 클립보드 방법 사용
        }
    }
    
    ; 클립보드 방법 (폴백)
    oldClip := ClipboardAll()
    A_Clipboard := ""
    
    Send("^c")  ; Ctrl+C
    
    if (!ClipWait(1)) {
        A_Clipboard := oldClip
        return ""
    }
    
    files := ""
    Loop Parse, A_Clipboard, "`n", "`r" {
        if (FileExist(A_LoopField)) {
            files .= A_LoopField . "`n"
        }
    }
    
    A_Clipboard := oldClip
    return RTrim(files, "`n")
}

/**
 * 파일 분류
 * @param {String} files - 파일 경로들 (줄바꿈으로 구분)
 * @return {Map} 분류된 파일 정보
 */
ClassifyFiles(files) {
    result := Map()
    result["orderPdf"] := ""
    result["printPdfs"] := []
    result["qrImage"] := ""
    
    coverPdf := ""  ; 표지 PDF 임시 저장
    normalPdfs := []  ; 일반 PDF들
    
    ; 각 파일 분류
    Loop Parse, files, "`n", "`r" {
        if (A_LoopField = "") {
            continue
        }
        
        filePath := Trim(A_LoopField)
        SplitPath(filePath, &fileName, , &ext)
        ext := StrLower(ext)
        
        ; PDF 파일
        if (ext = "pdf") {
            ; 의뢰서 체크
            if (InStr(fileName, "의뢰서")) {
                result["orderPdf"] := filePath
            }
            ; 표지 체크
            else if (InStr(fileName, "표지") || InStr(fileName, "cover")) {
                coverPdf := filePath
            }
            ; 일반 PDF
            else {
                normalPdfs.Push(filePath)
            }
        }
        ; 이미지 파일 (QR)
        else if (ext = "png" || ext = "jpg" || ext = "jpeg") {
            ; QR 키워드가 있거나 첫 번째 이미지를 QR로 간주
            if (InStr(fileName, "QR") || InStr(fileName, "qr") || result["qrImage"] = "") {
                result["qrImage"] := filePath
            }
        }
    }
    
    ; 표지를 첫 번째로 배치
    if (coverPdf != "") {
        result["printPdfs"].Push(coverPdf)
    }
    
    ; 나머지 PDF 추가
    for pdf in normalPdfs {
        result["printPdfs"].Push(pdf)
    }
    
    return result
}

/**
 * EXE 프로그램 실행
 * @param {String} orderPdf - 의뢰서 PDF 경로
 * @param {Array} printPdfs - 썸네일 PDF 경로 배열
 * @param {String} qrImage - QR 이미지 경로
 * @param {Number} preset - 프리셋 번호
 */
ExecuteProcess(orderPdf, printPdfs, qrImage, preset) {
    global ExePath, PlaySounds
    
    ; 명령줄 구성
    cmd := '"' . ExePath . '" --cli --preset ' . preset
    
    ; 의뢰서 추가
    cmd .= ' "' . orderPdf . '"'
    
    ; 썸네일 PDF들 추가
    for pdf in printPdfs {
        cmd .= ' "' . pdf . '"'
    }
    
    ; QR 이미지 추가
    if (qrImage != "") {
        cmd .= ' "' . qrImage . '"'
    }
    
    ; 실행
    try {
        exitCode := RunWait(cmd, , "Hide")
        
        if (exitCode = 0) {
            ; 성공
            if (PlaySounds) {
                SoundBeep(800, 200)
            }
            ShowNotification("✅ 처리가 완료되었습니다!", 2000)
        } else {
            ; 실패
            if (PlaySounds) {
                SoundBeep(300, 500)
            }
            ShowNotification("❌ 처리 실패 (오류 코드: " . exitCode . ")", 3000)
        }
    } catch Error as err {
        ShowNotification("실행 오류: " . err.Message, 3000)
    }
}

; ============================================
;     프로그램 제어 함수
; ============================================

/**
 * 설정 창 열기
 */
OpenSettings() {
    global ExePath
    
    try {
        Run('"' . ExePath . '" --settings')
        ShowNotification("설정 창을 여는 중...", 1000)
    } catch Error as err {
        ShowNotification("설정 창 열기 실패: " . err.Message, 2000)
    }
}

/**
 * GUI 모드 실행
 */
OpenGUI() {
    global ExePath
    
    try {
        Run('"' . ExePath . '"')
        ShowNotification("GUI 모드를 실행 중...", 1000)
    } catch Error as err {
        ShowNotification("GUI 실행 실패: " . err.Message, 2000)
    }
}

/**
 * 도움말 표시
 */
ShowHelp() {
    helpText := "
(
PDF 인쇄 의뢰서 자동화 시스템 v2

📌 사용 방법:
1. 파일 탐색기에서 파일들을 선택하세요
   - 의뢰서 PDF (필수)
   - 표지/내지 PDF (선택)
   - QR 이미지 (선택)

2. 프리셋 단축키를 누르세요
   Alt+Q : 프리셋 1로 처리
   Alt+W : 프리셋 2로 처리
   Alt+E : 프리셋 3로 처리
   Alt+R : 프리셋 4로 처리

📂 파일 이름 규칙:
• 의뢰서: 파일명에 '의뢰서' 포함
• 표지: 파일명에 '표지' 포함
• QR: 파일명에 'QR' 포함 또는 이미지 파일

⚙️ 프로그램 제어:
Alt+S : 설정 창 열기
Alt+G : GUI 모드 실행
Alt+H : 이 도움말 보기
Alt+Shift+R : 스크립트 재시작
Alt+Shift+Q : 스크립트 종료

💡 팁:
• 표지 PDF는 자동으로 오른쪽 50%만 사용됩니다
• 여러 PDF를 선택하면 순서대로 처리됩니다
• 각 프리셋은 독립적인 좌표 설정을 가집니다
)"
    
    MsgBox(helpText, "PDF 자동화 도움말", "Iconi")
}

/**
 * 스크립트 재시작
 */
ReloadScript() {
    ShowNotification("스크립트를 재시작합니다...", 1000)
    Sleep(1000)
    Reload()
}

/**
 * 스크립트 종료
 */
ExitScript() {
    result := MsgBox("PDF 자동화 시스템을 종료하시겠습니까?", "종료 확인", "YesNo Icon?")
    if (result = "Yes") {
        ShowNotification("프로그램을 종료합니다...", 1000)
        Sleep(1000)
        ExitApp()
    }
}

; ============================================
;     유틸리티 함수
; ============================================

/**
 * 알림 표시
 * @param {String} message - 표시할 메시지
 * @param {Number} duration - 표시 시간 (밀리초)
 */
ShowNotification(message, duration := 2000) {
    global ShowNotifications
    
    if (!ShowNotifications) {
        return
    }
    
    ToolTip(message)
    SetTimer(() => ToolTip(), -duration)
}

/**
 * 파일명만 추출 (경로 제외)
 * @param {String} path - 파일 전체 경로
 * @return {String} 파일명
 */
GetFileName(path) {
    SplitPath(path, &fileName)
    return fileName
}

; ============================================
;     트레이 메뉴 설정
; ============================================

; 트레이 아이콘 툴팁
A_IconTip := "PDF 자동화 시스템 v2`nAlt+H로 도움말"

; 트레이 메뉴 구성
A_TrayMenu.Delete()  ; 기본 메뉴 제거
A_TrayMenu.Add("설정 열기 (Alt+S)", (*) => OpenSettings())
A_TrayMenu.Add("GUI 모드 (Alt+G)", (*) => OpenGUI())
A_TrayMenu.Add()  ; 구분선
A_TrayMenu.Add("도움말 (Alt+H)", (*) => ShowHelp())
A_TrayMenu.Add()  ; 구분선
A_TrayMenu.Add("재시작", (*) => ReloadScript())
A_TrayMenu.Add("종료", (*) => ExitScript())

; ============================================
;     설정 파일 (선택사항)
; ============================================

; config.ini 파일이 있으면 설정 로드
LoadConfig() {
    global ShowNotifications, PlaySounds
    
    configFile := A_ScriptDir . "\config.ini"
    
    if (FileExist(configFile)) {
        try {
            ShowNotifications := IniRead(configFile, "General", "ShowNotifications", "true") = "true"
            PlaySounds := IniRead(configFile, "General", "PlaySounds", "true") = "true"
        } catch {
            ; 설정 파일 읽기 실패 시 기본값 사용
        }
    }
}

; 설정 로드
LoadConfig()

; ============================================
;     종료 시 정리
; ============================================

OnExit(ExitFunc)

ExitFunc(ExitReason, ExitCode) {
    ToolTip()  ; 툴팁 제거
    return 0
}