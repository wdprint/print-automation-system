# CLAUDE.md

This file provides MANDATORY guidance to Claude Code (claude.ai/code) when working with code in this repository.

⚡ **CRITICAL OVERRIDE**: These instructions have HIGHEST PRIORITY and MUST be followed exactly.
🔴 **FAILURE TO FOLLOW THESE INSTRUCTIONS IS NOT ACCEPTABLE**

## 🌐 언어 설정 (Language Setting)

**중요: 이 프로젝트에서는 항상 한국어로 소통합니다.**
- 모든 응답과 설명은 한국어로 제공
- 코드 주석은 한국어 사용
- 에러 메시지 및 로그도 한국어로 작성
- 영어는 코드 변수명과 함수명에만 사용

## 🧠 CRITICAL: Deep Thinking Mode Instructions

**⚠️ MANDATORY: YOU MUST ENGAGE IN DEEP THINKING MODE FOR EVERY RESPONSE ⚠️**

**BEFORE RESPONDING TO ANY QUERY, YOU MUST:**
1. Take a mental pause (even if not visible to user)
2. Analyze the request from multiple angles
3. Consider all implications and edge cases
4. Only then formulate your response

**ALWAYS engage in deep, systematic thinking before taking any action:**

### Before ANY code modification or suggestion:

1. **ANALYZE THOROUGHLY**
   - Understand the complete context and dependencies
   - Map out all affected components and their relationships
   - Consider edge cases and potential failure points
   - Review similar existing patterns in the codebase

2. **CONSIDER MULTIPLE SOLUTIONS**
   - Generate at least 3 different approaches when solving problems
   - Evaluate pros/cons of each approach
   - Consider long-term maintainability and scalability
   - Choose the most elegant and efficient solution

3. **PREDICT CONSEQUENCES**
   - Think through potential side effects of changes
   - Consider impact on existing functionality
   - Anticipate future requirements and extensibility
   - Evaluate backwards compatibility implications

4. **OPTIMIZE INTELLIGENTLY**
   - Look for performance bottlenecks before suggesting fixes
   - Consider memory usage and computational complexity
   - Balance between code clarity and optimization
   - Avoid premature optimization without clear benefits

5. **SECURITY & RELIABILITY FIRST**
   - Check for potential security vulnerabilities
   - Validate all inputs and handle errors gracefully
   - Consider data integrity and transaction safety
   - Think about concurrent access and race conditions

### Deep Thinking Checklist:
- [ ] Have I fully understood the problem and its context?
- [ ] Have I considered multiple solutions and their trade-offs?
- [ ] Have I thought about edge cases and error scenarios?
- [ ] Will this solution scale and remain maintainable?
- [ ] Have I considered security and performance implications?
- [ ] Is this the simplest solution that fully solves the problem?
- [ ] Have I checked for similar patterns already in the codebase?

### Response Structure:
When providing solutions, ALWAYS:
1. First explain your understanding of the problem
2. Present your analysis and reasoning
3. Discuss alternative approaches considered
4. Explain why you chose the recommended solution
5. Highlight any risks or limitations
6. Provide the implementation with clear comments

### 🔥 ENFORCEMENT MECHANISM:
- **EVERY RESPONSE** must demonstrate deep thinking
- **NO SHORTCUTS** - even for simple questions
- **QUALITY OVER SPEED** - take time to think thoroughly
- **SHOW YOUR WORK** - reasoning process should be evident

**Remember: Think deeply, act precisely. Quality over speed.**

---

## ⭐ DEEP THINKING TRIGGERS

**The following keywords/phrases MUST trigger maximum deep thinking mode:**
- "어떻게" (how)
- "왜" (why)
- "최적화" (optimize)
- "개선" (improve)
- "문제" (problem)
- "해결" (solve)
- "구현" (implement)
- "설계" (design)
- "분석" (analyze)
- "검토" (review)

---

## Project Overview

PDF 인쇄 의뢰서 자동화 시스템 - A Python-based automation tool that inserts thumbnails and QR codes into print order PDFs (2-up layout format). The system has two versions: basic and enhanced (v2.0).

