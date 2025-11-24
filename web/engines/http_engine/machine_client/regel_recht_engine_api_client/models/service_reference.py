from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.parameter import Parameter


T = TypeVar("T", bound="ServiceReference")


@_attrs_define
class ServiceReference:
    """
    Attributes:
        service (str): Referenced service identifier
        field (str): Field in the referenced service
        law (str): Associated law
        parameters (Union[Unset, list['Parameter']]): Service parameters
    """

    service: str
    field: str
    law: str
    parameters: Union[Unset, list["Parameter"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        service = self.service

        field = self.field

        law = self.law

        parameters: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.parameters, Unset):
            parameters = []
            for parameters_item_data in self.parameters:
                parameters_item = parameters_item_data.to_dict()
                parameters.append(parameters_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "service": service,
                "field": field,
                "law": law,
            }
        )
        if parameters is not UNSET:
            field_dict["parameters"] = parameters

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.parameter import Parameter

        d = dict(src_dict)
        service = d.pop("service")

        field = d.pop("field")

        law = d.pop("law")

        parameters = []
        _parameters = d.pop("parameters", UNSET)
        for parameters_item_data in _parameters or []:
            parameters_item = Parameter.from_dict(parameters_item_data)

            parameters.append(parameters_item)

        service_reference = cls(
            service=service,
            field=field,
            law=law,
            parameters=parameters,
        )

        service_reference.additional_properties = d
        return service_reference

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
