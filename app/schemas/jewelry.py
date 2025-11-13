import uuid
from enum import StrEnum

from pydantic import BaseModel, Field


class TargetAudience(StrEnum):
    MEN = "men"
    WOMEN = "women"
    UNISEX = "unisex"
    COUPLE = "couple"
    PERSONALIZED = "personalized"


class JewelryType(StrEnum):
    RING = "ring"
    EARRING = "earring"
    NECKLACE = "necklace"
    BRACELET = "bracelet"
    ANKLET = "anklet"
    BANGLE = "bangle"


class Metal(StrEnum):
    GOLD_18K = "18k_gold"
    GOLD_14K = "14k_gold"
    GOLD_10K = "10k_gold"
    SILVER = "silver"
    PLATINUM = "platinum"


class Gemstone(StrEnum):
    DIAMOND = "diamond"
    RUBY = "ruby"
    SAPPHIRE = "sapphire"
    EMERALD = "emerald"
    PEARL = "pearl"
    AMETHYST = "amethyst"
    TOPAZ = "topaz"
    GARNET = "garnet"
    AQUAMARINE = "aquamarine"


class Style(StrEnum):
    CLASSIC = "classic"
    MODERN = "modern"
    VINTAGE = "vintage"
    MINIMALIST = "minimalist"
    LUXURY = "luxury"
    PERSONALITY = "personality"
    NATURAL = "natural"


class Occasion(StrEnum):
    WEDDING = "wedding"
    ENGAGEMENT = "engagement"
    CASUAL = "casual"
    FORMAL = "formal"
    PARTY = "party"
    DAILY_WEAR = "daily_wear"


class Thickness(StrEnum):
    THIN = "thin"
    MEDIUM = "medium"
    THICK = "thick"


class JewelryProperties(BaseModel):
    """Schema for jewelry properties."""

    target_audience: TargetAudience | None = Field(None, description="Target audience: men, women, unisex, couple, personalized")
    jewelry_type: JewelryType | None = Field(None, description="Type: ring, earring, necklace, bracelet, anklet, bangle")
    metal: Metal | None = Field(None, description="Metal type: 18k_gold, 14k_gold, 10k_gold, silver, platinum")
    gemstone: Gemstone | None = Field(None, description="Gemstone: diamond, ruby, sapphire, emerald, pearl, amethyst, topaz, garnet, aquamarine")
    style: Style | None = Field(None, description="Style: classic, modern, vintage, minimalist, luxury, personality, natural")
    occasion: Occasion | None = Field(None, description="Occasion: wedding, engagement, casual, formal, party, daily_wear")
    color: str | None = Field(None, description="Dominant color: white gold, yellow gold, rose gold, etc.")
    thickness: Thickness | None = Field(None, description="Size or thickness: thin, medium, thick")
    inspiration: str | None = Field(None, description="Inspiring story or background")


class JewelryBase(BaseModel):
    """Base schema for jewelry."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the jewelry.")
    name: str = Field(description="Name of the jewelry.")
    description: str = Field(description="Detailed description of the jewelry.")
    properties: JewelryProperties = Field(description="Properties of the jewelry.")
    images: list[str] = Field(default_factory=list, description="List of image IDs for the jewelry.")
    three_d_model: str | None = Field(None, description="3D model ID for the jewelry.")


class JewelryDesign(JewelryBase):
    """Schema for a jewelry design."""
    reference_images: list[str] = Field(default_factory=list, description="List of reference image IDs for the jewelry design.")


class JewelryProduct(JewelryBase):
    """Schema for a jewelry product."""

    price: float = Field(description="Price of the jewelry product in VND.")

