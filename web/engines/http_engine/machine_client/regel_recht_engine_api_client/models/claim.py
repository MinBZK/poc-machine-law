from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.claim_status import ClaimStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="Claim")


@_attrs_define
class Claim:
    """Claim

    Attributes:
        id (UUID): Identifier of a claim
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.
        service (str): Specify the service that needs to be executed
        law (str): Specify the law that needs to be executed
        key (str):
        new_value (Any):
        reason (str):
        claimant (str):
        status (ClaimStatus):
        case_id (Union[Unset, UUID]): Identifier of a case
        old_value (Union[Unset, Any]):
        evidence_path (Union[Unset, str]):
    """

    id: UUID
    bsn: str
    service: str
    law: str
    key: str
    new_value: Any
    reason: str
    claimant: str
    status: ClaimStatus
    case_id: Unset | UUID = UNSET
    old_value: Unset | Any = UNSET
    evidence_path: Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        bsn = self.bsn

        service = self.service

        law = self.law

        key = self.key

        new_value = self.new_value

        reason = self.reason

        claimant = self.claimant

        status = self.status.value

        case_id: Unset | str = UNSET
        if not isinstance(self.case_id, Unset):
            case_id = str(self.case_id)

        old_value = self.old_value

        evidence_path = self.evidence_path

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "bsn": bsn,
                "service": service,
                "law": law,
                "key": key,
                "newValue": new_value,
                "reason": reason,
                "claimant": claimant,
                "status": status,
            }
        )
        if case_id is not UNSET:
            field_dict["caseId"] = case_id
        if old_value is not UNSET:
            field_dict["oldValue"] = old_value
        if evidence_path is not UNSET:
            field_dict["evidencePath"] = evidence_path

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        bsn = d.pop("bsn")

        service = d.pop("service")

        law = d.pop("law")

        key = d.pop("key")

        new_value = d.pop("newValue")

        reason = d.pop("reason")

        claimant = d.pop("claimant")

        status = ClaimStatus(d.pop("status"))

        _case_id = d.pop("caseId", UNSET)
        case_id: Unset | UUID
        if isinstance(_case_id, Unset):
            case_id = UNSET
        else:
            case_id = UUID(_case_id)

        old_value = d.pop("oldValue", UNSET)

        evidence_path = d.pop("evidencePath", UNSET)

        claim = cls(
            id=id,
            bsn=bsn,
            service=service,
            law=law,
            key=key,
            new_value=new_value,
            reason=reason,
            claimant=claimant,
            status=status,
            case_id=case_id,
            old_value=old_value,
            evidence_path=evidence_path,
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
