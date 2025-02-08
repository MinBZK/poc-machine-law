import asyncio
import logging
import random
from datetime import datetime, date

import numpy as np
import pandas as pd

from machine.service import Services

logging.basicConfig(level=logging.ERROR)


class LawSimulator:
    def __init__(self, simulation_date="2025-03-01"):
        self.simulation_date = simulation_date
        self.services = Services(simulation_date)
        self.results = []
        self.used_bsns = set()  # Track used BSNs

    def generate_bsn(self):
        while True:
            bsn = f"999{random.randint(100000, 999999)}"
            if bsn not in self.used_bsns:
                self.used_bsns.add(bsn)
                return bsn

    def generate_person(self, birth_year_range=(1940, 2007)):
        birth_date = date(
            random.randint(*birth_year_range),
            random.randint(1, 12),
            random.randint(1, 28)
        )
        age = (datetime.strptime(self.simulation_date, "%Y-%m-%d").date() - birth_date).days // 365

        # Also store study status for consistency
        is_student = age < 30 and random.random() < 0.6

        return {
            "bsn": self.generate_bsn(),
            "birth_date": birth_date,
            "age": age,
            "annual_income": min(max(int(np.random.lognormal(mean=10.8, sigma=0.4)), 0), 200000) * 100,
            "net_worth": min(max(int(np.random.lognormal(mean=11, sigma=1)), 0), 1000000) * 100,
            "work_years": min(max(0, (age - 15) * random.uniform(0.5, 0.9)), 50),
            "residence_years": min(max(0, (age - 15) * random.uniform(0.8, 1.0)), 50),
            "is_student": is_student,
            "study_grant": random.randint(2000, 4500) * 100 if is_student else 0
        }

    def generate_paired_people(self, num_people):
        pairs = []  # Store people in pairs (person, partner or None)
        while len([p for pair in pairs for p in pair if p is not None]) < num_people:
            person = self.generate_person()

            if random.random() < 0.6:  # 60% chance of partner
                age_diff = random.gauss(0, 5)
                partner = self.generate_person(
                    birth_year_range=(
                        person["birth_date"].year + int(age_diff) - 1,
                        person["birth_date"].year + int(age_diff) + 1
                    )
                )
                pairs.append((person, partner))
            else:
                pairs.append((person, None))

        return pairs

    def setup_test_data(self, pairs):
        # Flatten pairs into list of people with partner references
        people = []
        for person, partner in pairs:
            person["partner_bsn"] = partner["bsn"] if partner else None
            people.append(person)
            if partner:
                partner["partner_bsn"] = person["bsn"]
                people.append(partner)

        sources = {
            ('RvIG', 'personen'): [{
                'bsn': p['bsn'],
                'geboortedatum': p['birth_date'].isoformat(),
                'verblijfsadres': 'Amsterdam',
                'land_verblijf': 'NEDERLAND'
            } for p in people],

            ('RvIG', 'relaties'): [{
                'bsn': p['bsn'],
                'partnerschap_type': 'HUWELIJK' if p['partner_bsn'] else 'GEEN',
                'partner_bsn': p['partner_bsn']
            } for p in people],

            ('BELASTINGDIENST', 'inkomen'): [{
                'bsn': p['bsn'],
                'box1': p['annual_income'],
                'box2': 0,
                'box3': 0,
                'buitenlands': 0
            } for p in people],

            ('BELASTINGDIENST', 'vermogen'): [{
                'bsn': p['bsn'],
                'bezittingen': p['net_worth'],
                'schulden': 0
            } for p in people],

            ('UWV', 'dienstverbanden'): [{
                'bsn': p['bsn'],
                'start_date': p['birth_date'].isoformat(),
                'end_date': datetime.strptime(self.simulation_date, "%Y-%m-%d").date().isoformat()
            } for p in people],

            ('SVB', 'verzekerde_tijdvakken'): [{
                'bsn': p['bsn'],
                'woonperiodes': p['residence_years']
            } for p in people],

            ('RVZ', 'verzekeringen'): [{
                'bsn': p['bsn'],
                'polis_status': 'ACTIEF' if random.random() < 0.95 else 'INACTIEF'
            } for p in people],

            ('RVZ', 'verdragsverzekeringen'): [{
                'bsn': p['bsn'],
                'registratie': 'INACTIEF'
            } for p in people],

            ('DJI', 'detenties'): [{
                'bsn': p['bsn'],
                'status': 'VRIJ',
                'inrichting_type': 'GEEN'
            } for p in people],

            ('DJI', 'forensische_zorg'): [{
                'bsn': p['bsn'],
                'zorgtype': 'GEEN',
                'juridische_titel': 'GEEN'
            } for p in people],

            ('DUO', 'inschrijvingen'): [{
                'bsn': p['bsn'],
                'onderwijstype': 'HBO' if p['is_student'] else 'GEEN'
            } for p in people],

            ('DUO', 'studiefinanciering'): [{
                'bsn': p['bsn'],
                'aantal_studerend_gezin': random.randint(0, 3) if p['age'] < 30 else 0
            } for p in people],

            ('CBS', 'levensverwachting'): [
                {
                    'jaar': '2025',
                    'verwachting_65': 20.5
                }
            ],
        }

        for (service, table), data in sources.items():
            self.services.set_source_dataframe(service, table, pd.DataFrame(data))

        return people

    async def simulate_person(self, person):
        has_partner = bool(person["partner_bsn"])

        result = {
            "bsn": person["bsn"],
            "age": person["age"],
            "has_partner": has_partner,
            "income": person["annual_income"] / 100,
            "net_worth": person["net_worth"] / 100,
            "work_years": person["work_years"],
            "residence_years": person["residence_years"],
            "is_student": person["is_student"],
            "study_grant": person["study_grant"] / 100
        }

        zorgtoeslag = await self.services.evaluate("TOESLAGEN", "zorgtoeslagwet", {"BSN": person["bsn"]},
                                                   self.simulation_date)

        aow = await self.services.evaluate("SVB", "algemene_ouderdomswet", {"BSN": person["bsn"]}, self.simulation_date)

        result.update({
            "zorgtoeslag_eligible": zorgtoeslag.requirements_met,
            "zorgtoeslag_amount": zorgtoeslag.output.get('hoogte_toeslag', 0) / 100,
            "aow_eligible": aow.requirements_met,
            "aow_amount": aow.output.get('pension_amount', 0) / 100,
            "aow_accrual": aow.output.get('accrual_percentage', 0)
        })

        self.results.append(result)

    async def run_simulation(self, num_people=1000):
        pairs = self.generate_paired_people(num_people)
        people = self.setup_test_data(pairs)

        for person in people:
            await self.simulate_person(person)

        return pd.DataFrame(self.results)


