from dataclasses import dataclass
from typing import Callable, Any
from django_jwt_extended.request import REQUESTS
from module.util import django_header
from module.exceptions import (
    InvalidParamType,
    InvalidRule,
    InvalidOptional,
    InvalidDefault,
    InvalidRequest,
    InvalidParam,
    ValidationFailed,
)


class Validator:

    def __init__(self, request, paths: dict, params: list):
        if not any([isinstance(request, req) for req in REQUESTS]):
            raise InvalidRequest(request)
        for param in params:
            if param.__class__.__bases__[0] is not Param:
                raise InvalidParam(param)
        try:
            self.data = self.validate(request, paths, params)
            self.is_valid = True
        except ValidationFailed as e:
            self.is_valid = False
            self.error_msg = e.param
            self.data = {}

    def validate(self, request, paths, params):
        parsed_input = {}
        for param in params:
            if param.__class__ is Path:
                data = paths.get(param.name)
            elif param.__class__ is Query:
                data = request.GET.get(param.name)
            elif param.__class__ is Form:
                data = request.POST.get(param.name)
            elif param.__class__ is Header:
                header_v1, header_v2 = django_header(param.name)
                data = request.META.get(header_v1)
                if data is None:
                    data = request.META.get(header_v2)
            elif param.__class__ is Json:
                data = request.data.get(param.name)
            else: # File
                data = request.FILES.get(param.name)

            if data is None and param.default is not None:
                data = param.default
            elif data is None and not param.optional:
                raise ValidationFailed(
                    f'Required {param.__class__.__name__} parameter, '
                    f'"{param.name}" not given.'
                )
            if (
                data is not None
                and param.param_type is not None
                and not isinstance(data, param.param_type)
            ):
                raise ValidationFailed(
                    f'In [{param.__class__.__name__}] Params, '
                    f'{param.name} is not {param.param_type}.'
                )
            if (
                data is not None
                and param.rules[0] is not None
            ):
                for rule in param.rules:
                    if not rule.is_valid(data):
                        raise ValidationFailed(
                            f"'{param.name}' {rule.invalid_str()}"
                        )
            parsed_input[param.name] = data

        return parsed_input


@dataclass
class Param:
    name: str  # 파라미터 이름
    param_type: type = None  # type 오브젝트 or None
    default: Any = None  # param_type을 가진 오브젝트 or None
    rules: Any = None  # is_valid 매소드를 가진 오브젝트 or 해당 오브젝트 list
    optional: bool = False  # True or False

    def validate(self):
        if (
            self.param_type is not None
            and not isinstance(self.param_type, type)
        ):
            raise InvalidParamType(self.param_type)
        if (
            self.default is not None
            and self.param_type is not None
            and not isinstance(self.default, self.param_type)
        ):
            raise InvalidDefault(self.default)
        rules = self.rules if isinstance(self.rules, list) else [self.rules]
        for rule in rules:
            if (
                not isinstance(rule, object)
                and "is_valid" not in dir(rule)
            ):
                raise InvalidRule(rule)
        if not isinstance(self.optional, bool):
            raise InvalidOptional(self.optional)

    def __post_init__(self):
        self.validate()


class Path(Param):
    pass

class Query(Param):
    pass

class Form(Param):
    pass

class Header(Param):
    pass

class Json(Param):
    pass

class File(Param):
    pass


if __name__ == '__main__':
    pass