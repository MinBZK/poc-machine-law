"""Dashboard router for aggregate views and total calculations"""

from fastapi import APIRouter, Depends, Request

from web.dependencies import TODAY, get_machine_service, templates
from web.engines import EngineInterface

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# Map of laws to their output field names and whether they're per month (True) or per year (False)
LAW_MAPPING = {
    "zorgtoeslagwet": {
        "field": "hoogte_toeslag",
        "per_month": False,  # Yearly amount
        "type": "benefit",
        "display_name": "Zorgtoeslag",
    },
    "wet_op_de_huurtoeslag": {
        "field": "subsidiebedrag",
        "per_month": True,  # Monthly amount
        "type": "benefit",
        "display_name": "Huurtoeslag",
        "condition_field": "is_gerechtigd",  # Only count if this is True
    },
    "participatiewet/bijstand": {
        "field": "uitkeringsbedrag",
        "per_month": True,  # Monthly amount
        "type": "benefit",
        "display_name": "Bijstand",
    },
    "algemene_ouderdomswet": {
        "field": "pensioenbedrag",
        "per_month": True,  # Monthly amount
        "type": "benefit",
        "display_name": "AOW-pensioen",
    },
    "werkloosheidswet": {
        "field": "ww_uitkering_per_maand",
        "per_month": True,  # Monthly amount
        "type": "benefit",
        "display_name": "WW-uitkering",
    },
    "wet_op_het_kindgebonden_budget": {
        "field": "kindgebonden_budget_jaar",
        "per_month": False,  # Yearly amount
        "type": "benefit",
        "display_name": "Kindgebonden budget",
    },
    "wet_kinderopvang": {
        "field": "jaarbedrag",
        "per_month": False,  # Yearly amount
        "type": "benefit",
        "display_name": "Kinderopvangtoeslag",
        "condition_field": "is_gerechtigd",  # Only count if this is True
    },
    "wet_inkomstenbelasting": {
        "field": "totale_belastingschuld",
        "per_month": False,  # Yearly amount
        "type": "tax",
        "display_name": "Inkomstenbelasting",
    },
}


def calculate_yearly_amount(amount_in_cents: int, per_month: bool) -> int:
    """Convert amount to yearly total in cents"""
    if per_month:
        return amount_in_cents * 12
    return amount_in_cents


@router.get("/total-net-income")
async def total_net_income(
    request: Request,
    bsn: str,
    date: str = None,
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """Calculate total net income (benefits - taxes) for a citizen"""

    benefits = []
    taxes = []
    errors = []

    # Get all discoverable laws for this BSN
    discoverable_laws = machine_service.get_sorted_discoverable_service_laws(bsn)

    for service_law in discoverable_laws:
        service = service_law["service"]
        law = service_law["law"]

        # Check if we have mapping for this law
        if law not in LAW_MAPPING:
            continue

        law_config = LAW_MAPPING[law]

        try:
            # Evaluate the law
            result = machine_service.evaluate(
                service=service,
                law=law,
                parameters={"BSN": bsn},
                reference_date=TODAY,
                effective_date=date,  # Pass the date as effective_date
                approved=False,  # Show current state including pending changes
            )

            # Check if there's a condition field (e.g., is_gerechtigd for huurtoeslag)
            if "condition_field" in law_config:
                condition_met = result.output.get(law_config["condition_field"], False)
                if not condition_met:
                    continue  # Skip this law if condition not met

            # Get the amount
            amount = result.output.get(law_config["field"], 0)

            if amount and amount > 0:
                yearly_amount = calculate_yearly_amount(amount, law_config["per_month"])

                item = {
                    "law": law,
                    "service": service,
                    "name": law_config["display_name"],
                    "amount_cents": amount,
                    "yearly_amount_cents": yearly_amount,
                    "per_month": law_config["per_month"],
                    "monthly_display": amount / 100 if law_config["per_month"] else (amount / 12) / 100,
                    "yearly_display": yearly_amount / 100,
                }

                if law_config["type"] == "benefit":
                    benefits.append(item)
                else:
                    taxes.append(item)

        except Exception as e:
            errors.append({"law": law, "service": service, "error": str(e)})

    # Calculate totals
    total_benefits_yearly = sum(b["yearly_amount_cents"] for b in benefits)
    total_taxes_yearly = sum(t["yearly_amount_cents"] for t in taxes)
    net_income_yearly = total_benefits_yearly - total_taxes_yearly

    # Calculate monthly equivalents
    total_benefits_monthly = total_benefits_yearly / 12
    total_taxes_monthly = total_taxes_yearly / 12
    net_income_monthly = net_income_yearly / 12

    return templates.TemplateResponse(
        "partials/dashboard_total_widget.html",
        {
            "request": request,
            "bsn": bsn,
            "benefits": benefits,
            "taxes": taxes,
            "total_benefits_yearly_cents": total_benefits_yearly,
            "total_taxes_yearly_cents": total_taxes_yearly,
            "net_income_yearly_cents": net_income_yearly,
            "total_benefits_monthly_cents": total_benefits_monthly,
            "total_taxes_monthly_cents": total_taxes_monthly,
            "net_income_monthly_cents": net_income_monthly,
            "errors": errors,
        },
    )
