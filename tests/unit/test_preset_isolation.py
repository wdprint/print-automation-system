"""프리셋 격리 테스트 - 프리셋 간 독립성 검증"""

import sys
import os
import json
import copy
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.preset_manager import PresetManager
from config.settings_manager import SettingsManager

def test_preset_isolation():
    """프리셋 간 독립성 테스트"""
    print("="*60)
    print("프리셋 격리 테스트 시작")
    print("="*60)
    
    # 프리셋 매니저 초기화
    preset_manager = PresetManager()
    settings_manager = SettingsManager()
    
    # 테스트 1: 프리셋 1에 설정 저장
    print("\n[테스트 1] 프리셋 1에 설정 저장")
    test_settings_1 = {
        'coordinates': {
            'thumbnail_boxes': [
                {'x': 100, 'y': 100, 'width': 200, 'height': 300},
                {'x': 400, 'y': 100, 'width': 200, 'height': 300}
            ],
            'qr_boxes': [
                {'x': 150, 'y': 450, 'size': 80}
            ]
        },
        'blank_detection': {
            'enabled': True,
            'threshold': 90
        }
    }
    
    preset_manager.save_preset('1', test_settings_1, '테스트 프리셋 1')
    print("[OK] 프리셋 1 저장 완료")
    
    # 테스트 2: 프리셋 2에 다른 설정 저장
    print("\n[테스트 2] 프리셋 2에 다른 설정 저장")
    test_settings_2 = {
        'coordinates': {
            'thumbnail_boxes': [
                {'x': 200, 'y': 200, 'width': 250, 'height': 350},
                {'x': 500, 'y': 200, 'width': 250, 'height': 350}
            ],
            'qr_boxes': [
                {'x': 250, 'y': 550, 'size': 100}
            ]
        },
        'blank_detection': {
            'enabled': False,
            'threshold': 95
        }
    }
    
    preset_manager.save_preset('2', test_settings_2, '테스트 프리셋 2')
    print("[OK] 프리셋 2 저장 완료")
    
    # 테스트 3: 프리셋 1 다시 불러오기
    print("\n[테스트 3] 프리셋 1 다시 불러오기")
    loaded_preset_1 = preset_manager.get_preset('1')
    
    # 검증 1: 프리셋 1의 데이터가 변경되지 않았는지 확인
    print("\n[검증 1] 프리셋 1 데이터 무결성 확인")
    if loaded_preset_1:
        coords_1 = loaded_preset_1.get('coordinates', {})
        thumb_boxes_1 = coords_1.get('thumbnail_boxes', [])
        
        if thumb_boxes_1 and thumb_boxes_1[0]['x'] == 100:
            print("[PASS] 프리셋 1의 썸네일 X 좌표: 100 (정상)")
        else:
            print(f"[FAIL] 프리셋 1의 썸네일 X 좌표가 변경됨: {thumb_boxes_1[0]['x'] if thumb_boxes_1 else 'N/A'}")
    
    # 테스트 4: 프리셋 1 수정 후 프리셋 2 확인
    print("\n[테스트 4] 프리셋 1 수정 후 프리셋 2 영향 확인")
    test_settings_1_modified = copy.deepcopy(test_settings_1)
    test_settings_1_modified['coordinates']['thumbnail_boxes'][0]['x'] = 999
    preset_manager.save_preset('1', test_settings_1_modified, '수정된 프리셋 1')
    
    # 프리셋 2 다시 불러오기
    loaded_preset_2 = preset_manager.get_preset('2')
    
    # 검증 2: 프리셋 2가 영향받지 않았는지 확인
    print("\n[검증 2] 프리셋 2 독립성 확인")
    if loaded_preset_2:
        coords_2 = loaded_preset_2.get('coordinates', {})
        thumb_boxes_2 = coords_2.get('thumbnail_boxes', [])
        
        if thumb_boxes_2 and thumb_boxes_2[0]['x'] == 200:
            print("[PASS] 프리셋 2의 썸네일 X 좌표: 200 (정상 - 독립성 유지)")
        else:
            print(f"[FAIL] 프리셋 2가 영향받음: {thumb_boxes_2[0]['x'] if thumb_boxes_2 else 'N/A'}")
    
    # 테스트 5: 동일 참조 확인
    print("\n[테스트 5] 객체 참조 독립성 확인")
    preset_1_first = preset_manager.get_preset('1')
    preset_1_second = preset_manager.get_preset('1')
    
    # 첫 번째 가져온 데이터 수정
    if preset_1_first and 'coordinates' in preset_1_first:
        preset_1_first['coordinates']['test_value'] = 'modified'
    
    # 두 번째 가져온 데이터 확인
    if preset_1_second and 'coordinates' in preset_1_second:
        if 'test_value' not in preset_1_second['coordinates']:
            print("[PASS] get_preset이 독립적인 복사본을 반환함 (정상)")
        else:
            print("[FAIL] get_preset이 같은 참조를 반환함 (문제)")
    
    # 결과 요약
    print("\n" + "="*60)
    print("테스트 완료")
    print("="*60)
    
    # 프리셋 파일 내용 확인
    print("\n[프리셋 파일 내용]")
    presets_file = Path("data/presets.json")
    if presets_file.exists():
        with open(presets_file, 'r', encoding='utf-8') as f:
            presets_data = json.load(f)
            
        for key in ['1', '2']:
            if key in presets_data:
                preset = presets_data[key]
                print(f"\n프리셋 {key} ({preset.get('name', 'N/A')}):")
                if 'settings' in preset and 'coordinates' in preset['settings']:
                    coords = preset['settings']['coordinates']
                    if 'thumbnail_boxes' in coords and coords['thumbnail_boxes']:
                        print(f"  - 첫 번째 썸네일 X: {coords['thumbnail_boxes'][0].get('x', 'N/A')}")
                    if 'qr_boxes' in coords and coords['qr_boxes']:
                        print(f"  - 첫 번째 QR X: {coords['qr_boxes'][0].get('x', 'N/A')}")

if __name__ == "__main__":
    test_preset_isolation()