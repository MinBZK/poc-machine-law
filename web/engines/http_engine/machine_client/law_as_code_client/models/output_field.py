from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.temporal import Temporal
    from ..models.type_spec import TypeSpec


T = TypeVar("T", bound="OutputField")


@_attrs_define
class OutputField:
    """Output field extending BaseField

    Attributes:
        name (str): Field name
        description (str): Field description
        type_ (str): Field type
        citizen_relevance (str):
        type_spec (Union[Unset, TypeSpec]):
        temporal (Union[Unset, Temporal]):
        required (Union[None, Unset, bool]): Whether the field is required
    """

    name: str
    description: str
    type_: str
    citizen_relevance: str
    type_spec: Union[Unset, "TypeSpec"] = UNSET
    temporal: Union[Unset, "Temporal"] = UNSET
    required: Union[None, Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        type_ = self.type_

        citizen_relevance = self.citizen_relevance

        type_spec: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.type_spec, Unset):
            type_spec = self.type_spec.to_dict()

        temporal: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.temporal, Unset):
            temporal = self.temporal.to_dict()

        required: Union[None, Unset, bool]
        if isinstance(self.required, Unset):
            required = UNSET
        else:
            required = self.required

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "type": type_,
                "citizen_relevance": citizen_relevance,
            }
        )
        if type_spec is not UNSET:
            field_dict["type_spec"] = type_spec
        if temporal is not UNSET:
            field_dict["temporal"] = temporal
        if required is not UNSET:
            field_dict["required"] = required

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.temporal import Temporal
        from ..models.type_spec import TypeSpec

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        type_ = d.pop("type")

        citizen_relevance = d.pop("citizen_relevance")

        _type_spec = d.pop("type_spec", UNSET)
        type_spec: Union[Unset, TypeSpec]
        if isinstance(_type_spec, Unset):
            type_spec = UNSET
        else:
            type_spec = TypeSpec.from_dict(_type_spec)

        _temporal = d.pop("temporal", UNSET)
        temporal: Union[Unset, Temporal]
        if isinstance(_temporal, Unset):
            temporal = UNSET
        else:
            temporal = Temporal.from_dict(_temporal)

        def _parse_required(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        required = _parse_required(d.pop("required", UNSET))

        output_field = cls(
            name=name,
            description=description,
            type_=type_,
            citizen_relevance=citizen_relevance,
            type_spec=type_spec,
            temporal=temporal,
            required=required,
        )

        output_field.additional_properties = d
        return output_field

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
