
"""Jewelry 2D design agent for product image generation using OpenAI Responses API.

Uses OpenAI's Responses API with image_generation tool to create professional
product images from different angles. The API supports multi-turn image editing
for consistency across views.
"""
from typing import Optional
import base64
import logging
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.agents.concept_design_agent import JewelryDesignOutput
from app.utils.file_utils import FileUtils

# Configure logger
logger = logging.getLogger(__name__)


class GeneratedImage2D(BaseModel):
    """Schema for a single generated 2D image."""
    view_type: str = Field(description="Type of view: front, side, or top")
    prompt: str = Field(description="Prompt used to generate this image")
    file_id: str = Field(description="Short file ID for the generated image (e.g., 'a3f9k2m7')")
    mime_type: str = Field(default="image/png", description="MIME type of the generated image")


class JewelryDesign2DOutput(BaseModel):
    """Schema for 2D design output containing all generated images."""
    images: list[GeneratedImage2D] = Field(description="List of generated images from different views")
    design_name: str = Field(description="Name of the jewelry design")
    design_description: str = Field(description="Description of the jewelry design")


class Jewelry2DDesignAgent:
    """Agent for generating 2D product images of jewelry designs using OpenAI Responses API."""

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

    def __init__(self, model: str = "google/gemini-2.5-flash-image"):
        """
        Initialize the 2D design agent.

        Args:
            model: OpenAI model to use for image generation.
                   Supports: gpt-5, gpt-4o, gpt-4.1, o3, etc.
                   Defaults to gpt-5.
        """
        logger.info(f"Initializing Jewelry2DDesignAgent with model: {model}")
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
        design: JewelryDesignOutput,
        user_id: Optional[str] = None,
        reference_image_ids: Optional[list[str]] = None,
        style_context: Optional[str] = None
    ) -> JewelryDesign2DOutput:
        """
        Generate 2D product images from different angles for a jewelry design.

        This method generates images sequentially using the Responses API to maintain
        consistency across all views. Each image is generated with the context
        of previously generated images to ensure design coherence.

        Images are saved to the file service and returned as file IDs.

        Args:
            db: Database session for file service
            design: The jewelry design specification from the concept agent
            user_id: Optional user ID who owns the generated files
            reference_image_ids: Optional list of file IDs for reference images
            style_context: Optional additional styling instructions

        Returns:
            JewelryDesign2DOutput containing all generated images with file IDs
        """
        logger.info(f"Starting 2D image generation for design: {design.name}")

        # Convert reference image IDs to base64 for LLM input
        reference_images_base64 = None
        if reference_image_ids:
            logger.info(f"Loading {len(reference_image_ids)} reference images from file service")
            reference_images_base64 = FileUtils.file_ids_to_data_urls(db, reference_image_ids)
            logger.info(f"Converted {len(reference_images_base64)} reference images to base64")

        if style_context:
            logger.info(f"Style context: {style_context}")

        # Initialize results
        generated_images = []
        previous_response_id = None

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
                previous_views=[img.view_type for img in generated_images],
                is_first_view=len(generated_images) == 0
            )

            # Generate the image using Responses API
            logger.info(f"Calling OpenAI Responses API for {view_type} view")
            image_data_base64, mime_type, response_id = await self._generate_image(
                prompt=prompt,
                reference_images=reference_images_base64 if not generated_images else None,
                previous_response_id=previous_response_id
            )

            # Save the generated image to file service
            logger.info(f"Saving {view_type} view image to file service")
            filename = f"{design.name.replace(' ', '_')}_{view_type}_view.png"
            file_id = FileUtils.save_base64_to_file_service(
                db=db,
                base64_data=image_data_base64,
                filename=filename,
                content_type=mime_type,
                user_id=user_id
            )
            logger.info(f"Saved {view_type} view image with file ID: {file_id}")

            # Store the generated image with file ID
            generated_image = GeneratedImage2D(
                view_type=view_config["type"],
                prompt=prompt,
                file_id=file_id,
                mime_type=mime_type
            )
            generated_images.append(generated_image)
            previous_response_id = response_id
            logger.info(f"Successfully generated and saved {view_type} view")

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

        Includes comprehensive jewelry properties with detailed specifications
        to guide accurate and professional product image generation.

        Args:
            design: Jewelry design specification
            style_context: Additional styling context

        Returns:
            Formatted description string with complete jewelry specifications
        """
        desc_parts = [
            "=" * 60,
            f"JEWELRY DESIGN SPECIFICATION",
            "=" * 60,
            f"\nDesign Name: {design.name}",
            f"\nDescription:\n{design.description}",
            "\n" + "=" * 60,
            "DETAILED SPECIFICATIONS",
            "=" * 60
        ]

        # Add comprehensive properties with descriptions
        props = design.properties

        # Target Audience
        if props.target_audience:
            desc_parts.append(f"\n• Target Audience: {props.target_audience.value}")
            audience_guide = {
                "men": "masculine design elements, typically larger and bolder",
                "women": "elegant and refined design elements, delicate details",
                "unisex": "versatile design suitable for any gender",
                "couple": "matching or complementary design for pairs",
                "personalized": "unique, custom design with personal elements"
            }
            if props.target_audience.value in audience_guide:
                desc_parts.append(f"  → {audience_guide[props.target_audience.value]}")

        # Jewelry Type
        if props.jewelry_type:
            desc_parts.append(f"\n• Jewelry Type: {props.jewelry_type.value}")
            type_guide = {
                "ring": "circular band worn on finger, show band thickness and setting",
                "bracelet": "decorative chain or band for wrist, flexible design",
                "bangle": "rigid circular band for wrist, solid construction",
                "necklace": "decorative chain or pendant for neck, show chain details",
                "earring": "ornament for ear, show attachment mechanism",
                "anklet": "decorative chain for ankle, delicate design"
            }
            if props.jewelry_type.value in type_guide:
                desc_parts.append(f"  → {type_guide[props.jewelry_type.value]}")

        # Metal Type and Color
        if props.metal or props.color:
            metal_desc = []
            if props.metal:
                metal_desc.append(f"{props.metal.value}")
                metal_guide = {
                    "24k_gold": "pure gold, rich yellow color, soft and lustrous",
                    "22k_gold": "high gold content, warm yellow, slight hardness",
                    "18k_gold": "balanced gold alloy, durable, warm tone",
                    "14k_gold": "strong gold alloy, versatile, subtle gold tone",
                    "10k_gold": "durable gold alloy, pale gold color",
                    "silver": "bright white metal, high shine, cool tone",
                    "platinum": "premium white metal, dense, luxurious appearance"
                }
                if props.metal.value in metal_guide:
                    metal_desc.append(f"({metal_guide[props.metal.value]})")

            if props.color:
                color_guide = {
                    "white": "bright, cool, silvery appearance with high reflectivity",
                    "yellow": "warm, traditional gold color with rich luster",
                    "rose": "romantic pink-gold tone with copper undertones"
                }
                metal_desc.append(f"in {props.color} tone")
                if props.color in color_guide:
                    metal_desc.append(f"- {color_guide[props.color]}")

            desc_parts.append(f"\n• Metal: {' '.join(metal_desc)}")

        # Weight
        if props.weight:
            desc_parts.append(f"\n• Metal Weight: {props.weight}g")
            if props.weight < 2:
                desc_parts.append("  → Delicate, lightweight design")
            elif props.weight < 5:
                desc_parts.append("  → Medium weight, balanced presence")
            elif props.weight < 10:
                desc_parts.append("  → Substantial weight, solid construction")
            else:
                desc_parts.append("  → Heavy, bold statement piece")

        # Gemstone Details
        if props.gemstone:
            desc_parts.append(f"\n• Primary Gemstone: {props.gemstone.value}")
            gemstone_guide = {
                "diamond": "brilliant, clear crystal, maximum sparkle and fire",
                "sapphire": "deep blue stone, rich color, excellent clarity",
                "emerald": "vibrant green stone, natural inclusions, soft glow",
                "ruby": "deep red stone, rich color, inner fire",
                "amethyst": "purple stone, ranging from pale to deep violet",
                "citrine": "yellow to orange stone, warm sunny tones",
                "tourmaline": "variety of colors, excellent clarity, vibrant",
                "topaz": "clear to colored stone, high brilliance",
                "garnet": "deep red stone, rich warm tones",
                "peridot": "olive green stone, distinctive color",
                "spinel": "various colors, high brilliance, durable",
                "cubic_zirconia": "diamond simulant, high sparkle, clear",
                "aquamarine": "pale blue stone, sea-like transparency",
                "opal": "play of colors, iridescent, unique patterns",
                "moonstone": "milky appearance, blue sheen, ethereal glow",
                "pearl": "lustrous organic gem, smooth surface, soft glow"
            }
            if props.gemstone.value in gemstone_guide:
                desc_parts.append(f"  → {gemstone_guide[props.gemstone.value]}")

        # Gemstone Shape
        if props.shape:
            desc_parts.append(f"\n• Gemstone Cut/Shape: {props.shape.value}")
            shape_guide = {
                "round": "circular brilliant cut, maximum sparkle, classic",
                "oval": "elongated circular shape, elegant, flattering",
                "marquise": "pointed oval, eye-shaped, unique silhouette",
                "pear": "teardrop shape, elegant, distinctive",
                "heart": "romantic heart shape, symbolic",
                "radiant": "rectangular with cut corners, brilliant facets",
                "emerald": "rectangular step cut, elegant, sophisticated",
                "cushion": "rounded square, soft corners, vintage appeal",
                "princess": "square brilliant cut, modern, sharp angles"
            }
            if props.shape.value in shape_guide:
                desc_parts.append(f"  → {shape_guide[props.shape.value]}")

        # Gemstone Size
        if props.size:
            desc_parts.append(f"\n• Gemstone Size: {props.size} carats")
            if props.size < 0.25:
                desc_parts.append("  → Delicate accent stone, subtle presence")
            elif props.size < 0.5:
                desc_parts.append("  → Small featured stone, refined elegance")
            elif props.size < 1.0:
                desc_parts.append("  → Medium stone, noticeable presence")
            elif props.size < 2.0:
                desc_parts.append("  → Large centerpiece stone, significant impact")
            else:
                desc_parts.append("  → Very large statement stone, dramatic presence")

        # Design Style
        if props.style:
            desc_parts.append(f"\n• Design Style: {props.style.value}")
            style_guide = {
                "classic": "timeless traditional design, enduring appeal, elegant simplicity",
                "modern": "contemporary clean lines, minimalist aesthetic, innovative",
                "vintage": "antique-inspired details, ornate elements, nostalgic charm",
                "minimalist": "simple clean design, minimal embellishment, understated",
                "luxury": "opulent and elaborate, premium materials, extravagant details",
                "personality": "unique expressive design, individual character, artistic",
                "natural": "organic flowing forms, nature-inspired, soft curves"
            }
            if props.style.value in style_guide:
                desc_parts.append(f"  → {style_guide[props.style.value]}")

        # Occasion
        if props.occasion:
            desc_parts.append(f"\n• Intended Occasion: {props.occasion.value}")
            occasion_guide = {
                "wedding": "ceremonial significance, timeless design for lifetime wear",
                "engagement": "symbol of commitment, elegant and meaningful",
                "casual": "versatile everyday wear, comfortable and practical",
                "formal": "sophisticated for special events, refined elegance",
                "party": "eye-catching for celebrations, glamorous and festive",
                "daily_wear": "durable for regular use, comfortable and versatile"
            }
            if props.occasion.value in occasion_guide:
                desc_parts.append(f"  → {occasion_guide[props.occasion.value]}")

        # Inspiration
        if props.inspiration:
            desc_parts.append(f"\n• Design Inspiration:\n  {props.inspiration}")

        # Additional styling context
        if style_context:
            desc_parts.append(f"\n" + "=" * 60)
            desc_parts.append(f"ADDITIONAL STYLING NOTES")
            desc_parts.append("=" * 60)
            desc_parts.append(f"{style_context}")

        desc_parts.append("\n" + "=" * 60)

        return "\n".join(desc_parts)

    def _build_view_prompt(
        self,
        design: JewelryDesignOutput,
        view_config: dict,
        base_description: str,
        previous_views: list[str],
        is_first_view: bool = True
    ) -> str:
        """
        Build a detailed prompt for generating a specific view.

        Creates comprehensive instructions for professional product photography
        generation, including all jewelry specifications and rendering guidelines.

        Args:
            design: Jewelry design specification
            view_config: Configuration for this view (type, name, description)
            base_description: Base description of the jewelry
            previous_views: List of previously generated view types
            is_first_view: Whether this is the first view being generated

        Returns:
            Formatted prompt string for image generation
        """
        prompt_parts = []

        # Context about maintaining consistency
        if previous_views and not is_first_view:
            prompt_parts.append(
                f"EDIT THE PREVIOUS IMAGE to show the {view_config['name']} of the SAME jewelry design.\n"
                f"CRITICAL: Maintain PERFECT consistency with the previously generated "
                f"{', '.join(previous_views)} view(s).\n"
                f"Keep IDENTICAL: design details, materials, colors, gemstones, proportions, and overall style.\n"
                f"Change ONLY: camera angle/perspective to show the {view_config['type']} view.\n"
            )
        else:
            prompt_parts.append(
                f"DRAW a professional product photograph showing the {view_config['name']} "
                f"of this jewelry design.\n"
            )

        # Add base description with all specifications
        prompt_parts.append(base_description)

        # Add comprehensive rendering guidelines
        prompt_parts.append(
            f"\n{'=' * 60}\n"
            f"RENDERING GUIDELINES - {view_config['name'].upper()}\n"
            f"{'=' * 60}\n"
        )

        # View-specific camera and composition requirements
        prompt_parts.append(
            f"\n📷 CAMERA & COMPOSITION:\n"
            f"• Perspective: {view_config['description']}\n"
            f"• Framing: Center the jewelry in the frame with appropriate margins\n"
            f"• Focus: Sharp focus across entire jewelry piece\n"
            f"• Depth of field: Shallow to emphasize the jewelry, blur background\n"
            f"• Composition: Follow rule of thirds for visual appeal\n"
        )

        # Material rendering requirements
        props = design.properties
        prompt_parts.append(f"\n💎 MATERIAL RENDERING:\n")

        # Metal rendering
        if props.metal:
            prompt_parts.append(
                f"• Metal ({props.metal.value}):\n"
                f"  - Show realistic metal luster and reflectivity\n"
                f"  - Render surface smoothness or texture accurately\n"
                f"  - Display appropriate color tone ({props.color if props.color else 'default'})\n"
                f"  - Show natural highlights and shadows on curved surfaces\n"
                f"  - Depict any engravings or surface details clearly\n"
            )

        # Gemstone rendering
        if props.gemstone:
            prompt_parts.append(
                f"• Gemstone ({props.gemstone.value}, {props.shape.value if props.shape else 'unspecified'} cut):\n"
                f"  - Render brilliant light refraction and internal fire\n"
                f"  - Show authentic color and clarity of the {props.gemstone.value}\n"
                f"  - Display facets and cutting patterns clearly\n"
                f"  - Capture sparkle and light dispersion realistically\n"
                f"  - Show proper setting and prong work (if applicable)\n"
            )
            if props.size:
                prompt_parts.append(f"  - Accurate size representation: {props.size} carats\n")

        # Lighting requirements
        prompt_parts.append(
            f"\n💡 LIGHTING SETUP:\n"
            f"• Primary light: Soft, diffused from 45° angle to show form and depth\n"
            f"• Fill light: Gentle illumination to reduce harsh shadows\n"
            f"• Accent light: Highlights on metal surfaces for luster\n"
            f"• Gemstone lighting: Strategic positioning to maximize sparkle and fire\n"
            f"• Shadow: Subtle, natural-looking shadow beneath jewelry for grounding\n"
            f"• Reflections: Controlled reflections showing quality without distractions\n"
        )

        # Background and environment
        prompt_parts.append(
            f"\n🎨 BACKGROUND & ENVIRONMENT:\n"
            f"• Background: Pure white (RGB 255,255,255) or subtle gradient\n"
            f"• Surface: Reflective surface creating subtle mirror effect (optional)\n"
            f"• Context: No distracting elements, jewelry is sole focus\n"
            f"• Cleanliness: Pristine, dust-free, professional studio quality\n"
        )

        # Detail requirements based on jewelry type
        if props.jewelry_type:
            type_details = {
                "ring": [
                    "Show band curvature and thickness clearly",
                    "Display setting style and prong work",
                    "Reveal interior band details if visible from this angle",
                    "Show how ring sits (floating or on surface)"
                ],
                "necklace": [
                    "Show chain links and clasp details",
                    "Display pendant positioning and attachment",
                    "Reveal how chain drapes naturally",
                    "Show closure mechanism clearly"
                ],
                "bracelet": [
                    "Show link connections and flexibility",
                    "Display clasp and closure mechanism",
                    "Reveal how bracelet curves naturally",
                    "Show decorative elements spacing"
                ],
                "bangle": [
                    "Show circular form and rigidity",
                    "Display opening/closure if present",
                    "Reveal interior and exterior surfaces",
                    "Show thickness and weight visually"
                ],
                "earring": [
                    "Show attachment mechanism (post, hook, clip)",
                    "Display how earring hangs or sits",
                    "Reveal front and back if visible",
                    "Show symmetry if part of pair"
                ],
                "anklet": [
                    "Show delicate chain construction",
                    "Display clasp and adjustment mechanism",
                    "Reveal decorative charm details",
                    "Show scale relative to ankle wear"
                ]
            }

            if props.jewelry_type.value in type_details:
                prompt_parts.append(f"\n🔍 {props.jewelry_type.value.upper()}-SPECIFIC DETAILS:\n")
                for detail in type_details[props.jewelry_type.value]:
                    prompt_parts.append(f"• {detail}\n")

        # Quality and technical requirements
        prompt_parts.append(
            f"\n✨ QUALITY STANDARDS:\n"
            f"• Resolution: High-resolution product photography quality\n"
            f"• Clarity: Razor-sharp details, no blur or artifacts\n"
            f"• Color accuracy: True-to-life material colors\n"
            f"• Realism: Photorealistic rendering, not illustration\n"
            f"• Consistency: Matches specifications exactly\n"
            f"• Professional: Magazine-quality product photography\n"
        )

        # View-specific emphasis
        view_emphasis = {
            "front": [
                "This is the PRIMARY marketing view - make it captivating",
                "Emphasize the most attractive design features",
                "Show the jewelry as customers will first see it",
                "Balance all elements for visual harmony"
            ],
            "side": [
                "CRITICAL for 3D modeling - show ALL depth dimensions",
                "Display band/chain thickness accurately",
                "Reveal setting height and stone protrusion",
                "Show how the piece has volume and weight"
            ],
            "top": [
                "ESSENTIAL for 3D modeling - show complete overhead layout",
                "Display exact shape and proportions from above",
                "Reveal symmetry and geometric patterns",
                "Show structural elements and spacing accurately"
            ]
        }

        if view_config["type"] in view_emphasis:
            prompt_parts.append(f"\n⚠️ {view_config['type'].upper()} VIEW CRITICAL REQUIREMENTS:\n")
            for emphasis in view_emphasis[view_config["type"]]:
                prompt_parts.append(f"• {emphasis}\n")

        # Final reminder for consistency
        if not is_first_view:
            prompt_parts.append(
                f"\n🎯 CONSISTENCY CHECK:\n"
                f"• Same exact design as previous views\n"
                f"• Identical materials, colors, and finishes\n"
                f"• Same gemstone size, cut, and setting\n"
                f"• Same metal tone and surface treatment\n"
                f"• Same overall proportions and scale\n"
                f"• Only difference: camera angle\n"
            )

        prompt_parts.append(f"\n{'=' * 60}\n")

        return "\n".join(prompt_parts)

    async def _generate_image(
        self,
        prompt: str,
        reference_images: Optional[list[str]] = None,
        previous_response_id: Optional[str] = None
    ) -> tuple[str, str, str]:
        """
        Generate a single image using OpenAI Responses API.

        The Responses API supports multi-turn image editing by referencing
        previous responses, allowing consistent design across different views.

        Args:
            prompt: Text prompt for image generation
            reference_images: Optional reference images for the first generation
            previous_response_id: Optional ID of previous response for multi-turn editing

        Returns:
            Tuple of (base64 encoded image data, response ID)
        """
        # Build input for Responses API
        input_content = []

        # Add reference images if provided (for first view)
        # if reference_images and not previous_response_id:
        #     logger.info(f"Including {len(reference_images[:3])} reference images")
        #     for img_base64 in reference_images[:3]:  # Limit to 3 images
        #         # Ensure proper data URL format
        #         if not img_base64.startswith("data:"):
        #             img_base64 = f"data:image/jpeg;base64,{img_base64}"
        #
        #         input_content.append({
        #             "type": "input_image",
        #             "image_url": img_base64
        #         })

        # Add text prompt
        input_content.append({
            "type": "input_text",
            "text": prompt
        })

        # Build request parameters
        request_params = {
            "model": self.model,
            "input": [{"role": "user", "content": input_content}],
        }

        # Add previous response for multi-turn editing (for consistency)
        if previous_response_id:
            request_params["previous_response_id"] = previous_response_id
            logger.debug(f"Using previous response for consistency: {previous_response_id}")

        # Generate image using Responses API
        logger.debug(f"Calling Responses API with model: {self.model}")
        response = await self.client.responses.create(**request_params)

        # Extract the generated image from response
        image_data_base64 = None
        response_id = response.id

        if hasattr(response, 'output') and response.output:
            for output in response.output:
                # Look for image_generation_call output
                if output.type == "image_generation_call":
                    # The result field contains the base64 image data
                    if hasattr(output, 'result') and output.result:
                        image_data_base64 = output.result
                        logger.info(f"Successfully extracted generated image (response ID: {response_id})")
                        break

        if not image_data_base64:
            logger.error("No image data returned from Responses API")
            logger.error(f"Response: {response}")
            raise ValueError(f"Failed to generate image. No image_generation_call found in response output.")

        # Extract base64 data and mime type (pattern: data:<mime_type>;base64,<data>)
        header, b64data = image_data_base64.split(",", 1)
        image_data_base64 = b64data  # Keep only base64 data
        mime_type = header.split(";")[0][5:]  # Extract mime type

        # Image is already base64 encoded from the API
        logger.info(f"Generated image data length: {len(image_data_base64)} chars")

        return image_data_base64, mime_type, response_id