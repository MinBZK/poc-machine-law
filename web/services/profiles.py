from typing import Any

# Global service data that applies to all profiles
GLOBAL_SERVICES = {
    "CBS": {"levensverwachting": [{"jaar": 2025, "verwachting_65": 20.5}]},
    "KIESRAAD": {"verkiezingen": [{"type": "TWEEDE_KAMER", "verkiezingsdatum": "2025-05-05"}]},
    "JenV": {
        "jurisdicties": [
            {"gemeente": "Amsterdam", "arrondissement": "AMSTERDAM", "rechtbank": "RECHTBANK_AMSTERDAM"},
            {"gemeente": "Amstelveen", "arrondissement": "AMSTERDAM", "rechtbank": "RECHTBANK_AMSTERDAM"},
            {"gemeente": "Haarlem", "arrondissement": "NOORD-HOLLAND", "rechtbank": "RECHTBANK_NOORD_HOLLAND"},
            {"gemeente": "Alkmaar", "arrondissement": "NOORD-HOLLAND", "rechtbank": "RECHTBANK_NOORD_HOLLAND"},
            {"gemeente": "Rotterdam", "arrondissement": "ROTTERDAM", "rechtbank": "RECHTBANK_ROTTERDAM"},
            {"gemeente": "Utrecht", "arrondissement": "MIDDEN-NEDERLAND", "rechtbank": "RECHTBANK_MIDDEN_NEDERLAND"},
            {"gemeente": "Den Haag", "arrondissement": "DEN_HAAG", "rechtbank": "RECHTBANK_DEN_HAAG"},
            {"gemeente": "Groningen", "arrondissement": "NOORD-NEDERLAND", "rechtbank": "RECHTBANK_NOORD_NEDERLAND"},
            {"gemeente": "Maastricht", "arrondissement": "LIMBURG", "rechtbank": "RECHTBANK_LIMBURG"},
            {"gemeente": "Arnhem", "arrondissement": "GELDERLAND", "rechtbank": "RECHTBANK_GELDERLAND"},
        ]
    },
}
PROFILES = {
    "777777777": {
        "name": "Fatima Al-Zahra",
        "description": "Alleenstaande met laag inkomen en hoge huur, komt in aanmerking voor huurtoeslag",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "777777777",
                        "geboortedatum": "1991-04-15",
                        "verblijfsadres": "Utrecht",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "MAROKKAANS",
                    }
                ],
                "relaties": [
                    {
                        "bsn": "777777777",
                        "partnerschap_type": "GEEN",
                        "partner_bsn": None,
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "777777777",
                        "straat": "Rooseveltlaan",
                        "huisnummer": "42",
                        "postcode": "3527AK",
                        "woonplaats": "Utrecht",
                        "type": "WOONADRES",
                    }
                ],
            },
            "RVZ": {
                "verzekeringen": [
                    {
                        "bsn": "777777777",
                        "polis_status": "ACTIEF",
                        "verdrag_status": "GEEN",
                        "zorg_type": "BASIS",
                    }
                ]
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "777777777",
                        "loon_uit_dienstbetrekking": 1750000,
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 25000,
                        "eigen_woning": 0,
                    }
                ],
                "box2": [{"bsn": "777777777", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "777777777",
                        "spaargeld": 1200000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "777777777", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "777777777", "persoonsgebonden_aftrek": 85000}],
            },
            "IND": {
                "verblijfsvergunningen": [
                    {
                        "bsn": "777777777",
                        "type": "ONBEPAALDE_TIJD_REGULIER",
                        "status": "VERLEEND",
                        "ingangsdatum": "2010-05-12",
                        "einddatum": None,
                    }
                ]
            },
        },
    },
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
                        "loon_uit_dienstbetrekking": 1850000,
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": -60000,
                    }
                ],
                "box2": [{"bsn": "999993653", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
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
                "aftrekposten": [{"bsn": "999993653", "persoonsgebonden_aftrek": 120000}],
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
                        "uitkeringen_en_pensioenen": 1380000,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": -75000,
                    }
                ],
                "box2": [{"bsn": "999993654", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "999993654",
                        "spaargeld": 8500000,
                        "beleggingen": 3700000,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993654", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "999993654", "persoonsgebonden_aftrek": 230000}],
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
                ],
                "box2": [{"bsn": "999993655", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "999993655",
                        "spaargeld": 250000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993655", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "999993655", "persoonsgebonden_aftrek": 0}],
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
                        "winst_uit_onderneming": 3850000,  # Verhoogd naar €38.500
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": -110000,
                    }
                ],
                "box2": [{"bsn": "999993656", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "999993656",
                        "spaargeld": 1550000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993656", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "999993656", "persoonsgebonden_aftrek": 850000}],
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
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993657",
                        "loon_uit_dienstbetrekking": 0,
                        "uitkeringen_en_pensioenen": 1089000,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": -45000,
                    }
                ],
                "box2": [{"bsn": "999993657", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "999993657",
                        "spaargeld": 3250000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993657", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "999993657", "persoonsgebonden_aftrek": 180000}],
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
                "verblijfplaats": [
                    {
                        "bsn": "999993658",
                        "straat": "Science Park",
                        "huisnummer": "123",
                        "postcode": "1098XG",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
            },
            "RVZ": {"verzekeringen": [{"bsn": "999993658", "polis_status": "ACTIEF"}]},
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993658",
                        "loon_uit_dienstbetrekking": 825000,
                        "uitkeringen_en_pensioenen": 1025000,  # Studiefinanciering
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 230000,  # Bijbaantjes
                        "eigen_woning": 0,
                    }
                ],
                "box2": [{"bsn": "999993658", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "999993658",
                        "spaargeld": 1200000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 1800000,  # Studieschuld
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993658", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "999993658", "persoonsgebonden_aftrek": 75000}],
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
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993659",
                        "loon_uit_dienstbetrekking": 1750000,
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 350000,
                        "eigen_woning": 0,
                    }
                ],
                "box2": [{"bsn": "999993659", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "999993659",
                        "spaargeld": 950000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993659", "bedrag": 450000, "land": "DUITSLAND"}],
                "aftrekposten": [{"bsn": "999993659", "persoonsgebonden_aftrek": 65000}],
            },
            "DUO": {"inschrijvingen": [{"bsn": "999993659", "onderwijstype": "WO"}]},
            "IND": {
                "verblijfsvergunningen": [
                    {
                        "bsn": "999993659",
                        "type": "STUDIE",
                        "status": "VERLEEND",
                        "ingangsdatum": "2022-09-01",
                        "einddatum": "2025-08-31",
                    }
                ]
            },
        },
    },
    "999993660": {
        "name": "Lisa de Jong",
        "description": "Werkende ouder met jong kind, komt in aanmerking voor inkomensafhankelijke combinatiekorting",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993660",
                        "geboortedatum": "1998-05-15",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                    }
                ],
                "relaties": [
                    {
                        "bsn": "999993660",
                        "partnerschap_type": "GEEN",
                        "partner_bsn": None,
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "999993660",
                        "straat": "Prinsengracht",
                        "huisnummer": "42",
                        "postcode": "1015DX",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
                "CHILDREN_DATA": [{"bsn": "999993660", "kinderen": [{"geboortedatum": "2020-01-01"}]}],
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993660",
                        "loon_uit_dienstbetrekking": 3000000,
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": -90000,
                    }
                ],
                "box2": [{"bsn": "999993660", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "999993660",
                        "spaargeld": 2000000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "aftrekposten": [
                    {
                        "bsn": "999993660",
                        "persoonsgebonden_aftrek": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993660", "bedrag": 0, "land": "GEEN"}],
            },
            "RVZ": {
                "verzekeringen": [
                    {
                        "bsn": "999993660",
                        "polis_status": "ACTIEF",
                        "verdrag_status": "GEEN",
                        "zorg_type": "BASIS",
                    }
                ]
            },
        },
    },
}


def get_profile_data(bsn: str) -> dict[str, Any] | None:
    """Get profile data for a specific BSN"""
    return PROFILES.get(bsn)


def get_all_profiles() -> dict[str, dict[str, Any]]:
    """Get all available profiles"""
    return PROFILES
