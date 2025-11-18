"""
Prompt template system for MCP server - DRY principle applied
"""

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
    """Template for income and situation optimization analysis"""

    def __init__(self):
        super().__init__("optimize_income", "Optimize income and benefits")

    def _build_prompt(self, arguments: dict[str, str]) -> str:
        bsn = arguments["bsn"]

        return f"""You are analyzing different income scenarios to optimize benefits for citizen BSN {bsn}.

Test these common scenarios using overrides:

1. Use the `execute_law` tool with appropriate overrides to simulate the scenario
2. Calculate the difference in outcomes compared to the current situation
3. Analyze which scenario provides the best financial outcome
4. Consider any trade-offs or requirements for each scenario

## Override Usage Guide:

**Service Overrides** (for external service data like income, employment):
- Use lowercase field names
- Format: `{"SERVICE_NAME": {"field_name": value}}`
- Examples:
  - `{"UWV": {"inkomen": 3500000}}` (override income to €35,000)
  - `{"BELASTINGDIENST": {"vermogen": 50000}}` (override assets to €50,000)
  - `{"RVZ": {"verzekerd": true}}` (override insurance status)

**Source Overrides** (for internal law source data):
- Use ALL CAPS field names
- Format: `{"SOURCE_TYPE": {"FIELD_NAME": value}}`
- Examples:
  - `{"RVO": {"AANTAL_WERKNEMERS": 150}}` (override employee count)
  - `{"KVK": {"OMZET": 2000000}}` (override business turnover)
  - `{"CBS": {"LEVENSVERWACHTING": 85}}` (override life expectancy)

**Combined Example:**
```json
{
            "overrides": {
                "UWV": {"inkomen": 4000000},
        "RVO": {"AANTAL_WERKNEMERS": 200}
    }
}
```

Present a clear comparison table showing:
- Scenario description
- Key changes required
- Financial impact (monthly/yearly)
- Feasibility and requirements
- Recommendation

Highlight the most beneficial scenario and explain why."""


class CitizenReportPrompt(PromptTemplate):
    """Template for comprehensive citizen benefit report"""

    def __init__(self):
        super().__init__("generate_citizen_report", "Generate comprehensive benefit report")

    def _build_prompt(self, arguments: dict[str, str]) -> str:
        bsn = arguments["bsn"]
        include_projections = arguments.get("include_projections", "false").lower() == "true"

        prompt = f"""Generate a comprehensive benefits and eligibility report for citizen BSN {bsn}.

This should be a professional, citizen-facing report that includes:

1. **Personal Profile Summary**
   - Use `profile://{bsn}` resource to get citizen data
   - Summarize key demographics, income, family situation

2. **Current Benefit Status**
   - Check eligibility for all major benefits using available tools
   - Calculate current benefit amounts where eligible
   - Identify benefits currently being missed

3. **Financial Impact Analysis**
   - Total monthly benefits currently received
   - Total potential monthly benefits if all were claimed
   - Annual financial impact of unclaimed benefits

4. **Actionable Recommendations**
   - Which benefits to apply for immediately
   - Documentation needed for applications
   - Expected processing times and contact information

5. **Legal Compliance Notes**
   - Any obligations or requirements for benefit recipients
   - Reporting requirements for income changes
   - Renewal dates and procedures

Format as a professional report with clear sections, bullet points, and citizen-friendly language."""

        if include_projections:
            prompt += """

6. **Future Projections**
   - How benefits might change with age/life changes
   - Retirement benefit projections
   - Impact of potential policy changes"""

        return prompt

    def _build_description(self, arguments: dict[str, str]) -> str:
        return f"Generate comprehensive benefit report for BSN {arguments['bsn']}"


class OptimizationPrompt(PromptTemplate):
    """Template for benefit optimization advice"""

    def __init__(self):
        super().__init__("optimize_benefits", "Optimize benefit strategy")

    def _build_prompt(self, arguments: dict[str, str]) -> str:
        bsn = arguments["bsn"]
        focus_area = arguments.get("focus_area", "all")

        return f"""Provide benefit optimization advice for citizen BSN {bsn}, focusing on: {focus_area}

Perform a comprehensive analysis to maximize this person's benefits:

1. **Current Situation Analysis**
   - Get full profile using `profile://{bsn}`
   - Calculate all current benefits and eligibility
   - Identify optimization opportunities

2. **Income Optimization**
   - Analyze if income adjustments could increase net benefits
   - Consider timing of income (monthly vs yearly variations)
   - Self-employment vs employment benefit impacts
   - Use overrides to test different income scenarios: `{"UWV": {"inkomen": NEW_AMOUNT}}`

3. **Family Structure Optimization**
   - Impact of marriage/partnership on combined benefits
   - Child-related benefit optimization strategies
   - Housing arrangement considerations

4. **Strategic Recommendations**
   - Short-term actions (0-6 months)
   - Medium-term planning (6-24 months)
   - Long-term benefit strategy

5. **Risk Assessment**
   - Benefits at risk due to income/situation changes
   - Compliance requirements and monitoring
   - Appeal and recalculation procedures

Provide specific, actionable advice with quantified financial impacts where possible."""

    def _build_description(self, arguments: dict[str, str]) -> str:
        return f"Optimize benefit strategy for BSN {arguments['bsn']}"


