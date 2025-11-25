from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ClaimReject")


@_attrs_define
class ClaimReject:
    """Reject a claim

    Attributes:
        rejected_by (str): User that rejected the claim
        rejection_reason (str): Reason of the rejection
    """

    rejected_by: str
    rejection_reason: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        rejected_by = self.rejected_by

        rejection_reason = self.rejection_reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "rejectedBy": rejected_by,
                "rejectionReason": rejection_reason,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        rejected_by = d.pop("rejectedBy")

        rejection_reason = d.pop("rejectionReason")

        claim_reject = cls(
            rejected_by=rejected_by,
            rejection_reason=rejection_reason,
        )

        claim_reject.additional_properties = d
        return claim_reject

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
