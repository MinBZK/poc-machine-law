from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.profile_sources import ProfileSources


T = TypeVar("T", bound="Profile")


@_attrs_define
class Profile:
    """Profile

    Attributes:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.
        name (str): Name of the burger
        description (str): Description of the burger
        sources (ProfileSources): All sources for a certain profile
    """

    bsn: str
    name: str
    description: str
    sources: "ProfileSources"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        bsn = self.bsn

        name = self.name

        description = self.description

        sources = self.sources.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "bsn": bsn,
                "name": name,
                "description": description,
                "sources": sources,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.profile_sources import ProfileSources

        d = dict(src_dict)
        bsn = d.pop("bsn")

        name = d.pop("name")

        description = d.pop("description")

        sources = ProfileSources.from_dict(d.pop("sources"))

        profile = cls(
            bsn=bsn,
            name=name,
            description=description,
            sources=sources,
        )

        profile.additional_properties = d
        return profile

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
