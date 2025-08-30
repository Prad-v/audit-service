"""
Rule Evaluator Service

This module handles evaluation of alert rules, including simple and compound rules.
"""

import logging
import re
from typing import Dict, Any, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class RuleEvaluator:
    """Evaluates alert rules against event data"""
    
    def __init__(self):
        self.operators = {
            'eq': self._equals,
            'ne': self._not_equals,
            'gt': self._greater_than,
            'lt': self._less_than,
            'gte': self._greater_than_equal,
            'lte': self._less_than_equal,
            'in': self._in_list,
            'not_in': self._not_in_list,
            'contains': self._contains,
            'regex': self._regex_match
        }
    
    def evaluate_rule(self, rule: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """Evaluate a rule against event data"""
        try:
            rule_type = rule.get('rule_type', 'simple')
            
            if rule_type == 'simple':
                return self._evaluate_simple_rule(rule, event_data)
            elif rule_type == 'compound':
                return self._evaluate_compound_rule(rule, event_data)
            else:
                logger.error(f"Unknown rule type: {rule_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating rule: {e}")
            return False
    
    def _evaluate_simple_rule(self, rule: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """Evaluate a simple rule"""
        field = rule.get('field')
        operator = rule.get('operator')
        value = rule.get('value')
        case_sensitive = rule.get('case_sensitive', True)
        
        if not field or not operator or value is None:
            return False
        
        # Get field value from event data
        field_value = self._get_nested_value(event_data, field)
        
        # Evaluate condition
        return self.operators[operator](field_value, value, case_sensitive)
    
    def _evaluate_compound_rule(self, rule: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """Evaluate a compound rule with multiple conditions"""
        conditions = rule.get('conditions', [])
        group_operator = rule.get('group_operator', 'AND')
        
        if not conditions:
            return False
        
        # Evaluate each condition
        results = []
        for condition in conditions:
            result = self._evaluate_simple_rule(condition, event_data)
            results.append(result)
        
        # Apply group operator
        if group_operator == 'AND':
            return all(results)
        elif group_operator == 'OR':
            return any(results)
        else:
            logger.error(f"Unknown group operator: {group_operator}")
            return False
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get nested value from data using dot notation"""
        try:
            keys = field_path.split('.')
            value = data
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None
            
            return value
        except Exception:
            return None
    
    def _equals(self, field_value: Any, rule_value: Any, case_sensitive: bool = True) -> bool:
        """Check if field value equals rule value"""
        if field_value is None:
            return False
        
        if isinstance(field_value, str) and isinstance(rule_value, str) and not case_sensitive:
            return field_value.lower() == rule_value.lower()
        
        return field_value == rule_value
    
    def _not_equals(self, field_value: Any, rule_value: Any, case_sensitive: bool = True) -> bool:
        """Check if field value does not equal rule value"""
        return not self._equals(field_value, rule_value, case_sensitive)
    
    def _greater_than(self, field_value: Any, rule_value: Any, case_sensitive: bool = True) -> bool:
        """Check if field value is greater than rule value"""
        try:
            return float(field_value) > float(rule_value)
        except (ValueError, TypeError):
            return False
    
    def _less_than(self, field_value: Any, rule_value: Any, case_sensitive: bool = True) -> bool:
        """Check if field value is less than rule value"""
        try:
            return float(field_value) < float(rule_value)
        except (ValueError, TypeError):
            return False
    
    def _greater_than_equal(self, field_value: Any, rule_value: Any, case_sensitive: bool = True) -> bool:
        """Check if field value is greater than or equal to rule value"""
        try:
            return float(field_value) >= float(rule_value)
        except (ValueError, TypeError):
            return False
    
    def _less_than_equal(self, field_value: Any, rule_value: Any, case_sensitive: bool = True) -> bool:
        """Check if field value is less than or equal to rule value"""
        try:
            return float(field_value) <= float(rule_value)
        except (ValueError, TypeError):
            return False
    
    def _in_list(self, field_value: Any, rule_value: Any, case_sensitive: bool = True) -> bool:
        """Check if field value is in the rule value list"""
        if not isinstance(rule_value, list):
            return False
        
        if isinstance(field_value, str) and not case_sensitive:
            return field_value.lower() in [str(v).lower() for v in rule_value]
        
        return field_value in rule_value
    
    def _not_in_list(self, field_value: Any, rule_value: Any, case_sensitive: bool = True) -> bool:
        """Check if field value is not in the rule value list"""
        return not self._in_list(field_value, rule_value, case_sensitive)
    
    def _contains(self, field_value: Any, rule_value: Any, case_sensitive: bool = True) -> bool:
        """Check if field value contains rule value"""
        if not isinstance(field_value, str) or not isinstance(rule_value, str):
            return False
        
        if not case_sensitive:
            return rule_value.lower() in field_value.lower()
        
        return rule_value in field_value
    
    def _regex_match(self, field_value: Any, rule_value: Any, case_sensitive: bool = True) -> bool:
        """Check if field value matches regex pattern"""
        if not isinstance(field_value, str) or not isinstance(rule_value, str):
            return False
        
        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            return bool(re.search(rule_value, field_value, flags))
        except re.error:
            logger.error(f"Invalid regex pattern: {rule_value}")
            return False
