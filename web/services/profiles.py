# web/services/profiles.py
from typing import Dict, Any, Optional

# Profile data extracted from feature files
PROFILES = {
    "999993653": {
        "name": "Jan Jansen",
        "sources": {
            "RvIG": {
                "personen": [{
                    "bsn": "999993653",
                    "geboortedatum": "2005-01-01",
                    "verblijfsadres": "Amsterdam",
                    "land_verblijf": "NEDERLAND",
                    "nationaliteit": "NEDERLANDS"
                }],
                "relaties": [{
                    "bsn": "999993653",
                    "partnerschap_type": "GEEN",
                    "partner_bsn": None
                }],
                "verblijfplaats": [{
                    "bsn": "999993653",
                    "straat": "Kalverstraat",
                    "huisnummer": "1",
                    "postcode": "1012NX",
                    "woonplaats": "Amsterdam",
                    "type": "WOONADRES"
                }]
            },
            "RVZ": {
                "verzekeringen": [{
                    "bsn": "999993653",
                    "polis_status": "ACTIEF",
                    "verdrag_status": "GEEN",
                    "zorg_type": "BASIS"
                }]
            },
            "BELASTINGDIENST": {
                "box1": [{
                    "bsn": "999993653",
                    "loon_uit_dienstbetrekking": 79547,
                    "uitkeringen_en_pensioenen": 0,
                    "winst_uit_onderneming": 0,
                    "resultaat_overige_werkzaamheden": 0,
                    "eigen_woning": 0
                }],
                "box2": [{
                    "bsn": "999993653",
                    "dividend": 0,
                    "vervreemding_aandelen": 0
                }],
                "box3": [{
                    "bsn": "999993653",
                    "spaargeld": 5000,
                    "beleggingen": 0,
                    "onroerend_goed": 0,
                    "schulden": 0
                }],
                "buitenlands_inkomen": [{
                    "bsn": "999993653",
                    "bedrag": 0,
                    "land": "GEEN"
                }]
            },
            "DUO": {
                "inschrijvingen": [{
                    "bsn": "999993653",
                    "onderwijssoort": "MBO",
                    "niveau": 4
                }],
                "studiefinanciering": [{
                    "bsn": "999993653",
                    "aantal_studerende_broers_zussen": 0
                }]
            },
            "CBS": {
                "levensverwachting": [{
                    "jaar": 2025,
                    "verwachting_65": 20.5
                }]
            },
            "DJI": {
                "detenties": [{
                    "bsn": "999993653",
                    "status": "VRIJ",
                    "inrichting_type": "GEEN"
                }]
            },
            "SVB": {
                "verzekerde_tijdvakken": [{
                    "bsn": "999993653",
                    "woonperiodes": 35
                }]
            },
            "GEMEENTE_AMSTERDAM": {
                "werk_en_re_integratie": [{
                    "bsn": "999993653",
                    "arbeidsvermogen": "VOLLEDIG",
                    "re_integratie_traject": "Werkstage"
                }]
            },
            "IND": {
                "verblijfsvergunningen": [{
                    "bsn": "999993653",
                    "type": "ONBEPAALDE_TIJD_REGULIER",
                    "status": "VERLEEND",
                    "ingangsdatum": "2015-01-01",
                    "einddatum": None
                }]
            }
        }
    },
    # Maria's profile with similar complete data...
    "999993654": {
        "name": "Maria Pietersen",
        "sources": {
            # Similar complete data structure...
            "RvIG": {
                "personen": [{
                    "bsn": "999993654",
                    "geboortedatum": "1958-02-15",
                    "verblijfsadres": "Amsterdam",
                    "land_verblijf": "NEDERLAND",
                    "nationaliteit": "NEDERLANDS"
                }],
                "relaties": [{
                    "bsn": "999993654",
                    "partnerschap_type": "HUWELIJK",
                    "partner_bsn": "999993655"
                }]
            },
            "SVB": {
                "verzekerde_tijdvakken": [{
                    "bsn": "999993654",
                    "woonperiodes": 50
                }]
            },
            "CBS": {
                "levensverwachting": [{
                    "jaar": 2025,
                    "verwachting_65": 20.5
                }]
            },
            "BELASTINGDIENST": {
                "inkomen": [{
                    "bsn": "999993654",
                    "box1": 0,
                    "box2": 0,
                    "box3": 0,
                    "buitenlands": 0
                }],
                "box2": [{
                    "bsn": "999993654",
                    "dividend": 0,
                    "vervreemding_aandelen": 0
                }],
                "buitenlands_inkomen": [{
                    "bsn": "999993654",
                    "bedrag": 0,
                    "land": "GEEN"
                }]
            },
            "RVZ": {
                "verzekeringen": [{
                    "bsn": "999993654",
                    "polis_status": "ACTIEF",
                    "verdrag_status": "GEEN",
                    "zorg_type": "BASIS"
                }]
            }
        }
    }
}


def get_profile_data(bsn: str) -> Optional[Dict[str, Any]]:
    """Get profile data for a specific BSN"""
    return PROFILES.get(bsn)


def get_all_profiles() -> Dict[str, Dict[str, Any]]:
    """Get all available profiles"""
    return PROFILES
