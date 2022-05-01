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


