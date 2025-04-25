from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="CaseSubmit")


@_attrs_define
class CaseSubmit:
    """Case

    Attributes:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.
        service (str): Specify the service that needs to be executed
        law (str): Specify the law that needs to be executed
        parameters (Any):
        claimed_result (Any):
        approved_claims_only (bool):
    """

    bsn: str
    service: str
    law: str
    parameters: Any
    claimed_result: Any
    approved_claims_only: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        bsn = self.bsn

        service = self.service

        law = self.law

        parameters = self.parameters

        claimed_result = self.claimed_result

        approved_claims_only = self.approved_claims_only

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "bsn": bsn,
                "service": service,
                "law": law,
                "parameters": parameters,
                "claimedResult": claimed_result,
                "approvedClaimsOnly": approved_claims_only,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        bsn = d.pop("bsn")

        service = d.pop("service")

        law = d.pop("law")

        parameters = d.pop("parameters")

        claimed_result = d.pop("claimedResult")

        approved_claims_only = d.pop("approvedClaimsOnly")

        case_submit = cls(
            bsn=bsn,
            service=service,
            law=law,
            parameters=parameters,
            claimed_result=claimed_result,
            approved_claims_only=approved_claims_only,
        )

        case_submit.additional_properties = d
        return case_submit

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
