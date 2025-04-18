from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.service import Service


T = TypeVar("T", bound="ServiceLawsDiscoverableListResponse200")


@_attrs_define
class ServiceLawsDiscoverableListResponse200:
    """
    Attributes:
        data (list['Service']): List of all services
    """

    data: list["Service"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = []
        for componentsschemas_service_list_item_data in self.data:
            componentsschemas_service_list_item = componentsschemas_service_list_item_data.to_dict()
            data.append(componentsschemas_service_list_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.service import Service

        d = dict(src_dict)
        data = []
        _data = d.pop("data")
        for componentsschemas_service_list_item_data in _data:
            componentsschemas_service_list_item = Service.from_dict(componentsschemas_service_list_item_data)

            data.append(componentsschemas_service_list_item)

        service_laws_discoverable_list_response_200 = cls(
            data=data,
        )

        service_laws_discoverable_list_response_200.additional_properties = d
        return service_laws_discoverable_list_response_200

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
