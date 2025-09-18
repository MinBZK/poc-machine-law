# MCP + Claude Chat Client

Een interactieve CLI chat client die Nederlandse wetgeving toegankelijk maakt via natuurlijke taal, gebruikmakend van MCP (Model Context Protocol) en Claude.

## 🚀 Quick Start

### 1. Zorg dat MCP server draait
```bash
uv run web/main.py
```

### 2. Zet je Anthropic API key
```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

### 3. Start de chat client
```bash
uv run python law_mcp/chat_client.py
```

## 💬 Voorbeelden

```
👤 Jij: Mijn BSN is 100000001. Heb ik recht op huurtoeslag?
🤖 Claude: Ik ga even controleren of je recht hebt op huurtoeslag...
         [gebruikt MCP tool om profiel op te halen en huurtoeslag te berekenen]

👤 Jij: Wat betekent dit bedrag precies?
🤖 Claude: [geeft uitleg over de berekening en voorwaarden]

👤 Jij: Kan ik ook zorgtoeslag krijgen?
🤖 Claude: [controleert zorgtoeslag met jouw gegevens]
```

## 🔧 Hoe het werkt

1. **MCP Integration**: Verbindt met lokale MCP server voor toegang tot Nederlandse wetten
2. **Claude AI**: Gebruikt Claude's natuurlijke taalverwerking voor conversaties
3. **Tool Calls**: Claude roept automatisch MCP tools aan op basis van je vragen
4. **Nederlandse Context**: Geoptimaliseerd voor Nederlandse wetgeving en terminologie

## 🛠️ Technische Details

- **MCP Tools**: `execute_law`, `check_eligibility`, `calculate_benefit_amount`
- **Ondersteunde Wetten**: Huurtoeslag, Zorgtoeslag, AOW, WPM, en meer
- **Model**: Claude 3.5 Sonnet (20241022)
- **Transport**: FastMCP client over HTTP

## ⚡ Features

- ✅ Natuurlijke taal conversaties in het Nederlands
- ✅ Automatische tool selectie door Claude
- ✅ Real-time wetgeving uitvoering via MCP
- ✅ Interactieve CLI interface
- ✅ Conversatie geschiedenis
- ✅ Foutafhandeling en gebruiksvriendelijke feedback

## 🔍 Ondersteunde Vragen

- **Uitkeringen**: "Heb ik recht op huurtoeslag/zorgtoeslag?"
- **Berekeningen**: "Hoeveel krijg ik aan AOW?"
- **Voorwaarden**: "Wat zijn de voorwaarden voor...?"
- **Bedrijven**: "Moet mijn bedrijf WPM rapportage doen?" (gebruik KVK nummer)

Type `quit` om de chat te beëindigen.
