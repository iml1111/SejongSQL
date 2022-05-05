class SingletonInstane:
    __instance = None

    @classmethod
    def __getInstance(cls, *args, **kwargs):
        # First After
        return cls.__instance

    @classmethod
    def instance(cls, *args, **kwargs):
        # First
        cls.__instance = cls(*args, **kwargs)
        cls.instance = cls.__getInstance
        return cls.__instance