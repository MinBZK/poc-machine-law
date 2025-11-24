from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ClaimApprove")


@_attrs_define
class ClaimApprove:
    """Approve a claim

    Attributes:
        verified_by (str): User that verified the claim
        verified_value (str): Verified value for the claim
    """

    verified_by: str
    verified_value: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        verified_by = self.verified_by

        verified_value = self.verified_value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "verifiedBy": verified_by,
                "verifiedValue": verified_value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        verified_by = d.pop("verifiedBy")

        verified_value = d.pop("verifiedValue")

        claim_approve = cls(
            verified_by=verified_by,
            verified_value=verified_value,
        )

        claim_approve.additional_properties = d
        return claim_approve

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
