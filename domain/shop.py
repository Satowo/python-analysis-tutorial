from typing import List
from dataclasses import dataclass

from domain.price import Price

@dataclass
class Shop:
    name: str
    address: str
    prices: List[Price]
