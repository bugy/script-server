import re

from model.model_helper import is_empty, fill_parameter_values
from react.properties import ObservableList, ObservableDict, Property


class TemplateProperty:
    def __init__(self, template_config, parameters: ObservableList, value_wrappers: ObservableDict, empty=None) -> None:
        self._value_property = Property(None)
        self._template_config = template_config
        self._values = value_wrappers
        self._empty = empty
        self._parameters = parameters

        pattern = re.compile(r'\${([^}]+)\}')

        search_start = 0
        script_template = ''
        required_parameters = set()

        templates = template_config if isinstance(template_config, list) else [template_config]

        for template in templates:
            if template:
                while search_start < len(template):
                    match = pattern.search(template, search_start)
                    if not match:
                        script_template += template[search_start:]
                        break
                    param_start = match.start()
                    if param_start > search_start:
                        script_template += template[search_start:param_start]

                    param_name = match.group(1)
                    required_parameters.add(param_name)

                    search_start = match.end() + 1

        self.required_parameters = tuple(required_parameters)

        self._reload()

        if self.required_parameters:
            value_wrappers.subscribe(self._value_changed)
            parameters.subscribe(self)

    def _value_changed(self, parameter, old, new):
        if parameter in self.required_parameters:
            self._reload()

    def on_add(self, parameter, index):
        if parameter.name in self.required_parameters:
            self._reload()

    def on_remove(self, parameter):
        if parameter.name in self.required_parameters:
            self._reload()

    def _reload(self):
        values_filled = True
        for param_name in self.required_parameters:
            value_wrapper = self._values.get(param_name)
            if value_wrapper is None or is_empty(value_wrapper.mapped_script_value):
                values_filled = False
                break

        if self._template_config is None:
            self.value = None
        elif values_filled:
            if isinstance(self._template_config, list):
                values = []
                for single_template in self._template_config:
                    values.append(fill_parameter_values(self._parameters, single_template, self._values))
                self.value = values
            else:
                self.value = fill_parameter_values(self._parameters, self._template_config, self._values)
        else:
            self.value = self._empty

        self._value_property.set(self.value)

    def subscribe(self, observer):
        self._value_property.subscribe(observer)

    def unsubscribe(self, observer):
        self._value_property.unsubscribe(observer)

    def get(self):
        return self._value_property.get()
