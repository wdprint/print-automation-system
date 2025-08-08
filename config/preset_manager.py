"""프리셋 관리 모듈"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from .constants import PRESETS_FILE, DEFAULT_COORDINATES

class PresetManager:
    """프리셋 관리 - F1~F4 단축키 지원"""
    
    DEFAULT_PRESETS = {
        "1": {
            "name": "기본",
            "description": "표준 설정",
            "hotkey": "F1",
            "settings": {
                "coordinates": DEFAULT_COORDINATES
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
                "coordinates": DEFAULT_COORDINATES
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
                "coordinates": DEFAULT_COORDINATES
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
                "coordinates": DEFAULT_COORDINATES
            },
            "usage_count": 0,
            "last_used": None,
            "created_at": datetime.now().isoformat()
        }
    }
    
    def __init__(self):
        """프리셋 관리자 초기화"""
        self.presets_file = Path(PRESETS_FILE)
        self.presets = {}
        self.current_preset = "1"
        self.load_presets()
    
    def load_presets(self) -> bool:
        """프리셋 파일 로드"""
        try:
            # 파일이 없으면 기본값으로 생성
            if not self.presets_file.exists():
                self.presets = self.DEFAULT_PRESETS.copy()
                self.save_presets()
                return True
            
            # 프리셋 파일 읽기
            with open(self.presets_file, 'r', encoding='utf-8') as f:
                self.presets = json.load(f)
            
            # 누락된 프리셋 추가
            for key, default_preset in self.DEFAULT_PRESETS.items():
                if key not in self.presets:
                    self.presets[key] = default_preset
            
            return True
            
        except Exception as e:
            print(f"프리셋 로드 실패: {e}")
            self.presets = self.DEFAULT_PRESETS.copy()
            return False
    
    def save_presets(self) -> bool:
        """프리셋 파일 저장"""
        try:
            # 디렉토리 생성
            self.presets_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 파일 저장
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(self.presets, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"프리셋 저장 실패: {e}")
            return False
    
    def get_preset(self, preset_id: str) -> Optional[Dict]:
        """프리셋 데이터 가져오기"""
        # default, preset_1, preset_2, preset_3 형식을 1, 2, 3, 4로 매핑
        if preset_id == 'default':
            preset_key = '1'
        elif preset_id.startswith('preset_'):
            preset_key = preset_id.split('_')[1]
        else:
            preset_key = preset_id
        
        return self.presets.get(preset_key, {}).get('settings', {})
    
    def save_preset(self, preset_id: str, settings: Dict, name: str = None) -> bool:
        """
        현재 설정을 프리셋으로 저장
        
        Args:
            preset_id: 프리셋 ID (default, preset_1, preset_2, preset_3 또는 1, 2, 3, 4)
            settings: 저장할 설정
            name: 프리셋 이름 (선택사항)
            
        Returns:
            성공 여부
        """
        try:
            # default, preset_1, preset_2, preset_3 형식을 1, 2, 3, 4로 매핑
            if preset_id == 'default':
                preset_key = '1'
            elif preset_id.startswith('preset_'):
                preset_key = preset_id.split('_')[1]
            else:
                preset_key = preset_id
                
            if preset_key not in ["1", "2", "3", "4"]:
                raise ValueError(f"잘못된 프리셋 번호: {preset_key}")
            
            # 기존 프리셋 정보 가져오기
            existing_preset = self.presets.get(preset_key, {})
            
            # 프리셋 업데이트
            self.presets[preset_key] = {
                "name": name or existing_preset.get('name', f'프리셋 {preset_key}'),
                "description": existing_preset.get('description', f"F{preset_key} 단축키"),
                "hotkey": existing_preset.get('hotkey', f"F{preset_key}"),
                "settings": settings,  # 전체 설정 저장
                "usage_count": existing_preset.get('usage_count', 0) + 1,
                "last_used": datetime.now().isoformat(),
                "created_at": existing_preset.get('created_at', datetime.now().isoformat()),
                "modified_at": datetime.now().isoformat()
            }
            
            return self.save_presets()
            
        except Exception as e:
            print(f"프리셋 저장 실패: {e}")
            return False
    
    def load_preset(self, name_or_index: str) -> Optional[Dict]:
        """
        프리셋 불러오기
        
        Args:
            name_or_index: 프리셋 이름 또는 인덱스
            
        Returns:
            프리셋 데이터 또는 None
        """
        try:
            # 인덱스로 검색
            if name_or_index in self.presets:
                preset = self.presets[name_or_index]
                self._update_usage(name_or_index)
                return preset
            
            # 이름으로 검색
            for index, preset in self.presets.items():
                if preset.get('name') == name_or_index:
                    self._update_usage(index)
                    return preset
            
            print(f"프리셋을 찾을 수 없습니다: {name_or_index}")
            return None
            
        except Exception as e:
            print(f"프리셋 로드 실패: {e}")
            return None
    
    def quick_switch(self, index: int) -> bool:
        """
        F1~F4 단축키로 빠른 전환
        
        Args:
            index: 프리셋 번호 (1-4)
            
        Returns:
            성공 여부
        """
        try:
            str_index = str(index)
            if str_index not in self.presets:
                raise ValueError(f"잘못된 프리셋 번호: {index}")
            
            self.current_preset = str_index
            self._update_usage(str_index)
            
            # 설정 매니저에 적용
            from .settings_manager import SettingsManager
            settings_manager = SettingsManager()
            
            preset_data = self.presets[str_index]
            if 'coordinates' in preset_data:
                settings_manager.settings['coordinates'] = preset_data['coordinates']
                settings_manager.save()
            
            print(f"프리셋 {preset_data['name']} (F{index})로 전환되었습니다")
            return True
            
        except Exception as e:
            print(f"프리셋 전환 실패: {e}")
            return False
    
    def get_preset_list(self) -> List[Dict]:
        """
        프리셋 목록 가져오기
        
        Returns:
            프리셋 정보 리스트
        """
        preset_list = []
        for index, preset in self.presets.items():
            preset_list.append({
                'index': index,
                'name': preset.get('name', f'프리셋 {index}'),
                'description': preset.get('description', ''),
                'hotkey': preset.get('hotkey', f'F{index}'),
                'usage_count': preset.get('usage_count', 0),
                'last_used': preset.get('last_used'),
                'is_current': index == self.current_preset
            })
        
        # 인덱스로 정렬
        preset_list.sort(key=lambda x: x['index'])
        return preset_list
    
    def get_usage_stats(self) -> Dict:
        """
        프리셋 사용 통계
        
        Returns:
            통계 정보
        """
        total_usage = sum(p.get('usage_count', 0) for p in self.presets.values())
        
        stats = {
            'total_usage': total_usage,
            'most_used': None,
            'least_used': None,
            'presets': []
        }
        
        # 각 프리셋 통계
        for index, preset in self.presets.items():
            stats['presets'].append({
                'index': index,
                'name': preset.get('name'),
                'usage_count': preset.get('usage_count', 0),
                'last_used': preset.get('last_used')
            })
        
        # 가장 많이/적게 사용된 프리셋
        if stats['presets']:
            stats['presets'].sort(key=lambda x: x['usage_count'], reverse=True)
            stats['most_used'] = stats['presets'][0] if stats['presets'][0]['usage_count'] > 0 else None
            stats['least_used'] = stats['presets'][-1] if stats['presets'][-1]['usage_count'] < total_usage else None
        
        return stats
    
    def reset_preset(self, index: str) -> bool:
        """
        프리셋을 기본값으로 초기화
        
        Args:
            index: 프리셋 번호
            
        Returns:
            성공 여부
        """
        try:
            if index in self.DEFAULT_PRESETS:
                self.presets[index] = self.DEFAULT_PRESETS[index].copy()
                self.presets[index]['created_at'] = datetime.now().isoformat()
                return self.save_presets()
            return False
            
        except Exception as e:
            print(f"프리셋 초기화 실패: {e}")
            return False
    
    def _update_usage(self, index: str):
        """사용 통계 업데이트"""
        if index in self.presets:
            self.presets[index]['usage_count'] = self.presets[index].get('usage_count', 0) + 1
            self.presets[index]['last_used'] = datetime.now().isoformat()
            self.save_presets()