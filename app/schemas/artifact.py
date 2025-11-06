import uuid
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.jewelry import  JewelryDesign, JewelryProduct


class ArtifactBase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the artifact")
    type: str = Field(description="Type of artifact")


class JewelryDesignArtifact(ArtifactBase):
    type: Literal["design"] = Field(default="design", description="Artifact type indicating a jewelry design")
    design: JewelryDesign = Field(description="Jewelry design details")


class ProductRecommendationArtifact(ArtifactBase):
    type: Literal["recommendation"] = Field(default="recommendation", description="Artifact type indicating product recommendations")
    products: list[JewelryProduct] = Field(description="List of recommended jewelry products")


Artifact = JewelryDesignArtifact | ProductRecommendationArtifact
