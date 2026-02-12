from datetime import date, datetime
from enum import Enum
from typing import Any

from eventsourcing.domain import Aggregate, event
from eventsourcing.persistence import Transcoding


class CaseStatus(str, Enum):
    # Application review states
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    DECIDED = "DECIDED"
    OBJECTED = "OBJECTED"

    # Toeslag lifecycle states (AWIR process)
    BEREKEND = "BEREKEND"  # Aanspraak berekend (AWIR Art. 16 lid 1)
    VOORSCHOT = "VOORSCHOT"  # Voorschotbeschikking vastgesteld (AWIR Art. 16)
    LOPEND = "LOPEND"  # Maandelijkse cyclus actief
    DEFINITIEF = "DEFINITIEF"  # Definitieve beschikking (AWIR Art. 19)
    VEREFFEND = "VEREFFEND"  # Vereffening uitgevoerd (AWIR Art. 24, 26a)
    AFGEWEZEN = "AFGEWEZEN"  # Aanvraag afgewezen (AWIR Art. 16 lid 4)
    BEEINDIGD = "BEEINDIGD"  # Toeslag beëindigd


class CaseStatusTranscoding(Transcoding):
    @staticmethod
    def can_handle(obj: object) -> bool:
        return isinstance(obj, CaseStatus | str)

    @staticmethod
    def encode(obj: CaseStatus) -> str:
        if isinstance(obj, str):
            return obj
        return obj.value

    @staticmethod
    def decode(data: str) -> str:
        if isinstance(data, CaseStatus):
            return data.value
        return data  # Keep it as a string


Transcoding.register(CaseStatusTranscoding)