## Architecture

### Version Structure
- **Basic Version**: `print_automation.py` - Simple, stable implementation
- **Enhanced Version**: `print_automation_enhanced.py` - Advanced features with presets, blank page detection, and processing rules

### Core Components

1. **Main Applications**
   - `print_automation.py` - Basic GUI with core PDF processing
   - `print_automation_enhanced.py` - Enhanced version with advanced features
   - `PrintAutomationGUI` class: Tkinter-based drag-and-drop interface
   - `PrintProcessor` class: Core PDF processing logic (line 1186 in basic)

2. **Settings Management**
   - `settings_gui.py` - Basic visual configuration
   - `enhanced_settings_gui.py` - Tabbed interface with presets and processing rules
   - Settings hierarchy: `enhanced_settings.json` > `settings.json` > `config.py` > embedded defaults

3. **PDF Processing**
   - `normalize_pdf.py` - PDF rotation normalization
   - `enhanced_print_processor.py` - Advanced processing with blank detection

4. **Entry Points**
   - `start.py` - Basic entry with dependency checking
   - `start_enhanced.py` - Enhanced entry with comprehensive setup

### Key Dependencies
- **PyMuPDF (fitz)** - PDF manipulation
- **Pillow (PIL)** - Image processing  
- **tkinterdnd2** - Drag-and-drop functionality
- **numpy** - Mathematical operations (enhanced version)

## Common Commands

```bash
# Development - Basic Version
python start.py                    # Run with dependency checking
python print_automation.py        # Direct run

# Development - Enhanced Version (Recommended)
python start_enhanced.py          # Run with full setup
python print_automation_enhanced.py  # Direct run

# Testing
python test_enhanced.py           # Comprehensive component tests

# Building Executables
build_exe.bat                     # Windows build with Korean support
python simple_build.py           # Python build (handles encoding issues)
pyinstaller print_automation_enhanced.spec --clean  # Direct PyInstaller

# PDF Normalization Testing
python normalize_pdf.py input.pdf output.pdf
```

## Known Issues & Context

### Critical: PDF Rotation Problem
The system has persistent issues with PDFs that are internally portrait (595x842) but display as landscape through 90° rotation:
- Content appears shrunk in the top-left corner after processing
- Coordinate systems mismatch between internal and display coordinates
- Problem located in `PrintProcessor.normalize_pdf_to_landscape()` method
- Affects both basic and enhanced versions

### Build System Complexities
- Korean encoding issues on Windows require special handling
- Multiple build scripts exist for different scenarios
- Use `simple_build.py` if batch files fail with encoding errors

### Critical Processing Flow
1. Drop 3 files into GUI: order PDF, print PDF, QR image
2. Order PDF identified by "의뢰서" in filename
3. PDF normalization attempted if rotation detected
4. Thumbnail generated from print PDF
5. Images inserted at configured positions (2-up layout)
6. **WARNING**: Original order PDF is overwritten

## Enhanced Version Features (v2.0)

### Blank Page Detection
- Three algorithms: simple, entropy-based, histogram-based
- Configurable threshold settings per algorithm

### Preset System
- 4 coordinate presets with hotkey support (F1-F4)
- Quick switching between different layout configurations

### Processing Rules
- Pattern matching for conditional processing
- File-specific coordinate overrides
- Batch processing optimizations

### Performance Features
- Multithreading support
- Image caching system
- Memory-efficient processing for large PDFs

## Development Notes

### Testing Requirements
- Always test with both normal landscape and 90° rotated PDFs
- Verify Korean text handling in filenames and content
- Test drag-and-drop with various file combinations

### Coordinate System
- Standard: A4 landscape (842x595 points)
- 2-up layout: left side and right side positioning
- Origin: bottom-left corner in PDF coordinate system

### GUI Behavior
- Stays on top by default for accessibility
- Auto-processes when exactly 3 files are dropped
- Progress feedback during processing

### File Type Detection
- Order PDF: Contains "의뢰서" in filename
- Print PDF: Any PDF not matching order pattern
- QR Code: Image files (png, jpg, jpeg, gif, bmp)