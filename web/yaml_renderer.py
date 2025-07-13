"""
YAML to Regelspraak renderer
Converts YAML rule definitions to readable Dutch text
"""

from typing import Any


class RegelspraakRenderer:
    """Renders YAML rules in readable Dutch format"""

    def __init__(self, bwb_id: str = None):
        self.bwb_id = bwb_id
        self.colors = {
            "green": "#4CAF50",
            "blue": "#2196F3",
            "yellow": "#FFC107",
            "pink": "#E91E63",
            "gray": "#757575",
        }

    def render_rule(self, rule: dict[str, Any]) -> str:
        """Render a complete rule with all its actions"""
        html = []

        # Rule header
        if "description" in rule:
            html.append('<div class="rule-header">')
            html.append(f'<h3 class="rule-title">{rule["description"]}</h3>')
            if "rule_type" in rule:
                html.append(f'<span class="rule-type">{rule["rule_type"]}</span>')
            html.append("</div>")

        # Actions
        if "actions" in rule:
            html.append('<div class="rule-actions">')
            for action in rule["actions"]:
                html.append(self.render_action(action))
            html.append("</div>")

        return "\n".join(html)

    def render_action(self, action: dict[str, Any], indent: int = 0) -> str:
        """Render a single action"""
        indent_str = "  " * indent
        html = []

        # Handle direct assignment (no operation)
        if "output" in action and "value" in action and "operation" not in action:
            html.append(indent_str + '<div class="action-assign">')
            if "legal_basis" in action:
                html.append(self.render_legal_basis(action["legal_basis"], indent + 1))
            html.append(f'{indent_str}  De <span class="var-output">{action.get("output", "uitkomst")}</span> is')
            html.append(self.render_value(action["value"], indent + 1))
            html.append(indent_str + "</div>")
            return "\n".join(html)

        if "operation" in action:
            op = action["operation"]

            if op == "ASSIGN":
                html.append(indent_str + '<div class="action-assign">')
                if "legal_basis" in action:
                    html.append(self.render_legal_basis(action["legal_basis"], indent + 1))
                html.append(
                    f'{indent_str}  De <span class="var-output">{action.get("output", action.get("name", "uitkomst"))}</span> is'
                )
                if "value" in action:
                    html.append(self.render_value(action["value"], indent + 1))
                html.append(indent_str + "</div>")

            elif op == "IF":
                html.append(indent_str + '<div class="action-if">')
                # Add output name if present
                if "output" in action:
                    html.append(
                        f'{indent_str}  De <span class="var-output">{action.get("output", "uitkomst")}</span> is:'
                    )
                if "conditions" in action:
                    for i, condition in enumerate(action["conditions"]):
                        if i == 0:
                            html.append(indent_str + '  <div class="condition">')
                            html.append(indent_str + "    Indien ")
                        else:
                            html.append(indent_str + '  <div class="condition">')
                            html.append(indent_str + "    Anders indien ")

                        # Render test
                        if "test" in condition:
                            html.append(self.render_test(condition["test"], indent + 2))

                        # Render then
                        if "then" in condition:
                            html.append(indent_str + "    dan")
                            html.append(self.render_value(condition["then"], indent + 2))

                        html.append(indent_str + "  </div>")

                    # Render else
                    if "else" in condition:
                        html.append(indent_str + '  <div class="condition-else">')
                        html.append(indent_str + "    Anders")
                        html.append(self.render_value(condition["else"], indent + 2))
                        html.append(indent_str + "  </div>")

                html.append(indent_str + "</div>")

        return "\n".join(html)

    def render_test(self, test: dict[str, Any], indent: int = 0) -> str:
        """Render a test condition"""
        indent_str = "  " * indent
        html = []

        subject_html = self.render_value_inline(test["subject"]) if "subject" in test else ""

        op = test.get("operation", "")

        if op == "EQUALS":
            value_html = self.render_value_inline(test.get("value", ""))
            html.append(f'{indent_str}<span class="test">{subject_html} gelijk aan {value_html}</span>')
        elif op == "GREATER_THAN":
            if "values" in test:
                val1 = self.render_value_inline(test["values"][0])
                val2 = self.render_value_inline(test["values"][1])
                html.append(f'{indent_str}<span class="test">{val1} groter dan {val2}</span>')
            else:
                value_html = self.render_value_inline(test.get("value", ""))
                html.append(f'{indent_str}<span class="test">{subject_html} groter dan {value_html}</span>')
        elif op == "LESS_THAN":
            value_html = self.render_value_inline(test.get("value", ""))
            html.append(f'{indent_str}<span class="test">{subject_html} kleiner dan {value_html}</span>')
        elif op == "GREATER_OR_EQUAL":
            value_html = self.render_value_inline(test.get("value", ""))
            html.append(f'{indent_str}<span class="test">{subject_html} groter of gelijk aan {value_html}</span>')
        else:
            html.append(f'{indent_str}<span class="test">{op} {subject_html}</span>')

        return "\n".join(html)

    def render_value(self, value: Any, indent: int = 0) -> str:
        """Render a value (can be nested operations)"""
        indent_str = "  " * indent

        if isinstance(value, dict):
            if "operation" in value:
                return self.render_operation(value, indent)
            else:
                return f'{indent_str}<span class="value">{str(value)}</span>'
        elif isinstance(value, str):
            if value.startswith("$"):
                # Variable reference
                if value.isupper():
                    # Parameter
                    return f'{indent_str}<span class="var-param">{value}</span>'
                else:
                    # Input variable
                    return f'{indent_str}<span class="var-input">{value}</span>'
            else:
                return f'{indent_str}<span class="value">{value}</span>'
        elif isinstance(value, int | float):
            return f'{indent_str}<span class="value-number">{value}</span>'
        elif isinstance(value, bool):
            return f'{indent_str}<span class="value-bool">{"waar" if value else "onwaar"}</span>'
        else:
            return f'{indent_str}<span class="value">{str(value)}</span>'

    def render_value_inline(self, value: Any) -> str:
        """Render a value inline (no indentation)"""
        if isinstance(value, dict):
            if "operation" in value:
                return self.render_operation_inline(value)
            else:
                return f'<span class="value">{str(value)}</span>'
        elif isinstance(value, str):
            if value.startswith("$"):
                # Variable reference
                if value.isupper() or "_" in value:
                    # Parameter
                    return f'<span class="var-param">{value}</span>'
                else:
                    # Input variable
                    return f'<span class="var-input">{value}</span>'
            else:
                return f'<span class="value">{value}</span>'
        elif isinstance(value, int | float):
            # Format numbers nicely
            if isinstance(value, int) and value > 1000:
                # Format large numbers with dots as thousands separator
                formatted = f"{value:,}".replace(",", ".")
                return f'<span class="value-number">{formatted}</span>'
            return f'<span class="value-number">{value}</span>'
        elif isinstance(value, bool):
            return f'<span class="value-bool">{"waar" if value else "onwaar"}</span>'
        else:
            return f'<span class="value">{str(value)}</span>'

    def render_operation(self, operation: dict[str, Any], indent: int = 0) -> str:
        """Render an operation"""
        indent_str = "  " * indent
        html = []

        # Check for legal_basis in the operation
        if "legal_basis" in operation:
            html.append(self.render_legal_basis(operation["legal_basis"], indent))

        op = operation.get("operation", "")

        if op == "ADD":
            values = operation.get("values", [])
            if len(values) == 2:
                val1 = self.render_value_inline(values[0])
                val2 = self.render_value_inline(values[1])
                html.append(f"{indent_str}{val1} plus {val2}")
            else:
                html.append(indent_str + " plus ".join(self.render_value_inline(v) for v in values))
        elif op == "SUBTRACT":
            values = operation.get("values", [])
            if len(values) == 2:
                val1 = self.render_value_inline(values[0])
                val2 = self.render_value_inline(values[1])
                html.append(f"{indent_str}{val1} min {val2}")
        elif op == "MULTIPLY":
            values = operation.get("values", [])
            if len(values) == 2:
                val1 = self.render_value_inline(values[0])
                val2 = self.render_value_inline(values[1])
                html.append(f"{indent_str}{val1} keer {val2}")
        elif op == "DIVIDE":
            values = operation.get("values", [])
            if len(values) == 2:
                val1 = self.render_value_inline(values[0])
                val2 = self.render_value_inline(values[1])
                html.append(f"{indent_str}{val1} gedeeld door {val2}")
        elif op == "MAX":
            values = operation.get("values", [])
            html.append(indent_str + "maximaal " + " of ".join(self.render_value_inline(v) for v in values))
        elif op == "MIN":
            values = operation.get("values", [])
            html.append(indent_str + "minimaal " + " of ".join(self.render_value_inline(v) for v in values))
        elif op == "IF":
            # Nested IF operation
            return self.render_action(operation, indent)
        else:
            html.append(indent_str + op)

        return "\n".join(html)

    def render_operation_inline(self, operation: dict[str, Any]) -> str:
        """Render an operation inline"""
        op = operation.get("operation", "")

        if op == "ADD":
            values = operation.get("values", [])
            return "(" + " + ".join(self.render_value_inline(v) for v in values) + ")"
        elif op == "SUBTRACT":
            values = operation.get("values", [])
            if len(values) == 2:
                val1 = self.render_value_inline(values[0])
                val2 = self.render_value_inline(values[1])
                return f"({val1} - {val2})"
        elif op == "MULTIPLY":
            values = operation.get("values", [])
            if len(values) == 2:
                val1 = self.render_value_inline(values[0])
                val2 = self.render_value_inline(values[1])
                return f"({val1} × {val2})"
        elif op == "DIVIDE":
            values = operation.get("values", [])
            if len(values) == 2:
                val1 = self.render_value_inline(values[0])
                val2 = self.render_value_inline(values[1])
                return f"({val1} ÷ {val2})"
        elif op == "MIN":
            values = operation.get("values", [])
            return "het minimum van (" + " of ".join(self.render_value_inline(v) for v in values) + ")"
        elif op == "MAX":
            values = operation.get("values", [])
            return "het maximum van (" + " of ".join(self.render_value_inline(v) for v in values) + ")"
        elif op == "IF":
            # For inline IF, just return a placeholder - these should be handled differently
            return "[voorwaardelijke berekening]"
        else:
            return f"<{op}>"

    def render_legal_basis(self, legal_basis: dict[str, Any], indent: int = 0) -> str:
        """Render legal basis reference"""
        indent_str = "  " * indent
        article = legal_basis.get("article", "")
        paragraph = legal_basis.get("paragraph", "")
        bwb_id = legal_basis.get("bwb_id", self.bwb_id)

        ref = f"Artikel {article}"
        if paragraph:
            ref += f" lid {paragraph}"

        # Create link if we have BWB ID and article
        if bwb_id and article:
            link = f'<a href="/wetten/{bwb_id}/artikel/{article}" class="legal-basis-link">{ref}</a>'
            return f'{indent_str}<div class="legal-basis-inline">Op basis van {link}</div>'
        else:
            return f'{indent_str}<div class="legal-basis-inline">Op basis van {ref}</div>'

    def render_parameters(self, parameters: list[dict[str, Any]]) -> str:
        """Render parameters section"""
        html = ['<div class="parameters-section">']
        html.append("<h3>Parameters</h3>")
        html.append('<ul class="parameters-list">')

        for param in parameters:
            name = param.get("name", "")
            value = param.get("value", "")
            description = param.get("description", "")

            # Format value
            if isinstance(value, int | float):
                if isinstance(value, int) and value > 1000:
                    formatted_value = f"{value:,}".replace(",", ".")
                elif isinstance(value, float):
                    formatted_value = f"{value:.3f}".replace(".", ",")
                else:
                    formatted_value = str(value)
            else:
                formatted_value = str(value)

            html.append('<li class="parameter-item">')
            html.append(f'  <span class="param-name">{name}</span>: ')
            html.append(f'  <span class="param-value">{formatted_value}</span>')
            if description:
                html.append(f'  <span class="param-description">({description})</span>')
            html.append("</li>")

        html.append("</ul>")
        html.append("</div>")

        return "\n".join(html)

    def render_sources(self, sources: list[dict[str, Any]]) -> str:
        """Render sources section"""
        html = ['<div class="sources-section">']
        html.append("<h3>Bronnen</h3>")
        html.append('<ul class="sources-list">')

        for source in sources:
            name = source.get("name", "")
            description = source.get("description", "")
            service = source.get("service", "")
            law = source.get("legal_basis", {}).get("law", "")

            html.append('<li class="source-item">')
            html.append(f'  <span class="source-name">{description or name}</span>')
            if service:
                html.append(f'  uit <span class="source-service">{service}</span>')
            if law:
                html.append(f'  op basis van <span class="source-law">{law}</span>')
            html.append("</li>")

        html.append("</ul>")
        html.append("</div>")

        return "\n".join(html)

    def render_requirements(self, requirements: list[dict[str, Any]]) -> str:
        """Render requirements section"""
        html = ['<div class="requirements-section">']
        html.append("<h3>Voorwaarden</h3>")

        for req in requirements:
            if "all" in req:
                html.append('<div class="requirement-group">')
                html.append("<p>Alle volgende voorwaarden moeten voldaan zijn:</p>")
                html.append('<ul class="requirements-list">')
                for condition in req["all"]:
                    html.append('<li class="requirement-item">')
                    html.append(self.render_test(condition))
                    html.append("</li>")
                html.append("</ul>")
                html.append("</div>")
            elif "any" in req:
                html.append('<div class="requirement-group">')
                html.append("<p>Minstens één van de volgende voorwaarden moet voldaan zijn:</p>")
                html.append('<ul class="requirements-list">')
                for condition in req["any"]:
                    html.append('<li class="requirement-item">')
                    html.append(self.render_test(condition))
                    html.append("</li>")
                html.append("</ul>")
                html.append("</div>")

        html.append("</div>")
        return "\n".join(html)

    def render_definitions(self, definitions: dict[str, Any]) -> str:
        """Render definitions section"""
        html = ['<div class="definitions-section">']
        html.append("<h3>Definities en Parameters</h3>")
        html.append('<ul class="definitions-list">')

        for name, value in definitions.items():
            # Extract comment from the YAML if available
            comment = ""
            if isinstance(value, str) and "#" in value:
                parts = value.split("#", 1)
                value = parts[0].strip()
                comment = parts[1].strip()

            html.append('<li class="definition-item">')
            html.append(f'  <span class="definition-name">{name}</span>: ')

            # Format value based on type
            if isinstance(value, int | float):
                if isinstance(value, int) and value > 1000:
                    # Format large numbers with dots as thousands separator
                    formatted_value = f"{value:,}".replace(",", ".")
                    # Also show euro value if it appears to be in cents
                    if value > 10000:
                        euro_value = value / 100
                        formatted_value += f" (€ {euro_value:,.2f})".replace(",", ".")
                elif isinstance(value, float):
                    # Show percentage if value is between 0 and 1
                    formatted_value = f"{value:.2%}" if 0 <= value <= 1 else f"{value:.3f}".replace(".", ",")
                else:
                    formatted_value = str(value)
            else:
                formatted_value = str(value)

            html.append(f'  <span class="definition-value">{formatted_value}</span>')

            # Add comment/description if available
            if comment or (
                isinstance(value, int)
                and name
                in [
                    "MINIMUM_LEEFTIJD",
                    "KWALITEITSKORTINGSGRENS",
                    "AFTOPPINGSGRENS_1_2",
                    "AFTOPPINGSGRENS_3_PLUS",
                    "MAXIMALE_HUURGRENS",
                    "VERMOGENSGRENS_ALLEENSTAANDE",
                    "VERMOGENSGRENS_PARTNERS",
                    "INKOMENSGRENS_ALLEENSTAANDE",
                    "INKOMENSGRENS_PARTNERS",
                    "SUBSIDIEPERCENTAGE_ONDER_KWALITEITSKORTINGSGRENS",
                    "SUBSIDIEPERCENTAGE_TUSSEN_KWALITEIT_AFTOP",
                    "SUBSIDIEPERCENTAGE_BOVEN_AFTOP",
                    "MINIMUM_BASISHUUR_PERCENTAGE",
                    "MAXIMALE_SERVICEKOSTEN",
                    "KIND_VRIJSTELLING",
                    "LEEFTIJDSGRENS_KIND_INKOMEN",
                ]
            ):
                # Add known descriptions for common definitions
                descriptions = {
                    "MINIMUM_LEEFTIJD": "Minimumleeftijd voor huurtoeslag",
                    "KWALITEITSKORTINGSGRENS": "Kwaliteitskortingsgrens",
                    "AFTOPPINGSGRENS_1_2": "Aftoppingsgrens voor 1-2 persoons huishoudens",
                    "AFTOPPINGSGRENS_3_PLUS": "Aftoppingsgrens voor 3+ persoons huishoudens",
                    "MAXIMALE_HUURGRENS": "Maximale huurgrens voor huurtoeslag",
                    "VERMOGENSGRENS_ALLEENSTAANDE": "Vermogensgrens voor alleenstaanden",
                    "VERMOGENSGRENS_PARTNERS": "Vermogensgrens voor partners",
                    "INKOMENSGRENS_ALLEENSTAANDE": "Inkomensgrens voor alleenstaanden",
                    "INKOMENSGRENS_PARTNERS": "Inkomensgrens voor partners",
                    "SUBSIDIEPERCENTAGE_ONDER_KWALITEITSKORTINGSGRENS": "Subsidiepercentage onder kwaliteitskortingsgrens",
                    "SUBSIDIEPERCENTAGE_TUSSEN_KWALITEIT_AFTOP": "Subsidiepercentage tussen kwaliteitskortings- en aftoppingsgrens",
                    "SUBSIDIEPERCENTAGE_BOVEN_AFTOP": "Subsidiepercentage boven aftoppingsgrens",
                    "MINIMUM_BASISHUUR_PERCENTAGE": "Minimale eigen bijdrage als percentage van inkomen",
                    "MAXIMALE_SERVICEKOSTEN": "Maximale subsidiabele servicekosten",
                    "KIND_VRIJSTELLING": "Vrijstelling per kind voor inkomenstoets",
                    "LEEFTIJDSGRENS_KIND_INKOMEN": "Leeftijdsgrens voor kinderen in de inkomenstoets",
                }
                desc = comment or descriptions.get(name, "")
                if desc:
                    html.append(f'  <span class="definition-description">({desc})</span>')

            html.append("</li>")

        html.append("</ul>")
        html.append("</div>")

        return "\n".join(html)
