"""Jewelry design agent using OpenAI for structured output generation."""
from typing import Optional
import logging
import json
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from agents.schemas import JewelryPropertiesSchema
from app.config import settings
from app.schemas.user import User
from app.utils.file_utils import FileUtils

# Configure logger
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are an expert jewelry designer for PNJ Jewelry Corp, specializing in creating personalized jewelry designs.

Your role is to analyze customer requirements, reference images, context, and user information to create detailed jewelry design specifications.

Consider the following when creating designs:
1. User Demographics: Age, gender, marital status, region, and customer segment
2. Design Context: Occasion, style preferences, inspiration, and budget segment
3. Reference Images: Visual elements, patterns, and styles from provided images
4. Cultural Context: Vietnamese jewelry preferences and regional aesthetics
5. PNJ Brand Values: Quality, elegance, and personalization

Output a comprehensive jewelry design with:
- A creative and meaningful name
- Detailed description including materials, gemstones, and craftsmanship
- Complete properties including:
  * Target audience: men, women, unisex, couple, personalized
  * Jewelry type: ring, bracelet, bangle, necklace, earring, anklet
  * Metal: 24k_gold, 22k_gold, 18k_gold, 14k_gold, 10k_gold, silver, platinum
  * Color tone: white, yellow, rose
  * Weight (in grams)
  * Gemstone: diamond, sapphire, emerald, amethyst, ruby, citrine, tourmaline, topaz, garnet, peridot, spinel, cubic_zirconia, aquamarine, opal, moonstone, pearl
  * Shape: round, oval, marquise, pear, heart, radiant, emerald, cushion, princess
  * Size (in carats)
  * Style: classic, modern, vintage, minimalist, luxury, personality, natural
  * Occasion: wedding, engagement, casual, formal, party, daily_wear
  * Inspiration story

