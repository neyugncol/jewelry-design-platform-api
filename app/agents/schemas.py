from typing import Literal

from pydantic import BaseModel, Field

from schemas.jewelry import TargetAudience, JewelryType, Metal, ColorTone, Gemstone, Shape, Style, Occasion


class JewelryPropertiesSchema(BaseModel):
    target_audience: TargetAudience | None = Field(description="Target audience: men, women, unisex, couple, personalized")
    jewelry_type: JewelryType | None = Field(description="Type of jewelry: ring, bracelet, bangle, necklace, earring, anklet")
    metal: Metal | None = Field(description="Metal type: 24k_gold, 22k_gold, 18k_gold, 14k_gold, 10k_gold, silver, platinum")
    color: ColorTone | None = Field(description="Color tone of the metal: white, yellow, rose")
    weight: float | None = Field(description="Weight of the metal in grams")
    gemstone: Gemstone | None = Field(description="Type of gemstone: diamond, sapphire, emerald, amethyst, ruby, citrine, tourmaline, topaz, garnet, peridot, spinel, cubic_zirconia, aquamarine, opal, moonstone, pearl")
    shape: Shape | None = Field(description="Shape of the gemstone: round, oval, marquise, pear, heart, radiant, emerald, cushion, princess")
    size: float | None = Field(description="Size of the gemstone in carats")
    style: Style | None = Field(description="Style of jewelry design: classic, modern, vintage, minimalist, luxury, personality, natural")
    occasion: Occasion | None = Field(description="Occasion for wearing the jewelry: wedding, engagement, casual, formal, party, daily_wear")
    inspiration: str | None = Field(description="Inspiring story or background for the jewelry design")


class JewelryDesignSchema(BaseModel):
    name: str = Field(description="Name of the jewelry design")
    description: str = Field(description="Detailed description of the jewelry design")
    properties: JewelryPropertiesSchema = Field(description="Properties of the jewelry design")
    images: list[str] = Field(description="List of image ids for the design")
    three_d_model: str | None = Field(description="3D model ids if available")



class JewelryProductSchema(BaseModel):
    id: str = Field(description="Unique identifier for the jewelry design")
    name: str = Field(description="Name of the jewelry design")
    description: str = Field(description="Detailed description of the jewelry design")
    properties: JewelryPropertiesSchema = Field(description="Properties of the jewelry design")
    images: list[str] = Field(description="List of image ids for the design")
    three_d_model: str | None = Field(description="3D model ids if available")
    price: float = Field(description="Price of the jewelry product in VND.")


class ArtifactSchema(BaseModel):
    type: Literal["design", "recommendation"] = Field(description="Type of artifact: 'design' or 'recommendation'")
    design: JewelryDesignSchema | None = Field(None, description="Design object if type is 'design' else null")
    products: list[JewelryProductSchema] | None = Field(None, description="List of products if type is 'recommendation' else null")
