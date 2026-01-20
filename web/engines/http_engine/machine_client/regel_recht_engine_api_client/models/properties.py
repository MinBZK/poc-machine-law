from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.apply import Apply
    from ..models.base_field import BaseField
    from ..models.input_field import InputField
    from ..models.output_field import OutputField
    from ..models.properties_definitions import PropertiesDefinitions
    from ..models.source_field import SourceField


T = TypeVar("T", bound="Properties")


@_attrs_define
class Properties:
    """
    Attributes:
        parameters (Union[Unset, list['BaseField']]): Parameter fields
        sources (Union[Unset, list['SourceField']]): Source fields
        input_ (Union[Unset, list['InputField']]): Input fields
        output (Union[Unset, list['OutputField']]): Output fields
        definitions (Union[Unset, PropertiesDefinitions]): Additional definitions
        applies (Union[Unset, list['Apply']]): Application rules
    """

    parameters: Unset | list["BaseField"] = UNSET
    sources: Unset | list["SourceField"] = UNSET
    input_: Unset | list["InputField"] = UNSET
    output: Unset | list["OutputField"] = UNSET
    definitions: Union[Unset, "PropertiesDefinitions"] = UNSET
    applies: Unset | list["Apply"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        parameters: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.parameters, Unset):
            parameters = []
            for parameters_item_data in self.parameters:
                parameters_item = parameters_item_data.to_dict()
                parameters.append(parameters_item)

        sources: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.sources, Unset):
            sources = []
            for sources_item_data in self.sources:
                sources_item = sources_item_data.to_dict()
                sources.append(sources_item)

        input_: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.input_, Unset):
            input_ = []
            for input_item_data in self.input_:
                input_item = input_item_data.to_dict()
                input_.append(input_item)

        output: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.output, Unset):
            output = []
            for output_item_data in self.output:
                output_item = output_item_data.to_dict()
                output.append(output_item)

        definitions: Unset | dict[str, Any] = UNSET
        if not isinstance(self.definitions, Unset):
            definitions = self.definitions.to_dict()

        applies: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.applies, Unset):
            applies = []
            for applies_item_data in self.applies:
                applies_item = applies_item_data.to_dict()
                applies.append(applies_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if parameters is not UNSET:
            field_dict["parameters"] = parameters
        if sources is not UNSET:
            field_dict["sources"] = sources
        if input_ is not UNSET:
            field_dict["input"] = input_
        if output is not UNSET:
            field_dict["output"] = output
        if definitions is not UNSET:
            field_dict["definitions"] = definitions
        if applies is not UNSET:
            field_dict["applies"] = applies

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.apply import Apply
        from ..models.base_field import BaseField
        from ..models.input_field import InputField
        from ..models.output_field import OutputField
        from ..models.properties_definitions import PropertiesDefinitions
        from ..models.source_field import SourceField

        d = dict(src_dict)
        parameters = []
        _parameters = d.pop("parameters", UNSET)
        for parameters_item_data in _parameters or []:
            parameters_item = BaseField.from_dict(parameters_item_data)

            parameters.append(parameters_item)

        sources = []
        _sources = d.pop("sources", UNSET)
        for sources_item_data in _sources or []:
            sources_item = SourceField.from_dict(sources_item_data)

            sources.append(sources_item)

        input_ = []
        _input_ = d.pop("input", UNSET)
        for input_item_data in _input_ or []:
            input_item = InputField.from_dict(input_item_data)

            input_.append(input_item)

        output = []
        _output = d.pop("output", UNSET)
        for output_item_data in _output or []:
            output_item = OutputField.from_dict(output_item_data)

            output.append(output_item)

        _definitions = d.pop("definitions", UNSET)
        definitions: Unset | PropertiesDefinitions
        if isinstance(_definitions, Unset):
            definitions = UNSET
        else:
            definitions = PropertiesDefinitions.from_dict(_definitions)

        applies = []
        _applies = d.pop("applies", UNSET)
        for applies_item_data in _applies or []:
            applies_item = Apply.from_dict(applies_item_data)

            applies.append(applies_item)

        properties = cls(
            parameters=parameters,
            sources=sources,
            input_=input_,
            output=output,
            definitions=definitions,
            applies=applies,
        )

        properties.additional_properties = d
        return properties

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
