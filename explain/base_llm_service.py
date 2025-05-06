import abc
from functools import lru_cache
from typing import Any


class BaseLLMService(abc.ABC):
    """Base class for LLM services to define common interface"""

    @property
    def is_configured(self) -> bool:
        """Check if the service is properly configured"""
        return hasattr(self, "client") and self.client is not None

    @property
    def provider_name(self) -> str:
        """Get the provider name"""
        raise NotImplementedError()

    @property
    def model_id(self) -> str:
        """Get the model ID"""
        raise NotImplementedError()

    @abc.abstractmethod
    def chat_completion(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> Any | None:
        """Make a chat completion request to the LLM provider

        Args:
            messages: List of message objects with 'role' and 'content'
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling
            system: System prompt

        Returns:
            LLM response or None if service not configured
        """

    @abc.abstractmethod
    def get_completion_text(self, response: Any) -> str:
        """Extract the completion text from the provider's response

        Args:
            response: Provider-specific response object or None
                     if service not configured

        Returns:
            Extracted text content or error message if not configured
        """

    @lru_cache(maxsize=1000)  # Cache responses to avoid repeated calls
    def generate_explanation(self, path_json: str, rule_spec_json: str) -> str:
        """Generate explanation for a law evaluation path

        Args:
            path_json: JSON string of the evaluation path
            rule_spec_json: JSON string of the rule specification

        Returns:
            Generated explanation
        """
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

            # Use chat_completion with system message
            system = "Je bent een zeer behulpzame overheidsmedewerker die burgers uitlegt hoe een wet op hen werkt. Je geeft altijd duidelijke uitleg in begrijpelijk Nederlands (B1)."
            response = self.chat_completion(
                messages=[{"role": "user", "content": prompt}], max_tokens=1000, temperature=0, system=system
            )

            # Get text using standardized method
            return self.get_completion_text(response)

        except Exception as e:
            # Log the error and return a fallback message
            print(f"Error generating explanation with {self.provider_name}: {e}")
            return "We konden geen uitleg genereren. Probeer het later opnieuw."
