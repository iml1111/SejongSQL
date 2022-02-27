

class InvalidParamType(Exception):

    def __init__(self, param_type):
        self.param_type = param_type

    def __str__(self):
        return f'{self.param_type} is not "type" object.'


class InvalidRule(Exception):

    def __init__(self, param):
        self.param = param

    def __str__(self):
        return f'{self.param} is not "callable" object.'


class InvalidOptional(Exception):

    def __init__(self, param):
        self.param = param

    def __str__(self):
        return f'{self.param} is not "bool" object.'


class InvalidDefault(Exception):

    def __init__(self, param):
        self.param = param

    def __str__(self):
        return f'{self.param} not matched "param_type".'


class InvalidRequest(Exception):

    def __init__(self, param):
        self.param = param

    def __str__(self):
        return f'{self.param} is not Django supported "Request" Object.'


class InvalidParam(Exception):

    def __init__(self, param):
        self.param = param

    def __str__(self):
        return f'{self.param} is not "Param" Object.'


class ValidationFailed(Exception):

    def __init__(self, param):
        self.param = param

    def __str__(self):
        return f'Parameter validation failed: {self.param}'