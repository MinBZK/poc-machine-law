"""
YAML to Regelspraak renderer
Converts YAML rule definitions to readable Dutch text
"""

from typing import Any


class RegelspraakRenderer:
    """Renders YAML rules in readable Dutch format"""

    def __init__(self, bwb_id: str = None, law_content: dict = None):
        self.bwb_id = bwb_id
        self.law_content = law_content or {}
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
        if "actions" in rule:
            for action in rule["actions"]:
                html.append(self.render_action(action))
        return "\n".join(html)

    def render_requirements(self, requirements: list[dict[str, Any]]) -> str:
        """Render requirements section"""
        if not requirements:
            return ""

        html = [
            '<div class="requirements-section" style="background: rgba(30,41,59,0.5); padding: 15px; border-radius: 6px; border: 1px solid #334155;">'
        ]
        html.append('<ul style="list-style: none; padding: 0; margin: 0;">')

        for req in requirements:
            html.append('  <li style="margin-bottom: 0.5rem;">')

            # Handle different requirement formats
            if "description" in req:
                html.append(f"    {req.get('description', '')}")
            elif "all" in req:
                # Handle test-based requirements
                html.append('    <div style="color: #e2e8f0;">Alle volgende voorwaarden moeten voldaan zijn:</div>')
                html.append('    <ul style="list-style: none; padding: 0; margin-left: 20px; margin-top: 5px;">')
                for test in req["all"]:
                    html.append('      <li style="margin-bottom: 5px;">')
                    html.append(self.render_test_full(test, indent=3))
                    html.append("      </li>")
                html.append("    </ul>")
            elif "any" in req:
                # Handle "any" requirements
                html.append('    <div style="color: #e2e8f0;">Een van de volgende voorwaarden moet voldaan zijn:</div>')
                html.append('    <ul style="list-style: none; padding: 0; margin-left: 20px; margin-top: 5px;">')
                for test in req["any"]:
                    html.append('      <li style="margin-bottom: 5px;">')
                    html.append(self.render_test_full(test, indent=3))
                    html.append("      </li>")
                html.append("    </ul>")
            elif "operation" in req:
                # Single test requirement
                html.append(self.render_test_full(req, indent=2))

            if "legal_basis" in req:
                html.append(self.render_legal_basis(req["legal_basis"], indent=2))
            html.append("  </li>")

        html.append("</ul>")
        html.append("</div>")
        return "\n".join(html)

    def render_action(self, action: dict[str, Any], indent: int = 0) -> str:
        """Render a single action with ALL its details including nested operations"""
        indent_str = "  " * indent
        html = []

        # Start the action container
        html.append(
            indent_str
            + '<div class="action-container" style="margin-bottom: 15px; padding: 12px; background: rgba(30,41,59,0.5); border-radius: 6px; border: 1px solid #334155;">'
        )

        # Show the output field
        if "output" in action:
            html.append(
                f'{indent_str}  <div style="font-weight: 600; color: #67e8f9; margin-bottom: 8px;">Output: <span class="var-output">{action["output"]}</span></div>'
            )

        # Show top-level legal basis if exists
        if "legal_basis" in action:
            html.append(self.render_legal_basis(action["legal_basis"], indent + 1))

        # Render based on action type
        if "value" in action and "operation" not in action:
            # Simple assignment
            html.append(f'{indent_str}  <div style="margin-top: 8px;">De waarde wordt toegekend:</div>')
            html.append(self.render_value_full(action["value"], indent + 1))

        elif "operation" in action:
            op = action["operation"]

            if op == "IF":
                html.append(self.render_if_operation_full(action, indent + 1))
            elif op in ["ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "MIN", "MAX"]:
                html.append(self.render_arithmetic_operation_full(action, indent + 1))
            else:
                # Generic operation rendering
                html.append(f'{indent_str}  <div style="margin-top: 8px;">Berekening: {op}</div>')
                if "values" in action:
                    html.append(f'{indent_str}  <div style="margin-left: 15px; margin-top: 5px;">Waarden:</div>')
                    for val in action["values"]:
                        html.append(self.render_value_full(val, indent + 2))
                if "value" in action:
                    html.append(self.render_value_full(action["value"], indent + 2))

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
            if "values" in test:
                val1 = self.render_value_inline(test["values"][0])
                val2 = self.render_value_inline(test["values"][1])
                html.append(f'{indent_str}<span class="test">{val1} kleiner dan {val2}</span>')
            else:
                value_html = self.render_value_inline(test.get("value", ""))
                html.append(f'{indent_str}<span class="test">{subject_html} kleiner dan {value_html}</span>')
        elif op == "NOT_EQUALS":
            value_html = self.render_value_inline(test.get("value", ""))
            html.append(f'{indent_str}<span class="test">{subject_html} niet gelijk aan {value_html}</span>')
        elif op == "IS_TRUE":
            html.append(f'{indent_str}<span class="test">{subject_html} waar is</span>')
        elif op == "IS_FALSE":
            html.append(f'{indent_str}<span class="test">{subject_html} niet waar is</span>')
        elif op == "IN":
            values_html = ", ".join(self.render_value_inline(v) for v in test.get("values", []))
            html.append(f'{indent_str}<span class="test">{subject_html} een van [{values_html}] is</span>')
        elif op == "NOT_IN":
            values_html = ", ".join(self.render_value_inline(v) for v in test.get("values", []))
            html.append(f'{indent_str}<span class="test">{subject_html} geen van [{values_html}] is</span>')
        elif op == "AND":
            parts = []
            for sub_test in test.get("tests", []):
                parts.append(self.render_test(sub_test, 0).strip())
            html.append(f'{indent_str}<span class="test">(' + " EN ".join(parts) + ")</span>")
        elif op == "OR":
            parts = []
            for sub_test in test.get("tests", []):
                parts.append(self.render_test(sub_test, 0).strip())
            html.append(f'{indent_str}<span class="test">(' + " OF ".join(parts) + ")</span>")

        return "\n".join(html)

    def render_value(self, value: Any, indent: int = 0) -> str:
        """Render a value (can be literal, reference, or operation)"""
        indent_str = "  " * indent

        if isinstance(value, dict):
            if "parameter" in value:
                return f'{indent_str}    <span class="var-param">${value["parameter"]}</span>'
            elif "input" in value:
                return f'{indent_str}    <span class="var-input">{value["input"]}</span>'
            elif "operation" in value:
                return indent_str + "    " + self.render_operation(value)
            elif "output" in value:
                return f'{indent_str}    <span class="var-output">{value["output"]}</span>'
            elif "value" in value:
                return self.render_value(value["value"], indent)
        elif isinstance(value, int | float):
            return f'{indent_str}    <span class="value-number">{value}</span>'
        elif isinstance(value, bool):
            return f'{indent_str}    <span class="value-bool">{"waar" if value else "niet waar"}</span>'
        elif isinstance(value, str):
            return f'{indent_str}    "{value}"'
        else:
            return f"{indent_str}    {value}"

    def render_value_inline(self, value: Any) -> str:
        """Render a value inline (for use in sentences)"""
        if isinstance(value, dict):
            if "parameter" in value:
                return f'<span class="var-param">${value["parameter"]}</span>'
            elif "input" in value:
                return f'<span class="var-input">{value["input"]}</span>'
            elif "operation" in value:
                return self.render_operation(value)
            elif "output" in value:
                return f'<span class="var-output">{value["output"]}</span>'
            elif "value" in value:
                return self.render_value_inline(value["value"])
        elif isinstance(value, int | float):
            return f'<span class="value-number">{value}</span>'
        elif isinstance(value, bool):
            return f'<span class="value-bool">{"waar" if value else "niet waar"}</span>'
        elif isinstance(value, str):
            return f'"{value}"'
        else:
            return str(value)

    def render_operation(self, operation: dict[str, Any], indent: int = 0) -> str:
        """Render an operation"""
        indent_str = "  " * indent
        html = []

        op = operation.get("operation", "")

        if op == "ADD":
            values = operation.get("values", [])
            parts = [self.render_value_inline(v) for v in values]
            return " + ".join(parts)
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
            html.append(
                indent_str + "het minimum van (" + " of ".join(self.render_value_inline(v) for v in values) + ")"
            )
        elif op == "ROUND":
            value = self.render_value_inline(operation.get("value", 0))
            precision = operation.get("precision", 0)
            html.append(f"{indent_str}{value} afgerond op {precision} decimalen")
        elif op == "FLOOR":
            value = self.render_value_inline(operation.get("value", 0))
            html.append(f"{indent_str}{value} naar beneden afgerond")
        elif op == "CEIL":
            value = self.render_value_inline(operation.get("value", 0))
            html.append(f"{indent_str}{value} naar boven afgerond")
        elif op == "IF":
            # Inline conditional
            test = operation.get("test", {})
            then_val = operation.get("then", "")
            else_val = operation.get("else", "")
            test_str = self.render_test(test, 0).strip() if test else "voorwaarde"
            then_str = self.render_value_inline(then_val)
            else_str = self.render_value_inline(else_val) if else_val else "0"
            html.append(f"{indent_str}(als {test_str} dan {then_str} anders {else_str})")

        if html:
            return "\n".join(html)
        elif op == "IF":
            return "[voorwaardelijke berekening]"
        else:
            return f"<{op}>"

    def render_legal_basis(self, legal_basis: dict[str, Any], indent: int = 0) -> str:
        """Render legal basis reference"""
        indent_str = "  " * indent
        article = legal_basis.get("article", "")
        paragraph = legal_basis.get("paragraph", "")
        subparagraph = legal_basis.get("subparagraph", "")
        bwb_id = legal_basis.get("bwb_id", self.bwb_id)

        # Build reference text
        ref = f"→ Artikel {article}"
        if paragraph:
            ref += f" lid {paragraph}"
        if subparagraph:
            ref += f" onderdeel {subparagraph}"

        # Build anchor ID
        anchor = f"Artikel{article}"
        if paragraph:
            anchor += f"-para-{paragraph}"
        if subparagraph:
            anchor += f"-{subparagraph}"

        # Try to find the actual law text
        law_text = ""
        law_title = self.law_content.get("title", "")

        if self.law_content and "structure" in self.law_content:
            # Search for the article text
            article_found = False

            # First check chapters
            for chapter in self.law_content.get("structure", {}).get("chapters", []):
                # Check articles directly in chapters
                for art in chapter.get("articles", []):
                    if art.get("id") == f"Artikel{article}":
                        article_found = True
                        if paragraph and "paragraphs" in art:
                            for para in art.get("paragraphs", []):
                                if str(para.get("number")) == str(paragraph):
                                    law_text = para.get("content", "")
                                    if subparagraph and "subsections" in para:
                                        for sub in para.get("subsections", []):
                                            if sub.get("letter") == subparagraph:
                                                law_text = sub.get("content", "")
                                                break
                                    break
                        elif not paragraph and "paragraphs" in art and art["paragraphs"]:
                            # If no specific paragraph requested, show first paragraph
                            law_text = art["paragraphs"][0].get("content", "")
                            if len(law_text) > 300:
                                law_text = law_text[:300] + "..."
                        break

                if article_found:
                    break

                # Also check sections within chapters
                for section in chapter.get("sections", []):
                    for art in section.get("articles", []):
                        if art.get("id") == f"Artikel{article}":
                            article_found = True
                            if paragraph and "paragraphs" in art:
                                for para in art.get("paragraphs", []):
                                    if str(para.get("number")) == str(paragraph):
                                        law_text = para.get("content", "")
                                        if subparagraph and "subsections" in para:
                                            for sub in para.get("subsections", []):
                                                if sub.get("letter") == subparagraph:
                                                    law_text = sub.get("content", "")
                                                    break
                                        break
                            elif not paragraph and "paragraphs" in art and art["paragraphs"]:
                                # If no specific paragraph requested, show first paragraph
                                law_text = art["paragraphs"][0].get("content", "")
                                if len(law_text) > 300:
                                    law_text = law_text[:300] + "..."
                            break

                    if article_found:
                        break

                if article_found:
                    break

            # Also check flat structure (if no chapters)
            if not article_found:
                for art in self.law_content.get("structure", {}).get("articles", []):
                    if art.get("id") == f"Artikel{article}":
                        if paragraph and "paragraphs" in art:
                            for para in art.get("paragraphs", []):
                                if str(para.get("number")) == str(paragraph):
                                    law_text = para.get("content", "")
                                    if subparagraph and "subsections" in para:
                                        for sub in para.get("subsections", []):
                                            if sub.get("letter") == subparagraph:
                                                law_text = sub.get("content", "")
                                                break
                                    break
                        elif not paragraph and "paragraphs" in art and art["paragraphs"]:
                            # If no specific paragraph requested, show first paragraph
                            law_text = art["paragraphs"][0].get("content", "")
                            if len(law_text) > 300:
                                law_text = law_text[:300] + "..."
                        break

        # Get explanation if available
        explanation = legal_basis.get("explanation", "")

        # Convert newlines to HTML breaks in law text
        if law_text:
            # Replace double newlines with paragraph breaks
            law_text_html = law_text.replace("\n\n", '</p><p style="margin-top: 8px;">')
            # Replace single newlines with line breaks
            law_text_html = law_text_html.replace("\n", "<br>")
            # Wrap in paragraph tags
            law_text_html = f'<p style="margin: 0;">{law_text_html}</p>'
        else:
            law_text_html = "Wettekst wordt opgehaald..."

        # Convert newlines in explanation too
        if explanation:
            explanation_html = explanation.replace("\n\n", '</p><p style="margin-top: 8px;">')
            explanation_html = explanation_html.replace("\n", "<br>")
            explanation_html = f'<p style="margin: 0;">{explanation_html}</p>'
        else:
            explanation_html = ""

        # Create link if we have BWB ID and article
        if bwb_id and article:
            legal_basis_html = f"""<span class="pill-wrapper">
                <a href="/wetten/{bwb_id}#{anchor}" class="legal-basis-link">{ref}</a>
                <div class="pill-dropdown pill-dropdown-dark">
                    <div class="pill-preview-dark">
                        <div class="pill-preview-title">Wettekst uit {law_title if law_title else bwb_id}</div>
                        <div class="pill-preview-content" style="margin-bottom: 10px;">
                            <strong>Artikel {article}{f" lid {paragraph}" if paragraph else ""}{f" onderdeel {subparagraph}" if subparagraph else ""}:</strong><br>
                            <div style="display: block; margin-top: 8px; padding: 12px; background: rgba(255,255,255,0.05); border-radius: 4px; line-height: 1.6; font-style: italic;">
                                {law_text_html}
                            </div>
                        </div>
                        {f'<div class="pill-preview-content" style="margin-bottom: 10px; padding: 12px; background: rgba(255,255,255,0.05); border-radius: 4px;"><strong>Uitleg:</strong><br>{explanation_html}</div>' if explanation else ""}
                        <div class="pill-preview-content" style="font-size: 13px; opacity: 0.8;">
                            Klik om naar de volledige wettekst te gaan →
                        </div>
                    </div>
                </div>
            </span>"""
            return f'{indent_str}<div class="legal-basis-inline">{legal_basis_html}</div>'
        else:
            return f'{indent_str}<div class="legal-basis-inline">{ref}</div>'

    def render_if_operation_full(self, action: dict[str, Any], indent: int = 0) -> str:
        """Render a full IF operation with all conditions"""
        indent_str = "  " * indent
        html = []

        if "conditions" in action:
            for i, condition in enumerate(action["conditions"]):
                if i == 0:
                    html.append(
                        indent_str
                        + '<div class="condition" style="margin: 8px 0; padding-left: 15px; border-left: 3px solid #1e40af;">'
                    )
                    html.append(indent_str + '  <div style="font-weight: 500; color: #86efac;">Als</div>')
                else:
                    html.append(
                        indent_str
                        + '<div class="condition" style="margin: 8px 0; padding-left: 15px; border-left: 3px solid #1e40af;">'
                    )
                    html.append(indent_str + '  <div style="font-weight: 500; color: #86efac;">Anders als</div>')

                if "test" in condition:
                    html.append(self.render_test_full(condition["test"], indent + 1))

                if "then" in condition:
                    html.append(
                        indent_str + '  <div style="font-weight: 500; color: #86efac; margin-top: 5px;">Dan</div>'
                    )
                    html.append(self.render_value_full(condition["then"], indent + 1))

                html.append(indent_str + "</div>")

            # Check for else in last condition
            if "conditions" in action and action["conditions"] and "else" in action["conditions"][-1]:
                html.append(
                    indent_str
                    + '<div class="condition-else" style="margin: 8px 0; padding-left: 15px; border-left: 3px solid #be123c;">'
                )
                html.append(indent_str + '  <div style="font-weight: 500; color: #86efac;">Anders</div>')
                html.append(self.render_value_full(action["conditions"][-1]["else"], indent + 1))
                html.append(indent_str + "</div>")

        return "\n".join(html)

    def render_arithmetic_operation_full(self, action: dict[str, Any], indent: int = 0) -> str:
        """Render arithmetic operations with full details"""
        indent_str = "  " * indent
        html = []
        op = action.get("operation", "")

        op_names = {
            "ADD": "Optellen",
            "SUBTRACT": "Aftrekken",
            "MULTIPLY": "Vermenigvuldigen",
            "DIVIDE": "Delen",
            "MIN": "Minimum van",
            "MAX": "Maximum van",
        }

        html.append(f'{indent_str}<div style="margin-top: 8px;">')
        html.append(f'{indent_str}  <div style="font-weight: 500; color: #fb923c;">{op_names.get(op, op)}</div>')

        if "values" in action:
            html.append(f'{indent_str}  <div style="margin-left: 15px; margin-top: 3px;">')
            for i, val in enumerate(action["values"]):
                if i > 0:
                    symbol = {"ADD": "+", "SUBTRACT": "-", "MULTIPLY": "×", "DIVIDE": "÷"}.get(op, ", ")
                    html.append(f'{indent_str}    <span style="color: #94a3b8; margin: 0 5px;">{symbol}</span>')
                # Check if value is a complex operation with its own legal_basis
                if isinstance(val, dict) and "operation" in val:
                    html.append(self.render_value_full(val, indent + 2, inline=False))
                else:
                    html.append(self.render_value_full(val, indent + 2, inline=True))
            html.append(f"{indent_str}  </div>")

        # Show legal basis if at this level
        if "legal_basis" in action:
            html.append(self.render_legal_basis(action["legal_basis"], indent + 1))

        html.append(f"{indent_str}</div>")
        return "\n".join(html)

    def render_test_full(self, test: dict[str, Any], indent: int = 0) -> str:
        """Render test conditions with full details"""
        indent_str = "  " * indent
        html = []

        op = test.get("operation", "")
        op_names = {
            "EQUALS": "is gelijk aan",
            "NOT_EQUALS": "is niet gelijk aan",
            "GREATER_THAN": "is groter dan",
            "GREATER_OR_EQUAL": "is groter dan of gelijk aan",
            "LESS_THAN": "is kleiner dan",
            "LESS_OR_EQUAL": "is kleiner dan of gelijk aan",
            "IS_TRUE": "is waar",
            "IS_FALSE": "is niet waar",
            "IN": "is een van",
            "NOT_IN": "is geen van",
            "AND": "EN",
            "OR": "OF",
        }

        html.append(
            f'{indent_str}<div style="margin: 3px 0; padding: 8px; background: rgba(30,41,59,0.3); border-radius: 4px;">'
        )

        if "subject" in test:
            html.append(f"{indent_str}  <div>")
            html.append(self.render_value_full(test["subject"], 0, inline=True))
            html.append(f'<span style="color: #e2e8f0; margin: 0 8px;">{op_names.get(op, op)}</span>')
            if "value" in test:
                html.append(self.render_value_full(test["value"], 0, inline=True))
            html.append(f"{indent_str}  </div>")
        elif "values" in test and op in ["GREATER_THAN", "LESS_THAN"]:
            html.append(f"{indent_str}  <div>")
            html.append(self.render_value_full(test["values"][0], 0, inline=True))
            html.append(f'<span style="color: #e2e8f0; margin: 0 8px;">{op_names.get(op, op)}</span>')
            html.append(self.render_value_full(test["values"][1], 0, inline=True))
            html.append(f"{indent_str}  </div>")
        elif op in ["AND", "OR"]:
            html.append(f'{indent_str}  <div style="font-weight: 500; color: #c084fc;">{op_names.get(op, op)}</div>')
            for sub_test in test.get("tests", []):
                html.append(self.render_test_full(sub_test, indent + 1))

        html.append(f"{indent_str}</div>")
        return "\n".join(html)

    def render_value_full(self, value: Any, indent: int = 0, inline: bool = False) -> str:
        """Render values with full details including nested operations"""
        indent_str = "  " * indent if not inline else ""

        if isinstance(value, dict):
            if "operation" in value:
                # Nested operation
                if inline:
                    # Render inline operations properly
                    op = value["operation"]
                    if op in ["ADD", "SUBTRACT", "MULTIPLY", "DIVIDE"]:
                        symbol = {"ADD": "+", "SUBTRACT": "-", "MULTIPLY": "×", "DIVIDE": "÷"}.get(op, op)
                        if "values" in value and len(value["values"]) == 2:
                            val1 = self.render_value_full(value["values"][0], 0, inline=True)
                            val2 = self.render_value_full(value["values"][1], 0, inline=True)
                            return f"({val1} {symbol} {val2})"
                    elif op in ["MIN", "MAX"]:
                        op_name = {"MIN": "min", "MAX": "max"}.get(op, op)
                        if "values" in value:
                            vals = [self.render_value_full(v, 0, inline=True) for v in value["values"]]
                            return f"{op_name}({', '.join(vals)})"
                    # Fallback for other operations
                    return f'<span style="color: #fbbf24;">[{value["operation"]} berekening]</span>'
                else:
                    op = value["operation"]
                    html = [
                        f'{indent_str}<div style="margin: 3px 0; padding: 6px; background: rgba(30,41,59,0.2); border-radius: 4px;">'
                    ]

                    if op == "IF":
                        html.append(self.render_if_operation_full(value, indent + 1))
                    elif op in ["ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "MIN", "MAX"]:
                        # For arithmetic operations, pass the whole value dict which includes legal_basis
                        html.append(self.render_arithmetic_operation_full(value, indent + 1))
                    else:
                        html.append(f'{indent_str}  <div style="font-weight: 500; color: #fb923c;">{op}</div>')
                        if "values" in value:
                            for val in value["values"]:
                                html.append(self.render_value_full(val, indent + 1))
                        if "value" in value:
                            html.append(self.render_value_full(value["value"], indent + 1))
                        # Show legal_basis for non-arithmetic operations
                        if "legal_basis" in value:
                            html.append(self.render_legal_basis(value["legal_basis"], indent + 1))

                    html.append(f"{indent_str}</div>")
                    return "\n".join(html)
            elif "parameter" in value:
                style = 'style="color: #60a5fa; font-family: monospace; font-weight: 600;"'
                return f"{indent_str}<span {style}>${value['parameter']}</span>"
            elif "input" in value:
                style = 'style="color: #86efac; font-family: monospace; font-weight: 600;"'
                return f"{indent_str}<span {style}>{value['input']}</span>"
            elif "output" in value:
                style = 'style="color: #86efac; font-family: monospace; font-weight: 600; background: #064e3b; padding: 2px 6px; border-radius: 3px;"'
                return f"{indent_str}<span {style}>{value['output']}</span>"
            elif "value" in value:
                return self.render_value_full(value["value"], indent, inline)
        elif isinstance(value, int | float):
            style = 'style="color: #fb923c; font-weight: 600;"'
            return f"{indent_str}<span {style}>{value}</span>"
        elif isinstance(value, bool):
            style = 'style="color: #c084fc; font-weight: 600;"'
            return f"{indent_str}<span {style}>{'waar' if value else 'niet waar'}</span>"
        elif isinstance(value, str):
            if value.startswith("$"):
                # Reference to definition
                style = 'style="color: #60a5fa; font-family: monospace; font-weight: 600;"'
                return f"{indent_str}<span {style}>{value}</span>"
            else:
                return f'{indent_str}<span style="color: #e2e8f0;">"{value}"</span>'
        else:
            return f'{indent_str}<span style="color: #e2e8f0;">{value}</span>'

    def render_parameters(self, parameters: list[dict[str, Any]]) -> str:
        """Render parameters section"""
        html = ['<div class="parameters-section">']
        html.append('<h3 style="color: #e2e8f0; margin-bottom: 1rem;">Parameters</h3>')

        for param in parameters:
            html.append(f'<div id="parameters-{param.get("name", "")}" style="margin-bottom: 1rem;">')
            html.append(f'  <strong style="color: #60a5fa; font-family: monospace;">{param.get("name", "")}</strong>')
            html.append(f'  <span style="color: #94a3b8;">: {param.get("description", "")}</span>')

            if "legal_basis" in param:
                html.append(self.render_legal_basis(param["legal_basis"], indent=1))

            html.append("</div>")

        html.append("</div>")
        return "\n".join(html)
