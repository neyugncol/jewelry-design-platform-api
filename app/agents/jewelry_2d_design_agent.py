
"""Jewelry 2D design agent using Gemini for product image generation."""
from typing import Optional
import base64
import logging
import google.genai as genai
from google.genai import types
from pydantic import BaseModel, Field

from app.config import settings, api_key_pool
from app.agents.concept_design_agent import JewelryDesignOutput

# Configure logger
logger = logging.getLogger(__name__)


class GeneratedImage2D(BaseModel):
    """Schema for a single generated 2D image."""
    view_type: str = Field(description="Type of view: front, side, or top")
    prompt: str = Field(description="Prompt used to generate this image")
    image_data: str = Field(description="Base64 encoded image data")
    mime_type: str = Field(default="image/png", description="MIME type of the generated image")


class JewelryDesign2DOutput(BaseModel):
    """Schema for 2D design output containing all generated images."""
    images: list[GeneratedImage2D] = Field(description="List of generated images from different views")
    design_name: str = Field(description="Name of the jewelry design")
    design_description: str = Field(description="Description of the jewelry design")


class Jewelry2DDesignAgent:
    """Agent for generating 2D product images of jewelry designs using Gemini AI."""

    # Define the views to generate
    VIEWS = [
        {
            "type": "front",
            "name": "Front View",
            "description": "showcasing the primary design elements, face-on perspective, centered composition"
        },
        {
            "type": "side",
            "name": "Side View",
            "description": "displaying the profile and depth, 90-degree angle from the front, showing thickness and dimension"
        },
        {
            "type": "top",
            "name": "Top View",
            "description": "revealing the overhead perspective, bird's eye view, showing the full layout and proportions"
        }
    ]

    def __init__(self, model: str = None):
        """
        Initialize the 2D design agent.

        Args:
            model: Gemini image model to use. Defaults to settings.image_model
        """
        image_model = model or settings.image_model
        logger.info(f"Initializing Jewelry2DDesignAgent with model: {image_model}")
        self.client = genai.Client(api_key=api_key_pool.get_api_key())
        self.model = image_model

    async def run(
        self,
        design: JewelryDesignOutput,
        reference_images: Optional[list[str]] = None,
        style_context: Optional[str] = None
    ) -> JewelryDesign2DOutput:
        """
        Generate 2D product images from different angles for a jewelry design.

        This method generates images sequentially in a conversation to maintain
        consistency across all views. Each image is generated with the context
        of previously generated images to ensure design coherence.

        Args:
            design: The jewelry design specification from the concept agent
            reference_images: Optional list of base64 encoded reference images
            style_context: Optional additional styling instructions

        Returns:
            JewelryDesign2DOutput containing all generated images with metadata
        """
        logger.info(f"Starting 2D image generation for design: {design.name}")
        if reference_images:
            logger.debug(f"Including {len(reference_images)} reference images")
        if style_context:
            logger.debug(f"Style context: {style_context}")

        # Initialize conversation history for this run
        conversation_history = []

        # Initialize results
        generated_images = []

        # Build base design description for prompts
        base_description = self._build_base_description(design, style_context)

        # Generate each view sequentially to maintain consistency
        for view_config in self.VIEWS:
            view_type = view_config["type"]
            logger.info(f"Generating {view_type} view image ({len(generated_images) + 1}/3)")

            # Build prompt for this specific view
            prompt = self._build_view_prompt(
                design=design,
                view_config=view_config,
                base_description=base_description,
                previous_views=[img.view_type for img in generated_images]
            )

            # Generate the image
            logger.debug(f"Calling Gemini API for {view_type} view")
            image_data, conversation_history = await self._generate_image(
                prompt=prompt,
                conversation_history=conversation_history,
                reference_images=reference_images if not generated_images else None
            )

            # Store the generated image
            generated_image = GeneratedImage2D(
                view_type=view_config["type"],
                prompt=prompt,
                image_data=image_data,
                mime_type="image/png"
            )
            generated_images.append(generated_image)
            logger.info(f"Successfully generated {view_type} view")

        logger.info(f"Completed 2D generation: {len(generated_images)} images for {design.name}")
        return JewelryDesign2DOutput(
            images=generated_images,
            design_name=design.name,
            design_description=design.description
        )

    def _build_base_description(
        self,
        design: JewelryDesignOutput,
        style_context: Optional[str] = None
    ) -> str:
        """
        Build the base description of the jewelry for image generation.

        Args:
            design: Jewelry design specification
            style_context: Additional styling context

        Returns:
            Formatted description string
        """
        desc_parts = [f"Jewelry Design: {design.name}"]
        desc_parts.append(f"\n{design.description}")

        # Add properties details
        props = design.properties
        if props.jewelry_type:
            desc_parts.append(f"\nType: {props.jewelry_type.value}")
        if props.metal:
            desc_parts.append(f"Metal: {props.metal.value}")
        if props.gemstone:
            desc_parts.append(f"Gemstone: {props.gemstone.value}")
        if props.style:
            desc_parts.append(f"Style: {props.style.value}")
        if props.color:
            desc_parts.append(f"Color: {props.color}")
        if props.thickness:
            desc_parts.append(f"Thickness: {props.thickness.value}")
        if props.occasion:
            desc_parts.append(f"Occasion: {props.occasion.value}")
        if props.inspiration:
            desc_parts.append(f"Inspiration: {props.inspiration}")

        if style_context:
            desc_parts.append(f"\nAdditional Style: {style_context}")

        return "\n".join(desc_parts)

    def _build_view_prompt(
        self,
        design: JewelryDesignOutput,
        view_config: dict,
        base_description: str,
        previous_views: list[str]
    ) -> str:
        """
        Build a detailed prompt for generating a specific view.

        Args:
            design: Jewelry design specification
            view_config: Configuration for this view (type, name, description)
            base_description: Base description of the jewelry
            previous_views: List of previously generated view types

        Returns:
            Formatted prompt string for image generation
        """
        prompt_parts = []

        # Context about maintaining consistency
        if previous_views:
            prompt_parts.append(
                f"Generate the {view_config['name']} of the jewelry design, "
                f"maintaining perfect consistency with the previously generated "
                f"{', '.join(previous_views)} view(s)."
            )
        else:
            prompt_parts.append(
                f"Generate a high-quality product photograph of the {view_config['name']} "
                f"for this jewelry design."
            )

        # Add base description
        prompt_parts.append(f"\n{base_description}")

        # Add view-specific instructions
        prompt_parts.append(
            f"\nView Requirements:\n"
            f"- Perspective: {view_config['description']}\n"
            f"- Ensure all design elements are clearly visible from this angle\n"
            f"- Show accurate proportions, dimensions, and material details\n"
            f"- Display gemstones, engravings, and decorative elements clearly"
        )

        # Add photography requirements
        prompt_parts.append(
            f"\nPhotography Requirements:\n"
            f"- Professional product photography quality\n"
            f"- Clean white or subtle gradient background\n"
            f"- Optimal lighting to showcase metal luster and gemstone brilliance\n"
            f"- Sharp focus on all jewelry details\n"
            f"- Realistic materials and textures\n"
            f"- Suitable for 3D modeling reference and product showcase"
        )

        # Emphasis on 3D modeling compatibility
        if view_config["type"] in ["side", "top"]:
            prompt_parts.append(
                f"\nImportant: This {view_config['type']} view will be used as reference "
                f"for 3D model generation. Ensure depth, thickness, and structural details "
                f"are accurately represented and clearly visible."
            )

        return "\n".join(prompt_parts)

    async def _generate_image(
        self,
        prompt: str,
        conversation_history: list[dict],
        reference_images: Optional[list[str]] = None
    ) -> tuple[str, list[dict]]:
        """
        Generate a single image using Gemini and maintain conversation context.

        Args:
            prompt: Text prompt for image generation
            conversation_history: Conversation history for this generation sequence
            reference_images: Optional reference images for the first generation

        Returns:
            Tuple of (base64 encoded image data, updated conversation history)
        """
        # Prepare content parts
        content_parts = [{"text": prompt}]

        # Add reference images only for the first view to establish style
        if reference_images and not conversation_history:
            for img_base64 in reference_images[:5]:  # Limit to 5 images
                content_parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": img_base64
                    }
                })

        # Add current message to history
        conversation_history.append({
            "role": "user",
            "parts": content_parts
        })

        # Generate image using Gemini
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=conversation_history,
            config=types.GenerateContentConfig(
                temperature=0.7,  # Balanced creativity and consistency
                response_modalities=["IMAGE", "TEXT"]
            )
        )

        # Extract the generated image (Gemini returns bytes)
        image_bytes = None

        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    # Check if this part contains image data
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Extract bytes from Gemini response
                        image_bytes = part.inline_data.data
                        break

        if not image_bytes:
            logger.error("No image bytes returned from Gemini API")
            raise ValueError(f"Failed to generate image. Response: {response}")

        # Convert bytes to base64 for storage
        image_data_base64 = base64.b64encode(image_bytes).decode('utf-8')
        logger.debug(f"Generated image size: {len(image_bytes)} bytes")

        # Add the assistant's response to conversation history for context
        # Keep bytes in history for next generation
        conversation_history.append({
            "role": "model",
            "parts": [
                {"text": f"Generated image successfully."},
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": image_bytes
                    }
                }
            ]
        })

        return image_data_base64, conversation_history