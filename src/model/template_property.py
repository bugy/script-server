import re

from model.model_helper import is_empty, fill_parameter_values
from react.properties import ObservableList, ObservableDict, Property


class TemplateProperty:
    def __init__(self, template_config, parameters: ObservableList, value_wrappers: ObservableDict, empty=None) -> None:
        self._value_property = Property(None)
        self._values = value_wrappers
        self._empty = empty
        self._parameters = parameters

        pattern = re.compile(r'\${([^}]+)\}')

        search_start = 0
        script_template = ''

        self._multiple_templates = isinstance(template_config, list)
        if template_config:
            self._templates = template_config if isinstance(template_config, list) else [template_config]
        else:
            self._templates = []

        self._template_required_parameters = {}

        for template in self._templates:
            required_parameters = set()

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

            self._template_required_parameters[template] = required_parameters

        self.required_parameters = set().union(*self._template_required_parameters.values())

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
        if not self._templates:
            self.value = None
        else:
            any_values_filled = False
            values = []

            for template in self._templates:
                template_values_filled = True
                for param_name in self._template_required_parameters[template]:
                    value_wrapper = self._values.get(param_name)
                    if value_wrapper is None or is_empty(value_wrapper.mapped_script_value):
                        template_values_filled = False
                        break

                if template_values_filled:
                    values.append(fill_parameter_values(self._parameters, template, self._values))
                    any_values_filled = True

            if any_values_filled:
                if not self._multiple_templates:
                    self.value = values[0]
                else:
                    self.value = values
            else:
                self.value = self._empty

        self._value_property.set(self.value)

    def subscribe(self, observer):
        self._value_property.subscribe(observer)

    def unsubscribe(self, observer):
        self._value_property.unsubscribe(observer)

    def get(self):
        return self._value_property.get()
