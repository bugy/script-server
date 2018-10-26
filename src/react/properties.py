import itertools
from collections import UserList, UserDict

from typing import Optional, Iterable as Iterable, Mapping as Mapping, TypeVar

_T = TypeVar('_T')
_KT = TypeVar('_KT')
_VT = TypeVar('_VT')


class Property:
    def __init__(self, value=None):
        self._value = value
        self._observers = []
        self.bound = False

    def subscribe(self, observer):
        self._observers.append(observer)

    def unsubscribe(self, observer):
        self._observers.remove(observer)

    def set(self, new_value):
        if self.bound:
            raise Exception('Failed to set value to bound property')
        self._set_internal(new_value)

    def _set_internal(self, new_value):
        old_value = self._value

        if old_value == new_value:
            return

        self._value = new_value

        for observer in self._observers:
            observer(old_value, new_value)

    def get(self):
        return self._value

    def bind(self, another_property, map_function=None):
        def binder(old_value, new_value):
            if map_function:
                value = map_function(new_value)
            else:
                value = new_value

            self._set_internal(value)

        another_property.subscribe(binder)
        binder(None, another_property.get())


class ObservableList(UserList):
    def __init__(self, initlist: Optional[Iterable[_T]] = None) -> None:
        super().__init__()
        self._observers = []

        if initlist:
            self.extend(initlist)

    def subscribe(self, observer):
        self._observers.append(observer)

    def append(self, item: _T) -> None:
        super().append(item)

        for observer in self._observers:
            observer.on_add(item, len(self.data) - 1)

    def insert(self, i: int, item: _T) -> None:
        super().insert(i, item)

        for observer in self._observers:
            observer.on_add(item, i)

    def pop(self, i: int = ...) -> _T:
        item = super().pop(i)

        for observer in self._observers:
            observer.on_remove(item)

        return item

    def remove(self, item: _T) -> None:
        super().remove(item)

        for observer in self._observers:
            observer.on_remove(item)

    def clear(self) -> None:
        copy = list(self.data)

        super().clear()

        for item in copy:
            for observer in self._observers:
                observer.on_remove(item)

    def extend(self, other: Iterable[_T]) -> None:
        first_index = len(self.data)

        super().extend(other)

        for i, item in enumerate(other):
            for observer in self._observers:
                observer.on_add(item, first_index + i)


class ObservableDict(UserDict):
    def __init__(self, dict: Optional[Mapping[_KT, _VT]] = None, **kwargs: _VT) -> None:
        super().__init__(**kwargs)
        self._observers = []

        if dict:
            self.update(dict)

    def subscribe(self, observer):
        self._observers.append(observer)

    def unsubscribe(self, observer):
        if observer in self._observers:
            self._observers.remove(observer)

    def set(self, another_dict):
        old_values = dict(self)

        obsolete_keys = {key for key in self.keys() if key not in another_dict}
        for key in obsolete_keys:
            super().__delitem__(key)

        for key, value in another_dict.items():
            super().__setitem__(key, value)

        if self._observers:
            for obsolete_key in obsolete_keys:
                old_value = old_values[obsolete_key]
                for observer in self._observers:
                    observer(obsolete_key, old_value, None)

            for key, value in self.items():
                old_value = old_values.get(key)
                if old_value != value:
                    for observer in self._observers:
                        observer(key, old_value, value)

    def __setitem__(self, key: _KT, item: _VT) -> None:
        old_value = self.get(key)

        super().__setitem__(key, item)

        if self._observers:
            for observer in self._observers:
                observer(key, old_value, item)

    def __delitem__(self, key: _KT) -> None:
        old_value = self.get(key)

        super().__delitem__(key)

        if old_value is None:
            return

        if self._observers:
            for observer in self._observers:
                observer(key, old_value, None)


def observable_fields(*fields):
    def wrapper(cls):

        def subscribe(self, listener):
            if not hasattr(self, '_listeners'):
                setattr(self, '_listeners', [])
            self._listeners.append(listener)

        setattr(cls, 'subscribe', subscribe)

        for field_name in fields:
            prop_name = field_name + '_prop'

            class ObservableProperty:
                def __init__(self, prop_name):
                    self._prop_name = prop_name

                def __get__(self, instance, type=None):
                    if self._prop_name not in instance.__dict__:
                        p = Property()
                        setattr(instance, self._prop_name, p)
                        return p

                    return instance.__dict__[self._prop_name]

            class ObservableValueProperty:
                def __init__(self, prop_name, field_name):
                    self._prop_name = prop_name
                    self._field_name = field_name

                def __get__(self, instance, type=None):
                    return getattr(instance, self._prop_name).get()

                def __set__(self, instance, value, type=None):
                    property = getattr(instance, self._prop_name)
                    old_value = property.get()
                    property.set(value)

                    if old_value != value:
                        if hasattr(instance, '_listeners'):
                            for listener in instance._listeners:
                                listener(self._field_name, old_value, value)

            setattr(cls, prop_name, ObservableProperty(prop_name))
            setattr(cls, field_name, ObservableValueProperty(prop_name, field_name))

        return cls

    return wrapper


def mapped_property(property, map_function):
    result = Property()

    def updater(old_value, new_value):
        new_mapped = map_function(new_value)
        result.set(new_mapped)

    property.subscribe(updater)
    return result
