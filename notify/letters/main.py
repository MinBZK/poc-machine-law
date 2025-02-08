import tempfile
from pathlib import Path
from typst import compile
from typing import Optional
from datetime import datetime

from claims.aggregate import Claim, ClaimStatus


def create_brief(
        retouradres: str,
        addressee: str,
        addressee_title: str,
        addressee_address: str,
        addressee_postal: str,
        date: str,
        betreft: str,
        kenmerk: str,
        body_text: str,
        ondertekening: str,
        # New parameters
        ministerie: str = "Ministerie van Financiën",
        directoraat: str = "Directoraat-Generaal\nBelastingdienst",
        bezoekadres: str = "Korte Voorhout 7\n2511 CW Den Haag",
        postadres: str = "Postbus 20201\n2500 EE Den Haag",
        website: str = "www.rijksoverheid.nl",
        kenmerk_label: str = "Ons kenmerk",
        datum_label: str = "Datum",
        betreft_label: str = "Betreft",
        afsluiting: str = "Hoogachtend,",
        # Layout parameters
        main_column_width: str = "11cm",
        side_column_width: str = "4cm",
        label_column_width: str = "2.5cm",
) -> bytes:
    template = f"""
    #set page(
      margin: (left: 2.5cm, right: 2.5cm, top: 2.5cm, bottom: 2.5cm),
      paper: "a4"
    )

    #align(right)[
        #box(width: 3cm, height: 1.5cm)[ [{ministerie}] ]
    ]

    > {retouradres}

    #grid(
        columns: ({main_column_width}, {side_column_width}),
        gutter: 1cm,
        [
            {addressee}\\
            {addressee_title}\\
            {addressee_address}\\
            {addressee_postal}\\
            \\
            #grid(
                columns: ({label_column_width}, auto),
                gutter: 0cm,
                [
                {datum_label}\\
                {betreft_label}
                ],
                [
                {date}\\
                {betreft}
                ]
            )
        ],
        [
            *{directoraat}*\\
            \\
            {bezoekadres}\\
            {postadres}\\
            {website}\\
            \\
            *{kenmerk_label}*\\
            {kenmerk}
        ]
    )
    \\
    {body_text}
    \\
    \\
    {afsluiting}
    \\
    \\
    {ondertekening}
    """

    with tempfile.NamedTemporaryFile(mode='w', suffix='.typ', delete=False) as tmp:
        tmp.write(template)
        typ_path = Path(tmp.name)

    try:
        return compile(typ_path)
    finally:
        typ_path.unlink()


def generate_decision_letter(claim: Claim, service_name: str, status: ClaimStatus) -> bytes:
    """Generate a decision letter for a claim using the brief template"""

    # Format the addressee details from claim
    addressee_details = claim.citizen_data

    # Get explanation from claim evaluation
    explanation = claim.evaluation.explanation if claim.evaluation else ""

    # Configure service-specific branding
    service_branding = {
        "toeslagen": {
            "ministerie": "Ministerie van Financiën",
            "directoraat": "Directoraat-Generaal\nBelastingdienst",
        },
        "duo": {
            "ministerie": "Ministerie van Onderwijs, Cultuur en Wetenschap",
            "directoraat": "Dienst Uitvoering Onderwijs",
        },
        # Add more services as needed
    }

    branding = service_branding.get(service_name, service_branding["toeslagen"])

    # Generate decision text
    if status == ClaimStatus.APPROVED:
        decision_text = f"""Geachte {addressee_details.name},

Wij hebben uw aanvraag beoordeeld en besloten deze goed te keuren.

{explanation}

U hoeft geen verdere actie te ondernemen."""
    else:
        decision_text = f"""Geachte {addressee_details.name},

Wij hebben uw aanvraag beoordeeld en besloten deze af te wijzen.

{explanation}

Als u het niet eens bent met dit besluit, kunt u binnen zes weken bezwaar maken."""

    # Generate the PDF using create_brief
    return create_brief(
        retouradres=f"Retouradres {branding['directoraat']}",
        addressee=addressee_details.name,
        addressee_title="",  # Could be added to citizen data if needed
        addressee_address=addressee_details.street,
        addressee_postal=f"{addressee_details.postal_code} {addressee_details.city}",
        date=datetime.now().strftime("%d %B %Y"),
        betreft=f"Besluit aanvraag {claim.service_id}",
        kenmerk=claim.id,
        body_text=decision_text,
        ondertekening=f"Namens {branding['ministerie']},\n\nDe directeur",
        ministerie=branding['ministerie'],
        directoraat=branding['directoraat']
    )


# Example usage
if __name__ == "__main__":
    pdf_bytes = create_brief(
        retouradres="Retouradres Postbus 20201 2500 EE Den Haag",
        addressee="Autoriteit Persoonsgegevens",
        addressee_title="T.a.v. de heer mr. A. Wolfsen, voorzitter",
        addressee_address="Postbus 93374",
        addressee_postal="2509 AJ DEN HAAG",
        date="14 februari 2020",
        betreft="uw verzoek om inlichtingen inzake het onderzoek naar de verwerking van nationaliteit gegevens door Belastingdienst/Toeslagen",
        kenmerk="2020-0000009130",
        body_text="""Geachte heer Wolfsen,

Op 9 januari 2020 heeft de Autoriteit Persoonsgegevens (AP) een brief gestuurd.
In de brief verzoekt de AP om antwoord op een aantal vragen en om informatie.

De Belastingdienst/Toeslagen heeft de gevraagde informatie (documenten) op
27 januari 2020 aan de onderzoekers van de AP verstrekt.

De reactietermijn voor de beantwoording van de vragen is desgevraagd verlengd
tot en met 13 februari 2020.

Als bijlage bij deze brief stuur ik u de antwoorden op de vragen.

Een afschrift van deze brief wordt gestuurd aan de functionaris voor
gegevensbescherming bij het ministerie van Financiën.

Ik vertrouw erop u hiermee voldoende te hebben geïnformeerd.""",
        ondertekening="""De directeur-generaal Toeslagen,

R.J.A. Kerstens"""
    )

    # Save to file
    with open("brief.pdf", "wb") as f:
        f.write(pdf_bytes)
