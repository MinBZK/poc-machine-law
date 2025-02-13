from typing import Any

# Global service data that applies to all profiles
GLOBAL_SERVICES = {
    "CBS": {"levensverwachting": [{"jaar": 2025, "verwachting_65": 20.5}]},
    "KIESRAAD": {"verkiezingen": [{"type": "TWEEDE_KAMER", "verkiezingsdatum": "2025-05-05"}]},
    "JenV": {
        "jurisdicties": [
            {"gemeente": "AMSTERDAM", "arrondissement": "AMSTERDAM", "rechtbank": "RECHTBANK_AMSTERDAM"},
            {"gemeente": "AMSTELVEEN", "arrondissement": "AMSTERDAM", "rechtbank": "RECHTBANK_AMSTERDAM"},
            {"gemeente": "HAARLEM", "arrondissement": "NOORD-HOLLAND", "rechtbank": "RECHTBANK_NOORD_HOLLAND"},
            {"gemeente": "ALKMAAR", "arrondissement": "NOORD-HOLLAND", "rechtbank": "RECHTBANK_NOORD_HOLLAND"},
            {"gemeente": "ROTTERDAM", "arrondissement": "ROTTERDAM", "rechtbank": "RECHTBANK_ROTTERDAM"},
            {"gemeente": "UTRECHT", "arrondissement": "MIDDEN-NEDERLAND", "rechtbank": "RECHTBANK_MIDDEN_NEDERLAND"},
            {"gemeente": "DEN HAAG", "arrondissement": "DEN HAAG", "rechtbank": "RECHTBANK_DEN_HAAG"},
            {"gemeente": "GRONINGEN", "arrondissement": "NOORD-NEDERLAND", "rechtbank": "RECHTBANK_NOORD_NEDERLAND"},
            {"gemeente": "MAASTRICHT", "arrondissement": "LIMBURG", "rechtbank": "RECHTBANK_LIMBURG"},
            {"gemeente": "ARNHEM", "arrondissement": "GELDERLAND", "rechtbank": "RECHTBANK_GELDERLAND"},
        ]
    },
}
PROFILES = {
    "999993653": {
        "name": "Jan Jansen",
        "description": "Jongere met part-time baan naast MBO opleiding, komt in aanmerking voor zorgtoeslag",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993653",
                        "geboortedatum": "2005-01-01",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                    }
                ],
                "relaties": [
                    {
                        "bsn": "999993653",
                        "partnerschap_type": "GEEN",
                        "partner_bsn": None,
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "999993653",
                        "straat": "Kalverstraat",
                        "huisnummer": "1",
                        "postcode": "1012NX",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
            },
            "RVZ": {
                "verzekeringen": [
                    {
                        "bsn": "999993653",
                        "polis_status": "ACTIEF",
                        "verdrag_status": "GEEN",
                        "zorg_type": "BASIS",
                    }
                ]
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993653",
                        "loon_uit_dienstbetrekking": 79547,
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": 0,
                    }
                ],
                "box2": [{"bsn": "999993653", "dividend": 0, "vervreemding_aandelen": 0}],
                "box3": [
                    {
                        "bsn": "999993653",
                        "spaargeld": 5000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993653", "bedrag": 0, "land": "GEEN"}],
            },
            "DUO": {
                "inschrijvingen": [{"bsn": "999993653", "onderwijssoort": "MBO", "niveau": 4}],
                "studiefinanciering": [{"bsn": "999993653", "aantal_studerende_broers_zussen": 0}],
            },
            "DJI": {"detenties": [{"bsn": "999993653", "status": "VRIJ", "inrichting_type": "GEEN"}]},
            "SVB": {"verzekerde_tijdvakken": [{"bsn": "999993653", "woonperiodes": 35}]},
            "GEMEENTE_AMSTERDAM": {
                "werk_en_re_integratie": [
                    {
                        "bsn": "999993653",
                        "arbeidsvermogen": "VOLLEDIG",
                        "re_integratie_traject": "Werkstage",
                    }
                ]
            },
            "IND": {
                "verblijfsvergunningen": [
                    {
                        "bsn": "999993653",
                        "type": "ONBEPAALDE_TIJD_REGULIER",
                        "status": "VERLEEND",
                        "ingangsdatum": "2015-01-01",
                        "einddatum": None,
                    }
                ]
            },
        },
    },
    "999993654": {
        "name": "Maria Pietersen",
        "description": "AOW-gerechtigde met volledige opbouw, gehuwd, partner nog geen AOW-leeftijd",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993654",
                        "geboortedatum": "1948-02-15",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                    }
                ],
                "relaties": [
                    {
                        "bsn": "999993654",
                        "partnerschap_type": "HUWELIJK",
                        "partner_bsn": "999993655",
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "999993654",
                        "straat": "Kalverstraat",
                        "huisnummer": "1",
                        "postcode": "1012NX",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
            },
            "SVB": {"verzekerde_tijdvakken": [{"bsn": "999993654", "woonperiodes": 50}]},
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993654",
                        "loon_uit_dienstbetrekking": 0,
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": 0,
                    }
                ],
                "box2": [{"bsn": "999993654", "dividend": 0, "vervreemding_aandelen": 0}],
                "box3": [
                    {
                        "bsn": "999993654",
                        "spaargeld": 0,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993654", "bedrag": 0, "land": "GEEN"}],
            },
            "RVZ": {
                "verzekeringen": [
                    {
                        "bsn": "999993654",
                        "polis_status": "ACTIEF",
                        "verdrag_status": "GEEN",
                        "zorg_type": "BASIS",
                    }
                ]
            },
        },
    },
    "999993655": {
        "name": "Sarah de Wit",
        "description": "Dakloze met briefadres, recht op bijstand met woonkostentoeslag",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993655",
                        "geboortedatum": "1980-01-01",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                    }
                ],
                "relaties": [
                    {
                        "bsn": "999993655",
                        "partnerschap_type": "GEEN",
                        "partner_bsn": None,
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "999993655",
                        "straat": "De Regenboog Groep",
                        "huisnummer": "1",
                        "postcode": "1012NX",
                        "woonplaats": "Amsterdam",
                        "type": "BRIEFADRES",
                    }
                ],
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993655",
                        "loon_uit_dienstbetrekking": 0,
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": 0,
                    }
                ]
            },
            "GEMEENTE_AMSTERDAM": {
                "werk_en_re_integratie": [
                    {
                        "bsn": "999993655",
                        "arbeidsvermogen": "VOLLEDIG",
                        "re_integratie_traject": "Werkstage",
                    }
                ]
            },
        },
    },
    "999993656": {
        "name": "Peter Bakker",
        "description": "ZZP'er met laag inkomen, recht op aanvullende bijstand en startkapitaal",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993656",
                        "geboortedatum": "1985-01-01",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                    }
                ],
                "relaties": [
                    {
                        "bsn": "999993656",
                        "partnerschap_type": "GEEN",
                        "partner_bsn": None,
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "999993656",
                        "straat": "Kalverstraat",
                        "huisnummer": "1",
                        "postcode": "1012NX",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993656",
                        "loon_uit_dienstbetrekking": 0,
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 50000,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": 0,
                    }
                ]
            },
            "KVK": {
                "inschrijvingen": [
                    {
                        "bsn": "999993656",
                        "rechtsvorm": "EENMANSZAAK",
                        "status": "ACTIEF",
                        "activiteit": "Webdesign",
                    }
                ]
            },
        },
    },
    "999993657": {
        "name": "Emma Visser",
        "description": "Persoon met medische ontheffing, recht op bijstand zonder re-integratieverplichting",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993657",
                        "geboortedatum": "1975-01-01",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                    }
                ],
                "relaties": [
                    {
                        "bsn": "999993657",
                        "partnerschap_type": "GEEN",
                        "partner_bsn": None,
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "999993657",
                        "straat": "Kalverstraat",
                        "huisnummer": "1",
                        "postcode": "1012NX",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
            },
            "GEMEENTE_AMSTERDAM": {
                "werk_en_re_integratie": [
                    {
                        "bsn": "999993657",
                        "arbeidsvermogen": "MEDISCH_VOLLEDIG",
                        "ontheffing_reden": "Chronische ziekte",
                        "ontheffing_einddatum": "2026-01-01",
                    }
                ]
            },
        },
    },
    "999993658": {
        "name": "Thomas Mulder",
        "description": "Student met laag inkomen en studiefinanciering, recht op zorgtoeslag",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993658",
                        "geboortedatum": "2004-01-01",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                    }
                ],
                "relaties": [
                    {
                        "bsn": "999993658",
                        "partnerschap_type": "GEEN",
                        "partner_bsn": None,
                    }
                ],
            },
            "RVZ": {"verzekeringen": [{"bsn": "999993658", "polis_status": "ACTIEF"}]},
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993658",
                        "loon_uit_dienstbetrekking": 15000,
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": 0,
                    }
                ]
            },
            "DUO": {
                "inschrijvingen": [{"bsn": "999993658", "onderwijstype": "WO"}],
                "studiefinanciering": [{"bsn": "999993658", "aantal_studerend_gezin": 0}],
            },
        },
    },
    "999993659": {
        "name": "Anna Schmidt",
        "description": "Duitse student zonder stemrecht voor de Tweede Kamer",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993659",
                        "geboortedatum": "1990-01-01",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "DUITS",
                    }
                ],
                "relaties": [
                    {
                        "bsn": "999993659",
                        "partnerschap_type": "GEEN",
                        "partner_bsn": None,
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "999993659",
                        "straat": "Kalverstraat",
                        "huisnummer": "1",
                        "postcode": "1012NX",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
            },
            "DUO": {"inschrijvingen": [{"bsn": "999993659", "onderwijstype": "WO"}]},
        },
    },
}


def get_profile_data(bsn: str) -> dict[str, Any] | None:
    """Get profile data for a specific BSN"""
    return PROFILES.get(bsn)


def get_all_profiles() -> dict[str, dict[str, Any]]:
    """Get all available profiles"""
    return PROFILES
