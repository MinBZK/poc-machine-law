import os
from functools import lru_cache

import anthropic


class LLMService:
    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    @lru_cache(maxsize=1000)  # Cache responses to avoid repeated calls
    def generate_explanation(self, path_json: str, rule_spec_json: str) -> str:
        try:
            prompt = f"""
Je bent een behulpzame overheidsmedewerker die burgers uitlegt hoe hun aanvraag is beoordeeld.

Dit is het evaluatiepad van de aanvraag: {path_json}

En dit is de regelset die is gebruikt: {rule_spec_json}

Dit is het pad door de boom heen en de regelset. Geef een simpele Nederlandse uitleg.
Maak de uitleg persoonlijk (gebaseerd op het pad) en niet algemeen.
Bedragen zijn altijd in centen (dus deel door 100).

Dit is GEEN besluit.

In eenvoudig Nederlands voor een burger die duidelijk beschrijft wat er gebeurd.
In 1 KORTE paragraaf, benoem vooral de specifieke zaken voor deze burger.
Het moet een PARAGRAAF zijn die ik in een brief aan de burger kan sturen (dus niet de hele brief, geen aanhef en dergelijke).
Graag vriendelijk en behulpzaam.
"""

            message = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0,
                system="Je bent een behulpzame overheidsmedewerker die burgers uitlegt hoe hun aanvraag is beoordeeld. Je geeft altijd korte, duidelijke uitleg in begrijpelijk Nederlands.",
                messages=[{"role": "user", "content": prompt}],
            )

            return message.content[0].text

        except Exception as e:
            # Log the error and return a fallback message
            print(f"Error generating explanation: {e}")
            return "We hebben uw aanvraag beoordeeld volgens de regels van de wet. Op basis van uw persoonlijke situatie hebben we bepaald waar u recht op heeft."


# Initialize the service as a singleton
llm_service = LLMService()
