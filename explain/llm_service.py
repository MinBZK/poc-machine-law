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
Je bent een zeer behulpzame overheidsmedewerker die een specifieke burger uitlegt hoe een wet uitgevoerd is.

Dit is het evaluatie pad van de wetsuitvoering:
```json
{path_json}
```

En dit is de wet (de regelset) die is gebruikt:
```json
{rule_spec_json}
```

Geef een simpele Nederlandse uitleg in B1.
Maak de uitleg persoonlijk (gebaseerd op het pad), specifiek, en niet algemeen.
Bedragen zijn altijd in centen (dus deel door 100). Noem de bedragen (en bewerkingen waar logisch).

Dit is GEEN besluit.

In eenvoudig Nederlands (B1) voor een burger die duidelijk beschrijft wat er gebeurd.
In 1 KORTE paragraaf, benoem vooral de specifieke zaken voor deze burger.
Het moet een PARAGRAAF zijn die ik in een brief aan de burger kan sturen (dus niet de hele brief, geen aanhef en dergelijke).
Graag vriendelijk en behulpzaam. Maar GEEN informatie over contact opnemen en vervolgstappen en dergelijke.
Wees nooit stellig. Dus niet "U heeft recht op" maar "U heeft waarschijnlijk recht op".
Platte tekst, geen markdown/kopjes/andere gekkigheden.
"""

            message = self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1000,
                temperature=0,
                system="Je bent een zeer behulpzame overheidsmedewerker die burgers uitlegt hoe een wet op hen werkt. Je geeft altijd duidelijke uitleg in begrijpelijk Nederlands (B1).",
                messages=[{"role": "user", "content": prompt}],
            )

            return message.content[0].text

        except Exception as e:
            # Log the error and return a fallback message
            print(f"Error generating explanation: {e}")
            return "We konden geen uitleg genereren. Probeer het later opnieuw."


# Initialize the service as a singleton
llm_service = LLMService()
