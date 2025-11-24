from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="Law")


@_attrs_define
class Law:
    """Law

    Example:
        {'name': 'wet_inkomstenbelasting', 'discoverableBy': ['CITIZEN']}

    Attributes:
        name (str): Name of the law
        discoverable_by (list[str]): Who can discover this law
    """

    name: str
    discoverable_by: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        discoverable_by = self.discoverable_by

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "discoverableBy": discoverable_by,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        discoverable_by = cast(list[str], d.pop("discoverableBy"))

        law = cls(
            name=name,
            discoverable_by=discoverable_by,
        )

        law.additional_properties = d
        return law

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
