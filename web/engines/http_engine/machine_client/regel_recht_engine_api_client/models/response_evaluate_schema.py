from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.path_node import PathNode
    from ..models.response_evaluate_schema_input import ResponseEvaluateSchemaInput
    from ..models.response_evaluate_schema_output import ResponseEvaluateSchemaOutput


T = TypeVar("T", bound="ResponseEvaluateSchema")


@_attrs_define
class ResponseEvaluateSchema:
    """Evaluate response

    Attributes:
        output (ResponseEvaluateSchemaOutput):
        input_ (ResponseEvaluateSchemaInput):
        requirements_met (bool): Will be true when all requirements where met
        rulespec_id (UUID): Identifier of the rulespec
        missing_required (bool): Will be true when a required value is missing
        path (PathNode): path node
    """

    output: "ResponseEvaluateSchemaOutput"
    input_: "ResponseEvaluateSchemaInput"
    requirements_met: bool
    rulespec_id: UUID
    missing_required: bool
    path: "PathNode"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        output = self.output.to_dict()

        input_ = self.input_.to_dict()

        requirements_met = self.requirements_met

        rulespec_id = str(self.rulespec_id)

        missing_required = self.missing_required

        path = self.path.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "output": output,
                "input": input_,
                "requirementsMet": requirements_met,
                "rulespecId": rulespec_id,
                "missingRequired": missing_required,
                "path": path,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.path_node import PathNode
        from ..models.response_evaluate_schema_input import ResponseEvaluateSchemaInput
        from ..models.response_evaluate_schema_output import ResponseEvaluateSchemaOutput

        d = dict(src_dict)
        output = ResponseEvaluateSchemaOutput.from_dict(d.pop("output"))

        input_ = ResponseEvaluateSchemaInput.from_dict(d.pop("input"))

        requirements_met = d.pop("requirementsMet")

        rulespec_id = UUID(d.pop("rulespecId"))

        missing_required = d.pop("missingRequired")

        path = PathNode.from_dict(d.pop("path"))

        response_evaluate_schema = cls(
            output=output,
            input_=input_,
            requirements_met=requirements_met,
            rulespec_id=rulespec_id,
            missing_required=missing_required,
            path=path,
        )

        response_evaluate_schema.additional_properties = d
        return response_evaluate_schema

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
