from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.update_mapping import UpdateMapping


T = TypeVar("T", bound="Update")


@_attrs_define
class Update:
    """
    Attributes:
        method (str): Update method
        mapping (UpdateMapping): Field mapping configuration
    """

    method: str
    mapping: "UpdateMapping"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        method = self.method

        mapping = self.mapping.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "method": method,
                "mapping": mapping,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_mapping import UpdateMapping

        d = dict(src_dict)
        method = d.pop("method")

        mapping = UpdateMapping.from_dict(d.pop("mapping"))

        update = cls(
            method=method,
            mapping=mapping,
        )

        update.additional_properties = d
        return update

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
