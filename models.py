from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class BeanRoastingType(str, Enum):
    FILTER = "FILTER"
    ESPRESSO = "ESPRESSO"
    OMNI = "OMNI"


class Roast(str, Enum):
    CINNAMON_ROAST = "CINNAMON_ROAST"
    AMERICAN_ROAST = "AMERICAN_ROAST"
    NEW_ENGLAND_ROAST = "NEW_ENGLAND_ROAST"
    HALF_CITY_ROAST = "HALF_CITY_ROAST"
    MODERATE_LIGHT_ROAST = "MODERATE_LIGHT_ROAST"
    CITY_ROAST = "CITY_ROAST"
    CITY_PLUS_ROAST = "CITY_PLUS_ROAST"
    FULL_CITY_ROAST = "FULL_CITY_ROAST"
    FULL_CITY_PLUS_ROAST = "FULL_CITY_PLUS_ROAST"
    ITALIAN_ROAST = "ITALIAN_ROAST"
    VIEANNA_ROAST = "VIEANNA_ROAST"
    FRENCH_ROAST = "FRENCH_ROAST"
    CUSTOM_ROAST = "CUSTOM_ROAST"


class BeanMix(str, Enum):
    SINGLE_ORIGIN = "SINGLE_ORIGIN"
    BLEND = "BLEND"


class VarietyData(BaseModel):
    country: Optional[str] = None
    region: Optional[str] = None
    farm: Optional[str] = None
    farmer: Optional[str] = None
    variety: Optional[str] = None
    processing: Optional[str] = None
    elevation: Optional[str] = None
    harvest_time: Optional[str] = None
    certification: Optional[str] = None
    percentage: Optional[int] = None


class BeanData(BaseModel):
    coffee_name: str
    roaster: Optional[str] = None
    roasting_date: Optional[str] = None
    website: Optional[str] = None

    bean_roasting_type: Optional[BeanRoastingType] = None
    roast: Optional[Roast] = None
    roast_custom: Optional[str] = None
    degree_of_roast: Optional[float] = Field(None, ge=0, le=5)
    bean_mix: Optional[BeanMix] = None

    weight: Optional[int] = None
    cost: Optional[float] = None
    ean_article: Optional[str] = None
    flavour_profile: Optional[str] = None
    cupping_points: Optional[str] = None
    decaffeinated: bool = False

    varieties: list[VarietyData] = []
    notes: Optional[str] = None
