import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.evaluate_input import EvaluateInput
    from ..models.evaluate_parameters import EvaluateParameters


T = TypeVar("T", bound="Evaluate")


@_attrs_define
class Evaluate:
    """Evaluate.

    Example:
        {'service': 'TOESLAGEN', 'law': 'zorgtoeslagwet'}

    Attributes:
        service (str): Specify the service that needs to be executed
        law (str): Specify the law that needs to be executed
        parameters (Union[Unset, EvaluateParameters]):
        date (Union[Unset, datetime.date]): Can be used to overwrite the date used by the service Example: 2025-01-31.
        input_ (Union[Unset, EvaluateInput]):
        output (Union[Unset, str]): specify a requested output value
        approved (Union[Unset, bool]): only use approved claims, default to true
    """

    service: str
    law: str
    parameters: Union[Unset, "EvaluateParameters"] = UNSET
    date: Union[Unset, datetime.date] = UNSET
    input_: Union[Unset, "EvaluateInput"] = UNSET
    output: Union[Unset, str] = UNSET
    approved: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        service = self.service

        law = self.law

        parameters: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.parameters, Unset):
            parameters = self.parameters.to_dict()

        date: Union[Unset, str] = UNSET
        if not isinstance(self.date, Unset):
            date = self.date.isoformat()

        input_: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.input_, Unset):
            input_ = self.input_.to_dict()

        output = self.output

        approved = self.approved

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "service": service,
                "law": law,
            }
        )
        if parameters is not UNSET:
            field_dict["parameters"] = parameters
        if date is not UNSET:
            field_dict["date"] = date
        if input_ is not UNSET:
            field_dict["input"] = input_
        if output is not UNSET:
            field_dict["output"] = output
        if approved is not UNSET:
            field_dict["approved"] = approved

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.evaluate_input import EvaluateInput
        from ..models.evaluate_parameters import EvaluateParameters

        d = dict(src_dict)
        service = d.pop("service")

        law = d.pop("law")

        _parameters = d.pop("parameters", UNSET)
        parameters: Union[Unset, EvaluateParameters]
        if isinstance(_parameters, Unset):
            parameters = UNSET
        else:
            parameters = EvaluateParameters.from_dict(_parameters)

        _date = d.pop("date", UNSET)
        date: Union[Unset, datetime.date]
        if isinstance(_date, Unset):
            date = UNSET
        else:
            date = isoparse(_date).date()

        _input_ = d.pop("input", UNSET)
        input_: Union[Unset, EvaluateInput]
        if isinstance(_input_, Unset):
            input_ = UNSET
        else:
            input_ = EvaluateInput.from_dict(_input_)

        output = d.pop("output", UNSET)

        approved = d.pop("approved", UNSET)

        evaluate = cls(
            service=service,
            law=law,
            parameters=parameters,
            date=date,
            input_=input_,
            output=output,
            approved=approved,
        )

        evaluate.additional_properties = d
        return evaluate

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
