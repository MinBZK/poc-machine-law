"""
Prompt template system for MCP server - DRY principle applied
"""

import json

from mcp.types import GetPromptResult, PromptMessage, TextContent


class PromptTemplate:
    """Base class for prompt templates"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def generate(self, arguments: dict[str, str]) -> GetPromptResult:
        """Generate prompt result"""
        prompt_text = self._build_prompt(arguments)
        description = self._build_description(arguments)

        return GetPromptResult(
            description=description,
            messages=[PromptMessage(role="user", content=TextContent(type="text", text=prompt_text))],
        )

    def _build_prompt(self, arguments: dict[str, str]) -> str:
        """Override in subclasses to build the actual prompt text"""
        raise NotImplementedError

    def _build_description(self, arguments: dict[str, str]) -> str:
        """Override in subclasses to build the description"""
        return f"{self.description} for BSN {arguments.get('bsn', 'unknown')}"


class BenefitAnalysisPrompt(PromptTemplate):
    """Template for comprehensive benefit analysis"""

    def __init__(self):
        super().__init__("check_all_benefits", "Check all benefits")

    def _build_prompt(self, arguments: dict[str, str]) -> str:
        bsn = arguments["bsn"]
        include_details = arguments.get("include_details", "false").lower() == "true"

        prompt = f"""You are helping to check all available benefits for a Dutch citizen with BSN {bsn}.

Please follow these steps:

1. First, read the `laws://list` resource to discover what benefits are available
2. For relevant benefits, use the `check_eligibility` tool to verify eligibility
3. For benefits where the person is eligible, use the `execute_law` tool to get detailed results
4. Use the `calculate_benefit_amount` tool for specific financial calculations when needed
5. Summarize the findings, including:
   - Which benefits the person is eligible for
   - Estimated benefit amounts (monthly and yearly)
   - Any missing information that prevents eligibility
   - Recommended next steps

Focus on common benefits like healthcare allowance (zorgtoeslag), housing allowance (huurtoeslag), and child benefits first. Present results in a clear, citizen-friendly format."""

        if include_details:
            prompt += "\n\nInclude detailed calculation explanations and legal references where relevant."

        return prompt


class CalculationExplanationPrompt(PromptTemplate):
    """Template for explaining law calculations"""

    def __init__(self):
        super().__init__("explain_calculation", "Explain calculation")

    def _build_prompt(self, arguments: dict[str, str]) -> str:
        service = arguments["service"]
        law = arguments["law"]
        bsn = arguments["bsn"]

        return f"""You are explaining how the calculation works for {law} under service {service} for citizen BSN {bsn}.

Please follow these steps:

1. First, use the `law://{service}/{law}/spec` resource to get the law specification
2. Use the `execute_law` tool to run the calculation for this person
3. Use the `profile://{bsn}` resource to understand the person's data
4. Explain the calculation in simple terms, including:
   - What inputs were used
   - How the calculation works step by step
   - What the final result means
   - Any conditions or thresholds that apply
   - How changes in circumstances might affect the result

Use clear, non-technical language that a citizen can understand. Reference the specific legal articles where relevant."""

    def _build_description(self, arguments: dict[str, str]) -> str:
        return f"Explain {arguments['law']} calculation for BSN {arguments['bsn']}"


class ScenarioComparisonPrompt(PromptTemplate):
    """Template for comparing scenarios"""

    def __init__(self):
        super().__init__("compare_scenarios", "Compare scenarios")

    def _build_prompt(self, arguments: dict[str, str]) -> str:
        bsn = arguments["bsn"]
        scenarios = json.loads(arguments.get("scenarios", "[]"))
        scenarios_text = "\n".join([f"- Scenario {i + 1}: {scenario}" for i, scenario in enumerate(scenarios)])

        return f"""You are comparing different scenarios for citizen BSN {bsn}.

Scenarios to analyze:
{scenarios_text}

For each scenario:

1. Use the `execute_law` tool with appropriate overrides to simulate the scenario
2. Calculate the difference in outcomes compared to the current situation
3. Analyze which scenario provides the best financial outcome
4. Consider any trade-offs or requirements for each scenario

Present a clear comparison table showing:
- Scenario description
- Key changes required
- Financial impact (monthly/yearly)
- Feasibility and requirements
- Recommendation

Highlight the most beneficial scenario and explain why."""


# Registry of all prompt templates
PROMPT_TEMPLATES = {
    "check_all_benefits": BenefitAnalysisPrompt(),
    "explain_calculation": CalculationExplanationPrompt(),
    "compare_scenarios": ScenarioComparisonPrompt(),
}
