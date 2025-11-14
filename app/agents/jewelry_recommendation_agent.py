"""Jewelry recommendation agent using Gemini for similarity analysis."""
from typing import Optional
from pathlib import Path
import json
import logging
import google.genai as genai
from google.genai import types
from pydantic import BaseModel, Field

from app.config import settings, api_key_pool
from app.schemas.jewelry import JewelryProduct, JewelryDesign

# Configure logger
logger = logging.getLogger(__name__)


class ProductRecommendation(BaseModel):
    """Schema for a single product recommendation."""
    product_id: str = Field(description="ID of the recommended product")
    similarity_score: float = Field(description="Similarity score from 0.0 to 1.0", ge=0.0, le=1.0)
    reasoning: str = Field(description="Explanation of why this product is similar")


class RecommendationOutput(BaseModel):
    """Schema for recommendation output from AI."""
    recommendations: list[ProductRecommendation] = Field(
        description="List of product recommendations sorted by similarity (top 3-5)",
        max_length=5
    )


class JewelryRecommendationAgent:
    """Agent for recommending similar jewelry products using Gemini AI."""

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        products_dir: str = "data/processed_products"
    ):
        """
        Initialize the recommendation agent.

        Args:
            model: Gemini model to use. Defaults to settings.chat_model
            products_dir: Path to directory containing product JSON files
        """
        logger.info(f"Initializing JewelryRecommendationAgent with model: {model or settings.chat_model}")
        self.client = genai.Client(api_key=api_key_pool.get_api_key())
        self.model = model or settings.chat_model
        self.products_dir = Path(products_dir)
        self.products: list[JewelryProduct] = []

        # Load products on initialization
        self._load_products()

    def _load_products(self) -> None:
        """Load jewelry products from JSON files in directory."""
        logger.info(f"Loading products from: {self.products_dir}")

        if not self.products_dir.exists():
            logger.error(f"Products directory not found: {self.products_dir}")
            raise FileNotFoundError(
                f"Products directory not found: {self.products_dir}. "
                f"Please ensure the directory exists."
            )

        if not self.products_dir.is_dir():
            logger.error(f"Path is not a directory: {self.products_dir}")
            raise ValueError(f"Path is not a directory: {self.products_dir}")

        # Get all JSON files from the directory
        json_files = list(self.products_dir.glob("*.json"))

        if not json_files:
            logger.warning(f"No JSON files found in: {self.products_dir}")
            return

        # Load each product JSON file
        self.products = []
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    product_data = json.load(f)

                # Convert to JewelryProduct object
                product = JewelryProduct(**product_data)
                self.products.append(product)
                logger.debug(f"Loaded product: {product.id} - {product.name}")
            except Exception as e:
                logger.error(f"Error loading product from {json_file}: {e}")
                # Continue loading other products even if one fails
                continue

        logger.info(f"Successfully loaded {len(self.products)} products from catalog")

    def reload_products(self) -> None:
        """Reload products from directory (useful if products are updated)."""
        self._load_products()

    async def recommend(
        self,
        design: JewelryDesign,
        top_k: int = 5,
        min_similarity: float = 0.3
    ) -> list[JewelryProduct]:
        """
        Recommend similar products based on a jewelry design.

        Uses LLM to analyze the design and compare with all available products,
        returning the top-k most similar products.

        Args:
            design: The jewelry design to find similar products for
            top_k: Maximum number of recommendations to return (default: 5)
            min_similarity: Minimum similarity threshold (0.0-1.0, default: 0.3)

        Returns:
            List of JewelryProduct objects sorted by similarity (most similar first).
            Returns empty list if no products meet the minimum similarity threshold.
        """
        logger.info(f"Starting recommendation for design: {design.name}")
        logger.debug(f"Parameters: top_k={top_k}, min_similarity={min_similarity}")
        logger.debug(f"Available products in catalog: {len(self.products)}")

        if not self.products:
            logger.warning("No products available in catalog")
            return []

        # Build the analysis prompt
        prompt = self._build_recommendation_prompt(design, top_k, min_similarity)

        # Get recommendations from Gemini using structured output
        logger.info(f"Calling Gemini API for recommendations (model: {self.model})")
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=[{
                "role": "user",
                "parts": [{"text": prompt}]
            }],
            config=types.GenerateContentConfig(
                temperature=0.3,  # Lower temperature for more focused analysis
                response_mime_type="application/json",
                response_schema=RecommendationOutput,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=1000
                )
            )
        )

        # Parse the structured output
        recommendations_data = json.loads(response.text)
        recommendations = RecommendationOutput(**recommendations_data)

        # Filter by minimum similarity and get product objects
        similar_products = []
        product_dict = {p.id: p for p in self.products}

        for rec in recommendations.recommendations:
            if rec.similarity_score >= min_similarity:
                if rec.product_id in product_dict:
                    product = product_dict[rec.product_id]
                    similar_products.append(product)
                    logger.debug(f"Recommended: {product.name} (similarity: {rec.similarity_score:.2f})")
                else:
                    logger.warning(f"Product ID {rec.product_id} not found in catalog")

        logger.info(f"Returning {len(similar_products)} recommended products")
        return similar_products

    def _build_recommendation_prompt(
        self,
        design: JewelryDesign,
        top_k: int,
        min_similarity: float
    ) -> str:
        """
        Build the prompt for LLM to analyze similarity.

        Args:
            design: The jewelry design
            top_k: Number of recommendations requested
            min_similarity: Minimum similarity threshold

        Returns:
            Formatted prompt string
        """
        # Build design description
        design_desc = self._format_design_for_analysis(design)

        # Build products list
        products_desc = self._format_products_for_analysis()

        prompt = f"""You are an expert jewelry consultant analyzing product similarity.

# TASK
Analyze the provided jewelry design and recommend the top {top_k} most similar products from our catalog.

# INPUT DESIGN
{design_desc}

# AVAILABLE PRODUCTS
{products_desc}

# ANALYSIS REQUIREMENTS
1. Compare the design with EVERY product in the catalog
2. Consider multiple factors for similarity:
   - Target Audience: men, women, unisex, couple, personalized
   - Jewelry Type: ring, bracelet, bangle, necklace, earring, anklet
   - Metal Type: 24k_gold, 22k_gold, 18k_gold, 14k_gold, 10k_gold, silver, platinum
   - Color Tone: white, yellow, rose
   - Gemstones: diamond, sapphire, emerald, amethyst, ruby, citrine, tourmaline, topaz, garnet, peridot, spinel, cubic_zirconia, aquamarine, opal, moonstone, pearl
   - Gemstone Shape: round, oval, marquise, pear, heart, radiant, emerald, cushion, princess
   - Style: classic, modern, vintage, minimalist, luxury, personality, natural
   - Occasion: wedding, engagement, casual, formal, party, daily_wear
   - Weight and size specifications
   - Overall aesthetic and inspiration
   - Price range compatibility

3. Calculate a similarity score (0.0 to 1.0) for each product:
   - 1.0 = Perfect match in most aspects
   - 0.7-0.9 = Very similar, minor differences
   - 0.5-0.6 = Moderately similar, some key differences
   - 0.3-0.4 = Somewhat similar, different in several aspects
   - 0.0-0.2 = Very different, few similarities

4. Only include products with similarity >= {min_similarity}

5. Return the top {top_k} most similar products, sorted by similarity score (highest first)

6. For each recommendation, provide clear reasoning explaining:
   - What makes this product similar
   - Which specific attributes match
   - Any notable differences

# OUTPUT FORMAT
Return a JSON object with recommendations sorted by similarity score (descending).
If no products meet the minimum similarity threshold, return an empty recommendations list.
"""

        return prompt

    def _format_design_for_analysis(self, design: JewelryDesign) -> str:
        """Format design information for LLM analysis."""
        props = design.properties

        lines = [
            f"Name: {design.name}",
            f"Description: {design.description}",
            "\nProperties:"
        ]

        if props.target_audience:
            lines.append(f"  - Target Audience: {props.target_audience}")
        if props.jewelry_type:
            lines.append(f"  - Type: {props.jewelry_type}")
        if props.metal:
            lines.append(f"  - Metal: {props.metal}")
        if props.color:
            lines.append(f"  - Color Tone: {props.color}")
        if props.weight:
            lines.append(f"  - Weight: {props.weight}g")
        if props.gemstone:
            lines.append(f"  - Gemstone: {props.gemstone}")
        if props.shape:
            lines.append(f"  - Gemstone Shape: {props.shape}")
        if props.size:
            lines.append(f"  - Gemstone Size: {props.size} carats")
        if props.style:
            lines.append(f"  - Style: {props.style}")
        if props.occasion:
            lines.append(f"  - Occasion: {props.occasion}")
        if props.inspiration:
            lines.append(f"  - Inspiration: {props.inspiration}")

        return "\n".join(lines)

    def _format_products_for_analysis(self) -> str:
        """Format all products for LLM analysis."""
        product_lines = []

        for idx, product in enumerate(self.products, 1):
            props = product.properties

            # Build compact product description
            product_info = [
                f"\n## Product {idx}: {product.name} (ID: {product.id})",
                f"Description: {product.description}",
                f"Price: {product.price:,.0f} VND",
                "Properties:"
            ]

            if props.target_audience:
                product_info.append(f"  - Target: {props.target_audience}")
            if props.jewelry_type:
                product_info.append(f"  - Type: {props.jewelry_type}")
            if props.metal:
                product_info.append(f"  - Metal: {props.metal}")
            if props.color:
                product_info.append(f"  - Color Tone: {props.color}")
            if props.weight:
                product_info.append(f"  - Weight: {props.weight}g")
            if props.gemstone:
                product_info.append(f"  - Gemstone: {props.gemstone}")
            if props.shape:
                product_info.append(f"  - Shape: {props.shape}")
            if props.size:
                product_info.append(f"  - Size: {props.size} carats")
            if props.style:
                product_info.append(f"  - Style: {props.style}")
            if props.occasion:
                product_info.append(f"  - Occasion: {props.occasion}")

            product_lines.append("\n".join(product_info))

        return "\n".join(product_lines)

    def get_all_products(self) -> list[JewelryProduct]:
        """Get all loaded products."""
        return self.products

    def get_product_by_id(self, product_id: str) -> Optional[JewelryProduct]:
        """Get a specific product by ID."""
        for product in self.products:
            if product.id == product_id:
                return product
        return None
