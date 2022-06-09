import re
from .exceptions import InvalidRuleParameter
from abc import ABCMeta, abstractmethod


class ValidationRule(metaclass=ABCMeta):

    @staticmethod
    def _param_validate(param, param_type):
        if not isinstance(param, param_type):
            raise InvalidRuleParameter(param, param_type)
        return param

    def invalid_str(self):
        return f"doesn't not match the {self.__class__.__name__} rule"

    @abstractmethod
    def is_valid(self, data) -> bool:
        pass


class MinLen(ValidationRule):

    def __init__(self, num):
        self._num = self._param_validate(num, int)

    def invalid_str(self):
        return f"must be bigger than {self._num} elements."

    def is_valid(self, data):
        return self._num <= len(data)


class MaxLen(ValidationRule):

    def __init__(self, num):
        self._num = self._param_validate(num, int)

    def invalid_str(self):
        return f"must be less than {self._num} elements."

    def is_valid(self, data):
        return self._num >= len(data)


class IsAlNum(ValidationRule):

    def __init__(self):
        pass

    def invalid_str(self):
        return "must consist of numbers and alphabets."

    def is_valid(self, data):
        _len = len(data)

        _string = re.findall('[a-z,A-Z]', data)
        _num = re.findall('[1-9]', data)

        if _len != len(''.join(_string + _num)):
            return False
        
        if not _string:
            return False
        
        if not _num:
            return False
        
        return True
