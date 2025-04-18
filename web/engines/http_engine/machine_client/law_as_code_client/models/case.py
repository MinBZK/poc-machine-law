from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.case_status import CaseStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="Case")


@_attrs_define
class Case:
    """Claim

    Attributes:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.
        service (str): Specify the service that needs to be executed
        law (str): Specify the law that needs to be executed
        status (CaseStatus):
        approved (Union[Unset, bool]):
    """

    bsn: str
    service: str
    law: str
    status: CaseStatus
    approved: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        bsn = self.bsn

        service = self.service

        law = self.law

        status = self.status.value

        approved = self.approved

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "bsn": bsn,
                "service": service,
                "law": law,
                "status": status,
            }
        )
        if approved is not UNSET:
            field_dict["approved"] = approved

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        bsn = d.pop("bsn")

        service = d.pop("service")

        law = d.pop("law")

        status = CaseStatus(d.pop("status"))

        approved = d.pop("approved", UNSET)

        case = cls(
            bsn=bsn,
            service=service,
            law=law,
            status=status,
            approved=approved,
        )

        case.additional_properties = d
        return case

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
