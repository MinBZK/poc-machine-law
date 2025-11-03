import itertools
import json
import logging
import random
import sys
import uuid
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm.auto import tqdm

from machine.law_parameter_config import (
    _ensure_registry_initialized,
    create_overrides,
    find_law_config_by_technical_name,
)
from machine.service import Services

# Create a logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# Directory for storing populations
POPULATIONS_DIR = Path("data/populations")


class LawSimulator:
    def __init__(self, simulation_date="2025-03-01", law_parameters=None) -> None:
        self.simulation_date = simulation_date
        self.services = Services(simulation_date)

        # Initialize the law parameter registry with our Services instance
        # This prevents eventsourcing conflicts in subprocess contexts
        _ensure_registry_initialized(services=self.services)

        self.results = []
        self.used_bsns = set()  # Track used BSNs
        self.law_parameters = law_parameters or {}

        # DEBUG: Log received law parameters
        if self.law_parameters:
            logger.info(f"Received law_parameters with keys: {list(self.law_parameters.keys())}")
            for law_name, params in self.law_parameters.items():
                if params:
                    logger.info(f"  {law_name}: {len(params)} parameters")

        # CBS demographic data for more realistic simulation
        self.age_distribution = {
            (18, 30): 0.18,  # 18-30 year olds: 18%
            (30, 45): 0.25,  # 30-45 year olds: 25%
            (45, 67): 0.32,  # 45-67 year olds: 32%
            (67, 85): 0.20,  # 67-85 year olds: 20%
            (85, 100): 0.05,  # 85+ year olds: 5%
        }

        # Income distribution (log-normal parameters) based on income deciles
        # Adjusted to create more variation
        self.income_distribution_params = {
            "low": {"mean": 9.9, "sigma": 0.5},  # Lower incomes (avg ~€20k)
            "middle": {"mean": 10.7, "sigma": 0.3},  # Middle incomes (avg ~€44k)
            "high": {"mean": 11.3, "sigma": 0.45},  # Higher incomes (avg ~€80k)
        }

        # Add some people with zero income to qualify for bijstand
        self.zero_income_prob = 0.05  # 5% chance of having zero income

        # Housing information based on CBS data
        self.housing_distribution = {
            "rent": 0.43,  # 43% renters
            "own": 0.57,  # 57% homeowners
        }

        # Rent cost distributions (in euros) for rent calculation
        # Updated to reflect 2025 Dutch rental market
        # Social housing: €650-€808 (liberalization threshold 2025)
        # Private sector: €900-€1500+
        self.rent_distribution = {
            "low": (550, 700),  # Social housing range
            "medium": (700, 850),  # Upper social/lower private
            "high": (850, 1200),  # Private sector (some eligible for huurtoeslag)
        }

    @staticmethod
    def save_population(population_id: str, people: list, params: dict) -> None:
        """Save a population to disk for reuse."""
        POPULATIONS_DIR.mkdir(parents=True, exist_ok=True)

        # Convert dates to ISO format for JSON serialization
        serializable_people = []
        for person in people:
            person_copy = person.copy()
            person_copy["birth_date"] = person["birth_date"].isoformat()
            # Convert children data
            if "children_data" in person_copy:
                for child in person_copy["children_data"]:
                    child["birth_date"] = child["birth_date"].isoformat()
            serializable_people.append(person_copy)

        # Save population data
        population_file = POPULATIONS_DIR / f"{population_id}.json"
        with open(population_file, "w") as f:
            json.dump(serializable_people, f, indent=2)

        # Save metadata
        metadata = {
            "population_id": population_id,
            "created_at": datetime.now().isoformat(),
            "num_people": len(people),
            "params": params,
            "demographics": {
                "avg_age": sum(p["age"] for p in people) / len(people),
                "with_partners_pct": sum(1 for p in people if p["has_partner"]) / len(people) * 100,
                "students_pct": sum(1 for p in people if p["is_student"]) / len(people) * 100,
                "renters_pct": sum(1 for p in people if p["housing_type"] == "rent") / len(people) * 100,
                "with_children_pct": sum(1 for p in people if p["has_children"]) / len(people) * 100,
            },
        }

        metadata_file = POPULATIONS_DIR / f"{population_id}.meta.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved population {population_id} with {len(people)} people")

    @staticmethod
    def load_population(population_id: str) -> list:
        """Load a previously saved population from disk."""
        population_file = POPULATIONS_DIR / f"{population_id}.json"

        if not population_file.exists():
            raise FileNotFoundError(f"Population {population_id} not found")

        with open(population_file) as f:
            people_data = json.load(f)

        # Convert ISO format strings back to date objects
        for person in people_data:
            person["birth_date"] = date.fromisoformat(person["birth_date"])
            # Convert children data
            if "children_data" in person:
                for child in person["children_data"]:
                    child["birth_date"] = date.fromisoformat(child["birth_date"])

        logger.info(f"Loaded population {population_id} with {len(people_data)} people")
        return people_data

    @staticmethod
    def list_populations() -> list[dict]:
        """List all saved populations with their metadata."""
        if not POPULATIONS_DIR.exists():
            return []

        populations = []
        for meta_file in POPULATIONS_DIR.glob("*.meta.json"):
            try:
                with open(meta_file) as f:
                    metadata = json.load(f)
                populations.append(metadata)
            except Exception as e:
                logger.error(f"Error reading metadata file {meta_file}: {e}")

        # Sort by creation date, newest first
        populations.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return populations

    @staticmethod
    def delete_population(population_id: str) -> bool:
        """Delete a saved population and its metadata."""
        population_file = POPULATIONS_DIR / f"{population_id}.json"
        metadata_file = POPULATIONS_DIR / f"{population_id}.meta.json"

        deleted = False
        if population_file.exists():
            population_file.unlink()
            deleted = True
        if metadata_file.exists():
            metadata_file.unlink()
            deleted = True

        if deleted:
            logger.info(f"Deleted population {population_id}")
        return deleted

    def generate_bsn(self):
        while True:
            bsn = f"999{random.randint(100000, 999999)}"
            if bsn not in self.used_bsns:
                self.used_bsns.add(bsn)
                return bsn

    def generate_person(self, birth_year_range=None):
        """Generate a realistic person with demographics based on CBS data"""
        # Select age range based on distribution
        if not birth_year_range:
            age_range = random.choices(
                list(self.age_distribution.keys()), weights=list(self.age_distribution.values())
            )[0]
            current_year = datetime.strptime(self.simulation_date, "%Y-%m-%d").year
            birth_year_range = (current_year - age_range[1], current_year - age_range[0])

        birth_date = date(
            random.randint(*birth_year_range),
            random.randint(1, 12),
            random.randint(1, 28),
        )
        age = (datetime.strptime(self.simulation_date, "%Y-%m-%d").date() - birth_date).days // 365

        # Select income level based on age (simplified model)
        if age < 30:
            income_level = random.choices(["low", "middle", "high"], weights=[0.6, 0.3, 0.1])[0]
        elif age < 45:
            income_level = random.choices(["low", "middle", "high"], weights=[0.3, 0.5, 0.2])[0]
        elif age < 67:
            income_level = random.choices(["low", "middle", "high"], weights=[0.25, 0.45, 0.3])[0]
        else:
            income_level = random.choices(["low", "middle", "high"], weights=[0.5, 0.4, 0.1])[0]

        # Generate income based on selected level
        # Chance for zero income (to qualify for bijstand)
        if random.random() < self.zero_income_prob:
            annual_income = 0
        else:
            income_params = self.income_distribution_params[income_level]
            annual_income = (
                min(max(int(np.random.lognormal(mean=income_params["mean"], sigma=income_params["sigma"])), 0), 200000)
                * 100
            )

        # If person is above retirement age, adjust income to reflect pension
        if age >= 67:
            annual_income = min(annual_income, 50000 * 100)  # Cap at €50,000 for retirees
            annual_income = max(annual_income, 15000 * 100)  # Minimum €15,000 for retirees (AOW)

        # For students, income is much lower
        if age < 30 and random.random() < 0.4:  # 40% chance for young people to be students
            is_student = True
            annual_income = min(annual_income, 20000 * 100)  # Cap student income at €20,000
            annual_income = max(annual_income, 5000 * 100)  # Minimum student income €5,000
            study_grant = random.randint(2000, 4500) * 100  # €2,000 - €4,500 annual study grant
        else:
            is_student = False
            study_grant = 0

        # Calculate net worth based on age and income
        # Young people have less wealth, older people have more
        net_worth_multiplier = max(0.5, min(age / 25, 8))  # Ranges from 0.5 to 8
        # Students have much less net worth
        if is_student:
            net_worth_multiplier *= 0.4

        net_worth = annual_income * net_worth_multiplier * random.uniform(0.8, 1.2)
        net_worth = min(max(net_worth, 0), 2000000 * 100)  # Cap at €2,000,000

        # Determine housing situation
        # Students and young people are more likely to rent
        rent_probability = self.housing_distribution["rent"]
        if age < 30:
            rent_probability = 0.8
        elif age < 40:
            rent_probability = 0.55
        elif age > 67:
            rent_probability = 0.35  # Elderly often own their homes

        # People with lower incomes are more likely to rent
        if annual_income < 2500000:  # Less than €25,000
            rent_probability += 0.2

        housing_type = "rent" if random.random() < rent_probability else "own"

        # Calculate rent or mortgage
        if housing_type == "rent":
            # Determine appropriate rent range based on income
            # Make rents lower for lower incomes to qualify for huurtoeslag
            if annual_income < 2000000:  # Less than €20,000
                rent_range = self.rent_distribution["low"]
                # Give some people exactly the values from the feature file
                if random.random() < 0.3:  # 30% chance
                    rent_amount = 65000  # €650 as in feature file
                    rent_service_costs = 5000  # €50 as in feature file
                    eligible_service_costs = 4800  # €48 as in feature file
                else:
                    # Calculate monthly rent
                    rent_amount = int(random.randint(*rent_range) * 100)  # Convert to cents
                    rent_service_costs = int(random.randint(80, 120) * 100)  # €80-€120 service costs
                    eligible_service_costs = min(rent_service_costs, 3000)  # Max €30 eligible for most
            elif annual_income < 4000000:  # Less than €40,000
                rent_range = self.rent_distribution["medium"]
                # Calculate monthly rent
                rent_amount = int(random.randint(*rent_range) * 100)  # Convert to cents
                rent_service_costs = int(random.randint(100, 150) * 100)  # €100-€150 service costs
                eligible_service_costs = min(rent_service_costs, 3000)  # Max €30 eligible
            else:
                rent_range = self.rent_distribution["high"]
                # Calculate monthly rent
                rent_amount = int(random.randint(*rent_range) * 100)  # Convert to cents
                rent_service_costs = int(random.randint(120, 200) * 100)  # €120-€200 service costs
                eligible_service_costs = min(rent_service_costs, 3000)  # Max €30 eligible
        else:
            # For homeowners, estimate mortgage payment
            rent_amount = 0
            rent_service_costs = 0
            eligible_service_costs = 0

        # Generate more data for other laws
        is_detained = random.random() < 0.002  # 0.2% chance of being detained
        is_incarcerated = is_detained

        # Has Dutch nationality (random with high probability)
        has_dutch_nationality = random.random() < 0.9

        # Generate children data only for adults 23-55
        has_children = False
        children_data = []
        if 23 <= age <= 55:
            has_children_prob = min(0.7, (age - 23) * 0.03)  # Increases with age up to 0.7
            has_children = random.random() < has_children_prob

            if has_children:
                num_children = random.choices([1, 2, 3, 4], weights=[0.4, 0.4, 0.15, 0.05])[0]
                for i in range(num_children):
                    child_age = random.randint(0, min(20, age - 23))
                    child_birth_year = datetime.now().year - child_age
                    children_data.append(
                        {
                            "bsn": self.generate_bsn(),  # Generate BSN for child
                            "birth_date": date(child_birth_year, random.randint(1, 12), random.randint(1, 28)),
                            "age": child_age,
                            "zorgbehoefte": random.random() < 0.05,  # 5% chance of special care needs
                        }
                    )

        return {
            "bsn": self.generate_bsn(),
            "birth_date": birth_date,
            "age": age,
            "annual_income": annual_income,
            "net_worth": net_worth,
            "work_years": min(max(0, (age - 18) * random.uniform(0.5, 0.9)), 50),
            "residence_years": min(max(0, (age - 15) * random.uniform(0.8, 1.0)), 50),
            "is_student": is_student,
            "study_grant": study_grant,
            "is_detained": is_detained,
            "is_incarcerated": is_incarcerated,
            "has_dutch_nationality": has_dutch_nationality,
            "has_children": has_children,
            "children_data": children_data,
            "housing_type": housing_type,
            "rent_amount": rent_amount,
            "rent_service_costs": rent_service_costs,
            "eligible_service_costs": eligible_service_costs,
        }

    def generate_paired_people(self, num_people):
        pairs = []  # Store people in pairs (person, partner or None)

        while True:
            current_count = len([p for pair in pairs for p in pair if p is not None])
            if current_count >= num_people:
                break

            person = self.generate_person()

            # Check if we need only one more person
            if current_count + 1 == num_people:
                # Just add the single person without a partner
                pairs.append((person, None))
                break

            # Partnership probability based on age
            partner_prob = 0.1
            if 25 <= person["age"] < 35:
                partner_prob = 0.4
            elif 35 <= person["age"] < 60:
                partner_prob = 0.7
            elif person["age"] >= 60:
                partner_prob = 0.6

            # Check if adding a partner would exceed our target
            if current_count + 2 > num_people:
                # Don't add a partner if it would exceed num_people
                pairs.append((person, None))
            elif random.random() < partner_prob:  # Chance of partner
                age_diff = random.gauss(0, 5)
                birth_year_min = person["birth_date"].year + int(age_diff) - 1
                birth_year_max = person["birth_date"].year + int(age_diff) + 1

                # Ensure birth years are reasonable
                birth_year_min = max(birth_year_min, 1925)
                birth_year_max = max(birth_year_max, birth_year_min + 1)

                partner = self.generate_person(birth_year_range=(birth_year_min, birth_year_max))
                pairs.append((person, partner))
            else:
                pairs.append((person, None))

        return pairs

    def setup_test_data(self, pairs, random_seed=None):
        # Set random seed if provided (for reproducibility with loaded populations)
        if random_seed is not None:
            # Convert string seed to integer if needed (e.g., UUID strings)
            if isinstance(random_seed, str):
                # Convert UUID string to integer using hash
                random_seed = int(uuid.UUID(random_seed).int % (2**32))
            random.seed(random_seed)
            np.random.seed(random_seed)

        # Flatten pairs into list of people with partner references
        people = []
        for person, partner in pairs:
            person["partner_bsn"] = partner["bsn"] if partner else None
            person["has_partner"] = partner is not None
            people.append(person)
            if partner:
                partner["partner_bsn"] = person["bsn"]
                partner["has_partner"] = True
                people.append(partner)

        # Prepare CBS demographic data
        sources = {
            ("CBS", "levensverwachting"): [{"jaar": "2025", "verwachting_65": 20.5}],
            # KIESRAAD data for elections
            ("KIESRAAD", "verkiezingen"): [{"type": "TWEEDE_KAMER", "verkiezingsdatum": "2025-10-29"}],
            # RvIG data (Personal Information)
            ("RvIG", "personen"): [
                {
                    "bsn": p["bsn"],
                    "geboortedatum": p["birth_date"].isoformat(),
                    "verblijfsadres": "Amsterdam",
                    "land_verblijf": "NEDERLAND",
                    "nationaliteit": "NEDERLANDS" if p["has_dutch_nationality"] else "BUITENLANDS",
                    "age": p["age"],
                    "has_dutch_nationality": p["has_dutch_nationality"],
                    "has_partner": p["has_partner"],
                    "residence_address": p.get("residence_address")
                    or f"Teststraat {random.randint(1, 999)}, {random.randint(1000, 9999)}AB Amsterdam",
                    "has_fixed_address": True,
                    "household_size": 1 + (1 if p["has_partner"] else 0) + len(p.get("children_data", [])),
                }
                for p in people
            ],
            # RvIG relationship data
            ("RvIG", "relaties"): [
                {
                    "bsn": p["bsn"],
                    "partnerschap_type": "HUWELIJK" if p["has_partner"] else "GEEN",
                    "partner_bsn": p["partner_bsn"],
                    # Add children directly in the format expected by features
                    "children": [{"bsn": child["bsn"]} for child in p.get("children_data", [])]
                    if p.get("children_data")
                    else [],
                }
                for p in people
            ],
            # RvIG Address data
            ("RvIG", "verblijfplaats"): [
                {
                    "bsn": p["bsn"],
                    "straat": p.get("straat") or ("Kalverstraat" if random.random() < 0.7 else "Teststraat"),
                    "huisnummer": p.get("huisnummer") or str(random.randint(1, 999)),
                    "postcode": p.get("postcode") or f"{random.randint(1000, 9999)}AB",
                    "woonplaats": "Amsterdam",
                    "type": p.get("address_type") or ("WOONADRES" if random.random() < 0.95 else "BRIEFADRES"),
                }
                for p in people
            ],
            # Tax data
            ("BELASTINGDIENST", "box1"): [
                {
                    "bsn": p["bsn"],
                    "loon_uit_dienstbetrekking": p["annual_income"] if not p["is_student"] else p["annual_income"] // 2,
                    "uitkeringen_en_pensioenen": p["annual_income"] // 2 if p["age"] >= 67 else 0,
                    "winst_uit_onderneming": 0,
                    "resultaat_overige_werkzaamheden": 0,
                    "eigen_woning": -int(p["annual_income"] * 0.1) if p["housing_type"] == "own" else 0,
                }
                for p in people
            ],
            # Income data (used by huurtoeslag)
            ("UWV", "income"): [
                {
                    "bsn": p["bsn"],
                    "value": p["annual_income"],
                }
                for p in people
            ],
            # Partner income data (used by huurtoeslag)
            ("UWV", "partner_income"): [
                {
                    "bsn": p["bsn"],
                    "value": people[i + 1]["annual_income"]
                    if i + 1 < len(people) and p.get("partner_bsn") == people[i + 1]["bsn"]
                    else 0,
                }
                for i, p in enumerate(people)
                if i % 2 == 0
                # Only do this for first of each potential pair
            ]
            + [
                {
                    "bsn": p["bsn"],
                    "value": people[i - 1]["annual_income"]
                    if i - 1 >= 0 and p.get("partner_bsn") == people[i - 1]["bsn"]
                    else 0,
                }
                for i, p in enumerate(people)
                if i % 2 == 1
                # Only do this for second of each potential pair
            ],
            ("BELASTINGDIENST", "box2"): [
                {"bsn": p["bsn"], "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0} for p in people
            ],
            ("BELASTINGDIENST", "box3"): [
                {
                    "bsn": p["bsn"],
                    "spaargeld": int(p["net_worth"] * 0.4),
                    "beleggingen": int(p["net_worth"] * 0.1),
                    "onroerend_goed": int(p["net_worth"] * 0.5) if p["housing_type"] == "own" else 0,
                    "schulden": int(p["annual_income"] * 0.05) if random.random() < 0.2 else 0,
                }
                for p in people
            ],
            ("BELASTINGDIENST", "monthly_income"): [
                {
                    "bsn": p["bsn"],
                    "bedrag": p["annual_income"] // 12,
                }
                for p in people
            ],
            ("BELASTINGDIENST", "assets"): [
                {
                    "bsn": p["bsn"],
                    "bedrag": p["net_worth"],
                }
                for p in people
            ],
            # Net worth data (used by huurtoeslag)
            ("BELASTINGDIENST", "net_worth"): [
                {
                    "bsn": p["bsn"],
                    "value": p["net_worth"],
                }
                for p in people
            ],
            # Combined net worth data (used by huurtoeslag for people with partners)
            ("BELASTINGDIENST", "combined_net_worth"): [
                {
                    "bsn": p["bsn"],
                    "value": p["net_worth"]
                    + (
                        people[i + 1]["net_worth"]
                        if i + 1 < len(people) and p.get("partner_bsn") == people[i + 1]["bsn"]
                        else 0
                    ),
                }
                for i, p in enumerate(people)
                if i % 2 == 0
                # Only do this for first of each potential pair
            ]
            + [
                {
                    "bsn": p["bsn"],
                    "value": p["net_worth"]
                    + (
                        people[i - 1]["net_worth"] if i - 1 >= 0 and p.get("partner_bsn") == people[i - 1]["bsn"] else 0
                    ),
                }
                for i, p in enumerate(people)
                if i % 2 == 1
                # Only do this for second of each potential pair
            ],
            # Buitenlands inkomen (missing in warnings)
            ("UWV", "FOREIGN_INCOME"): [
                {
                    "bsn": p["bsn"],
                    "value": 0,  # Geen buitenlands inkomen
                }
                for p in people
            ],
            # Partner buitenlands inkomen
            ("UWV", "PARTNER_FOREIGN_INCOME"): [
                {
                    "bsn": p["bsn"],
                    "value": 0,  # Partner geen buitenlands inkomen
                }
                for p in people
            ],
            # HOUSEHOLD veld dat ontbreekt - met members array dat age en income bevat
            ("RvIG", "HOUSEHOLD"): [
                {
                    "bsn": p["bsn"],
                    "value": {
                        "size": 1 + (1 if p["has_partner"] else 0) + len(p.get("children_data", [])),
                        "composition": "ALLEENSTAANDE"
                        if not p["has_partner"] and not p.get("children_data")
                        else "ALLEENSTAANDE_MET_KINDEREN"
                        if not p["has_partner"] and p.get("children_data")
                        else "PARTNERS_ZONDER_KINDEREN"
                        if p["has_partner"] and not p.get("children_data")
                        else "PARTNERS_MET_KINDEREN",
                        "members": [{"age": p["age"], "income": p["annual_income"]}]
                        + (
                            [
                                {
                                    "age": next(
                                        (partner for partner in people if partner["bsn"] == p["partner_bsn"]),
                                        {"age": 30},
                                    )["age"],
                                    "income": next(
                                        (partner for partner in people if partner["bsn"] == p["partner_bsn"]),
                                        {"annual_income": 0},
                                    )["annual_income"],
                                }
                            ]
                            if p["has_partner"] and p["partner_bsn"]
                            else []
                        ),
                    },
                }
                for p in people
            ],
            # Employment data
            ("UWV", "dienstverbanden"): [
                {
                    "bsn": p["bsn"],
                    "start_date": (p["birth_date"].replace(year=p["birth_date"].year + 18)).isoformat(),
                    "end_date": datetime.strptime(self.simulation_date, "%Y-%m-%d").date().isoformat(),
                    "uren_per_week": random.randint(8, 40) if not p["is_student"] else random.randint(4, 16),
                    "worked_hours": (1920 if random.random() < 0.8 else random.randint(1000, 1920))
                    if not p["is_student"]
                    else random.randint(500, 1000),
                }
                for p in people
            ],
            # Add worked_hours for UWV that's required by kinderopvangtoeslag
            ("UWV", "worked_hours"): [
                {
                    "bsn": p["bsn"],
                    "value": (1920 if random.random() < 0.8 else random.randint(1000, 1920))
                    if not p["is_student"]
                    else random.randint(500, 1000),
                }
                for p in people
            ],
            # Add insured_years for kinderopvangtoeslag
            ("UWV", "insured_years"): [
                {
                    "bsn": p["bsn"],
                    "value": min(max(3, int(p["work_years"])), 30),  # Minimum 3 years, max 30
                }
                for p in people
            ],
            # SVB insurance data
            ("SVB", "verzekerde_tijdvakken"): [
                {
                    "bsn": p["bsn"],
                    "woonperiodes": p["residence_years"],
                }
                for p in people
            ],
            # SVB retirement age
            ("SVB", "retirement_age"): [
                {
                    "bsn": p["bsn"],
                    "leeftijd": 67 + random.randint(0, 3) / 10,  # 67.0-67.3
                }
                for p in people
            ],
            # Healthcare insurance data
            ("RVZ", "verzekeringen"): [
                {
                    "bsn": p["bsn"],
                    "polis_status": "ACTIEF" if random.random() < 0.95 else "INACTIEF",
                    "verdrag_status": "GEEN",
                    "zorg_type": "BASIS",
                    "has_insurance": random.random() < 0.95,
                    "has_act_insurance": random.random() < 0.05,
                }
                for p in people
            ],
            # Healthcare treaty data
            ("RVZ", "verdragsverzekeringen"): [
                {
                    "bsn": p["bsn"],
                    "registratie": "INACTIEF",
                }
                for p in people
            ],
            # Detention data
            ("DJI", "detenties"): [
                {
                    "bsn": p["bsn"],
                    "status": "GEDETINEERD" if p["is_detained"] else "VRIJ",
                    "inrichting_type": "REGULIER" if p["is_detained"] else "GEEN",
                    "is_gedetineerd": p["is_detained"],
                    "is_detainee": p["is_detained"],
                }
                for p in people
            ],
            ("DJI", "forensische_zorg"): [
                {
                    "bsn": p["bsn"],
                    "zorgtype": "KLINISCH" if p["is_detained"] and random.random() < 0.1 else "GEEN",
                    "juridische_titel": "TBS" if p["is_detained"] and random.random() < 0.1 else "GEEN",
                    "is_forensic": p["is_detained"] and random.random() < 0.1,
                }
                for p in people
            ],
            # Education data
            ("DUO", "inschrijvingen"): [
                {
                    "bsn": p["bsn"],
                    "onderwijstype": ("HBO" if random.random() < 0.5 else "WO") if p["is_student"] else "GEEN",
                    "onderwijssoort": ("HBO" if random.random() < 0.5 else "WO") if p["is_student"] else "GEEN",
                    "niveau": 4 if p["is_student"] else 0,
                }
                for p in people
            ],
            ("DUO", "studiefinanciering"): [
                {
                    "bsn": p["bsn"],
                    "aantal_studerend_gezin": random.randint(0, 3) if p["age"] < 30 else 0,
                    "ontvangt_studiefinanciering": p["is_student"],
                    "aantal_studerende_broers_zussen": random.randint(0, 2) if p["age"] < 30 else 0,
                }
                for p in people
            ],
            ("DUO", "is_student"): [
                {
                    "bsn": p["bsn"],
                    "waarde": p["is_student"],
                }
                for p in people
            ],
            ("DUO", "receives_study_grant"): [
                {
                    "bsn": p["bsn"],
                    "waarde": p["is_student"],
                }
                for p in people
            ],
            # Municipal data (Amsterdam)
            ("GEMEENTE_AMSTERDAM", "werk_en_re_integratie"): [
                {
                    "bsn": p["bsn"],
                    "arbeidsvermogen": random.choices(
                        ["VOLLEDIG", "GEDEELTELIJK", "MEDISCH_VOLLEDIG", "GEEN"], weights=[0.8, 0.1, 0.05, 0.05]
                    )[0],
                    "re_integratie_traject": random.choice(
                        ["Werkstage", "Ondernemerscoaching", "Zelfstandigentraject", "Geen"]
                    ),
                    "ontheffing_reden": "Chronische ziekte" if random.random() < 0.05 else None,
                    "ontheffing_einddatum": (
                        datetime.strptime(self.simulation_date, "%Y-%m-%d").date() + pd.Timedelta(days=365)
                    ).isoformat()
                    if random.random() < 0.05
                    else None,
                }
                for p in people
            ],
            # IND data (residence permits)
            ("IND", "verblijfsvergunningen"): [
                {
                    "bsn": p["bsn"],
                    "type": "PERMANENT" if not p["has_dutch_nationality"] else "NEDERLANDS",
                    "status": "VERLEEND",
                    "ingangsdatum": (
                        p["birth_date"].replace(year=p["birth_date"].year + max(0, 18 - random.randint(0, 5)))
                    ).isoformat(),
                    "einddatum": None,
                }
                for p in people
            ],
            ("IND", "residence_permit_type"): [
                {
                    "bsn": p["bsn"],
                    "type": "PERMANENT" if not p["has_dutch_nationality"] else "NEDERLANDS",
                }
                for p in people
            ],
            # KVK data (Chamber of Commerce)
            ("KVK", "is_entrepreneur"): [
                {
                    "bsn": p["bsn"],
                    "waarde": random.random() < 0.1,  # 10% chance of being entrepreneur
                }
                for p in people
            ],
            ("KVK", "is_active_entrepreneur"): [
                {
                    "bsn": p["bsn"],
                    "waarde": random.random() < 0.1,  # 10% chance of being active entrepreneur
                }
                for p in people
            ],
            # KVK inschrijvingen data for bijstand
            ("KVK", "inschrijvingen"): [
                {
                    "bsn": p["bsn"],
                    "rechtsvorm": random.choice(["EENMANSZAAK", "BV", "VOF"]),
                    "status": "ACTIEF" if random.random() < 0.9 else "INACTIEF",
                    "activiteit": random.choice(["Webdesign", "Consultancy", "Horeca", "Retail", "Transport"]),
                }
                for p in people
                if random.random() < 0.1  # Only 10% of people have KVK registrations
            ],
            # JenV data (ministry of Justice)
            ("JenV", "jurisdicties"): [
                {"gemeente": "Amsterdam", "arrondissement": "AMSTERDAM", "rechtbank": "RECHTBANK_AMSTERDAM"},
                {"gemeente": "Amstelveen", "arrondissement": "AMSTERDAM", "rechtbank": "RECHTBANK_AMSTERDAM"},
                {"gemeente": "Haarlem", "arrondissement": "NOORD-HOLLAND", "rechtbank": "RECHTBANK_NOORD_HOLLAND"},
                {"gemeente": "Rotterdam", "arrondissement": "ROTTERDAM", "rechtbank": "RECHTBANK_ROTTERDAM"},
                {
                    "gemeente": "Utrecht",
                    "arrondissement": "MIDDEN-NEDERLAND",
                    "rechtbank": "RECHTBANK_MIDDEN_NEDERLAND",
                },
                {"gemeente": "Den Haag", "arrondissement": "DEN_HAAG", "rechtbank": "RECHTBANK_DEN_HAAG"},
            ],
        }

        # Add housing data for rent calculation
        [
            {
                "bsn": p["bsn"],
                "huur": p["rent_amount"],
                "servicekosten": p["rent_service_costs"],
                "subsidiabeleservicekosten": p["eligible_service_costs"],
            }
            for p in people
            if p["housing_type"] == "rent"
        ]

        # IMPORTANT: Huurtoeslag requires CLAIMS, not regular data sources
        # We'll submit these as claims after loading all other data

        # Add household members and children required by huurtoeslag with the correct format
        # Voorbeeld uit de feature file toont dat deze velden niet als 'value' worden verwacht, maar direct
        # Voor elk persoon, maak huishoudleden en kinderen data aan als VALUE object (niet als directe velden)
        household_members = []
        for p in people:
            # Verzamel huishoudleden (anderen dan de persoon zelf)
            household_data = []
            if p["has_partner"] and p["partner_bsn"]:
                # Vind de partner in de people list
                partner = next((partner for partner in people if partner["bsn"] == p["partner_bsn"]), None)
                if partner:
                    household_data.append({"age": partner["age"], "income": partner["annual_income"]})

            # Value field zoals in YAML verwacht
            household_members.append({"bsn": p["bsn"], "value": household_data})

        sources[("RvIG", "household_members")] = household_members

        # Add children with correct format based on feature file
        children_data = []
        for p in people:
            child_list = []
            if p.get("children_data"):
                # Format children data correctly for the law
                for child in p["children_data"]:
                    child_list.append(
                        {
                            "age": child["age"],
                            "income": 0,  # Assume children have no income for simplicity
                        }
                    )

            # Value field zoals in YAML verwacht
            children_data.append({"bsn": p["bsn"], "value": child_list})

        sources[("RvIG", "children")] = children_data

        # Load data to services
        for (service, table), data in sources.items():
            self.services.set_source_dataframe(service, table, pd.DataFrame(data))

        # Add children data as separate tables for some people
        children_by_bsn = {}
        for p in people:
            if p["has_children"] and p["children_data"]:
                children_by_bsn[p["bsn"]] = p["children_data"]

        if children_by_bsn:
            children_data = [
                {
                    "bsn": bsn,
                    "kinderen": [
                        {
                            "geboortedatum": child["birth_date"].isoformat(),
                            "zorgbehoefte": child.get("zorgbehoefte", False),
                        }
                        for child in children
                    ],
                }
                for bsn, children in children_by_bsn.items()
            ]
            self.services.set_source_dataframe("RvIG", "CHILDREN_DATA", pd.DataFrame(children_data))

            # Add childcare data for people with young children
            childcare_data = []

            # Children BSNs mapping for RvIG references
            children_bsns = {}

            for bsn, children in children_by_bsn.items():
                young_children = [c for c in children if c["age"] < 12]
                if young_children:
                    # Create CHILDREN_BSNS mapping for this person
                    bsns_list = []

                    for child in young_children:
                        # Create BSN for child
                        child_bsn = self.generate_bsn()
                        bsns_list.append(child_bsn)

                        childcare_hours = random.randint(20, 40) * 52  # 20-40 hours per week
                        # Make sure the childcare rates are limited to max allowed
                        soort_opvang = "DAGOPVANG" if child["age"] < 4 else "BSO"
                        max_uurtarief = (
                            902 if soort_opvang == "DAGOPVANG" else 766
                        )  # Max rates in cents according to law
                        # Generate realistic childcare data
                        lrk_nummer = f"LRK{random.randint(100000, 999999)}"
                        childcare_data.append(
                            {
                                "bsn": bsn,
                                "kind_bsn": child_bsn,
                                "uren_per_jaar": min(childcare_hours, 2500),  # Limit to 2500 hours/year
                                "uurtarief": random.randint(700, max_uurtarief),  # Below max tarief
                                "soort_opvang": soort_opvang,
                                "LRK_registratienummer": lrk_nummer,
                            }
                        )

                    # Store the BSNs list for this person
                    children_bsns[bsn] = bsns_list

            # Add CHILDREN_BSNS references that the childcare law needs
            if children_bsns:
                children_bsns_data = [
                    {
                        "bsn": bsn,
                        "value": [{"bsn": child_bsn} for child_bsn in bsns_list],
                        # Format needs to match feature file format
                    }
                    for bsn, bsns_list in children_bsns.items()
                ]
                children_bsns_df = pd.DataFrame(children_bsns_data)
                self.services.set_source_dataframe("RvIG", "children_bsns", children_bsns_df)

            if childcare_data:
                # Add childcare provider KVK number - exactly as in the feature file
                childcare_kvk_data = [
                    {
                        "bsn": item["bsn"],
                        "value": f"{random.randint(10000000, 99999999)}",  # String without KVK prefix
                    }
                    for item in childcare_data
                ]
                kvk_df = pd.DataFrame(childcare_kvk_data).drop_duplicates(subset=["bsn"])
                self.services.set_source_dataframe("TOESLAGEN", "CHILDCARE_KVK", kvk_df)

                # Add DECLARED_HOURS with all records for each BSN
                # Exact format zoals in feature file
                hours_by_bsn = {}
                for item in childcare_data:
                    bsn = item["bsn"]
                    if bsn not in hours_by_bsn:
                        hours_by_bsn[bsn] = []

                    # Format exact zoals in kinderopvangtoeslag.feature - important to match
                    hours_by_bsn[bsn].append(
                        {
                            "kind_bsn": item["kind_bsn"],
                            "uren_per_jaar": item["uren_per_jaar"],
                            "uurtarief": item["uurtarief"],
                            "soort_opvang": item["soort_opvang"],
                            "LRK_registratienummer": item["LRK_registratienummer"],
                        }
                    )

                declared_hours_data = [{"bsn": bsn, "value": hours_list} for bsn, hours_list in hours_by_bsn.items()]
                declared_hours_df = pd.DataFrame(declared_hours_data)
                self.services.set_source_dataframe("TOESLAGEN", "DECLARED_HOURS", declared_hours_df)

                # Add expected partner hours for childcare
                partner_hours_data = [
                    {
                        "bsn": bsn,
                        # Gebaseerd op feature file: 0 voor alleenstaanden, 20+ voor mensen met partner
                        "value": 0
                        if not any(p["bsn"] == bsn and p["has_partner"] for p in people)
                        else random.randint(24, 40),
                    }
                    for bsn in hours_by_bsn
                ]
                partner_hours_df = pd.DataFrame(partner_hours_data)
                self.services.set_source_dataframe("TOESLAGEN", "EXPECTED_PARTNER_HOURS", partner_hours_df)

                # Ensure worked_hours is also set correctly for the UWV data
                worked_hours_data = [
                    {
                        "bsn": p["bsn"],
                        "value": random.randint(1600, 2000)
                        if p.get("has_children") and not p["is_student"]
                        else random.randint(800, 1000),
                    }
                    for p in people
                    if p.get("has_children")
                ]
                worked_hours_df = pd.DataFrame(worked_hours_data)
                self.services.set_source_dataframe("UWV", "worked_hours", worked_hours_df)

                # Add insured_years data for people with children - required by kinderopvangtoeslag
                insured_years_data = [
                    {
                        "bsn": p["bsn"],
                        "value": min(max(3, int(p["work_years"])), 10),  # Between 3 and 10 years
                    }
                    for p in people
                    if p.get("has_children")
                ]
                insured_years_df = pd.DataFrame(insured_years_data)
                self.services.set_source_dataframe("UWV", "insured_years", insured_years_df)

        # Submit claims for huurtoeslag (rent subsidy)
        # These are required as claims, not regular data sources
        renters_count = 0
        claims_submitted = 0
        for person in people:
            if person["housing_type"] == "rent":
                renters_count += 1
                bsn = person["bsn"]
                try:
                    # Submit claim for HUURPRIJS (rent price)
                    claim1 = self.services.claim_manager.submit_claim(
                        service="TOESLAGEN",
                        key="HUURPRIJS",
                        new_value=person["rent_amount"],
                        reason="Simulated rent claim",
                        claimant="BURGER",
                        law="wet_op_de_huurtoeslag",
                        bsn=bsn,
                        auto_approve=True,
                    )
                    # Submit claim for SERVICEKOSTEN (service costs)
                    claim2 = self.services.claim_manager.submit_claim(
                        service="TOESLAGEN",
                        key="SERVICEKOSTEN",
                        new_value=person["rent_service_costs"],
                        reason="Simulated service costs claim",
                        claimant="BURGER",
                        law="wet_op_de_huurtoeslag",
                        bsn=bsn,
                        auto_approve=True,
                    )
                    # Submit claim for SUBSIDIABELE_SERVICEKOSTEN (subsidizable service costs)
                    claim3 = self.services.claim_manager.submit_claim(
                        service="TOESLAGEN",
                        key="SUBSIDIABELE_SERVICEKOSTEN",
                        new_value=person["eligible_service_costs"],
                        reason="Simulated subsidizable service costs claim",
                        claimant="BURGER",
                        law="wet_op_de_huurtoeslag",
                        bsn=bsn,
                        auto_approve=True,
                    )
                    claims_submitted += 1
                    logger.debug(
                        f"Submitted huurtoeslag claims for BSN {bsn}: rent={person['rent_amount']}, claims={claim1},{claim2},{claim3}"
                    )
                except Exception as e:
                    logger.error(f"Error submitting huurtoeslag claims for BSN {bsn}: {e}")
                    import traceback

                    logger.error(traceback.format_exc())

        print(f"Submitted huurtoeslag claims for {claims_submitted}/{renters_count} renters", file=sys.stderr)

        # Submit claims for kinderopvangtoeslag (childcare subsidy)
        parents_count = 0
        childcare_claims_submitted = 0
        for person in people:
            if person.get("has_children") and person.get("children_data"):
                # Check if any children are under 12
                young_children = [child for child in person["children_data"] if child["age"] < 12]
                if young_children:
                    parents_count += 1
                    bsn = person["bsn"]
                    try:
                        # Submit KvK number claim
                        self.services.claim_manager.submit_claim(
                            service="TOESLAGEN",
                            key="KINDEROPVANG_KVK",
                            new_value="12345678",  # Simulated childcare provider KvK
                            reason="Simulated childcare provider",
                            claimant="BURGER",
                            law="wet_kinderopvang",
                            bsn=bsn,
                            auto_approve=True,
                        )

                        # Submit childcare hours for each young child
                        aangegeven_uren = []
                        for child in young_children:
                            # Simulate different childcare hours based on child age
                            if child["age"] < 4:
                                # Daycare for toddlers (full-time)
                                hours_per_year = 2000
                                hourly_rate = 850  # €8.50 per hour
                                care_type = "DAGOPVANG"
                            else:
                                # After school care for school-age children
                                hours_per_year = 800
                                hourly_rate = 750  # €7.50 per hour
                                care_type = "BUITENSCHOOLSE_OPVANG"

                            aangegeven_uren.append(
                                {
                                    "kind_bsn": child["bsn"],
                                    "uren_per_jaar": hours_per_year,
                                    "uurtarief": hourly_rate,
                                    "soort_opvang": care_type,
                                }
                            )

                        # Submit childcare hours claim
                        self.services.claim_manager.submit_claim(
                            service="TOESLAGEN",
                            key="AANGEGEVEN_UREN",
                            new_value=aangegeven_uren,
                            reason="Simulated childcare hours",
                            claimant="BURGER",
                            law="wet_kinderopvang",
                            bsn=bsn,
                            auto_approve=True,
                        )

                        # Submit partner hours (0 if no partner, otherwise partner's worked hours)
                        partner_hours = 0
                        if person.get("has_partner"):
                            # Assume partner works full-time
                            partner_hours = 1920

                        self.services.claim_manager.submit_claim(
                            service="TOESLAGEN",
                            key="VERWACHTE_PARTNER_UREN",
                            new_value=partner_hours,
                            reason="Simulated partner work hours",
                            claimant="BURGER",
                            law="wet_kinderopvang",
                            bsn=bsn,
                            auto_approve=True,
                        )

                        childcare_claims_submitted += 1
                        logger.debug(
                            f"Submitted kinderopvangtoeslag claims for BSN {bsn} with {len(young_children)} young children"
                        )
                    except Exception as e:
                        logger.error(f"Error submitting kinderopvangtoeslag claims for BSN {bsn}: {e}")
                        import traceback

                        logger.error(traceback.format_exc())

        print(
            f"Submitted kinderopvangtoeslag claims for {childcare_claims_submitted}/{parents_count} parents with young children",
            file=sys.stderr,
        )

        # Store generated random values back into people for reproducibility
        for p in people:
            rvig_person = next((x for x in sources[("RvIG", "personen")] if x["bsn"] == p["bsn"]), None)
            if rvig_person:
                p["residence_address"] = rvig_person["residence_address"]

            rvig_address = next((x for x in sources[("RvIG", "verblijfplaats")] if x["bsn"] == p["bsn"]), None)
            if rvig_address:
                p["straat"] = rvig_address["straat"]
                p["huisnummer"] = rvig_address["huisnummer"]
                p["postcode"] = rvig_address["postcode"]
                p["address_type"] = rvig_address["type"]

        return people

    def simulate_person(self, person) -> None:
        """Simulate all applicable laws for a person and calculate besteedbaar inkomen"""
        has_partner = bool(person["partner_bsn"])

        # Base result with personal information
        result = {
            "bsn": person["bsn"],
            "age": person["age"],
            "has_partner": has_partner,
            "housing_type": person["housing_type"],
            "rent_amount": person["rent_amount"] / 100 if person["housing_type"] == "rent" else 0,
            "income": person["annual_income"] / 100,
            "net_worth": person["net_worth"] / 100,
            "work_years": person["work_years"],
            "residence_years": person["residence_years"],
            "is_student": person["is_student"],
            "study_grant": person["study_grant"] / 100,
            "has_dutch_nationality": person["has_dutch_nationality"],
            "is_detained": person["is_detained"],
            "has_children": person["has_children"],
            "children_count": len(person.get("children_data", [])),
            "youngest_child_age": min([c["age"] for c in person.get("children_data", [1000])])
            if person.get("children_data")
            else None,
        }

        # Evaluate all relevant laws
        try:
            # 1. Zorgtoeslag (healthcare subsidy)
            zorgtoeslag_input, zorgtoeslag_defs = self._create_law_overrides("zorgtoeslagwet")
            zorgtoeslag = self.services.evaluate(
                "TOESLAGEN",
                "zorgtoeslagwet",
                {"BSN": person["bsn"]},
                self.simulation_date,
                overwrite_input=zorgtoeslag_input,
                overwrite_definitions=zorgtoeslag_defs,
            )

            # Also evaluate 2024 version for comparison if simulating in 2025
            zorgtoeslag_2024 = None
            if self.simulation_date.startswith("2025"):
                try:
                    zorgtoeslag_2024 = self.services.evaluate(
                        "TOESLAGEN",
                        "zorgtoeslagwet",
                        {"BSN": person["bsn"]},
                        "2024-12-31",
                        overwrite_input=zorgtoeslag_input,
                        overwrite_definitions=zorgtoeslag_defs,
                    )
                except Exception:
                    pass

            # 2. AOW (state pension)
            aow = self.services.evaluate("SVB", "algemene_ouderdomswet", {"BSN": person["bsn"]}, self.simulation_date)

            # 3. Huurtoeslag (rent subsidy)
            try:
                huurtoeslag_input, huurtoeslag_defs = self._create_law_overrides("wet_op_de_huurtoeslag")
                huurtoeslag = self.services.evaluate(
                    "TOESLAGEN",
                    "wet_op_de_huurtoeslag",
                    {"BSN": person["bsn"]},
                    self.simulation_date,
                    overwrite_input=huurtoeslag_input,
                    overwrite_definitions=huurtoeslag_defs,
                )
            except Exception as e:
                logger.debug(f"Error evaluating huurtoeslag for BSN {person['bsn']}: {e}")
                huurtoeslag = None

            # 4. Bijstand (social assistance)
            try:
                bijstand_input, bijstand_defs = self._create_law_overrides("participatiewet/bijstand")
                bijstand = self.services.evaluate(
                    "GEMEENTE_AMSTERDAM",
                    "participatiewet/bijstand",
                    {"BSN": person["bsn"]},
                    self.simulation_date,
                    overwrite_input=bijstand_input,
                    overwrite_definitions=bijstand_defs,
                )
            except Exception:
                bijstand = None

            # 5. Kinderopvangtoeslag (childcare subsidy)
            # Alleen proberen voor mensen met kinderen onder 12 jaar
            kinderopvangtoeslag = None
            if person["has_children"] and any(child["age"] < 12 for child in person.get("children_data", [])):
                try:
                    kinderopvang_input, kinderopvang_defs = self._create_law_overrides("wet_kinderopvang")
                    kinderopvangtoeslag = self.services.evaluate(
                        "TOESLAGEN",
                        "wet_kinderopvang",
                        {"BSN": person["bsn"]},
                        self.simulation_date,
                        overwrite_input=kinderopvang_input,
                        overwrite_definitions=kinderopvang_defs,
                    )
                except Exception as e:
                    logger.debug(f"Error evaluating kinderopvangtoeslag for BSN {person['bsn']}: {e}")
                    kinderopvangtoeslag = None

            # 6. Kindgebonden budget
            kindgebonden_budget = None
            if person["has_children"]:
                try:
                    kindgebonden_budget_input, kindgebonden_budget_defs = self._create_law_overrides(
                        "wet_op_het_kindgebonden_budget"
                    )
                    kindgebonden_budget = self.services.evaluate(
                        "TOESLAGEN",
                        "wet_op_het_kindgebonden_budget",
                        {"BSN": person["bsn"]},
                        self.simulation_date,
                        overwrite_input=kindgebonden_budget_input,
                        overwrite_definitions=kindgebonden_budget_defs,
                    )
                except Exception as e:
                    logger.debug(f"Error evaluating kindgebonden budget for BSN {person['bsn']}: {e}")
                    kindgebonden_budget = None

            # 7. WW-uitkering (unemployment benefit)
            ww_uitkering = None
            try:
                ww_input, ww_defs = self._create_law_overrides("werkloosheidswet")
                ww_uitkering = self.services.evaluate(
                    "UWV",
                    "werkloosheidswet",
                    {"BSN": person["bsn"]},
                    self.simulation_date,
                    overwrite_input=ww_input,
                    overwrite_definitions=ww_defs,
                )
            except Exception as e:
                logger.debug(f"Error evaluating WW-uitkering for BSN {person['bsn']}: {e}")
                ww_uitkering = None

            # 8. Kiesrecht (voting rights)
            kiesrecht_input, kiesrecht_defs = self._create_law_overrides("kieswet")
            kiesrecht = self.services.evaluate(
                "KIESRAAD",
                "kieswet",
                {"BSN": person["bsn"]},
                self.simulation_date,
                overwrite_input=kiesrecht_input,
                overwrite_definitions=kiesrecht_defs,
            )

            # 9. Inkomstenbelasting (income tax)
            ib_overwrite_input, ib_overwrite_definitions = self._create_law_overrides("wet_inkomstenbelasting")
            inkomstenbelasting = self.services.evaluate(
                "BELASTINGDIENST",
                "wet_inkomstenbelasting",
                {"BSN": person["bsn"]},
                self.simulation_date,
                overwrite_input=ib_overwrite_input,
                overwrite_definitions=ib_overwrite_definitions,
            )
        except Exception:
            return None

        result.update(
            {
                # Zorgtoeslag (yearly amount in eurocents, convert to monthly euros)
                "zorgtoeslag_eligible": zorgtoeslag.requirements_met,
                "zorgtoeslag_amount": zorgtoeslag.output.get("hoogte_toeslag", 0) / 100 / 12,
                # Zorgtoeslag 2024 comparison (if available)
                "zorgtoeslag_2024_amount": zorgtoeslag_2024.output.get("hoogte_toeslag", 0) / 100 / 12
                if zorgtoeslag_2024
                else None,
                # AOW
                "aow_eligible": aow.requirements_met,
                "aow_amount": aow.output.get("pensioenbedrag", 0) / 100,
                "aow_accrual": aow.output.get("opbouwpercentage", 0),
                # Huurtoeslag
                "huurtoeslag_eligible": huurtoeslag.requirements_met if huurtoeslag else False,
                "huurtoeslag_amount": huurtoeslag.output.get("subsidiebedrag", 0) / 100 if huurtoeslag else 0,
                "huurtoeslag_base_rent": huurtoeslag.output.get("basishuur", 0) / 100 if huurtoeslag else 0,
                # Bijstand
                "bijstand_eligible": bijstand.requirements_met if bijstand else False,
                "bijstand_amount": bijstand.output.get("uitkeringsbedrag", 0) / 100 if bijstand else 0,
                "bijstand_housing": bijstand.output.get("woonkostentoeslag", 0) / 100 if bijstand else 0,
                "bijstand_startup": bijstand.output.get("startkapitaal", 0) / 100 if bijstand else 0,
                # Kinderopvangtoeslag
                "kinderopvangtoeslag_eligible": kinderopvangtoeslag.requirements_met if kinderopvangtoeslag else False,
                "kinderopvangtoeslag_amount": kinderopvangtoeslag.output.get("jaarbedrag", 0) / 100 / 12
                if kinderopvangtoeslag
                else 0,
                # Kindgebonden budget
                "kindgebonden_budget_eligible": kindgebonden_budget.requirements_met if kindgebonden_budget else False,
                "kindgebonden_budget_amount": kindgebonden_budget.output.get("kindgebonden_budget_jaar", 0) / 100 / 12
                if kindgebonden_budget
                else 0,
                # WW-uitkering
                "ww_eligible": ww_uitkering.requirements_met if ww_uitkering else False,
                "ww_amount": ww_uitkering.output.get("ww_uitkering_per_maand", 0) / 100 if ww_uitkering else 0,
                # Kiesrecht
                "voting_rights": kiesrecht.output.get("heeft_stemrecht", False),
                # Belasting
                "tax_due": inkomstenbelasting.output.get("totale_belastingschuld", 0) / 100,
                "tax_credits": inkomstenbelasting.output.get("totale_heffingskortingen", 0) / 100,
                "tax_box1": inkomstenbelasting.output.get("box1_belasting", 0) / 100,
                "tax_box2": inkomstenbelasting.output.get("box2_belasting", 0) / 100,
                "tax_box3": inkomstenbelasting.output.get("box3_belasting", 0) / 100,
            }
        )

        # Calculate besteedbaar inkomen (disposable income) - monthly
        monthly_income = person["annual_income"] / 12 / 100  # Convert to euros and monthly
        tax_monthly = result["tax_due"] / 12

        # Add benefits
        benefits = (
            result["zorgtoeslag_amount"]
            + result["aow_amount"]
            + result["huurtoeslag_amount"]
            + result["bijstand_amount"]
            + result["bijstand_housing"]
            + result["kinderopvangtoeslag_amount"]
            + result["kindgebonden_budget_amount"]
            + result["ww_amount"]
        )

        # Calculate housing costs (rent or mortgage)
        housing_costs = result["rent_amount"] if person["housing_type"] == "rent" else monthly_income * 0.3

        # Calculate disposable income (after tax, benefits, and housing costs)
        result["disposable_income"] = monthly_income - tax_monthly + benefits
        result["disposable_income_after_housing"] = result["disposable_income"] - housing_costs

        # Add income components for breakdown
        result["income_components"] = {
            "monthly_pretax_income": monthly_income,
            "monthly_tax": tax_monthly,
            "zorgtoeslag": result["zorgtoeslag_amount"],
            "huurtoeslag": result["huurtoeslag_amount"],
            "aow": result["aow_amount"],
            "bijstand": result["bijstand_amount"] + result["bijstand_housing"],
            "kinderopvangtoeslag": result["kinderopvangtoeslag_amount"],
            "kindgebonden_budget": result["kindgebonden_budget_amount"],
            "ww": result["ww_amount"],
            "housing_costs": housing_costs,
        }

        self.results.append(result)

    def _create_law_overrides(self, law_name):
        """
        Create override dicts for a specific law based on UI parameters.

        Uses the law_parameter_config registry to map UI parameters to engine overrides.
        This eliminates hardcoded law-specific logic.

        Args:
            law_name: Technical law name (e.g., "wet_inkomstenbelasting")

        Returns:
            Tuple of (overwrite_input, overwrite_definitions):
            - overwrite_input: Dict for input overrides {service: {field: value}}
            - overwrite_definitions: Dict for definition overrides {field: value}
        """
        # Find law config by technical name
        config = find_law_config_by_technical_name(law_name)
        if not config:
            logger.debug(f"No config found for technical law name: {law_name}")
            return {}, {}

        # Check if we have UI parameters for this law
        ui_law_name = config.ui_name
        logger.debug(f"Looking for UI law name '{ui_law_name}' (from technical name '{law_name}') in law_parameters")
        logger.debug(f"Available law_parameters keys: {list(self.law_parameters.keys())}")

        if ui_law_name not in self.law_parameters:
            logger.debug(f"No parameters found for UI law name: {ui_law_name}")
            return {}, {}

        logger.info(f"Found {len(self.law_parameters[ui_law_name])} parameters for {ui_law_name}")

        # Create overrides using registry
        overwrite_input, overwrite_definitions = create_overrides(ui_law_name, self.law_parameters[ui_law_name])

        # Log info about definition overrides if present
        if overwrite_definitions:
            logger.info(f"Applying definition overrides for {law_name}: {list(overwrite_definitions.keys())}")

        return overwrite_input, overwrite_definitions

    def create_population(self, num_people=1000, save=True, population_params=None):
        """Create a new population and optionally save it."""
        import sys

        print(f"Generating {num_people} people with realistic demographics...", file=sys.stderr)
        pairs = self.generate_paired_people(num_people)

        print("Setting up test data sources...", file=sys.stderr)
        people = self.setup_test_data(pairs)

        if save:
            population_id = str(uuid.uuid4())
            params = population_params or {
                "num_people": num_people,
                "simulation_date": self.simulation_date,
            }
            self.save_population(population_id, people, params)
            print(f"Saved population as {population_id}", file=sys.stderr)
            return population_id, people
        else:
            return None, people

    def run_simulation(self, num_people=1000, population_id=None):
        """Run simulation with either a new or existing population."""
        import sys

        # Use existing population if provided
        if population_id:
            print(f"Loading existing population {population_id}...", file=sys.stderr)
            people = self.load_population(population_id)
            # Re-setup data sources with loaded population
            # Note: Don't reinitialize Services to avoid registration conflicts
            # Use population_id as random seed for reproducibility
            self.setup_test_data_from_people(people, random_seed=population_id)
        else:
            # Create new population
            _, people = self.create_population(num_people, save=False)

        total_people = len(people)

        print(f"Simulating laws for {total_people} people...", file=sys.stderr)
        progress_bar = tqdm(total=total_people, desc="Simulating", unit="person", file=sys.stderr)
        for person in people:
            self.simulate_person(person)
            progress_bar.update(1)
        progress_bar.close()

        # Convert to DataFrame
        results_df = pd.DataFrame([r for r in self.results if r is not None])

        # Return only if we have sufficient data
        if len(results_df) > 0:
            return results_df
        else:
            raise ValueError("Simulation failed to generate valid results")

    def setup_test_data_from_people(self, people, random_seed=None):
        """Setup test data from pre-existing people list (for loaded populations)."""
        # Convert the people list into pairs format expected by setup_test_data
        # This is a bit of a hack but maintains compatibility
        pairs = []
        processed_bsns = set()

        for person in people:
            if person["bsn"] in processed_bsns:
                continue

            processed_bsns.add(person["bsn"])

            # Find partner if exists
            partner = None
            if person.get("partner_bsn"):
                partner = next((p for p in people if p["bsn"] == person["partner_bsn"]), None)
                if partner:
                    processed_bsns.add(partner["bsn"])

            pairs.append((person, partner))

        # Now call the original setup_test_data with the random seed
        return self.setup_test_data(pairs, random_seed=random_seed)

    def calculate_law_breakdowns(self, df, law_name, eligible_col, amount_col):
        """Calculate breakdowns by various demographics for a specific law."""
        # Handle special case for voting_rights which uses same column for eligible and amount
        if law_name == "voting_rights":
            amount_col = eligible_col

        breakdowns = {}

        # By age group
        age_bins = [0, 30, 45, 67, 85, 150]
        age_labels = ["18-30", "30-45", "45-67", "67-85", "85+"]
        df["age_group"] = pd.cut(df["age"], bins=age_bins, labels=age_labels)

        age_breakdown = (
            df.groupby("age_group", observed=True)
            .agg({eligible_col: ["sum", "count", "mean"], amount_col: "mean"})
            .round(2)
        )

        breakdowns["by_age"] = {}
        if len(age_breakdown) > 0:
            for age in age_breakdown.index:
                row = age_breakdown.loc[age]
                try:
                    breakdowns["by_age"][str(age)] = {
                        "eligible_count": int(row[(eligible_col, "sum")]),
                        "total_count": int(row[(eligible_col, "count")]),
                        "eligible_pct": float(row[(eligible_col, "mean")] * 100),
                        "avg_amount": float(row[(amount_col, "mean")]) if pd.notna(row[(amount_col, "mean")]) else 0,
                    }
                except (KeyError, TypeError):
                    breakdowns["by_age"][str(age)] = {
                        "eligible_count": 0,
                        "total_count": 0,
                        "eligible_pct": 0,
                        "avg_amount": 0,
                    }

        # By income bracket
        income_bins = [0, 20000, 40000, 60000, 1000000]
        income_labels = ["€0-20k", "€20-40k", "€40-60k", "€60k+"]
        df["income_bracket"] = pd.cut(df["income"], bins=income_bins, labels=income_labels)

        income_breakdown = (
            df.groupby("income_bracket", observed=True)
            .agg({eligible_col: ["sum", "count", "mean"], amount_col: "mean"})
            .round(2)
        )

        breakdowns["by_income"] = {}
        if len(income_breakdown) > 0:
            for bracket in income_breakdown.index:
                row = income_breakdown.loc[bracket]
                try:
                    breakdowns["by_income"][str(bracket)] = {
                        "eligible_count": int(row[(eligible_col, "sum")]),
                        "total_count": int(row[(eligible_col, "count")]),
                        "eligible_pct": float(row[(eligible_col, "mean")] * 100),
                        "avg_amount": float(row[(amount_col, "mean")]) if pd.notna(row[(amount_col, "mean")]) else 0,
                    }
                except (KeyError, TypeError):
                    breakdowns["by_income"][str(bracket)] = {
                        "eligible_count": 0,
                        "total_count": 0,
                        "eligible_pct": 0,
                        "avg_amount": 0,
                    }

        # By housing type (if relevant)
        if "housing_type" in df.columns and law_name in ["huurtoeslag"]:
            housing_breakdown = (
                df.groupby("housing_type", observed=True)
                .agg({eligible_col: ["sum", "count", "mean"], amount_col: "mean"})
                .round(2)
            )

            breakdowns["by_housing"] = {}
            if len(housing_breakdown) > 0:
                for housing in housing_breakdown.index:
                    row = housing_breakdown.loc[housing]
                    try:
                        breakdowns["by_housing"][str(housing)] = {
                            "eligible_count": int(row[(eligible_col, "sum")]),
                            "total_count": int(row[(eligible_col, "count")]),
                            "eligible_pct": float(row[(eligible_col, "mean")] * 100),
                            "avg_amount": float(row[(amount_col, "mean")])
                            if pd.notna(row[(amount_col, "mean")])
                            else 0,
                        }
                    except (KeyError, TypeError):
                        breakdowns["by_housing"][str(housing)] = {
                            "eligible_count": 0,
                            "total_count": 0,
                            "eligible_pct": 0,
                            "avg_amount": 0,
                        }

        # By partner status
        partner_breakdown = (
            df.groupby("has_partner", observed=True)
            .agg({eligible_col: ["sum", "count", "mean"], amount_col: "mean"})
            .round(2)
        )

        breakdowns["by_partner"] = {
            "with_partner": {"eligible_count": 0, "total_count": 0, "eligible_pct": 0, "avg_amount": 0},
            "without_partner": {"eligible_count": 0, "total_count": 0, "eligible_pct": 0, "avg_amount": 0},
        }

        if True in partner_breakdown.index:
            row = partner_breakdown.loc[True]
            try:
                breakdowns["by_partner"]["with_partner"] = {
                    "eligible_count": int(row[(eligible_col, "sum")]),
                    "total_count": int(row[(eligible_col, "count")]),
                    "eligible_pct": float(row[(eligible_col, "mean")] * 100),
                    "avg_amount": float(row[(amount_col, "mean")]) if pd.notna(row[(amount_col, "mean")]) else 0,
                }
            except (KeyError, TypeError):
                pass

        if False in partner_breakdown.index:
            row = partner_breakdown.loc[False]
            try:
                breakdowns["by_partner"]["without_partner"] = {
                    "eligible_count": int(row[(eligible_col, "sum")]),
                    "total_count": int(row[(eligible_col, "count")]),
                    "eligible_pct": float(row[(eligible_col, "mean")] * 100),
                    "avg_amount": float(row[(amount_col, "mean")]) if pd.notna(row[(amount_col, "mean")]) else 0,
                }
            except (KeyError, TypeError):
                pass

        return breakdowns

    def calculate_tax_breakdowns(self, df):
        """Calculate tax breakdowns by demographics."""
        breakdowns = {}

        # By age group
        age_bins = [0, 30, 45, 67, 85, 150]
        age_labels = ["18-30", "30-45", "45-67", "67-85", "85+"]
        df["age_group"] = pd.cut(df["age"], bins=age_bins, labels=age_labels)

        age_breakdown = df.groupby("age_group", observed=True).agg({"tax_due": "mean", "income": "mean"}).round(2)

        breakdowns["by_age"] = {}
        if len(age_breakdown) > 0:
            for age in age_breakdown.index:
                row = age_breakdown.loc[age]
                try:
                    avg_tax = float(row["tax_due"])
                    avg_income = float(row["income"])
                    breakdowns["by_age"][str(age)] = {
                        "avg_amount": avg_tax,
                        "avg_rate": (avg_tax / avg_income * 100) if avg_income > 0 else 0,
                        "eligible_pct": 100.0,  # Everyone pays tax
                    }
                except (KeyError, TypeError):
                    breakdowns["by_age"][str(age)] = {"avg_amount": 0, "avg_rate": 0, "eligible_pct": 100.0}

        # By income bracket
        income_bins = [0, 20000, 40000, 60000, 1000000]
        income_labels = ["€0-20k", "€20-40k", "€40-60k", "€60k+"]
        df["income_bracket"] = pd.cut(df["income"], bins=income_bins, labels=income_labels)

        income_breakdown = (
            df.groupby("income_bracket", observed=True).agg({"tax_due": "mean", "income": "mean"}).round(2)
        )

        breakdowns["by_income"] = {}
        if len(income_breakdown) > 0:
            for bracket in income_breakdown.index:
                row = income_breakdown.loc[bracket]
                try:
                    avg_tax = float(row["tax_due"])
                    avg_income = float(row["income"])
                    breakdowns["by_income"][str(bracket)] = {
                        "avg_amount": avg_tax,
                        "avg_rate": (avg_tax / avg_income * 100) if avg_income > 0 else 0,
                        "eligible_pct": 100.0,
                    }
                except (KeyError, TypeError):
                    breakdowns["by_income"][str(bracket)] = {"avg_amount": 0, "avg_rate": 0, "eligible_pct": 100.0}

        # By partner status
        partner_breakdown = df.groupby("has_partner", observed=True).agg({"tax_due": "mean", "income": "mean"}).round(2)

        breakdowns["by_partner"] = {
            "with_partner": {"avg_amount": 0, "avg_rate": 0, "eligible_pct": 100.0},
            "without_partner": {"avg_amount": 0, "avg_rate": 0, "eligible_pct": 100.0},
        }

        if True in partner_breakdown.index:
            row = partner_breakdown.loc[True]
            try:
                avg_tax = float(row["tax_due"])
                avg_income = float(row["income"])
                breakdowns["by_partner"]["with_partner"] = {
                    "avg_amount": avg_tax,
                    "avg_rate": (avg_tax / avg_income * 100) if avg_income > 0 else 0,
                    "eligible_pct": 100.0,
                }
            except (KeyError, TypeError):
                pass

        if False in partner_breakdown.index:
            row = partner_breakdown.loc[False]
            try:
                avg_tax = float(row["tax_due"])
                avg_income = float(row["income"])
                breakdowns["by_partner"]["without_partner"] = {
                    "avg_amount": avg_tax,
                    "avg_rate": (avg_tax / avg_income * 100) if avg_income > 0 else 0,
                    "eligible_pct": 100.0,
                }
            except (KeyError, TypeError):
                pass

        return breakdowns

    def calculate_disposable_income_breakdowns(self, df):
        """Calculate disposable income breakdowns by demographics."""
        breakdowns = {}

        # By age group
        age_bins = [0, 30, 45, 67, 85, 150]
        age_labels = ["18-30", "30-45", "45-67", "67-85", "85+"]
        df["age_group"] = pd.cut(df["age"], bins=age_bins, labels=age_labels)

        age_breakdown = (
            df.groupby("age_group", observed=True)
            .agg({"disposable_income": ["mean", "median"], "disposable_income_after_housing": "mean"})
            .round(2)
        )

        breakdowns["by_age"] = {}
        if len(age_breakdown) > 0:
            for age in age_breakdown.index:
                row = age_breakdown.loc[age]
                try:
                    breakdowns["by_age"][str(age)] = {
                        "avg_monthly": float(row[("disposable_income", "mean")]),
                        "median_monthly": float(row[("disposable_income", "median")]),
                        "after_housing_avg": float(row[("disposable_income_after_housing", "mean")]),
                    }
                except (KeyError, TypeError):
                    breakdowns["by_age"][str(age)] = {"avg_monthly": 0, "median_monthly": 0, "after_housing_avg": 0}

        # By income bracket
        income_bins = [0, 20000, 40000, 60000, 1000000]
        income_labels = ["€0-20k", "€20-40k", "€40-60k", "€60k+"]
        df["income_bracket"] = pd.cut(df["income"], bins=income_bins, labels=income_labels)

        income_breakdown = (
            df.groupby("income_bracket", observed=True)
            .agg({"disposable_income": ["mean", "median"], "disposable_income_after_housing": "mean"})
            .round(2)
        )

        breakdowns["by_income"] = {}
        if len(income_breakdown) > 0:
            for bracket in income_breakdown.index:
                row = income_breakdown.loc[bracket]
                try:
                    breakdowns["by_income"][str(bracket)] = {
                        "avg_monthly": float(row[("disposable_income", "mean")]),
                        "median_monthly": float(row[("disposable_income", "median")]),
                        "after_housing_avg": float(row[("disposable_income_after_housing", "mean")]),
                    }
                except (KeyError, TypeError):
                    breakdowns["by_income"][str(bracket)] = {
                        "avg_monthly": 0,
                        "median_monthly": 0,
                        "after_housing_avg": 0,
                    }

        # By housing type
        housing_breakdown = (
            df.groupby("housing_type", observed=True)
            .agg({"disposable_income": ["mean", "median"], "disposable_income_after_housing": "mean"})
            .round(2)
        )

        breakdowns["by_housing"] = {}
        if len(housing_breakdown) > 0:
            for housing_type in housing_breakdown.index:
                row = housing_breakdown.loc[housing_type]
                try:
                    breakdowns["by_housing"][str(housing_type)] = {
                        "avg_monthly": float(row[("disposable_income", "mean")]),
                        "median_monthly": float(row[("disposable_income", "median")]),
                        "after_housing_avg": float(row[("disposable_income_after_housing", "mean")]),
                    }
                except (KeyError, TypeError):
                    breakdowns["by_housing"][str(housing_type)] = {
                        "avg_monthly": 0,
                        "median_monthly": 0,
                        "after_housing_avg": 0,
                    }

        return breakdowns

    def get_summary_with_breakdowns(self, results_df, simulation_date):
        """Generate summary statistics with demographic breakdowns for web API."""
        # Calculate summary statistics
        summary = {
            "demographics": {
                "total_people": len(results_df),
                "avg_age": float(results_df["age"].mean()),
                "with_partners_pct": float(results_df["has_partner"].mean() * 100),
                "students_pct": float(results_df["is_student"].mean() * 100),
                "renters_pct": float((results_df["housing_type"] == "rent").mean() * 100),
                "with_children_pct": float(results_df["has_children"].mean() * 100),
            },
            "income": {
                "avg_annual": float(results_df["income"].mean()),
                "median_annual": float(results_df["income"].median()),
            },
            "laws": {
                "zorgtoeslagwet": {
                    "eligible_pct": float(results_df["zorgtoeslag_eligible"].mean() * 100),
                    "avg_amount": float(results_df[results_df["zorgtoeslag_eligible"]]["zorgtoeslag_amount"].mean())
                    if any(results_df["zorgtoeslag_eligible"])
                    else 0,
                    "breakdowns": self.calculate_law_breakdowns(
                        results_df, "zorgtoeslag", "zorgtoeslag_eligible", "zorgtoeslag_amount"
                    ),
                },
                "huurtoeslag": {
                    "eligible_pct": float(results_df["huurtoeslag_eligible"].mean() * 100),
                    "avg_amount": float(results_df[results_df["huurtoeslag_eligible"]]["huurtoeslag_amount"].mean())
                    if any(results_df["huurtoeslag_eligible"])
                    else 0,
                    "breakdowns": self.calculate_law_breakdowns(
                        results_df, "huurtoeslag", "huurtoeslag_eligible", "huurtoeslag_amount"
                    ),
                },
                "algemeneouderdomswet": {
                    "eligible_pct": float(results_df["aow_eligible"].mean() * 100),
                    "avg_amount": float(results_df[results_df["aow_eligible"]]["aow_amount"].mean())
                    if any(results_df["aow_eligible"])
                    else 0,
                    "breakdowns": self.calculate_law_breakdowns(results_df, "aow", "aow_eligible", "aow_amount"),
                },
                "bijstand": {
                    "eligible_pct": float(results_df["bijstand_eligible"].mean() * 100),
                    "avg_amount": float(results_df[results_df["bijstand_eligible"]]["bijstand_amount"].mean())
                    if any(results_df["bijstand_eligible"])
                    else 0,
                    "breakdowns": self.calculate_law_breakdowns(
                        results_df, "bijstand", "bijstand_eligible", "bijstand_amount"
                    ),
                },
                "kinderopvang": {
                    "eligible_pct": float(results_df["kinderopvangtoeslag_eligible"].mean() * 100),
                    "avg_amount": float(
                        results_df[results_df["kinderopvangtoeslag_eligible"]]["kinderopvangtoeslag_amount"].mean()
                    )
                    if any(results_df["kinderopvangtoeslag_eligible"])
                    else 0,
                    "breakdowns": self.calculate_law_breakdowns(
                        results_df, "kinderopvangtoeslag", "kinderopvangtoeslag_eligible", "kinderopvangtoeslag_amount"
                    ),
                },
                "kindgebonden_budget": {
                    "eligible_pct": float(results_df["kindgebonden_budget_eligible"].mean() * 100),
                    "avg_amount": float(
                        results_df[results_df["kindgebonden_budget_eligible"]]["kindgebonden_budget_amount"].mean()
                    )
                    if any(results_df["kindgebonden_budget_eligible"])
                    else 0,
                    "breakdowns": self.calculate_law_breakdowns(
                        results_df, "kindgebonden_budget", "kindgebonden_budget_eligible", "kindgebonden_budget_amount"
                    ),
                },
                "ww": {
                    "eligible_pct": float(results_df["ww_eligible"].mean() * 100),
                    "avg_amount": float(results_df[results_df["ww_eligible"]]["ww_amount"].mean())
                    if any(results_df["ww_eligible"])
                    else 0,
                    "breakdowns": self.calculate_law_breakdowns(results_df, "ww", "ww_eligible", "ww_amount"),
                },
                "voting_rights": {
                    "eligible_pct": float(results_df["voting_rights"].mean() * 100),
                    "breakdowns": self.calculate_law_breakdowns(
                        results_df, "voting_rights", "voting_rights", "voting_rights"
                    ),
                },
                "inkomstenbelasting": {
                    "avg_tax": float(results_df["tax_due"].mean()),
                    "avg_tax_rate": float((results_df["tax_due"] / results_df["income"]).mean() * 100),
                    "avg_tax_credits": float(results_df["tax_credits"].mean()),
                    "avg_box1": float(results_df["tax_box1"].mean()),
                    "avg_box2": float(results_df["tax_box2"].mean()),
                    "avg_box3": float(results_df["tax_box3"].mean()),
                    "breakdowns": self.calculate_tax_breakdowns(results_df),
                },
            },
            "disposable_income": {
                "avg_monthly": float(results_df["disposable_income"].mean()),
                "median_monthly": float(results_df["disposable_income"].median()),
                "after_housing_avg": float(results_df["disposable_income_after_housing"].mean()),
                "breakdowns": self.calculate_disposable_income_breakdowns(results_df),
            },
        }

        return {
            "status": "success",
            "summary": summary,
            "total_people": len(results_df),
            "simulation_date": simulation_date,
        }


def format_money(amount):
    """Format money values consistently"""
    return f"€{amount:.2f}"


def analyze_by_groups(df, value_col, group_cols, groupby_col, agg_funcs=None):
    """Analyze a value column across different groups"""
    if agg_funcs is None:
        agg_funcs = ["mean", "min", "max", "count"]

    result = {}
    for col in group_cols:
        if col == groupby_col:
            continue

        # Skip if column doesn't exist
        if col not in df.columns:
            continue

        # Group by column and calculate statistics for value_col
        if pd.api.types.is_numeric_dtype(df[col]):
            # For numeric columns, create bins
            bins = pd.qcut(df[col], 4, duplicates="drop")
            grouped = df.groupby(bins)[value_col].agg(agg_funcs)
        else:
            # For categorical columns, use as is
            grouped = df.groupby(col)[value_col].agg(agg_funcs)

        result[col] = grouped

    return result


def print_law_statistics(df, law_name, law_eligible_col, law_amount_col):
    """Print detailed statistics for a specific law"""
    # Skip if columns don't exist
    if law_eligible_col not in df.columns or law_amount_col not in df.columns:
        print(f"Statistics for {law_name} not available")
        return

    # Calculate eligibility rate
    eligible_count = df[law_eligible_col].sum()
    eligibility_rate = eligible_count / len(df) * 100
    print(f"\n{law_name} Statistics:")
    print(f"Eligible: {eligible_count} people ({eligibility_rate:.1f}%)")

    if eligible_count == 0:
        print(f"No eligible people for {law_name}")
        return

    # Eligible only dataframe
    eligible_df = df[df[law_eligible_col]]

    # Basic amount statistics
    amounts = eligible_df[law_amount_col]
    print(f"Average amount: {format_money(amounts.mean())}")
    print(f"Amount range: {format_money(amounts.min())} - {format_money(amounts.max())}")

    # By income quartile
    income_bins = pd.qcut(df["income"], 4, labels=["Q1", "Q2", "Q3", "Q4"])
    df_with_quartile = df.copy()
    df_with_quartile["income_quartile"] = income_bins

    # Eligibility by income quartile
    eligibility_by_quartile = df_with_quartile.groupby("income_quartile", observed=True)[law_eligible_col].mean() * 100
    print("Eligibility by income quartile:")
    for quartile, rate in eligibility_by_quartile.items():
        quartile_df = df_with_quartile[df_with_quartile["income_quartile"] == quartile]
        income_range = (quartile_df["income"].min(), quartile_df["income"].max())
        print(f"  {quartile} (€{income_range[0]:.0f}-€{income_range[1]:.0f}): {rate:.1f}%")

    # Average amount by income quartile for eligible people
    eligible_with_quartile = df_with_quartile[df_with_quartile[law_eligible_col]]
    if len(eligible_with_quartile) > 0:
        amount_by_quartile = eligible_with_quartile.groupby("income_quartile", observed=True)[law_amount_col].mean()
        print("Average amount by income quartile:")
        for quartile, amount in amount_by_quartile.items():
            print(f"  {quartile}: {format_money(amount)}")

    # By age group
    age_bins = [0, 30, 45, 67, 85, 100]
    age_labels = ["<30", "30-45", "45-67", "67-85", "85+"]
    df_with_age_group = df.copy()
    df_with_age_group["age_group"] = pd.cut(df["age"], bins=age_bins, labels=age_labels, right=False)

    # Eligibility by age group
    eligibility_by_age = df_with_age_group.groupby("age_group", observed=True)[law_eligible_col].mean() * 100
    print("Eligibility by age group:")
    for age_group, rate in eligibility_by_age.items():
        print(f"  {age_group}: {rate:.1f}%")

    # Average amount by age group for eligible people
    eligible_with_age = df_with_age_group[df_with_age_group[law_eligible_col]]
    if len(eligible_with_age) > 0:
        amount_by_age = eligible_with_age.groupby("age_group", observed=True)[law_amount_col].mean()
        print("Average amount by age group:")
        for age_group, amount in amount_by_age.items():
            print(f"  {age_group}: {format_money(amount)}")

    # By housing type (if applicable)
    if "housing_type" in df.columns:
        eligibility_by_housing = df.groupby("housing_type")[law_eligible_col].mean() * 100
        print("Eligibility by housing type:")
        for housing_type, rate in eligibility_by_housing.items():
            print(f"  {housing_type}: {rate:.1f}%")

        # Average amount by housing type for eligible people
        eligible_with_housing = df[df[law_eligible_col]]
        if len(eligible_with_housing) > 0:
            amount_by_housing = eligible_with_housing.groupby("housing_type", observed=True)[law_amount_col].mean()
            print("Average amount by housing type:")
            for housing_type, amount in amount_by_housing.items():
                print(f"  {housing_type}: {format_money(amount)}")


def main() -> None:
    print("\n🇳🇱 Starting Dutch law simulation...")
    simulator = LawSimulator()

    # Run the simulation with progress bar
    results = simulator.run_simulation(num_people=1000)

    # Print summary statistics
    print("\n📊 === POPULATION DEMOGRAPHICS ===")
    print(f"Total people: {len(results)}")
    print(f"👫 With partners: {(results['has_partner'].mean() * 100):.1f}%")
    print(f"🎓 Students: {(results['is_student'].mean() * 100):.1f}%")
    print(f"⏳ Average age: {results['age'].mean():.1f} years")
    print(f"📅 Age range: {results['age'].min():.0f}-{results['age'].max():.0f} years")
    print(f"🏘️ Renters: {(results['housing_type'] == 'rent').mean() * 100:.1f}%")
    print(f"👶 With children: {(results['has_children']).mean() * 100:.1f}%")

    print("\n💰 === INCOME STATISTICS (DEMOGRAPHICS) ===")
    print(f"💼 Average annual income: {format_money(results['income'].mean())}")
    print(f"📊 Median annual income: {format_money(results['income'].median())}")

    print("\n📊 Income quartiles:")
    income_quantiles = results["income"].quantile([0.25, 0.5, 0.75])
    print(f"  25th percentile: {format_money(income_quantiles[0.25])}")
    print(f"  50th percentile: {format_money(income_quantiles[0.5])}")
    print(f"  75th percentile: {format_money(income_quantiles[0.75])}")

    print("\n💶 === BESTEEDBAAR INKOMEN (DISPOSABLE INCOME) ===")
    print(f"💸 Average monthly disposable income: {format_money(results['disposable_income'].mean())}")
    print(f"📊 Median monthly disposable income: {format_money(results['disposable_income'].median())}")
    print(f"🏠 After housing costs: {format_money(results['disposable_income_after_housing'].mean())}")

    print("\n👥 Disposable income by age group:")
    age_bins = [0, 30, 45, 67, 85, 100]
    age_labels = ["<30", "30-45", "45-67", "67-85", "85+"]
    for i, (lower, upper) in enumerate(itertools.pairwise(age_bins)):
        group = results[(results["age"] >= lower) & (results["age"] < upper)]
        if len(group) > 0:
            print(f"  {age_labels[i]}: {format_money(group['disposable_income'].mean())}")

    print("\n🏘️ Disposable income by housing type:")
    for housing_type, group in results.groupby("housing_type", observed=True):
        print(f"  {housing_type}: {format_money(group['disposable_income'].mean())}")

    print("\n💰 Disposable income by income quartile:")
    income_bins = pd.qcut(results["income"], 4, labels=["Q1 (lowest)", "Q2", "Q3", "Q4 (highest)"])
    results_with_quartile = results.copy()
    results_with_quartile["income_quartile"] = income_bins
    for quartile, group in results_with_quartile.groupby("income_quartile", observed=True):
        income_range = (group["income"].min(), group["income"].max())
        print(
            f"  {quartile} (€{income_range[0]:.0f}-€{income_range[1]:.0f}): {format_money(group['disposable_income'].mean())}"
        )

    # Individual law statistics
    print("\n⚖️ === INDIVIDUAL LAW STATISTICS ===")

    # Zorgtoeslag
    print_law_statistics(results, "🏥 Zorgtoeslag (Healthcare Subsidy)", "zorgtoeslag_eligible", "zorgtoeslag_amount")

    # Huurtoeslag
    print_law_statistics(results, "🏠 Huurtoeslag (Rent Subsidy)", "huurtoeslag_eligible", "huurtoeslag_amount")

    # AOW
    print_law_statistics(results, "👴 AOW (State Pension)", "aow_eligible", "aow_amount")

    # Bijstand
    print_law_statistics(results, "🤲 Bijstand (Social Assistance)", "bijstand_eligible", "bijstand_amount")

    # Kinderopvangtoeslag
    print_law_statistics(
        results,
        "👶 Kinderopvangtoeslag (Childcare Subsidy)",
        "kinderopvangtoeslag_eligible",
        "kinderopvangtoeslag_amount",
    )

    # Inkomstenbelasting
    print("\n💸 Inkomstenbelasting (Income Tax) Statistics:")
    print(f"Average tax due: {format_money(results['tax_due'].mean())}")
    print(f"Average tax rate: {(results['tax_due'] / results['income']).mean() * 100:.1f}%")
    print(f"Average tax credits: {format_money(results['tax_credits'].mean())}")
    print("Tax by box:")
    print(f"  Box 1 (work/home): {format_money(results['tax_box1'].mean())}")
    print(f"  Box 2 (shares): {format_money(results['tax_box2'].mean())}")
    print(f"  Box 3 (savings): {format_money(results['tax_box3'].mean())}")

    # Kiesrecht
    voting_eligible = results["voting_rights"].mean() * 100
    print("\n🗳️ Kiesrecht (Voting Rights) Statistics:")
    print(f"Eligible to vote: {voting_eligible:.1f}%")

    # By nationality
    voting_by_nationality = results.groupby("has_dutch_nationality", observed=True)["voting_rights"].mean() * 100
    print("Voting eligibility by nationality:")
    for has_dutch, rate in voting_by_nationality.items():
        nationality = "Dutch" if has_dutch else "Non-Dutch"
        print(f"  {nationality}: {rate:.1f}%")

    print("\n✅ Simulation complete!")


if __name__ == "__main__":
    main()
