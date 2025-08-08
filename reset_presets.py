#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""프리셋 초기화 스크립트 - 문제 해결용"""

import os
import json
from pathlib import Path
from datetime import datetime

# 프리셋 파일 경로
PRESETS_FILE = Path("data/presets.json")

def reset_presets():
    """프리셋을 기본값으로 초기화"""
    print("=" * 60)
    print("프리셋 초기화 스크립트")
    print("=" * 60)
    
    # 기본 좌표 설정
    DEFAULT_COORDINATES = {
        "page_size": {"width": 842, "height": 595},
        "thumbnail_boxes": [
            {
                "id": "thumb_1",
                "name": "썸네일 1",
                "x": 230,
                "y": 234,
                "width": 160,
                "height": 250,
                "rotation": 0,
                "opacity": 1.0
            },
            {
                "id": "thumb_2", 
                "name": "썸네일 2",
                "x": 658,
                "y": 228,
                "width": 160,
                "height": 250,
                "rotation": 0,
                "opacity": 1.0
            }
        ],
        "qr_boxes": [
            {
                "id": "qr_1",
                "name": "QR 왼쪽",
                "x": 315,
                "y": 500,
                "size": 70,
                "rotation": 0
            },
            {
                "id": "qr_2",
                "name": "QR 오른쪽",
                "x": 730,
                "y": 500,
                "size": 70,
                "rotation": 0
            }
        ]
    }
    
    # 새로운 프리셋 구조
    NEW_PRESETS = {
        "1": {
            "name": "기본",
            "description": "표준 설정",
            "hotkey": "F1",
            "settings": {
                "coordinates": DEFAULT_COORDINATES,
                "blank_detection": {
                    "enabled": False,
                    "threshold": 95,
                    "algorithm": "simple"
                },
                "thumbnail": {
                    "grayscale": False,
                    "contrast": 1.0,
                    "sharpness": 1.0,
                    "brightness": 1.0
                },
                "performance": {
                    "multithreading": True,
                    "max_workers": 4,
                    "cache_enabled": True,
                    "cache_size_mb": 100
                }
            },
            "usage_count": 0,
            "last_used": None,
            "created_at": datetime.now().isoformat()
        },
        "2": {
            "name": "프리셋 2",
            "description": "사용자 정의 2",
            "hotkey": "F2",
            "settings": {
                "coordinates": DEFAULT_COORDINATES,
                "blank_detection": {
                    "enabled": False,
                    "threshold": 95,
                    "algorithm": "simple"
                },
                "thumbnail": {
                    "grayscale": False,
                    "contrast": 1.0,
                    "sharpness": 1.0,
                    "brightness": 1.0
                },
                "performance": {
                    "multithreading": True,
                    "max_workers": 4,
                    "cache_enabled": True,
                    "cache_size_mb": 100
                }
            },
            "usage_count": 0,
            "last_used": None,
            "created_at": datetime.now().isoformat()
        },
        "3": {
            "name": "프리셋 3",
            "description": "사용자 정의 3",
            "hotkey": "F3",
            "settings": {
                "coordinates": DEFAULT_COORDINATES,
                "blank_detection": {
                    "enabled": False,
                    "threshold": 95,
                    "algorithm": "simple"
                },
                "thumbnail": {
                    "grayscale": False,
                    "contrast": 1.0,
                    "sharpness": 1.0,
                    "brightness": 1.0
                },
                "performance": {
                    "multithreading": True,
                    "max_workers": 4,
                    "cache_enabled": True,
                    "cache_size_mb": 100
                }
            },
            "usage_count": 0,
            "last_used": None,
            "created_at": datetime.now().isoformat()
        },
        "4": {
            "name": "프리셋 4",
            "description": "사용자 정의 4",
            "hotkey": "F4",
            "settings": {
                "coordinates": DEFAULT_COORDINATES,
                "blank_detection": {
                    "enabled": False,
                    "threshold": 95,
                    "algorithm": "simple"
                },
                "thumbnail": {
                    "grayscale": False,
                    "contrast": 1.0,
                    "sharpness": 1.0,
                    "brightness": 1.0
                },
                "performance": {
                    "multithreading": True,
                    "max_workers": 4,
                    "cache_enabled": True,
                    "cache_size_mb": 100
                }
            },
            "usage_count": 0,
            "last_used": None,
            "created_at": datetime.now().isoformat()
        }
    }
    
    # 기존 파일 백업
    if PRESETS_FILE.exists():
        backup_path = PRESETS_FILE.with_suffix('.backup.json')
        print(f"\n기존 프리셋 파일을 백업합니다: {backup_path}")
        
        with open(PRESETS_FILE, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(old_data, f, ensure_ascii=False, indent=2)
        
        print("✅ 백업 완료")
    
    # 디렉토리 생성
    PRESETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 새 프리셋 저장
    with open(PRESETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(NEW_PRESETS, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 프리셋 파일이 초기화되었습니다: {PRESETS_FILE}")
    
    print("\n초기화된 프리셋:")
    for key, preset in NEW_PRESETS.items():
        print(f"  {preset['hotkey']}: {preset['name']} - {preset['description']}")
    
    print("\n" + "=" * 60)
    print("프리셋 초기화 완료!")
    print("이제 설정 창을 열어 프리셋을 사용할 수 있습니다.")
    print("=" * 60)

if __name__ == "__main__":
    reset_presets()