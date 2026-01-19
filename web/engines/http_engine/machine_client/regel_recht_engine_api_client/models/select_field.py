from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.action import Action


T = TypeVar("T", bound="SelectField")


@_attrs_define
class SelectField:
    """
    Attributes:
        name (str): Field name
        description (str): Field description
        type_ (str): Field type
        value (Union['Action', Any]): Represents a value in an operation (can be a primitive value or nested action)
    """

    name: str
    description: str
    type_: str
    value: Union["Action", Any]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.action import Action

        name = self.name

        description = self.description

        type_ = self.type_

        value: Union[Any, dict[str, Any]]
        if isinstance(self.value, Action):
            value = self.value.to_dict()
        else:
            value = self.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "type": type_,
                "value": value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.action import Action

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        type_ = d.pop("type")

        def _parse_value(data: object) -> Union["Action", Any]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_action_value_type_0 = Action.from_dict(data)

                return componentsschemas_action_value_type_0
            except:  # noqa: E722
                pass
            return cast(Union["Action", Any], data)

        value = _parse_value(d.pop("value"))

        select_field = cls(
            name=name,
            description=description,
            type_=type_,
            value=value,
        )

        select_field.additional_properties = d
        return select_field

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
