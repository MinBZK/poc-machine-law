from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.case_status import CaseStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.case_appeal_status import CaseAppealStatus
    from ..models.case_objection_status import CaseObjectionStatus


T = TypeVar("T", bound="Case")


@_attrs_define
class Case:
    """Case

    Attributes:
        id (UUID): Identifier of a case
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.
        service (str): Specify the service that needs to be executed
        law (str): Specify the law that needs to be executed
        parameters (Any):
        claimed_result (Any):
        verified_result (Any):
        approved_claims_only (bool):
        rulespec_id (UUID): Identifier of the rulespec
        status (CaseStatus):
        approved (Union[Unset, bool]):
        objection_status (Union[Unset, CaseObjectionStatus]): Parameters to set the objection status
        appeal_status (Union[Unset, CaseAppealStatus]): Parameters to set the objection status
        claim_ids (Union[Unset, list[UUID]]):
    """

    id: UUID
    bsn: str
    service: str
    law: str
    parameters: Any
    claimed_result: Any
    verified_result: Any
    approved_claims_only: bool
    rulespec_id: UUID
    status: CaseStatus
    approved: Unset | bool = UNSET
    objection_status: Union[Unset, "CaseObjectionStatus"] = UNSET
    appeal_status: Union[Unset, "CaseAppealStatus"] = UNSET
    claim_ids: Unset | list[UUID] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        bsn = self.bsn

        service = self.service

        law = self.law

        parameters = self.parameters

        claimed_result = self.claimed_result

        verified_result = self.verified_result

        approved_claims_only = self.approved_claims_only

        rulespec_id = str(self.rulespec_id)

        status = self.status.value

        approved = self.approved

        objection_status: Unset | dict[str, Any] = UNSET
        if not isinstance(self.objection_status, Unset):
            objection_status = self.objection_status.to_dict()

        appeal_status: Unset | dict[str, Any] = UNSET
        if not isinstance(self.appeal_status, Unset):
            appeal_status = self.appeal_status.to_dict()

        claim_ids: Unset | list[str] = UNSET
        if not isinstance(self.claim_ids, Unset):
            claim_ids = []
            for claim_ids_item_data in self.claim_ids:
                claim_ids_item = str(claim_ids_item_data)
                claim_ids.append(claim_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "bsn": bsn,
                "service": service,
                "law": law,
                "parameters": parameters,
                "claimedResult": claimed_result,
                "verifiedResult": verified_result,
                "approvedClaimsOnly": approved_claims_only,
                "rulespecId": rulespec_id,
                "status": status,
            }
        )
        if approved is not UNSET:
            field_dict["approved"] = approved
        if objection_status is not UNSET:
            field_dict["objectionStatus"] = objection_status
        if appeal_status is not UNSET:
            field_dict["appealStatus"] = appeal_status
        if claim_ids is not UNSET:
            field_dict["claim_ids"] = claim_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.case_appeal_status import CaseAppealStatus
        from ..models.case_objection_status import CaseObjectionStatus

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        bsn = d.pop("bsn")

        service = d.pop("service")

        law = d.pop("law")

        parameters = d.pop("parameters")

        claimed_result = d.pop("claimedResult")

        verified_result = d.pop("verifiedResult")

        approved_claims_only = d.pop("approvedClaimsOnly")

        rulespec_id = UUID(d.pop("rulespecId"))

        status = CaseStatus(d.pop("status"))

        approved = d.pop("approved", UNSET)

        _objection_status = d.pop("objectionStatus", UNSET)
        objection_status: Unset | CaseObjectionStatus
        if isinstance(_objection_status, Unset):
            objection_status = UNSET
        else:
            objection_status = CaseObjectionStatus.from_dict(_objection_status)

        _appeal_status = d.pop("appealStatus", UNSET)
        appeal_status: Unset | CaseAppealStatus
        if isinstance(_appeal_status, Unset):
            appeal_status = UNSET
        else:
            appeal_status = CaseAppealStatus.from_dict(_appeal_status)

        claim_ids = []
        _claim_ids = d.pop("claim_ids", UNSET)
        for claim_ids_item_data in _claim_ids or []:
            claim_ids_item = UUID(claim_ids_item_data)

            claim_ids.append(claim_ids_item)

        case = cls(
            id=id,
            bsn=bsn,
            service=service,
            law=law,
            parameters=parameters,
            claimed_result=claimed_result,
            verified_result=verified_result,
            approved_claims_only=approved_claims_only,
            rulespec_id=rulespec_id,
            status=status,
            approved=approved,
            objection_status=objection_status,
            appeal_status=appeal_status,
            claim_ids=claim_ids,
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