class Case(Aggregate):
    @event("Submitted")
    def __init__(
        self,
        bsn: str,
        service_type: str,
        law: str,
        parameters: dict,
        claimed_result: dict,
        verified_result: dict,
        rulespec_uuid: str,
        approved_claims_only: bool,
        aanvraag_datum: date | None = None,
    ) -> None:
        self.claim_ids = None
        self.bsn = bsn
        self.service = service_type
        self.law = law
        self.rulespec_uuid = rulespec_uuid

        self.approved_claims_only = approved_claims_only
        self.claimed_result = claimed_result
        self.verified_result = verified_result
        self.parameters = parameters
        self.disputed_parameters = None
        self.evidence = None
        self.reason = None
        self.verifier_id = None
        self.objection_status = None

        # Add created_at timestamp - use provided aanvraag_datum or current time
        self.created_at = datetime.combine(aanvraag_datum, datetime.min.time()) if aanvraag_datum else datetime.now()

        self.approved = None
        self.status = CaseStatus.SUBMITTED

        # Toeslag lifecycle fields (AWIR process)
        # Berekende aanspraak
        self.heeft_aanspraak: bool | None = None
        self.berekend_jaarbedrag: int | None = None  # in eurocent

        # Voorschot
        self.voorschot_jaarbedrag: int | None = None
        self.voorschot_maandbedrag: int | None = None
        self.voorschot_beschikking_datum: date | None = None

        # Afwijzing
        self.afwijzing_datum: date | None = None

        # Maandelijkse gegevens
        self.huidige_maand: int = 0
        self.maandelijkse_berekeningen: list[dict[str, Any]] = []
        self.maandelijkse_betalingen: list[dict[str, Any]] = []

        # Definitieve afrekening
        self.definitief_jaarbedrag: int | None = None
        self.definitieve_beschikking_datum: date | None = None

        # Vereffening
        self.vereffening_type: str | None = None  # NABETALING, TERUGVORDERING, GEEN
        self.vereffening_bedrag: int | None = None
        self.vereffening_datum: date | None = None

        # IB-aanslag (AWIR Art. 19)
        self.ib_aanslag_inkomen: int | None = None
        self.ib_aanslag_datum: date | None = None
        self.deadline_definitief: date | None = None
        self.kwijtschelding_reden: str | None = None

        # Beschikkingen historie
        self.beschikkingen: list[dict[str, Any]] = []

        # Berekeningsjaar (extracted from parameters, or derived from created_at)
        self.berekeningsjaar: int | None = parameters.get("berekeningsjaar") or self.created_at.year

        # Year transition tracking (voor multi-jaar toeslagen)
        self.vorig_jaar_case_id: str | None = None

    @event("LinkedToPreviousYear")
    def link_to_previous_year(self, vorig_jaar_case_id: str) -> None:
        """Link this case to the previous year's case (automatic continuation)"""
        self.vorig_jaar_case_id = vorig_jaar_case_id

    @event("Reset")
    def reset(
        self,
        parameters: dict,
        claimed_result: dict,
        verified_result: dict,
        approved_claims_only: bool,
    ) -> None:
        """Reset a case with new parameters and results"""
        self.approved_claims_only = approved_claims_only
        self.claimed_result = claimed_result
        self.verified_result = verified_result
        self.parameters = parameters
        self.disputed_parameters = None
        self.evidence = None
        self.reason = None
        self.verifier_id = None
        self.status = CaseStatus.SUBMITTED
        self.approved = None

    @event("AutomaticallyDecided")
    def decide_automatically(self, verified_result: dict, parameters: dict, approved: bool) -> None:
        if self.status not in [CaseStatus.SUBMITTED, CaseStatus.OBJECTED]:
            raise ValueError("Can only automatically decide on submitted cases or objections")
        self.verified_result = verified_result
        self.parameters = parameters
        self.status = CaseStatus.DECIDED
        self.approved = approved

    @event("AddedToManualReview")
    def select_for_manual_review(
        self, verifier_id: str, reason: str, claimed_result: dict, verified_result: dict
    ) -> None:
        if self.status not in [CaseStatus.SUBMITTED, CaseStatus.OBJECTED, CaseStatus.BEREKEND]:
            raise ValueError("Can only add to review from submitted, objection or berekend status")
        self.status = CaseStatus.IN_REVIEW
        self.verified_result = verified_result
        self.claimed_result = claimed_result
        self.reason = reason
        self.verifier_id = verifier_id

    @event("Decided")
    def decide(self, verified_result: dict, reason: str, verifier_id: str, approved: bool) -> None:
        if self.status not in [CaseStatus.IN_REVIEW, CaseStatus.OBJECTED]:
            raise ValueError("Can only manually decide on cases in review or objections")
        self.status = CaseStatus.DECIDED
        self.approved = approved
        self.reason = reason
        self.verified_result = verified_result
        self.verifier_id = verifier_id

    @event("Objected")
    def object(self, reason: str) -> None:
        if self.status not in [CaseStatus.DECIDED, CaseStatus.AFGEWEZEN]:
            raise ValueError("Can only object decided or rejected cases")
        self.status = CaseStatus.OBJECTED
        self.reason = reason

    @event("ObjectionStatusDetermined")
    def determine_objection_status(
        self,
        possible: bool | None = None,  # bezwaar_mogelijk
        not_possible_reason: str | None = None,  # reden_niet_mogelijk
        objection_period: int | None = None,  # bezwaartermijn in weeks
        decision_period: int | None = None,  # beslistermijn in weeks
        extension_period: int | None = None,
    ) -> None:  # verdagingstermijn in weeks
        """Determine the objection status and periods"""
        if not hasattr(self, "objection_status") or self.objection_status is None:
            self.objection_status = {}

        updates = {}
        if possible is not None:
            updates["possible"] = possible
        if not_possible_reason is not None:
            updates["not_possible_reason"] = not_possible_reason
        if objection_period is not None:
            updates["objection_period"] = objection_period
        if decision_period is not None:
            updates["decision_period"] = decision_period
        if extension_period is not None:
            updates["extension_period"] = extension_period

        self.objection_status.update(updates)

    @event("ObjectionAdmissibilityDetermined")
    def determine_objection_admissibility(self, admissible: bool | None = None) -> None:
        """Determine whether an objection is admissible (ontvankelijk)"""
        if not hasattr(self, "objection_status") or self.objection_status is None:
            self.objection_status = {}

        if admissible is not None:
            self.objection_status["admissible"] = admissible

    def can_object(self) -> bool:
        """
        Check if objection is possible for this case.
        Returns False if:
        - objection_status is not set
        - possible flag is not set
        - possible flag is explicitly set to False
        """
        if not hasattr(self, "objection_status") or self.objection_status is None:
            return False
        return bool(self.objection_status.get("possible", False))

    @event("AppealStatusDetermined")
    def determine_appeal_status(
        self,
        possible: bool | None = None,  # beroep_mogelijk
        not_possible_reason: str | None = None,  # reden_niet_mogelijk
        appeal_period: int | None = None,  # beroepstermijn in weeks
        direct_appeal: bool | None = None,  # direct beroep mogelijk
        direct_appeal_reason: str | None = None,  # reden voor direct beroep
        competent_court: str | None = None,  # bevoegde rechtbank
        court_type: str | None = None,  # type rechter
    ) -> None:
        """Determine the appeal status and periods for a case"""
        if not hasattr(self, "appeal_status") or self.appeal_status is None:
            self.appeal_status = {}

        updates = {}
        if possible is not None:
            updates["possible"] = possible
        if not_possible_reason is not None:
            updates["not_possible_reason"] = not_possible_reason
        if appeal_period is not None:
            updates["appeal_period"] = appeal_period
        if direct_appeal is not None:
            updates["direct_appeal"] = direct_appeal
        if direct_appeal_reason is not None:
            updates["direct_appeal_reason"] = direct_appeal_reason
        if competent_court is not None:
            updates["competent_court"] = competent_court
        if court_type is not None:
            updates["court_type"] = court_type

        self.appeal_status.update(updates)

    def can_appeal(self) -> bool:
        """
        Check if appeal is possible for this case.
        Returns False if:
        - appeal_status is not set
        - possible flag is not set
        - possible flag is explicitly set to False
        """
        if not hasattr(self, "appeal_status") or self.appeal_status is None:
            return False
        return bool(self.appeal_status.get("possible", False))

    @event("ClaimCreated")
    def add_claim(self, claim_id: str) -> None:
        """Record when a new claim is created for this case"""
        if not hasattr(self, "claim_ids") or self.claim_ids is None:
            self.claim_ids = set()
        self.claim_ids.add(claim_id)

    @event("ClaimApproved")
    def approve_claim(self, claim_id: str) -> None:
        """Record when a claim is approved"""
        if not hasattr(self, "claim_ids") or self.claim_ids is None:
            self.claim_ids = set()
        if claim_id not in self.claim_ids:
            self.claim_ids.add(claim_id)

    @event("ClaimRejected")
    def reject_claim(self, claim_id: str) -> None:
        """Record when a claim is rejected"""
        if not hasattr(self, "claim_ids") or self.claim_ids is None:
            self.claim_ids = set()
        if claim_id not in self.claim_ids:
            self.claim_ids.add(claim_id)

    # =========================================================================
    # Toeslag lifecycle events (AWIR process)
    # =========================================================================

    @event("AanspraakBerekend")
    def bereken_aanspraak(
        self,
        heeft_aanspraak: bool,
        berekend_jaarbedrag: int,
        berekening_datum: date | None = None,
        berekening_details: dict[str, Any] | None = None,
    ) -> None:
        """Aanspraak op toeslag berekend (AWIR Art. 16 lid 1)"""
        self.heeft_aanspraak = heeft_aanspraak
        self.berekend_jaarbedrag = berekend_jaarbedrag
        self.status = CaseStatus.BEREKEND

    @event("Afgewezen")
    def wijs_af(
        self,
        reden: str,
        afwijzing_datum: date | None = None,
    ) -> None:
        """Aanvraag afgewezen wegens geen aanspraak (AWIR Art. 16 lid 4)"""
        self.status = CaseStatus.AFGEWEZEN
        self.afwijzing_datum = afwijzing_datum or date.today()
        if not hasattr(self, "beschikkingen") or self.beschikkingen is None:
            self.beschikkingen = []
        self.beschikkingen.append(
            {
                "type": "AFWIJZING",
                "datum": self.afwijzing_datum,
                "reden": reden,
            }
        )

    @event("VoorschotBeschikkingVastgesteld")
    def stel_voorschot_vast(
        self,
        jaarbedrag: int,
        maandbedrag: int,
        beschikking_datum: date | None = None,
    ) -> None:
        """Voorschotbeschikking vastgesteld (AWIR Art. 16)"""
        self.voorschot_jaarbedrag = jaarbedrag
        self.voorschot_maandbedrag = maandbedrag
        self.voorschot_beschikking_datum = beschikking_datum or date.today()
        self.status = CaseStatus.VOORSCHOT

        if not hasattr(self, "beschikkingen") or self.beschikkingen is None:
            self.beschikkingen = []

        # Only add beschikking if there isn't already a VOORSCHOT beschikking
        has_voorschot = any(b.get("type") == "VOORSCHOT" for b in self.beschikkingen)
        if not has_voorschot:
            self.beschikkingen.append(
                {
                    "type": "VOORSCHOT",
                    "datum": self.voorschot_beschikking_datum,
                    "jaarbedrag": jaarbedrag,
                    "maandbedrag": maandbedrag,
                }
            )

    @event("MaandGestart")
    def start_maand(self, maand: int) -> None:
        """Start van een nieuwe maand in het toeslagjaar"""
        self.huidige_maand = maand
        if self.status == CaseStatus.VOORSCHOT:
            self.status = CaseStatus.LOPEND

    @event("MaandHerberekend")
    def herbereken_maand(
        self,
        maand: int,
        berekend_bedrag: int,
        berekening_datum: date | None = None,
        trigger: str = "schedule",  # "schedule" of "data_change"
        gewijzigde_data: list[str] | None = None,
    ) -> None:
        """Maandelijkse herberekening uitgevoerd (AWIR Art. 16 lid 5, Art. 17)"""
        if not hasattr(self, "maandelijkse_berekeningen") or self.maandelijkse_berekeningen is None:
            self.maandelijkse_berekeningen = []
        self.maandelijkse_berekeningen.append(
            {
                "maand": maand,
                "berekend_bedrag": berekend_bedrag,
                "berekening_datum": berekening_datum or date.today(),
                "trigger": trigger,
                "gewijzigde_data": gewijzigde_data or [],
            }
        )

    @event("MaandBetaald")
    def betaal_maand(
        self,
        maand: int,
        betaald_bedrag: int,
        betaal_datum: date | None = None,
        basis: str = "voorschot",  # "voorschot" of "herzien"
    ) -> None:
        """Maandelijkse betaling uitgevoerd (AWIR Art. 22)"""
        if not hasattr(self, "maandelijkse_betalingen") or self.maandelijkse_betalingen is None:
            self.maandelijkse_betalingen = []
        self.maandelijkse_betalingen.append(
            {
                "maand": maand,
                "betaald_bedrag": betaald_bedrag,
                "betaal_datum": betaal_datum or date.today(),
                "basis": basis,
            }
        )

    @event("VoorschotHerzien")
    def herzien_voorschot(
        self,
        nieuw_jaarbedrag: int,
        nieuw_maandbedrag: int,
        reden: str,
        herzien_datum: date | None = None,
    ) -> None:
        """Voorschot herzien na wijziging (AWIR Art. 16 lid 5)"""
        self.voorschot_jaarbedrag = nieuw_jaarbedrag
        self.voorschot_maandbedrag = nieuw_maandbedrag

        if not hasattr(self, "beschikkingen") or self.beschikkingen is None:
            self.beschikkingen = []
        self.beschikkingen.append(
            {
                "type": "HERZIEN_VOORSCHOT",
                "datum": herzien_datum or date.today(),
                "jaarbedrag": nieuw_jaarbedrag,
                "maandbedrag": nieuw_maandbedrag,
                "reden": reden,
            }
        )

    @event("DefinitieveBeschikkingVastgesteld")
    def stel_definitief_vast(
        self,
        definitief_jaarbedrag: int,
        beschikking_datum: date | None = None,
    ) -> None:
        """Definitieve beschikking vastgesteld (AWIR Art. 19)"""
        self.definitief_jaarbedrag = definitief_jaarbedrag
        self.definitieve_beschikking_datum = beschikking_datum or date.today()
        self.status = CaseStatus.DEFINITIEF

        if not hasattr(self, "beschikkingen") or self.beschikkingen is None:
            self.beschikkingen = []
        self.beschikkingen.append(
            {
                "type": "DEFINITIEF",
                "datum": self.definitieve_beschikking_datum,
                "jaarbedrag": definitief_jaarbedrag,
            }
        )

    @event("Vereffend")
    def vereffen(
        self,
        vereffening_type: str,  # "NABETALING", "TERUGVORDERING", "GEEN"
        vereffening_bedrag: int,
        vereffening_datum: date | None = None,
    ) -> None:
        """Vereffening uitgevoerd (AWIR Art. 24, Art. 26a)"""
        self.vereffening_type = vereffening_type
        self.vereffening_bedrag = vereffening_bedrag
        self.status = CaseStatus.VEREFFEND

        if not hasattr(self, "beschikkingen") or self.beschikkingen is None:
            self.beschikkingen = []
        self.beschikkingen.append(
            {
                "type": f"VEREFFENING_{vereffening_type}",
                "datum": vereffening_datum or date.today(),
                "bedrag": vereffening_bedrag,
            }
        )

    @event("Beeindigd")
    def beeindig(self, reden: str, einddatum: date | None = None) -> None:
        """Toeslag beëindigd (bijv. geen voortzetting volgend jaar)"""
        self.status = CaseStatus.BEEINDIGD

    @event("IBAanslagOntvangen")
    def ib_aanslag_ontvangen(
        self,
        vastgesteld_inkomen: int,
        aanslag_datum: date,
        deadline_definitief: date,
    ) -> None:
        """
        IB-aanslag ontvangen (AWIR Art. 19 trigger).

        Dit event triggert de definitieve vaststellingsprocedure:
        - 6 maanden na IB-aanslag moet definitieve beschikking zijn vastgesteld
        - Uiterlijk 31 december van het jaar volgend op het berekeningsjaar
        """
        self.ib_aanslag_inkomen = vastgesteld_inkomen
        self.ib_aanslag_datum = aanslag_datum
        self.deadline_definitief = deadline_definitief

        if not hasattr(self, "beschikkingen") or self.beschikkingen is None:
            self.beschikkingen = []
        self.beschikkingen.append(
            {
                "type": "IB_AANSLAG_ONTVANGEN",
                "datum": aanslag_datum,
                "vastgesteld_inkomen": vastgesteld_inkomen,
                "deadline_definitief": deadline_definitief,
            }
        )

    @event("TerugvorderingKwijtgescholden")
    def terugvordering_kwijtgescholden(
        self,
        oorspronkelijk_bedrag: int,
        reden: str,
        kwijtschelding_datum: date | None = None,
    ) -> None:
        """
        Terugvordering kwijtgescholden (AWIR Art. 26a).

        Art. 26a: Terugvorderingen onder de doelmatigheidsgrens (€116)
        worden niet ingevorderd maar kwijtgescholden.
        """
        self.vereffening_type = "KWIJTGESCHOLDEN"
        self.vereffening_bedrag = 0
        self.kwijtschelding_reden = reden
        self.status = CaseStatus.VEREFFEND

        if not hasattr(self, "beschikkingen") or self.beschikkingen is None:
            self.beschikkingen = []
        self.beschikkingen.append(
            {
                "type": "KWIJTSCHELDING",
                "datum": kwijtschelding_datum or date.today(),
                "oorspronkelijk_bedrag": oorspronkelijk_bedrag,
                "reden": reden,
            }
        )

    # =========================================================================
    # Toeslag helper properties
    # =========================================================================

    @property
    def totaal_betaald(self) -> int:
        """Som van alle betaalde bedragen"""
        if not hasattr(self, "maandelijkse_betalingen") or self.maandelijkse_betalingen is None:
            return 0
        return sum(b["betaald_bedrag"] for b in self.maandelijkse_betalingen)

    @property
    def totaal_berekend(self) -> int:
        """Som van alle herberekende bedragen"""
        if not hasattr(self, "maandelijkse_berekeningen") or self.maandelijkse_berekeningen is None:
            return 0
        return sum(b["berekend_bedrag"] for b in self.maandelijkse_berekeningen)

    @property
    def verschil_met_voorschot(self) -> int | None:
        """Verschil tussen herberekend en voorschot (positief = nabetaling)"""
        if self.definitief_jaarbedrag is None:
            return None
        return self.definitief_jaarbedrag - self.totaal_betaald

    def get_berekening_voor_maand(self, maand: int) -> dict[str, Any] | None:
        """Haal de laatste berekening op voor een specifieke maand"""
        if not hasattr(self, "maandelijkse_berekeningen") or self.maandelijkse_berekeningen is None:
            return None
        for b in reversed(self.maandelijkse_berekeningen):
            if b["maand"] == maand:
                return b
        return None

    def get_betaling_voor_maand(self, maand: int) -> dict[str, Any] | None:
        """Haal de betaling op voor een specifieke maand"""
        if not hasattr(self, "maandelijkse_betalingen") or self.maandelijkse_betalingen is None:
            return None
        for b in self.maandelijkse_betalingen:
            if b["maand"] == maand:
                return b
        return None

    # =========================================================================
    # Bericht onderwerp properties (voor YAML trigger mappings)
    # =========================================================================

    @property
    def _law_display_name(self) -> str:
        """Leesbare naam voor de wet (bijv. 'Zorgtoeslag' voor 'zorgtoeslagwet')"""
        # Map law identifiers to readable names
        law_names = {
            "zorgtoeslagwet": "Zorgtoeslag",
            "huurtoeslag": "Huurtoeslag",
            "kinderopvangtoeslag": "Kinderopvangtoeslag",
            "kindgebonden_budget": "Kindgebonden budget",
        }
        return law_names.get(self.law, self.law.replace("_", " ").title() if self.law else "Toeslag")

    @property
    def voorschot_onderwerp(self) -> str:
        """Onderwerp voor voorschotbeschikking bericht"""
        jaar = self.berekeningsjaar or (self.created_at.year if hasattr(self, "created_at") else "")
        return f"Uw voorschotbeschikking {self._law_display_name} {jaar}"

    @property
    def afwijzing_onderwerp(self) -> str:
        """Onderwerp voor afwijzingsbeschikking bericht"""
        jaar = self.berekeningsjaar or (self.created_at.year if hasattr(self, "created_at") else "")
        return f"Beslissing op uw aanvraag {self._law_display_name} {jaar}"

    @property
    def definitief_onderwerp(self) -> str:
        """Onderwerp voor definitieve beschikking bericht"""
        jaar = self.berekeningsjaar or (self.created_at.year if hasattr(self, "created_at") else "")
        return f"Uw definitieve beschikking {self._law_display_name} {jaar}"
