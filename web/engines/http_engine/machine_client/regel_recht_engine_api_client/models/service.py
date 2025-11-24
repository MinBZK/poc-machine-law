from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.law import Law


T = TypeVar("T", bound="Service")


@_attrs_define
class Service:
    """Service

    Example:
        {'name': 'BELASTINGDIENST', 'laws': [{'name': 'wet_inkomstenbelasting', 'discoverableBy': ['CITIZEN']}]}

    Attributes:
        name (str): Service name
        laws (list['Law']):
    """

    name: str
    laws: list["Law"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        laws = []
        for laws_item_data in self.laws:
            laws_item = laws_item_data.to_dict()
            laws.append(laws_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "laws": laws,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.law import Law

        d = dict(src_dict)
        name = d.pop("name")

        laws = []
        _laws = d.pop("laws")
        for laws_item_data in _laws:
            laws_item = Law.from_dict(laws_item_data)

            laws.append(laws_item)

        service = cls(
            name=name,
            laws=laws,
        )

        service.additional_properties = d
        return service

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
