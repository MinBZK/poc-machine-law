package model

import (
	"fmt"
	"time"
)

// GetProfileProperties extracts key properties from a profile with emoji representations
func GetProfileProperties(profile Profile) []string {
	properties := []string{}

	// Check if sources and RvIG data exist
	rvigData, hasRvIG := profile.Sources["RvIG"]
	if !hasRvIG {
		return properties
	}

	// Extract person data
	personenData, hasPersoon := rvigData["personen"]
	if !hasPersoon || len(personenData) == 0 {
		return properties
	}

	personData := personenData[0]

	// Add nationality
	if nationality, ok := personData["nationaliteit"].(string); ok {
		switch nationality {
		case "NEDERLANDS":
			properties = append(properties, "🇳🇱 Nederlands")
		case "DUITS":
			properties = append(properties, "🇩🇪 Duits")
		case "MAROKKAANS":
			properties = append(properties, "🇲🇦 Marokkaans")
		default:
			properties = append(properties, fmt.Sprintf("🌍 %s", nationality))
		}
	}

	// Add age
	if birthDateStr, ok := personData["geboortedatum"].(string); ok {
		birthDate, err := time.Parse("2006-01-02", birthDateStr)
		if err == nil {
			age := calculateAge(birthDate)
			properties = append(properties, fmt.Sprintf("🗓️ %d jaar", age))
		}
	}

	// Add children
	if childrenData, hasChildren := rvigData["CHILDREN_DATA"]; hasChildren {
		for _, childEntry := range childrenData {
			if kinderen, ok := childEntry["kinderen"].([]interface{}); ok {
				numChildren := len(kinderen)
				if numChildren == 1 {
					properties = append(properties, "👶 1 kind")
				} else if numChildren > 1 {
					properties = append(properties, fmt.Sprintf("👨‍👩‍👧‍👦 %d kinderen", numChildren))
				}
			}
		}
	}

	// Add housing status
	if verblijfplaatsData, hasVerblijfplaats := rvigData["verblijfplaats"]; hasVerblijfplaats && len(verblijfplaatsData) > 0 {
		addressData := verblijfplaatsData[0]
		if addressType, ok := addressData["type"].(string); ok {
			switch addressType {
			case "WOONADRES":
				properties = append(properties, "🏠 Vast woonadres")
			case "BRIEFADRES":
				properties = append(properties, "📫 Briefadres")
			}
		}
	}

	// Add work status
	isEntrepreneur := false
	if kvkData, hasKVK := profile.Sources["KVK"]; hasKVK {
		if entrepreneurData, hasEntrepreneur := kvkData["is_entrepreneur"]; hasEntrepreneur {
			for _, entry := range entrepreneurData {
				if waarde, ok := entry["waarde"]; ok && waarde != nil && waarde != false {
					isEntrepreneur = true
					properties = append(properties, "💼 ZZP'er")
					break
				}
			}
		}
	}

	if uwvData, hasUWV := profile.Sources["UWV"]; hasUWV {
		if arbeidsverhoudingenData, hasArbeidsverhouding := uwvData["arbeidsverhoudingen"]; hasArbeidsverhouding {
			for _, relation := range arbeidsverhoudingenData {
				if dienstverbandType, ok := relation["dienstverband_type"].(string); ok {
					if dienstverbandType != "GEEN" && !isEntrepreneur {
						properties = append(properties, "👔 In loondienst")
						break
					}
				}
			}
		}

		// Add disability status
		if arbeidsongeschiktheidData, hasArbeidsongeschiktheid := uwvData["arbeidsongeschiktheid"]; hasArbeidsongeschiktheid {
			for _, disability := range arbeidsongeschiktheidData {
				if percentage, ok := disability["percentage"]; ok {
					properties = append(properties, fmt.Sprintf("♿ %v%% arbeidsongeschikt", percentage))
				}
			}
		}
	}

	// Add student status
	if duoData, hasDUO := profile.Sources["DUO"]; hasDUO {
		if inschrijvingenData, hasInschrijvingen := duoData["inschrijvingen"]; hasInschrijvingen {
			for _, enrollment := range inschrijvingenData {
				if onderwijssoort, ok := enrollment["onderwijssoort"].(string); ok {
					if onderwijssoort != "GEEN" {
						properties = append(properties, "🎓 Student")
						break
					}
				}
			}
		}
	}

	return properties
}

// calculateAge calculates age in years from a birth date
func calculateAge(birthDate time.Time) int {
	now := time.Now()
	age := now.Year() - birthDate.Year()

	// Adjust if birthday hasn't occurred this year
	if now.Month() < birthDate.Month() || (now.Month() == birthDate.Month() && now.Day() < birthDate.Day()) {
		age--
	}

	return age
}
