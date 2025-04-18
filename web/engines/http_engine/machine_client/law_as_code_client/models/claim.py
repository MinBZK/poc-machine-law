from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="Claim")


@_attrs_define
class Claim:
    """Claim

    Attributes:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.
        service (str): Specify the service that needs to be executed
        law (str): Specify the law that needs to be executed
        key (str):
    """

    bsn: str
    service: str
    law: str
    key: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        bsn = self.bsn

        service = self.service

        law = self.law

        key = self.key

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "bsn": bsn,
                "service": service,
                "law": law,
                "key": key,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        bsn = d.pop("bsn")

        service = d.pop("service")

        law = d.pop("law")

        key = d.pop("key")

        claim = cls(
            bsn=bsn,
            service=service,
            law=law,
            key=key,
        )

        claim.additional_properties = d
        return claim

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
