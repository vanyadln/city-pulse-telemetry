from dataclasses import dataclass
from typing import List

@dataclass
class City:
    name: str
    lat: float
    lng: float
    subreddits: List[str]
    news_query: str

CITIES = [
    City("New York",     40.7128,  -74.0060, ["nyc", "newyorkcity", "manhattan"],        "New York City"),
    City("Los Angeles",  34.0522, -118.2437, ["losangeles", "LAlist", "california"],      "Los Angeles"),
    City("Chicago",      41.8781,  -87.6298, ["chicago", "ChicagoSuburbs"],               "Chicago"),
    City("Houston",      29.7604,  -95.3698, ["houston", "HoustonJobs"],                  "Houston Texas"),
    City("London",       51.5074,   -0.1278, ["london", "unitedkingdom", "casualuk"],     "London UK"),
    City("Mumbai",       19.0760,   72.8777, ["mumbai", "india", "IndiaInvestments"],     "Mumbai India"),
    City("Tokyo",        35.6762,  139.6503, ["japan", "Tokyo", "japanlife"],             "Tokyo Japan"),
    City("Sydney",      -33.8688,  151.2093, ["sydney", "australia", "AustralianPolitics"],"Sydney Australia"),
    City("Berlin",       52.5200,   13.4050, ["berlin", "germany", "de"],                 "Berlin Germany"),
    City("São Paulo",   -23.5505,  -46.6333, ["brasil", "saopaulo", "Curitiba"],          "São Paulo Brazil"),
    City("Dubai",        25.2048,   55.2708, ["dubai", "UAE", "expats"],                  "Dubai UAE"),
    City("Singapore",    1.3521,   103.8198, ["singapore", "SingaporeRaw"],               "Singapore"),
]