Be specific and detailed in your descriptions to guide the craftsmen and ensure customer satisfaction.
""".strip()


class JewelryDesignOutput(BaseModel):
    """Schema for jewelry design output from AI (without images/3D model)."""
    name: str = Field(description="Name of the jewelry design.")
    description: str = Field(description="Detailed description of the jewelry design.")
    properties: JewelryPropertiesSchema = Field(description="Properties and characteristics of the jewelry design.")


class JewelryConceptDesignAgent:
    """Agent for generating jewelry designs using OpenAI API."""

    def __init__(self, model: str = "google/gemini-2.5-pro"):
        """
        Initialize the jewelry design agent.

        Args:
            model: Model to use for generation (via FAL endpoint)
        """
        logger.info(f"Initializing JewelryConceptDesignAgent with model: {model}")
        self.model = model

        # Initialize OpenAI client with FAL endpoint
        self.client = AsyncOpenAI(
            api_key="",
            base_url="https://fal.run/openrouter/router/openai/v1",
            default_headers={
                "Authorization": f"Key {settings.fal_key}"
            }
        )

    async def run(
        self,
        db: Session,
        description: str,
        user: User,
        context: Optional[str] = None,
        reference_image_ids: Optional[list[str]] = None
    ) -> JewelryDesignOutput:
        """
        Generate a jewelry design based on inputs.

        Args:
            db: Database session for file service
            description: User's description of desired jewelry
            user: User information (demographics, preferences)
            context: Additional context about the design requirements
            reference_image_ids: List of file IDs for reference images

        Returns:
            JewelryDesignOutput with complete design specifications
        """
        logger.info("Starting concept design generation")
        logger.info(f"Description length: {len(description)} chars")
        if user:
            logger.info(f"User: {user.name}, segment: {user.segment}, age: {user.age}")

        # Convert reference image IDs to base64 for LLM input
        reference_images_base64 = None
        if reference_image_ids:
            logger.info(f"Loading {len(reference_image_ids)} reference images from file service")
            reference_images_base64 = FileUtils.file_ids_to_data_urls(db, reference_image_ids)
            logger.info(f"Converted {len(reference_images_base64)} reference images to base64")

        # Build the prompt with all available information
        prompt = self._build_prompt(description, user, context)

        # Note: Reference images support would require vision model
        if reference_images_base64:
            logger.warning(f"Reference images provided but not yet supported with OpenAI client (TODO: implement vision)")

        # Generate design using structured output
        logger.info(f"Calling OpenAI API for concept design (model: {self.model})")

        # Prepare JSON schema for structured output
        response_schema = {
            "type": "json_schema",
            "json_schema": {
                "name": "jewelry_design_output",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the jewelry design."
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of the jewelry design."
                        },
                        "properties": {
                            "type": "object",
                            "description": "Properties and characteristics of the jewelry design.",
                            "properties": {
                                "target_audience": {
                                    "type": ["string", "null"],
                                    "enum": ["men", "women", "unisex", "couple", "personalized", None]
                                },
                                "jewelry_type": {
                                    "type": ["string", "null"],
                                    "enum": ["ring", "bracelet", "bangle", "necklace", "earring", "anklet", None]
                                },
                                "metal": {
                                    "type": ["string", "null"],
                                    "enum": ["24k_gold", "22k_gold", "18k_gold", "14k_gold", "10k_gold", "silver", "platinum", None]
                                },
                                "color": {
                                    "type": ["string", "null"],
                                    "enum": ["white", "yellow", "rose", None]
                                },
                                "weight": {
                                    "type": ["number", "null"]
                                },
                                "gemstone": {
                                    "type": ["string", "null"],
                                    "enum": ["diamond", "sapphire", "emerald", "amethyst", "ruby", "citrine", "tourmaline", "topaz", "garnet", "peridot", "spinel", "cubic_zirconia", "aquamarine", "opal", "moonstone", "pearl", None]
                                },
                                "shape": {
                                    "type": ["string", "null"],
                                    "enum": ["round", "oval", "marquise", "pear", "heart", "radiant", "emerald", "cushion", "princess", None]
                                },
                                "size": {
                                    "type": ["number", "null"]
                                },
                                "style": {
                                    "type": ["string", "null"],
                                    "enum": ["classic", "modern", "vintage", "minimalist", "luxury", "personality", "natural", None]
                                },
                                "occasion": {
                                    "type": ["string", "null"],
                                    "enum": ["wedding", "engagement", "casual", "formal", "party", "daily_wear", None]
                                },
                                "inspiration": {
                                    "type": ["string", "null"]
                                }
                            },
                            "required": ["target_audience", "jewelry_type", "metal", "color", "weight", "gemstone", "shape", "size", "style", "occasion", "inspiration"],
                            "additionalProperties": False
                        }
                    },
                    "required": ["name", "description", "properties"],
                    "additionalProperties": False
                }
            }
        }

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,  # Creative but controlled
            response_format=response_schema
        )

        # Parse the structured output
        design_data = response.choices[0].message.content

        # Convert to JewelryDesignOutput
        design_dict = json.loads(design_data)
        design = JewelryDesignOutput(**design_dict)

        logger.info(f"Successfully generated concept design: {design.name}")
        logger.info(f"Design properties: type={design.properties.jewelry_type}, metal={design.properties.metal}, style={design.properties.style}")

        return design

    def _build_prompt(
        self,
        description: str,
        user: User,
        context: Optional[str] = None
    ) -> str:
        """
        Build a comprehensive prompt for design generation.

        Args:
            description: User's jewelry description
            user: User information
            context: Additional context

        Returns:
            Formatted prompt string
        """
        prompt_parts = ["# Jewelry Design Request\n"]

        # User description
        prompt_parts.append(f"## Customer Description\n{description}\n")

        # User information
        prompt_parts.append("## Customer Profile")
        if user.name:
            prompt_parts.append(f"- Name: {user.name}")
        if user.gender:
            prompt_parts.append(f"- Gender: {user.gender}")
        if user.age:
            prompt_parts.append(f"- Age: {user.age}")
        if user.marital_status:
            prompt_parts.append(f"- Marital Status: {user.marital_status}")
        if user.segment:
            prompt_parts.append(f"- Customer Segment: {user.segment}")
        if user.region:
            prompt_parts.append(f"- Region: {user.region}")
        if user.nationality:
            prompt_parts.append(f"- Nationality: {user.nationality}")
        prompt_parts.append("")

        # Additional context
        if context:
            prompt_parts.append(f"## Additional Context\n{context}\n")

        # Instructions
        prompt_parts.append("""
## Instructions
Based on the customer's description, profile, and any reference images provided, create a detailed jewelry design specification.

Ensure the design:
- Matches the customer's preferences and demographics
- Is appropriate for their customer segment (economic, middle, premium, luxury)
- Considers cultural and regional preferences
- Has a meaningful name that resonates with the inspiration or occasion
- Includes comprehensive technical details for production

Select appropriate values from the available property options:
- Target Audience: men, women, unisex, couple, personalized
- Jewelry Type: ring, bracelet, bangle, necklace, earring, anklet
- Metal: 24k_gold, 22k_gold, 18k_gold, 14k_gold, 10k_gold, silver, platinum
- Color Tone: white, yellow, rose
- Gemstone: diamond, sapphire, emerald, amethyst, ruby, citrine, tourmaline, topaz, garnet, peridot, spinel, cubic_zirconia, aquamarine, opal, moonstone, pearl
- Gemstone Shape: round, oval, marquise, pear, heart, radiant, emerald, cushion, princess
- Style: classic, modern, vintage, minimalist, luxury, personality, natural
- Occasion: wedding, engagement, casual, formal, party, daily_wear

Generate a complete jewelry design with all applicable properties filled out.
""")

        return "\n".join(prompt_parts)
