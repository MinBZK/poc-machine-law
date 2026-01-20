from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.action import Action


T = TypeVar("T", bound="Condition")


@_attrs_define
class Condition:
    """Conditional logic with test, then, and optional else

    Attributes:
        test (Union[Unset, Action]):
        then (Union['Action', Any, Unset]): Represents a value in an operation (can be a primitive value or nested
            action)
        else_ (Union['Action', Any, Unset]): Represents a value in an operation (can be a primitive value or nested
            action)
    """

    test: Union[Unset, "Action"] = UNSET
    then: Union["Action", Any, Unset] = UNSET
    else_: Union["Action", Any, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.action import Action

        test: Unset | dict[str, Any] = UNSET
        if not isinstance(self.test, Unset):
            test = self.test.to_dict()

        then: Any | Unset | dict[str, Any]
        if isinstance(self.then, Unset):
            then = UNSET
        elif isinstance(self.then, Action):
            then = self.then.to_dict()
        else:
            then = self.then

        else_: Any | Unset | dict[str, Any]
        if isinstance(self.else_, Unset):
            else_ = UNSET
        elif isinstance(self.else_, Action):
            else_ = self.else_.to_dict()
        else:
            else_ = self.else_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if test is not UNSET:
            field_dict["test"] = test
        if then is not UNSET:
            field_dict["then"] = then
        if else_ is not UNSET:
            field_dict["else"] = else_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.action import Action

        d = dict(src_dict)
        _test = d.pop("test", UNSET)
        test: Unset | Action
        if isinstance(_test, Unset):
            test = UNSET
        else:
            test = Action.from_dict(_test)

        def _parse_then(data: object) -> Union["Action", Any, Unset]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_action_value_type_0 = Action.from_dict(data)

                return componentsschemas_action_value_type_0
            except:  # noqa: E722
                pass
            return cast(Union["Action", Any, Unset], data)

        then = _parse_then(d.pop("then", UNSET))

        def _parse_else_(data: object) -> Union["Action", Any, Unset]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_action_value_type_0 = Action.from_dict(data)

                return componentsschemas_action_value_type_0
            except:  # noqa: E722
                pass
            return cast(Union["Action", Any, Unset], data)

        else_ = _parse_else_(d.pop("else", UNSET))

        condition = cls(
            test=test,
            then=then,
            else_=else_,
        )

        condition.additional_properties = d
        return condition

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
