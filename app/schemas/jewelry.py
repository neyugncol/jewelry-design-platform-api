import uuid
from enum import StrEnum

from pydantic import BaseModel, Field


class TargetAudience(StrEnum):
    """Target audience for jewelry products."""
    MEN = "men"
    WOMEN = "women"
    UNISEX = "unisex"
    COUPLE = "couple"
    PERSONALIZED = "personalized"


class JewelryType(StrEnum):
    """Type of jewelry item."""
    RING = "ring"
    BRACELET = "bracelet"
    BANGLE = "bangle"
    NECKLACE = "necklace"
    EARRING = "earring"
    ANKLET = "anklet"


class Metal(StrEnum):
    """Type of metal used in jewelry."""
    GOLD_24K = "24k_gold"
    GOLD_22K = "22k_gold"
    GOLD_18K = "18k_gold"
    GOLD_14K = "14k_gold"
    GOLD_10K = "10k_gold"
    SILVER = "silver"
    PLATINUM = "platinum"


class ColorTone(StrEnum):
    """Color tone of the metal."""
    WHITE = "white"
    YELLOW = "yellow"
    ROSE = "rose"


class Gemstone(StrEnum):
    """Type of gemstone used in jewelry."""
    DIAMOND = "diamond"
    SAPPHIRE = "sapphire"
    EMERALD = "emerald"
    AMETHYST = "amethyst"
    RUBY = "ruby"
    CITRINE = "citrine"
    TOURMALINE = "tourmaline"
    TOPAZ = "topaz"
    GARNET = "garnet"
    PERIDOT = "peridot"
    SPINEL = "spinel"
    CUBIC_ZIRCONIA = "cubic_zirconia"
    AQUAMARINE = "aquamarine"
    OPAL = "opal"
    MOONSTONE = "moonstone"
    PEARL = "pearl"


class Shape(StrEnum):
    """Shape of gemstone."""
    ROUND = "round"
    OVAL = "oval"
    MARQUISE = "marquise"
    PEAR = "pear"
    HEART = "heart"
    RADIANT = "radiant"
    EMERALD = "emerald"
    CUSHION = "cushion"
    PRINCESS = "princess"


class Style(StrEnum):
    """Style of jewelry design."""
    CLASSIC = "classic"
    MODERN = "modern"
    VINTAGE = "vintage"
    MINIMALIST = "minimalist"
    LUXURY = "luxury"
    PERSONALITY = "personality"
    NATURAL = "natural"


class Occasion(StrEnum):
    """Occasion for wearing the jewelry."""
    WEDDING = "wedding"
    ENGAGEMENT = "engagement"
    CASUAL = "casual"
    FORMAL = "formal"
    PARTY = "party"
    DAILY_WEAR = "daily_wear"


class JewelryProperties(BaseModel):
    """Schema for jewelry properties."""

    target_audience: TargetAudience | None = Field(None, description="Target audience: men, women, unisex, couple, personalized")
    jewelry_type: JewelryType | None = Field(None, description="Type of jewelry: ring, bracelet, bangle, necklace, earring, anklet")
    metal: Metal | None = Field(None, description="Metal type: 24k_gold, 22k_gold, 18k_gold, 14k_gold, 10k_gold, silver, platinum")
    color: ColorTone | None = Field(None, description="Color tone of the metal: white, yellow, rose")
    weight: float | None = Field(None, description="Weight of the metal in grams")
    gemstone: Gemstone | None = Field(None, description="Type of gemstone: diamond, sapphire, emerald, amethyst, ruby, citrine, tourmaline, topaz, garnet, peridot, spinel, cubic_zirconia, aquamarine, opal, moonstone, pearl")
    shape: Shape | None = Field(None, description="Shape of the gemstone: round, oval, marquise, pear, heart, radiant, emerald, cushion, princess")
    size: float | None = Field(None, description="Size of the gemstone in carats")
    style: Style | None = Field(None, description="Style of jewelry design: classic, modern, vintage, minimalist, luxury, personality, natural")
    occasion: Occasion | None = Field(None, description="Occasion for wearing the jewelry: wedding, engagement, casual, formal, party, daily_wear")
    inspiration: str | None = Field(None, description="Inspiring story or background for the jewelry design")


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

