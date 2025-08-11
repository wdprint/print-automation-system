#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple EXE Builder for PDF Automation System
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build():
    """Build single EXE file"""
    
    print("=" * 50)
    print("PDF Automation System - EXE Builder")
    print("=" * 50)
    
    # Clean old build
    for dir in ['build', 'dist', '__pycache__']:
        if os.path.exists(dir):
            print(f"Cleaning {dir}...")
            shutil.rmtree(dir)
    
    # Remove spec files
    for spec in Path('.').glob('*.spec'):
        spec.unlink()
    
    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--name=print_automation',
        '--onefile',
        '--windowed',
        '--noconfirm',
        '--clean',
        '--add-data=data;data',
        '--hidden-import=tkinter',
        '--hidden-import=tkinterdnd2', 
        '--hidden-import=PIL',
        '--hidden-import=fitz',
        '--hidden-import=PyPDF2',
        'main.py'
    ]
    
    print("\nBuilding EXE... (this may take 5-10 minutes)")
    print("Command:", ' '.join(cmd))
    print()
    
    # Run PyInstaller
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("\n[ERROR] Build failed!")
        return False
    
    # Check if EXE was created
    exe_path = Path('dist/print_automation.exe')
    if not exe_path.exists():
        print("\n[ERROR] EXE file not created!")
        return False
    
    # Get file size
    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"\n[SUCCESS] EXE created: {exe_path}")
    print(f"File size: {size_mb:.2f} MB")
    
    # Copy additional files
    print("\nCopying additional files...")
    files_to_copy = [
        ('pdf_automation_v2.ahk', 'dist/pdf_automation_v2.ahk'),
        ('config.ini', 'dist/config.ini'),
        ('data/settings.json', 'dist/settings.json'),
        ('data/presets.json', 'dist/presets.json'),
    ]
    
    for src, dst in files_to_copy:
        if Path(src).exists():
            shutil.copy2(src, dst)
            print(f"  Copied: {src}")
    
    print("\n" + "=" * 50)
    print("BUILD COMPLETE!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Test print_automation.exe")
    print("2. Compress dist folder")
    print("3. Distribute to users")
    
    return True

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("Python 3.8+ required")
        sys.exit(1)
    
    # Check PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
    
    # Build
    success = build()
    if not success:
        sys.exit(1)