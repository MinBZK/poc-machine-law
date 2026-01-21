from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ClaimSubmit")


@_attrs_define
class ClaimSubmit:
    """Submit a new claim

    Attributes:
        service (str): Service identifier
        key (str): Key to be claimed
        new_value (Any):
        reason (str): Reason for the claim
        claimant (str): Identity of the claimant
        law (str): Legal basis for the claim
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.
        case_id (Union[None, UUID, Unset]): Optional identifier of the related case
        old_value (Union[Unset, Any]):
        evidence_path (Union[None, Unset, str]): Path to evidence supporting the claim
        auto_approve (Union[Unset, bool]): Whether to automatically approve the claim Default: False.
    """

    service: str
    key: str
    new_value: Any
    reason: str
    claimant: str
    law: str
    bsn: str
    case_id: None | UUID | Unset = UNSET
    old_value: Unset | Any = UNSET
    evidence_path: None | Unset | str = UNSET
    auto_approve: Unset | bool = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        service = self.service

        key = self.key

        new_value = self.new_value

        reason = self.reason

        claimant = self.claimant

        law = self.law

        bsn = self.bsn

        case_id: None | Unset | str
        if isinstance(self.case_id, Unset):
            case_id = UNSET
        elif isinstance(self.case_id, UUID):
            case_id = str(self.case_id)
        else:
            case_id = self.case_id

        old_value = self.old_value

        evidence_path: None | Unset | str
        if isinstance(self.evidence_path, Unset):
            evidence_path = UNSET
        else:
            evidence_path = self.evidence_path

        auto_approve = self.auto_approve

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "service": service,
                "key": key,
                "newValue": new_value,
                "reason": reason,
                "claimant": claimant,
                "law": law,
                "bsn": bsn,
            }
        )
        if case_id is not UNSET:
            field_dict["caseId"] = case_id
        if old_value is not UNSET:
            field_dict["oldValue"] = old_value
        if evidence_path is not UNSET:
            field_dict["evidencePath"] = evidence_path
        if auto_approve is not UNSET:
            field_dict["autoApprove"] = auto_approve

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        service = d.pop("service")

        key = d.pop("key")

        new_value = d.pop("newValue")

        reason = d.pop("reason")

        claimant = d.pop("claimant")

        law = d.pop("law")

        bsn = d.pop("bsn")

        def _parse_case_id(data: object) -> None | UUID | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                case_id_type_0 = UUID(data)

                return case_id_type_0
            except:  # noqa: E722
                pass
            return cast(None | UUID | Unset, data)

        case_id = _parse_case_id(d.pop("caseId", UNSET))

        old_value = d.pop("oldValue", UNSET)

        def _parse_evidence_path(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        evidence_path = _parse_evidence_path(d.pop("evidencePath", UNSET))

        auto_approve = d.pop("autoApprove", UNSET)

        claim_submit = cls(
            service=service,
            key=key,
            new_value=new_value,
            reason=reason,
            claimant=claimant,
            law=law,
            bsn=bsn,
            case_id=case_id,
            old_value=old_value,
            evidence_path=evidence_path,
            auto_approve=auto_approve,
        )

        claim_submit.additional_properties = d
        return claim_submit

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
