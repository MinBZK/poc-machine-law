"""
XML parser for DMN 1.3 files.

Parses DMN XML into Python data structures defined in models.py.
"""
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional

from .exceptions import DMNParseError
from .models import (
    BusinessKnowledgeModel,
    DecisionService,
    DecisionTable,
    DecisionTableInput,
    DecisionTableOutput,
    DecisionTableRule,
    DMNDecision,
    DMNImport,
    DMNInput,
    DMNOutput,
    DMNSpec,
    ExpressionType,
    HitPolicy,
    LiteralExpression,
)

# DMN 1.3 namespace
DMN_NS = {
    'dmn': 'https://www.omg.org/spec/DMN/20191111/MODEL/',
    'feel': 'https://www.omg.org/spec/DMN/20191111/FEEL/',
}


class DMNXMLParser:
    """Parses DMN XML files into DMNSpec objects."""

    def __init__(self):
        self.namespace_map = DMN_NS

    def parse(self, file_path: Path) -> DMNSpec:
        """
        Parse a DMN XML file.

        Args:
            file_path: Path to the DMN file

        Returns:
            Parsed DMNSpec object

        Raises:
            DMNParseError: If parsing fails
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Extract namespace if different from default
            if root.tag.startswith('{'):
                actual_ns = root.tag[1:].split('}')[0]
                if 'DMN' in actual_ns:
                    self.namespace_map['dmn'] = actual_ns

            return self._parse_definitions(root, file_path)

        except ET.ParseError as e:
            raise DMNParseError(f"Failed to parse DMN XML: {e}") from e
        except Exception as e:
            raise DMNParseError(f"Unexpected error parsing DMN: {e}") from e

    def _parse_definitions(self, root: ET.Element, file_path: Path) -> DMNSpec:
        """Parse the root definitions element."""
        dmn_id = root.get('id', 'unknown')
        name = root.get('name', 'Unnamed DMN')
        namespace = root.get('namespace', '')
        exporter = root.get('exporter')

        spec = DMNSpec(
            id=dmn_id,
            name=name,
            namespace=namespace,
            exporter=exporter,
            file_path=file_path,
        )

        # Parse imports first
        for import_elem in root.findall('dmn:import', self.namespace_map):
            dmn_import = self._parse_import(import_elem)
            spec.imports.append(dmn_import)

        # Parse input data
        for input_elem in root.findall('dmn:inputData', self.namespace_map):
            dmn_input = self._parse_input_data(input_elem)
            spec.inputs[dmn_input.id] = dmn_input

        # Parse Business Knowledge Models
        for bkm_elem in root.findall('dmn:businessKnowledgeModel', self.namespace_map):
            bkm = self._parse_bkm(bkm_elem)
            spec.bkms[bkm.id] = bkm

        # Parse decisions
        for decision_elem in root.findall('dmn:decision', self.namespace_map):
            decision = self._parse_decision(decision_elem)
            spec.decisions[decision.id] = decision

        # Parse decision services
        for service_elem in root.findall('dmn:decisionService', self.namespace_map):
            service = self._parse_decision_service(service_elem)
            spec.decision_services[service.id] = service

        return spec

    def _parse_import(self, elem: ET.Element) -> DMNImport:
        """Parse an import element."""
        return DMNImport(
            namespace=elem.get('namespace', ''),
            location_uri=elem.get('locationURI', ''),
            import_type=elem.get('importType', ''),
        )

    def _parse_input_data(self, elem: ET.Element) -> DMNInput:
        """Parse an input data element."""
        input_id = elem.get('id', '')
        name = elem.get('name', '')

        # Get variable name from variable element
        var_elem = elem.find('dmn:variable', self.namespace_map)
        if var_elem is not None:
            var_name = var_elem.get('name', name.lower().replace(' ', '_'))
            type_ref = var_elem.get('typeRef', 'Any')
        else:
            var_name = name.lower().replace(' ', '_')
            type_ref = 'Any'

        return DMNInput(
            id=input_id,
            name=name,
            variable_name=var_name,
            type_ref=type_ref,
        )

    def _parse_bkm(self, elem: ET.Element) -> BusinessKnowledgeModel:
        """Parse a Business Knowledge Model."""
        bkm_id = elem.get('id', '')
        name = elem.get('name', '')

        # Get variable
        var_elem = elem.find('dmn:variable', self.namespace_map)
        if var_elem is not None:
            var_name = var_elem.get('name', name.lower().replace(' ', '_'))
            type_ref = var_elem.get('typeRef', 'Any')
        else:
            var_name = name.lower().replace(' ', '_')
            type_ref = 'Any'

        # Parse encapsulated logic
        encap_elem = elem.find('dmn:encapsulatedLogic', self.namespace_map)
        parameters = []
        expression = None

        if encap_elem is not None:
            # Parse formal parameters
            for param_elem in encap_elem.findall('dmn:formalParameter', self.namespace_map):
                param_name = param_elem.get('name', '')
                param_type = param_elem.get('typeRef', 'Any')
                parameters.append(DMNInput(
                    id=f"{bkm_id}_param_{param_name}",
                    name=param_name,
                    variable_name=param_name,
                    type_ref=param_type,
                ))

            # Parse expression
            lit_expr_elem = encap_elem.find('dmn:literalExpression', self.namespace_map)
            if lit_expr_elem is not None:
                expression = self._parse_literal_expression(lit_expr_elem)

        return BusinessKnowledgeModel(
            id=bkm_id,
            name=name,
            variable_name=var_name,
            parameters=parameters,
            expression=expression,
            type_ref=type_ref,
        )

    def _parse_decision(self, elem: ET.Element) -> DMNDecision:
        """Parse a decision element."""
        decision_id = elem.get('id', '')
        name = elem.get('name', '')

        # Get variable
        var_elem = elem.find('dmn:variable', self.namespace_map)
        if var_elem is not None:
            var_name = var_elem.get('name', name.lower().replace(' ', '_'))
            type_ref = var_elem.get('typeRef', 'Any')
        else:
            var_name = name.lower().replace(' ', '_')
            type_ref = 'Any'

        # Parse information requirements (inputs and decisions)
        required_inputs = []
        required_decisions = []

        for info_req_elem in elem.findall('dmn:informationRequirement', self.namespace_map):
            # Check for required input
            req_input_elem = info_req_elem.find('dmn:requiredInput', self.namespace_map)
            if req_input_elem is not None:
                href = req_input_elem.get('href', '')
                if href.startswith('#'):
                    required_inputs.append(href[1:])

            # Check for required decision
            req_decision_elem = info_req_elem.find('dmn:requiredDecision', self.namespace_map)
            if req_decision_elem is not None:
                href = req_decision_elem.get('href', '')
                if href.startswith('#'):
                    required_decisions.append(href[1:])

        # Parse knowledge requirements (BKMs)
        required_knowledge = []
        for know_req_elem in elem.findall('dmn:knowledgeRequirement', self.namespace_map):
            req_know_elem = know_req_elem.find('dmn:requiredKnowledge', self.namespace_map)
            if req_know_elem is not None:
                href = req_know_elem.get('href', '')
                if href.startswith('#'):
                    required_knowledge.append(href[1:])

        # Parse expression (decision table or literal expression)
        expression = None
        expression_type = ExpressionType.LITERAL

        # Check for decision table
        dt_elem = elem.find('dmn:decisionTable', self.namespace_map)
        if dt_elem is not None:
            expression = self._parse_decision_table(dt_elem)
            expression_type = ExpressionType.DECISION_TABLE

        # Check for literal expression
        if expression is None:
            lit_expr_elem = elem.find('dmn:literalExpression', self.namespace_map)
            if lit_expr_elem is not None:
                expression = self._parse_literal_expression(lit_expr_elem)
                expression_type = ExpressionType.LITERAL

        return DMNDecision(
            id=decision_id,
            name=name,
            variable_name=var_name,
            expression_type=expression_type,
            expression=expression,
            required_inputs=required_inputs,
            required_decisions=required_decisions,
            required_knowledge=required_knowledge,
            type_ref=type_ref,
        )

    def _parse_decision_table(self, elem: ET.Element) -> DecisionTable:
        """Parse a decision table."""
        hit_policy_str = elem.get('hitPolicy', 'UNIQUE')
        try:
            hit_policy = HitPolicy(hit_policy_str)
        except ValueError:
            hit_policy = HitPolicy.UNIQUE

        # Parse inputs
        inputs = []
        for input_elem in elem.findall('dmn:input', self.namespace_map):
            dt_input = self._parse_decision_table_input(input_elem)
            inputs.append(dt_input)

        # Parse outputs
        outputs = []
        for output_elem in elem.findall('dmn:output', self.namespace_map):
            dt_output = self._parse_decision_table_output(output_elem)
            outputs.append(dt_output)

        # Parse rules
        rules = []
        for rule_elem in elem.findall('dmn:rule', self.namespace_map):
            rule = self._parse_decision_table_rule(rule_elem)
            rules.append(rule)

        return DecisionTable(
            hit_policy=hit_policy,
            inputs=inputs,
            outputs=outputs,
            rules=rules,
        )

    def _parse_decision_table_input(self, elem: ET.Element) -> DecisionTableInput:
        """Parse a decision table input column."""
        input_id = elem.get('id', '')
        label = elem.get('label', '')

        # Parse input expression
        expr_elem = elem.find('dmn:inputExpression', self.namespace_map)
        input_expr = ''
        type_ref = 'Any'

        if expr_elem is not None:
            type_ref = expr_elem.get('typeRef', 'Any')
            text_elem = expr_elem.find('dmn:text', self.namespace_map)
            if text_elem is not None and text_elem.text:
                input_expr = text_elem.text.strip()

        return DecisionTableInput(
            id=input_id,
            label=label,
            input_expression=input_expr,
            type_ref=type_ref,
        )

    def _parse_decision_table_output(self, elem: ET.Element) -> DecisionTableOutput:
        """Parse a decision table output column."""
        output_id = elem.get('id', '')
        label = elem.get('label', '')
        name = elem.get('name', label.lower().replace(' ', '_'))
        type_ref = elem.get('typeRef', 'Any')

        return DecisionTableOutput(
            id=output_id,
            label=label,
            name=name,
            type_ref=type_ref,
        )

    def _parse_decision_table_rule(self, elem: ET.Element) -> DecisionTableRule:
        """Parse a decision table rule."""
        rule_id = elem.get('id', '')

        # Parse input entries
        input_entries = []
        for input_entry_elem in elem.findall('dmn:inputEntry', self.namespace_map):
            text_elem = input_entry_elem.find('dmn:text', self.namespace_map)
            if text_elem is not None and text_elem.text:
                input_entries.append(text_elem.text.strip())
            else:
                input_entries.append('-')  # Default "any" value

        # Parse output entries
        output_entries = []
        for output_entry_elem in elem.findall('dmn:outputEntry', self.namespace_map):
            text_elem = output_entry_elem.find('dmn:text', self.namespace_map)
            if text_elem is not None and text_elem.text:
                output_entries.append(text_elem.text.strip())
            else:
                output_entries.append('')

        return DecisionTableRule(
            id=rule_id,
            input_entries=input_entries,
            output_entries=output_entries,
        )

    def _parse_literal_expression(self, elem: ET.Element) -> LiteralExpression:
        """Parse a literal expression."""
        type_ref = elem.get('typeRef', 'Any')
        text_elem = elem.find('dmn:text', self.namespace_map)

        text = ''
        if text_elem is not None and text_elem.text:
            text = text_elem.text.strip()

        return LiteralExpression(text=text, type_ref=type_ref)

    def _parse_decision_service(self, elem: ET.Element) -> DecisionService:
        """Parse a decision service."""
        service_id = elem.get('id', '')
        name = elem.get('name', '')

        # Parse output decisions
        output_decisions = []
        for output_elem in elem.findall('dmn:outputDecision', self.namespace_map):
            href = output_elem.get('href', '')
            if href.startswith('#'):
                output_decisions.append(href[1:])

        # Parse input data
        input_data = []
        for input_elem in elem.findall('dmn:inputData', self.namespace_map):
            href = input_elem.get('href', '')
            if href.startswith('#'):
                input_data.append(href[1:])

        return DecisionService(
            id=service_id,
            name=name,
            output_decisions=output_decisions,
            input_data=input_data,
        )
