from typing import TYPE_CHECKING

import pandas as pd

from ..evaluation_result import EvaluationResult, create_result
from .source_reference import SourceReference

if TYPE_CHECKING:
    from ..context import NrmlRuleContext


class TableValueProvider:
    """Provider for table-based data sources"""

    def __init__(self, dataframes: dict[str, pd.DataFrame]) -> None:
        self.dataframes = dataframes
        self._source_references: dict[str, SourceReference] = {
            "NATIONALITEIT": SourceReference.from_dict(
                {
                    "table": "personen",
                    "field": "nationaliteit",
                    "select_on": [
                        {
                            "name": "bsn",
                            "description": "Burgerservicenummer van de persoon",
                            "type": "string",
                            "value": "bsn",
                        }
                    ],
                }
            )
        }
        self.providable_values = self._compute_providable_values()

    def _compute_providable_values(self) -> set[str]:
        """Compute set of values that this provider can provide from source references"""
        return {key.upper() for key in self._source_references}

    def can_provide_value(self, name: str) -> bool:
        """Check if the provider can provide a value for the given name"""
        return name.upper() in self.providable_values

    def get_value(self, value_name: str, context: "NrmlRuleContext") -> EvaluationResult:
        """Get value from dataframe by name and wrap in EvaluationResult"""
        # Get source reference for the value
        value_name_upper = value_name.upper()
        source_ref = self._source_references.get(value_name_upper)

        if not source_ref:
            return create_result(
                success=False,
                error=f"No source reference found for '{value_name}'",
                source="TableValueProvider",
                action="GET VALUE",
            )

        # Get the dataframe for the table
        dataframe = self.dataframes.get(source_ref.table)
        if dataframe is None or dataframe.empty:
            return create_result(
                success=False,
                error=f"Dataframe '{source_ref.table}' is empty or not found",
                source="TableValueProvider",
                action="GET VALUE",
            )

        # Filter dataframe using select_on fields
        filtered_df = dataframe
        for select_on in source_ref.select_on:
            # Extract parameter name from value (e.g., "$BSN" → "BSN")
            param_name = select_on.value.upper()

            # Get parameter value from context (case-insensitive)
            param_value = context.get_parameter_value(param_name)
            if param_value is None:
                return create_result(
                    success=False,
                    error=f"Parameter '{param_name}' not found in context",
                    source="TableValueProvider",
                    action="GET_VALUE",
                )

            # Filter dataframe
            filtered_df = filtered_df[filtered_df[select_on.name] == param_value]

        # Check if any rows match the filter
        if filtered_df.empty:
            return create_result(
                success=False,
                error=f"No rows found in table '{source_ref.table}' matching the filter criteria",
                source="TableValueProvider",
                action="GET_VALUE",
            )

        # Find the column with matching field name (case-insensitive)
        column_name = None
        for col in filtered_df.columns:
            if str(col).upper() == source_ref.field.upper():
                column_name = col
                break

        if column_name is None:
            return create_result(
                success=False,
                error=f"Field '{source_ref.field}' not found in table '{source_ref.table}'",
                source="TableValueProvider",
                action="GET_VALUE",
            )

        # Get the value from the first row of the matched column
        value = filtered_df[column_name].iloc[0]

        return create_result(
            success=True,
            value=value,
            source="TableValueProvider",
            action=f"GET_VALUE: Found value for {value_name} in '{source_ref.table}.{column_name}'",
        )
