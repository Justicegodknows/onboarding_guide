# Product dataclass for extracted product items
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Product:
	"""Represents a product extracted from the website."""
	name: Optional[str] = None  # Name of the product
	price: Optional[str] = None  # Price as a string (normalized later)
	description: Optional[str] = None  # Product description
	url: Optional[str] = None  # Product page URL