class LegalResearchPrompt(PromptTemplate):
    """Template for legal research and compliance"""

    def __init__(self):
        super().__init__("legal_research", "Research legal requirements and compliance")

    def _build_prompt(self, arguments: dict[str, str]) -> str:
        topic = arguments.get("topic", "general compliance")
        law = arguments.get("law", "")
        service = arguments.get("service", "")

        prompt = f"""Conduct legal research on: {topic}

Research focus: {f"Law: {law}, Service: {service}" if law and service else "General Dutch benefit law"}

Please provide:

1. **Legal Foundation**
   - Relevant laws and regulations
   - Key legal articles and sections
   - Recent changes or updates to legislation

2. **Compliance Requirements**
   - Citizen obligations under these laws
   - Reporting and notification requirements
   - Documentation and evidence requirements

3. **Rights and Protections**
   - Citizen rights under the legislation
   - Appeal and objection procedures
   - Data protection and privacy rights

4. **Practical Implications**
   - How these laws affect daily life
   - Common compliance issues and how to avoid them
   - Best practices for staying compliant

5. **Recent Developments**
   - Court cases affecting interpretation
   - Policy changes or clarifications
   - Upcoming legislative changes

Use clear, accessible language while maintaining legal accuracy."""

        if law and service:
            prompt += f"""

Focus specifically on the implementation of {law} by {service}, including:
- Service-specific procedures and requirements
- How this service interprets the law
- Common issues with this particular implementation"""

        return prompt

    def _build_description(self, arguments: dict[str, str]) -> str:
        topic = arguments.get("topic", "general compliance")
        return f"Legal research on: {topic}"


class AppealAssistancePrompt(PromptTemplate):
    """Template for benefit appeal and objection assistance"""

    def __init__(self):
        super().__init__("appeal_assistance", "Appeal and objection assistance")

    def _build_prompt(self, arguments: dict[str, str]) -> str:
        bsn = arguments["bsn"]
        decision_type = arguments.get("decision_type", "benefit decision")
        service = arguments.get("service", "")

        return f"""Provide assistance with appealing a {decision_type} for citizen BSN {bsn}.

Service involved: {service if service else "Not specified"}

Help with the appeal process:

1. **Decision Analysis**
   - Get citizen profile using `profile://{bsn}`
   - Analyze the decision against legal requirements
   - Identify potential grounds for appeal

2. **Legal Grounds Assessment**
   - Review applicable laws and regulations
   - Check if decision follows proper legal procedures
   - Identify factual or legal errors in the decision

3. **Evidence Collection**
   - What evidence supports the appeal
   - How to obtain missing documentation
   - Timeline for evidence gathering

4. **Appeal Strategy**
   - Best grounds for the appeal
   - Procedural steps and deadlines
   - Expected timeline and process

5. **Practical Guidance**
   - How to write the appeal letter
   - Required forms and documentation
   - Where to submit and follow up

6. **Alternative Options**
   - Informal resolution possibilities
   - Mediation or administrative review
   - Legal aid resources if needed

Provide specific, actionable guidance tailored to this citizen's situation and the type of decision being appealed."""

    def _build_description(self, arguments: dict[str, str]) -> str:
        decision_type = arguments.get("decision_type", "benefit decision")
        return f"Appeal assistance for {decision_type} - BSN {arguments['bsn']}"


# Registry of all prompt templates
PROMPT_TEMPLATES = {
    "check_all_benefits": BenefitAnalysisPrompt(),
    "explain_calculation": CalculationExplanationPrompt(),
    "optimize_income": ScenarioComparisonPrompt(),
    "generate_citizen_report": CitizenReportPrompt(),
    "optimize_benefits": OptimizationPrompt(),
    "legal_research": LegalResearchPrompt(),
    "appeal_assistance": AppealAssistancePrompt(),
}
