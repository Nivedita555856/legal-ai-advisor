from typing import List, Dict

class LawyerFinder:
    """Suggest lawyers based on location and practice area."""

    LAWYERS_DB = {
        "Mumbai": [
            {"name": "Harish Salve", "practice_areas": ["Constitutional Law", "Commercial Litigation"], "experience": 35, "firm": "SA Law Chambers", "contact": "harish.salve@salaw.com", "rating": 4.9},
            {"name": "Janak Dwarkadas", "practice_areas": ["Corporate Law", "M&A"], "experience": 40, "firm": "Dwarkadas & Co", "contact": "janak@dwarkadas.com", "rating": 4.8},
            {"name": "Zia Mody", "practice_areas": ["M&A", "Private Equity", "Contract Law"], "experience": 38, "firm": "AZB & Partners", "contact": "zia.mody@azbpartners.com", "rating": 4.9},
        ],
        "Delhi": [
            {"name": "Mukul Rohatgi", "practice_areas": ["Constitutional Law", "Arbitration"], "experience": 42, "firm": "Rohatgi & Co", "contact": "mukul@rohatgi.com", "rating": 4.9},
            {"name": "Pinky Anand", "practice_areas": ["Family Law", "Constitutional Law"], "experience": 30, "firm": "Anand Law Partners", "contact": "pinky@anandlaw.com", "rating": 4.7},
            {"name": "Dushyant Dave", "practice_areas": ["Supreme Court", "Human Rights"], "experience": 38, "firm": "Dave Chambers", "contact": "dd@davechambers.com", "rating": 4.8},
        ],
        "Bangalore": [
            {"name": "Kiran S", "practice_areas": ["IT Law", "Startup Law", "Contract Law"], "experience": 15, "firm": "Kiran Legal", "contact": "kiran@kiranlegal.com", "rating": 4.6},
            {"name": "Arvind Datar", "practice_areas": ["Tax Law", "Commercial Law", "Arbitration"], "experience": 38, "firm": "Datar Chambers", "contact": "arvind@datar.com", "rating": 4.8},
            {"name": "Nisha George", "practice_areas": ["Employment Law", "Data Privacy", "GDPR"], "experience": 12, "firm": "George Legal", "contact": "nisha@georgelegal.com", "rating": 4.5},
        ],
        "Chennai": [
            {"name": "Krishnan V", "practice_areas": ["Corporate Law", "Arbitration", "M&A"], "experience": 22, "firm": "Krishnan & Co", "contact": "krishnan@krishnanlaw.com", "rating": 4.6},
            {"name": "Suresh Ramasubramanian", "practice_areas": ["Intellectual Property", "IT Law"], "experience": 18, "firm": "IP Legal Partners", "contact": "suresh@iplegal.com", "rating": 4.5},
            {"name": "Meenakshi Rajan", "practice_areas": ["Family Law", "Property Law"], "experience": 25, "firm": "Rajan Associates", "contact": "meenakshi@rajanlaw.com", "rating": 4.7},
        ],
        "Hyderabad": [
            {"name": "Vikram Nair", "practice_areas": ["Corporate Law", "Real Estate", "Contract Law"], "experience": 20, "firm": "Nair Legal", "contact": "vikram@nairlegal.com", "rating": 4.6},
            {"name": "Padma Rao", "practice_areas": ["Employment Law", "Labour Law"], "experience": 16, "firm": "Rao Law Firm", "contact": "padma@raolaw.com", "rating": 4.5},
        ],
    }

    async def find(self, area: str = "Bangalore", practice_area: str = None, limit: int = 3) -> List[Dict]:
        """Find lawyers by city and practice area."""
        city_lawyers = self.LAWYERS_DB.get(area, self.LAWYERS_DB.get("Bangalore", []))

        if practice_area:
            filtered = [
                l for l in city_lawyers
                if any(practice_area.lower() in pa.lower() for pa in l["practice_areas"])
            ]
            if not filtered:
                filtered = city_lawyers  # fallback to all city lawyers
        else:
            filtered = city_lawyers

        # Sort by rating desc
        filtered = sorted(filtered, key=lambda x: x.get("rating", 0), reverse=True)
        return filtered[:limit]

    async def find_by_speciality(self, speciality: str) -> List[Dict]:
        """Search across all cities for a speciality."""
        results = []
        for city, lawyers in self.LAWYERS_DB.items():
            for l in lawyers:
                if any(speciality.lower() in pa.lower() for pa in l["practice_areas"]):
                    results.append({**l, "city": city})
        return sorted(results, key=lambda x: x.get("rating", 0), reverse=True)[:5]
