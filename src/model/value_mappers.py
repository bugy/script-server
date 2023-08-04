import abc

from model.model_helper import read_dict


class ValueMapper(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def map_to_script_value(self, user_value):
        pass

    @abc.abstractmethod
    def map_to_ui_value(self, script_value):
        pass


class DictBasedValueMapper(ValueMapper):

    def __init__(self, mappings) -> None:
        self._mappings = mappings

    def map_to_script_value(self, user_value):
        if user_value is None:
            return None

        if not self._mappings:
            return user_value

        str_user_value = str(user_value)

        for script_value, mapped_user_value in self._mappings.items():
            if mapped_user_value == str_user_value:
                return script_value

        return user_value

    def map_to_ui_value(self, script_value):
        if script_value is None:
            return None

        if not self._mappings:
            return script_value

        str_value = str(script_value)

        if str_value in self._mappings:
            return self._mappings[str_value]

        return script_value


def create_ui_value_mapper(config) -> ValueMapper:
    mappings_config = read_dict(config, 'values_ui_mapping', {})

    return DictBasedValueMapper(mappings_config)
