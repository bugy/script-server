class ScriptValueWrapper:
    def __init__(self, user_value, mapped_script_value, script_arg, secure_value=None):
        self.user_value = user_value
        self.mapped_script_value = mapped_script_value
        self.script_arg = script_arg
        self.secure_value = secure_value

    def get_secure_value(self):
        if self.secure_value is not None:
            return self.secure_value
        return self.script_arg

    def __str__(self) -> str:
        if self.secure_value is not None:
            return str(self.secure_value)

        return str(self.script_arg)

    def __eq__(self, o: object) -> bool:
        return isinstance(o, ScriptValueWrapper) and (self.mapped_script_value == o.mapped_script_value)

    def __hash__(self) -> int:
        return hash(self.mapped_script_value)