async def main():
    simulator = LawSimulator()
    results = await simulator.run_simulation(num_people=1000)
    results.to_csv('simulation_results.csv', index=False)

    print("\nPopulation Statistics:")
    print(f"Total people: {len(results)}")
    print(f"With partners: {(results['has_partner'].mean() * 100):.1f}%")
    print(f"Students: {(results['is_student'].mean() * 100):.1f}%")
    print(f"Average age: {results['age'].mean():.1f} years")
    print(f"Age range: {results['age'].min():.0f}-{results['age'].max():.0f} years")
    print(f"\nIncome Statistics:")
    print(f"Average income: €{results['income'].mean():.2f}")
    print(f"Income percentiles:")
    for p in [10, 25, 50, 75, 90]:
        print(f"  {p}th: €{results['income'].quantile(p / 100):.2f}")

    print(f"\nZorgtoeslag Statistics:")
    eligible = results[results['zorgtoeslag_eligible']]
    print(f"Eligible: {(len(eligible) / len(results) * 100):.1f}%")
    print(f"Average amount: €{eligible['zorgtoeslag_amount'].mean():.2f}")
    print(f"Amount range: €{eligible['zorgtoeslag_amount'].min():.2f}-€{eligible['zorgtoeslag_amount'].max():.2f}")
    print(f"By income quartile (eligible %):")
    for i, (lower, upper) in enumerate(zip(results['income'].quantile([0, 0.25, 0.5, 0.75]),
                                           results['income'].quantile([0.25, 0.5, 0.75, 1.0]))):
        quartile = results[(results['income'] >= lower) & (results['income'] < upper)]
        pct = (quartile['zorgtoeslag_eligible'].mean() * 100)
        print(f"  Q{i + 1} (€{lower:.0f}-€{upper:.0f}): {pct:.1f}%")

    print(f"\nAOW Statistics:")
    eligible = results[results['aow_eligible']]
    print(f"Eligible: {(len(eligible) / len(results) * 100):.1f}%")
    print(f"Average amount: €{eligible['aow_amount'].mean():.2f}")
    print(f"Average accrual: {(results['aow_accrual'].mean() * 100):.1f}%")
    print(f"By age group (eligible %):")
    age_bins = [0, 50, 60, 65, 67, 150]
    age_labels = ['<50', '50-60', '60-65', '65-67', '67+']
    for i, (lower, upper) in enumerate(zip(age_bins[:-1], age_bins[1:])):
        group = results[(results['age'] >= lower) & (results['age'] < upper)]
        if len(group) > 0:
            pct = (group['aow_eligible'].mean() * 100)
            print(f"  {age_labels[i]}: {pct:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
