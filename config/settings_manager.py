"""설정 파일 관리 모듈"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
import shutil

from .constants import (
    SETTINGS_FILE, 
    DEFAULT_COORDINATES, 
    DEFAULT_BLANK_THRESHOLD,
    DEFAULT_MAX_WORKERS,
    DEFAULT_CACHE_SIZE_MB
)

class SettingsManager:
    """설정 파일 관리 및 접근"""
    
    DEFAULT_SETTINGS = {
        "version": "2.1",
        "coordinates": {
            "page_size": {"width": 842, "height": 595},
            # 썸네일 좌표를 배열로 변경 - 동적 추가/삭제 가능
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
            # QR 코드도 배열로 변경 (선택사항)
            "qr_boxes": [
                {
                    "id": "qr_1",
                    "name": "QR 1",
                    "x": 315,
                    "y": 500,
                    "size": 70,
                    "rotation": 0
                },
                {
                    "id": "qr_2",
                    "name": "QR 2",
                    "x": 730,
                    "y": 500,
                    "size": 70,
                    "rotation": 0
                }
            ]
        },
        
        # v1 통합: 썸네일 향상 설정
        "thumbnail": {
            "max_width": 160,
            "max_height": 250,
            "page_selection": "1",
            "multi_page": False,
            "grayscale": False,
            "contrast": 1.0,
            "sharpness": 1.0,
            "quality": 95
        },
        
        # v1 통합: QR 코드 설정
        "qr": {
            "max_width": 70,
            "max_height": 70,
            "quality": 95
        },
        
        # v1 통합: 백지 감지 설정
        "blank_detection": {
            "enabled": True,  # 기본값을 True로 변경
            "threshold": DEFAULT_BLANK_THRESHOLD,
            "algorithm": "simple",
            "exclude_areas": {
                "header": 50,
                "footer": 50,
                "left_margin": 20,
                "right_margin": 20
            },
            "cache_enabled": True
        },
        
        # v1 통합: 처리 규칙
        "processing_rules": {
            "enabled": False,
            "rules": []
        },
        
        # v1 통합: 프리셋 시스템
        "presets": {
            "default": {
                "name": "기본 설정",
                "description": "표준 처리 설정",
                "hotkey": "F1",
                "last_used": None,
                "use_count": 0,
                "settings": {}
            }
        },
        
        # v1 통합: PDF 정규화 설정
        "pdf_normalize": {
            "enabled": True,
            "target_orientation": "landscape",  # landscape, portrait, auto
            "auto_detect": True
        },
        
        # v1 통합: 성능 설정
        "performance": {
            "multithreading": True,
            "max_workers": DEFAULT_MAX_WORKERS,
            "max_concurrent_files": 3,
            "cache_enabled": True,
            "cache_size_mb": DEFAULT_CACHE_SIZE_MB,
            "log_level": "INFO"
        },
        
        # v1 통합: UI 설정
        "ui": {
            "language": "ko",
            "theme": "default",
            "window_always_on_top": True,
            "show_tooltips": True,
            "confirm_before_process": False,
            "auto_save_settings": True
        },
        
        # v1 통합: 파일 처리 설정
        "file_processing": {
            "overwrite_original": True,
            "backup_before_save": False,
            "backup_suffix": "_backup",
            "auto_normalize": True,
            "rasterize_final": False
        },
        
        "last_modified": None
    }
    
    def __init__(self):
        """설정 관리자 초기화"""
        self.settings_file = Path(SETTINGS_FILE)
        self.settings = {}
        self.load()
    
    def load(self) -> bool:
        """설정 파일 로드"""
        try:
            # 설정 파일이 없으면 기본값으로 생성
            if not self.settings_file.exists():
                self.settings = self.DEFAULT_SETTINGS.copy()
                self.save()
                return True
            
            # 설정 파일 읽기
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
            
            # 기본 설정과 병합 (새로운 키가 추가된 경우 대응)
            self.settings = self._merge_settings(
                self.DEFAULT_SETTINGS.copy(), 
                loaded_settings
            )
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"설정 파일 읽기 오류: {e}")
            # 백업 생성 후 기본값으로 초기화
            self._backup_corrupted_settings()
            self.settings = self.DEFAULT_SETTINGS.copy()
            self.save()
            return False
            
        except Exception as e:
            print(f"설정 로드 실패: {e}")
            self.settings = self.DEFAULT_SETTINGS.copy()
            return False
    
    def save(self) -> bool:
        """설정 파일 저장"""
        try:
            # 디렉토리 생성
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 저장 시간 업데이트
            self.settings['last_modified'] = datetime.now().isoformat()
            
            # 파일 저장
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"설정 저장 실패: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        설정 값 가져오기 (점 표기법 지원)
        
        Args:
            key: 설정 키 (예: 'coordinates.thumbnail.left.x')
            default: 기본값
            
        Returns:
            설정 값 또는 기본값
        """
        try:
            keys = key.split('.')
            value = self.settings
            
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                    if value is None:
                        return default
                else:
                    return default
            
            return value
            
        except Exception:
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """
        설정 값 저장 (점 표기법 지원)
        
        Args:
            key: 설정 키 (예: 'coordinates.thumbnail.left.x')
            value: 저장할 값
            
        Returns:
            성공 여부
        """
        try:
            keys = key.split('.')
            target = self.settings
            
            # 마지막 키 전까지 탐색
            for k in keys[:-1]:
                if k not in target:
                    target[k] = {}
                target = target[k]
            
            # 값 설정
            target[keys[-1]] = value
            
            # 자동 저장
            return self.save()
            
        except Exception as e:
            print(f"설정 값 저장 실패: {e}")
            return False
    
    def get_coordinates(self, position: str = 'left') -> Dict:
        """
        좌표 설정 가져오기
        
        Args:
            position: 'left' 또는 'right'
            
        Returns:
            좌표 딕셔너리
        """
        return {
            'thumbnail': self.get(f'coordinates.thumbnail.{position}', {}),
            'qr': self.get(f'coordinates.qr.{position}', {})
        }
    
    def set_coordinates(self, position: str, coord_type: str, values: Dict) -> bool:
        """
        좌표 설정 저장
        
        Args:
            position: 'left' 또는 'right'
            coord_type: 'thumbnail' 또는 'qr'
            values: 좌표 값 딕셔너리
            
        Returns:
            성공 여부
        """
        return self.set(f'coordinates.{coord_type}.{position}', values)
    
    def reset_to_defaults(self) -> bool:
        """설정을 기본값으로 초기화"""
        self.settings = self.DEFAULT_SETTINGS.copy()
        return self.save()
    
    def export_settings(self, filepath: str) -> bool:
        """설정 내보내기"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"설정 내보내기 실패: {e}")
            return False
    
    def import_settings(self, filepath: str) -> bool:
        """설정 가져오기"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                imported = json.load(f)
            
            # 유효성 검증
            if 'coordinates' not in imported or 'version' not in imported:
                raise ValueError("올바른 설정 파일이 아닙니다")
            
            # 기본 설정과 병합
            self.settings = self._merge_settings(
                self.DEFAULT_SETTINGS.copy(),
                imported
            )
            
            return self.save()
            
        except Exception as e:
            print(f"설정 가져오기 실패: {e}")
            return False
    
    def _merge_settings(self, base: Dict, overlay: Dict) -> Dict:
        """설정 병합 (재귀적)"""
        for key, value in overlay.items():
            if key in base:
                if isinstance(base[key], dict) and isinstance(value, dict):
                    base[key] = self._merge_settings(base[key], value)
                else:
                    base[key] = value
            else:
                base[key] = value
        return base
    
    def _backup_corrupted_settings(self):
        """손상된 설정 파일 백업"""
        try:
            if self.settings_file.exists():
                backup_name = f"settings_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                backup_path = self.settings_file.parent / backup_name
                shutil.copy(self.settings_file, backup_path)
                print(f"손상된 설정 파일을 백업했습니다: {backup_path}")
        except Exception as e:
            print(f"백업 실패: {e}")
    
    def load_preset(self, preset_name: str) -> bool:
        """프리셋 로드 - v1 통합"""
        try:
            presets = self.settings.get("presets", {})
            
            if preset_name not in presets:
                self.logger.warning(f"프리셋을 찾을 수 없습니다: {preset_name}")
                return False
            
            preset_data = presets[preset_name]
            preset_settings = preset_data.get("settings", {})
            
            # 프리셋 설정 적용
            for key, value in preset_settings.items():
                if key in self.settings:
                    if isinstance(self.settings[key], dict) and isinstance(value, dict):
                        self.settings[key].update(value)
                    else:
                        self.settings[key] = value
            
            # 사용 통계 업데이트
            presets[preset_name]["last_used"] = datetime.now().isoformat()
            presets[preset_name]["use_count"] = presets[preset_name].get("use_count", 0) + 1
            
            return self.save()
            
        except Exception as e:
            print(f"프리셋 로드 실패: {e}")
            return False
    
    def save_preset(self, preset_name: str, description: str = "", hotkey: str = "") -> bool:
        """현재 설정을 프리셋으로 저장"""
        try:
            presets = self.settings.get("presets", {})
            
            # 현재 설정에서 프리셋에 포함할 항목들
            preset_settings = {
                "coordinates": self.settings.get("coordinates", {}),
                "thumbnail": self.settings.get("thumbnail", {}),
                "qr": self.settings.get("qr", {}),
                "blank_detection": self.settings.get("blank_detection", {}),
                "pdf_normalize": self.settings.get("pdf_normalize", {})
            }
            
            presets[preset_name] = {
                "name": preset_name,
                "description": description,
                "hotkey": hotkey,
                "created": datetime.now().isoformat(),
                "last_used": None,
                "use_count": 0,
                "settings": preset_settings
            }
            
            self.settings["presets"] = presets
            return self.save()
            
        except Exception as e:
            print(f"프리셋 저장 실패: {e}")
            return False
    
    def delete_preset(self, preset_name: str) -> bool:
        """프리셋 삭제"""
        try:
            presets = self.settings.get("presets", {})
            
            if preset_name == "default":
                print("기본 프리셋은 삭제할 수 없습니다")
                return False
            
            if preset_name in presets:
                del presets[preset_name]
                self.settings["presets"] = presets
                return self.save()
            
            return False
            
        except Exception as e:
            print(f"프리셋 삭제 실패: {e}")
            return False
    
    def get_preset_list(self) -> list:
        """프리셋 목록 반환"""
        presets = self.settings.get("presets", {})
        return list(presets.keys())
    
    def get_preset_info(self, preset_name: str) -> dict:
        """프리셋 정보 반환"""
        presets = self.settings.get("presets", {})
        return presets.get(preset_name, {})
    
    def add_processing_rule(self, rule: dict) -> bool:
        """처리 규칙 추가"""
        try:
            rules = self.settings.get("processing_rules", {})
            if not isinstance(rules, dict):
                rules = {"enabled": False, "rules": []}
            
            rules_list = rules.get("rules", [])
            rules_list.append(rule)
            
            rules["rules"] = rules_list
            self.settings["processing_rules"] = rules
            
            return self.save()
            
        except Exception as e:
            print(f"처리 규칙 추가 실패: {e}")
            return False
    
    def remove_processing_rule(self, rule_index: int) -> bool:
        """처리 규칙 제거"""
        try:
            rules = self.settings.get("processing_rules", {})
            rules_list = rules.get("rules", [])
            
            if 0 <= rule_index < len(rules_list):
                del rules_list[rule_index]
                rules["rules"] = rules_list
                self.settings["processing_rules"] = rules
                return self.save()
            
            return False
            
        except Exception as e:
            print(f"처리 규칙 제거 실패: {e}")
            return False
    
    def get_processing_rules(self) -> list:
        """처리 규칙 목록 반환"""
        rules = self.settings.get("processing_rules", {})
        return rules.get("rules", [])
    
    def is_processing_rules_enabled(self) -> bool:
        """처리 규칙 활성화 상태 확인"""
        rules = self.settings.get("processing_rules", {})
        return rules.get("enabled", False)
    
    def set_processing_rules_enabled(self, enabled: bool) -> bool:
        """처리 규칙 활성화/비활성화"""
        rules = self.settings.get("processing_rules", {})
        if not isinstance(rules, dict):
            rules = {"enabled": False, "rules": []}
        
        rules["enabled"] = enabled
        self.settings["processing_rules"] = rules
        
        return self.save()