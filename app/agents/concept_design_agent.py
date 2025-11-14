"""Jewelry design agent using Gemini for structured output generation."""
from typing import Optional
import logging
import google.genai as genai
from google.genai import types
from pydantic import BaseModel, Field

from agents.schemas import JewelryPropertiesSchema
from app.config import settings, api_key_pool
from app.schemas.user import User
from app.schemas.jewelry import JewelryProperties

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
    """Agent for generating jewelry designs using Gemini AI."""

    def __init__(self, model: str = "gemini-2.5-flash"):
        """
        Initialize the jewelry design agent.

        Args:
            model: Gemini model to use for generation
        """
        logger.info(f"Initializing JewelryConceptDesignAgent with model: {model}")
        self.client = genai.Client(api_key=api_key_pool.get_api_key())
        self.model = model

    async def run(
        self,
        description: str,
        user: User,
        context: Optional[str] = None,
        reference_images: Optional[list[str]] = None
    ) -> JewelryDesignOutput:
        """
        Generate a jewelry design based on inputs.

        Args:
            description: User's description of desired jewelry
            user: User information (demographics, preferences)
            context: Additional context about the design requirements
            reference_images: List of base64 encoded reference images

        Returns:
            JewelryDesignOutput with complete design specifications
        """
        logger.info("Starting concept design generation")
        logger.debug(f"Description length: {len(description)} chars")
        if user:
            logger.debug(f"User: {user.name}, segment: {user.segment}, age: {user.age}")

        # Build the prompt with all available information
        prompt = self._build_prompt(description, user, context)

        # Prepare content parts
        content_parts = [{"text": prompt}]

        # Add reference images if provided
        if reference_images:
            logger.info(f"Including {len(reference_images[:5])} reference images")
            for img_base64 in reference_images[:5]:  # Limit to 5 images
                content_parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": img_base64
                    }
                })

        # Generate design using structured output
        logger.info(f"Calling Gemini API for concept design (model: {self.model})")
        response = self.client.models.generate_content(
            model=self.model,
            contents=[{
                "role": "user",
                "parts": content_parts
            }],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.8,  # Creative but controlled
                response_mime_type="application/json",
                response_schema=JewelryDesignOutput,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=1000
                )
            )
        )

        # Parse the structured output
        design_data = response.text

        # Convert to JewelryDesignOutput
        import json
        design_dict = json.loads(design_data)
        design = JewelryDesignOutput(**design_dict)

        logger.info(f"Successfully generated concept design: {design.name}")
        logger.debug(f"Design properties: type={design.properties.jewelry_type}, metal={design.properties.metal}, style={design.properties.style}")

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
