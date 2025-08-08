"""처리 규칙 엔진 - 파일명 패턴에 따른 자동 처리"""

import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from config.settings_manager import SettingsManager
from utils.logger import setup_logger


class RulesEngine:
    """파일명 패턴에 따른 처리 규칙 엔진"""
    
    def __init__(self, settings_manager: SettingsManager):
        """
        규칙 엔진 초기화
        
        Args:
            settings_manager: 설정 관리자
        """
        self.settings = settings_manager
        self.logger = setup_logger(self.__class__.__name__)
        
        # 내장 규칙 정의
        self.builtin_rules = [
            {
                "name": "표지 처리",
                "pattern": r"표지|cover|겉표지",
                "description": "표지가 포함된 파일의 특수 처리",
                "action": {
                    "type": "modify_settings",
                    "changes": {
                        "qr.skip": True,
                        "thumbnail.opacity": 0.8,
                        "blank_detection.enabled": False
                    }
                },
                "priority": 10,
                "enabled": True
            },
            {
                "name": "급행 처리",
                "pattern": r"급행|urgent|긴급|rush",
                "description": "급행 처리가 필요한 파일",
                "action": {
                    "type": "priority",
                    "level": "high",
                    "notify": True
                },
                "priority": 20,
                "enabled": True
            },
            {
                "name": "대량 인쇄물",
                "pattern": r"대량|bulk|mass|\d{3,}장",
                "description": "대량 인쇄물 최적화 처리",
                "action": {
                    "type": "modify_settings", 
                    "changes": {
                        "thumbnail.quality": 80,
                        "performance.multithreading": True,
                        "blank_detection.enabled": True
                    }
                },
                "priority": 5,
                "enabled": True
            },
            {
                "name": "소량 정밀 인쇄",
                "pattern": r"소량|정밀|고품질|premium|\d{1,2}장",
                "description": "소량 정밀 인쇄물 고품질 처리",
                "action": {
                    "type": "modify_settings",
                    "changes": {
                        "thumbnail.quality": 100,
                        "thumbnail.sharpness": 1.2,
                        "performance.multithreading": False
                    }
                },
                "priority": 15,
                "enabled": True
            },
            {
                "name": "카다로그/브로셔",
                "pattern": r"카다로그|catalog|브로셔|brochure|팜플렛",
                "description": "카다로그/브로셔 특화 처리",
                "action": {
                    "type": "modify_settings",
                    "changes": {
                        "thumbnail.multi_page": True,
                        "thumbnail.page_selection": "1,2,3",
                        "thumbnail.quality": 95
                    }
                },
                "priority": 8,
                "enabled": True
            }
        ]
    
    def apply_rules(self, file_path: str, current_settings: Dict) -> Dict[str, Any]:
        """
        파일명에 따라 처리 규칙 적용
        
        Args:
            file_path: 파일 경로
            current_settings: 현재 설정
            
        Returns:
            Dict[str, Any]: 적용된 규칙 정보와 수정된 설정
        """
        try:
            if not self.settings.is_processing_rules_enabled():
                return {"applied": False, "reason": "처리 규칙이 비활성화됨"}
            
            filename = os.path.basename(file_path)
            self.logger.debug(f"규칙 적용 대상 파일: {filename}")
            
            # 적용 가능한 규칙 찾기
            matching_rules = self._find_matching_rules(filename)
            
            if not matching_rules:
                return {"applied": False, "reason": "매칭되는 규칙 없음"}
            
            # 우선순위순으로 정렬
            matching_rules.sort(key=lambda x: x.get("priority", 0), reverse=True)
            
            applied_rules = []
            modified_settings = current_settings.copy()
            
            # 각 규칙 적용
            for rule in matching_rules:
                if self._apply_single_rule(rule, modified_settings, filename):
                    applied_rules.append({
                        "name": rule["name"],
                        "pattern": rule["pattern"],
                        "action": rule["action"]
                    })
            
            result = {
                "applied": len(applied_rules) > 0,
                "applied_rules": applied_rules,
                "rule_count": len(applied_rules),
                "filename": filename,
                "timestamp": datetime.now().isoformat()
            }
            
            if applied_rules:
                self.logger.info(f"규칙 적용 완료: {len(applied_rules)}개 규칙 → {filename}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"규칙 적용 중 오류: {e}")
            return {"applied": False, "error": str(e)}
    
    def _find_matching_rules(self, filename: str) -> List[Dict]:
        """파일명에 매칭되는 규칙 찾기"""
        matching_rules = []
        
        # 사용자 정의 규칙
        user_rules = self.settings.get_processing_rules()
        all_rules = user_rules + self.builtin_rules
        
        for rule in all_rules:
            if not rule.get("enabled", True):
                continue
            
            pattern = rule.get("pattern", "")
            if not pattern:
                continue
            
            try:
                # 정규표현식 매칭
                if re.search(pattern, filename, re.IGNORECASE):
                    matching_rules.append(rule)
                    self.logger.debug(f"규칙 매칭: {rule['name']} → {filename}")
                    
            except re.error as e:
                self.logger.error(f"잘못된 정규표현식 패턴: {pattern} - {e}")
                continue
        
        return matching_rules
    
    def _apply_single_rule(self, rule: Dict, settings: Dict, filename: str) -> bool:
        """단일 규칙 적용"""
        try:
            action = rule.get("action", {})
            action_type = action.get("type", "")
            
            if action_type == "modify_settings":
                return self._apply_settings_changes(action.get("changes", {}), settings)
                
            elif action_type == "priority":
                return self._apply_priority_change(action, settings)
                
            elif action_type == "skip_processing":
                settings["_skip_processing"] = True
                return True
                
            elif action_type == "custom_preset":
                preset_name = action.get("preset_name")
                return self._apply_custom_preset(preset_name, settings)
                
            elif action_type == "notification":
                return self._apply_notification(action, filename)
                
            else:
                self.logger.warning(f"알 수 없는 액션 타입: {action_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"규칙 적용 실패: {e}")
            return False
    
    def _apply_settings_changes(self, changes: Dict, settings: Dict) -> bool:
        """설정 변경 적용"""
        try:
            for key, value in changes.items():
                # 점 표기법 지원 (예: "thumbnail.quality")
                keys = key.split('.')
                target = settings
                
                # 마지막 키 전까지 탐색
                for k in keys[:-1]:
                    if k not in target:
                        target[k] = {}
                    target = target[k]
                
                # 값 설정
                target[keys[-1]] = value
                self.logger.debug(f"설정 변경: {key} = {value}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"설정 변경 실패: {e}")
            return False
    
    def _apply_priority_change(self, action: Dict, settings: Dict) -> bool:
        """우선순위 변경 적용"""
        try:
            level = action.get("level", "normal")
            notify = action.get("notify", False)
            
            settings["_priority_level"] = level
            settings["_priority_notify"] = notify
            
            if level == "high":
                # 고우선순위 처리를 위한 설정 최적화
                settings["performance"]["multithreading"] = True
                settings["performance"]["max_workers"] = min(8, settings["performance"]["max_workers"] * 2)
            
            self.logger.info(f"우선순위 설정: {level}")
            return True
            
        except Exception as e:
            self.logger.error(f"우선순위 변경 실패: {e}")
            return False
    
    def _apply_custom_preset(self, preset_name: str, settings: Dict) -> bool:
        """커스텀 프리셋 적용"""
        try:
            if not preset_name:
                return False
            
            preset_info = self.settings.get_preset_info(preset_name)
            if not preset_info:
                self.logger.warning(f"프리셋을 찾을 수 없습니다: {preset_name}")
                return False
            
            preset_settings = preset_info.get("settings", {})
            
            # 프리셋 설정을 현재 설정에 병합
            for key, value in preset_settings.items():
                if isinstance(settings.get(key), dict) and isinstance(value, dict):
                    settings[key].update(value)
                else:
                    settings[key] = value
            
            self.logger.info(f"프리셋 적용: {preset_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"프리셋 적용 실패: {e}")
            return False
    
    def _apply_notification(self, action: Dict, filename: str) -> bool:
        """알림 처리"""
        try:
            message = action.get("message", f"특수 처리 파일: {filename}")
            level = action.get("level", "info")
            
            if level == "warning":
                self.logger.warning(message)
            elif level == "error":
                self.logger.error(message)
            else:
                self.logger.info(message)
            
            return True
            
        except Exception as e:
            self.logger.error(f"알림 처리 실패: {e}")
            return False
    
    def validate_rule(self, rule: Dict) -> Dict[str, Any]:
        """규칙 유효성 검증"""
        errors = []
        warnings = []
        
        # 필수 필드 검증
        required_fields = ["name", "pattern", "action"]
        for field in required_fields:
            if field not in rule:
                errors.append(f"필수 필드 누락: {field}")
        
        # 패턴 검증
        pattern = rule.get("pattern", "")
        if pattern:
            try:
                re.compile(pattern)
            except re.error as e:
                errors.append(f"잘못된 정규표현식: {e}")
        
        # 액션 검증
        action = rule.get("action", {})
        if not isinstance(action, dict):
            errors.append("action은 딕셔너리여야 합니다")
        else:
            action_type = action.get("type", "")
            if not action_type:
                errors.append("action.type이 필요합니다")
            elif action_type not in ["modify_settings", "priority", "skip_processing", "custom_preset", "notification"]:
                warnings.append(f"알 수 없는 액션 타입: {action_type}")
        
        # 우선순위 검증
        priority = rule.get("priority", 0)
        if not isinstance(priority, int) or priority < 0:
            warnings.append("priority는 0 이상의 정수여야 합니다")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def test_rule(self, rule: Dict, test_filename: str) -> Dict[str, Any]:
        """규칙 테스트"""
        try:
            # 규칙 유효성 검증
            validation = self.validate_rule(rule)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": "규칙이 유효하지 않습니다",
                    "validation": validation
                }
            
            # 패턴 매칭 테스트
            pattern = rule["pattern"]
            matches = bool(re.search(pattern, test_filename, re.IGNORECASE))
            
            result = {
                "success": True,
                "matches": matches,
                "rule_name": rule["name"],
                "pattern": pattern,
                "test_filename": test_filename,
                "validation": validation
            }
            
            # 매칭되는 경우 액션 시뮬레이션
            if matches:
                action = rule.get("action", {})
                result["simulated_action"] = self._simulate_action(action)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _simulate_action(self, action: Dict) -> Dict[str, Any]:
        """액션 시뮬레이션 (실제 적용 없이 테스트)"""
        simulation = {
            "type": action.get("type", "unknown"),
            "description": ""
        }
        
        action_type = action.get("type", "")
        
        if action_type == "modify_settings":
            changes = action.get("changes", {})
            simulation["description"] = f"{len(changes)}개 설정 변경"
            simulation["changes"] = changes
            
        elif action_type == "priority":
            level = action.get("level", "normal")
            simulation["description"] = f"우선순위: {level}"
            simulation["priority_level"] = level
            
        elif action_type == "skip_processing":
            simulation["description"] = "처리 건너뛰기"
            
        elif action_type == "custom_preset":
            preset_name = action.get("preset_name", "")
            simulation["description"] = f"프리셋 적용: {preset_name}"
            simulation["preset_name"] = preset_name
            
        elif action_type == "notification":
            message = action.get("message", "")
            simulation["description"] = f"알림: {message}"
            simulation["message"] = message
        
        return simulation
    
    def get_builtin_rules(self) -> List[Dict]:
        """내장 규칙 목록 반환"""
        return self.builtin_rules.copy()
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """규칙 사용 통계"""
        user_rules = self.settings.get_processing_rules()
        builtin_rules = self.builtin_rules
        
        stats = {
            "total_rules": len(user_rules) + len(builtin_rules),
            "user_rules": len(user_rules),
            "builtin_rules": len(builtin_rules),
            "enabled_rules": 0,
            "disabled_rules": 0,
            "rules_enabled_globally": self.settings.is_processing_rules_enabled()
        }
        
        all_rules = user_rules + builtin_rules
        for rule in all_rules:
            if rule.get("enabled", True):
                stats["enabled_rules"] += 1
            else:
                stats["disabled_rules"] += 1
        
        return stats