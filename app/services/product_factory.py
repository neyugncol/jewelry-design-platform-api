"""
Factory for loading product data and initializing recommendation agent.

This module provides utilities to:
1. Load processed product data from JSON files
2. Save product images to ImageService
3. Create and initialize JewelryRecommendationAgent
"""
import json
import base64
import re
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.schemas.jewelry import JewelryProduct
from app.services.image_service import ImageService
from app.agents.jewelry_recommendation_agent import JewelryRecommendationAgent
from app.models.image import Image


class ProductFactory:
    """Factory for loading and managing jewelry products."""

    def __init__(
        self,
        products_dir: str = "data/processed_products",
        system_user_id: str = "system"
    ):
        """
        Initialize the product factory.

        Args:
            products_dir: Directory containing processed product JSON files
            system_user_id: User ID to use for system-created images
        """
        self.products_dir = Path(products_dir)
        self.system_user_id = system_user_id
        self.image_service = ImageService()

    def load_products_from_files(
        self,
        limit: Optional[int] = None
    ) -> list[JewelryProduct]:
        """
        Load products from JSON files without database interaction.

        Args:
            limit: Optional limit on number of products to load

        Returns:
            List of JewelryProduct objects with images as data URLs
        """
        if not self.products_dir.exists():
            raise FileNotFoundError(f"Products directory not found: {self.products_dir}")

        products = []
        json_files = list(self.products_dir.glob("*.json"))

        if limit:
            json_files = json_files[:limit]

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    product_data = json.load(f)

                product = JewelryProduct(**product_data)
                products.append(product)

            except Exception as e:
                print(f"Warning: Could not load {json_file.name}: {e}")
                continue

        return products

    def extract_base64_from_data_url(self, data_url: str) -> Optional[tuple[bytes, str]]:
        """
        Extract base64 data and content type from data URL.

        Args:
            data_url: Data URL (e.g., "data:image/png;base64,iVBORw0...")

        Returns:
            Tuple of (image_bytes, content_type) or None if invalid
        """
        # Match data URL pattern: data:image/png;base64,{data}
        match = re.match(r'data:image/([^;]+);base64,(.+)', data_url)

        if not match:
            return None

        image_format = match.group(1)  # png, jpeg, etc.
        base64_data = match.group(2)

        try:
            image_bytes = base64.b64decode(base64_data)
            content_type = f"image/{image_format}"
            return image_bytes, content_type
        except Exception:
            return None

    def save_product_images_to_db(
        self,
        product: JewelryProduct,
        db: Session,
        overwrite: bool = False
    ) -> list[str]:
        """
        Save product images to database via ImageService.

        Args:
            product: JewelryProduct with images as data URLs
            db: Database session
            overwrite: If True, always create new images. If False, skip if already exist

        Returns:
            List of image IDs saved to database
        """
        image_ids = []

        for idx, image_url in enumerate(product.images):
            # Extract base64 data from data URL
            result = self.extract_base64_from_data_url(image_url)

            if not result:
                print(f"  Warning: Could not parse image {idx + 1} for product {product.id}")
                continue

            image_bytes, content_type = result

            # Generate filename
            filename = f"{product.id}_image_{idx + 1}.png"

            # Check if image already exists (by filename and user)
            if not overwrite:
                existing_image = db.query(Image).filter(
                    Image.filename == filename,
                    Image.user_id == self.system_user_id
                ).first()

                if existing_image:
                    image_ids.append(existing_image.id)
                    continue

            # Save new image
            try:
                image = self.image_service.save_image(
                    file_content=image_bytes,
                    filename=filename,
                    content_type=content_type,
                    user_id=self.system_user_id,
                    db=db
                )
                image_ids.append(image.id)

            except Exception as e:
                print(f"  Error saving image {idx + 1} for product {product.id}: {e}")
                continue

        return image_ids

    def load_products_with_db_images(
        self,
        db: Session,
        limit: Optional[int] = None,
        overwrite_images: bool = False
    ) -> list[JewelryProduct]:
        """
        Load products from files and save images to database.

        This replaces data URL images with database image IDs.

        Args:
            db: Database session
            limit: Optional limit on number of products to load
            overwrite_images: If True, recreate all images. If False, reuse existing

        Returns:
            List of JewelryProduct objects with database image IDs
        """
        products = self.load_products_from_files(limit=limit)

        print(f"\n📦 Loading {len(products)} products into database...")

        for product in products:
            print(f"  Processing: {product.name}")

            # Save images to database
            image_ids = self.save_product_images_to_db(
                product=product,
                db=db,
                overwrite=overwrite_images
            )

            # Update product with database image IDs
            product.images = image_ids

            print(f"    ✓ {len(image_ids)} images saved")

        print(f"\n✅ Loaded {len(products)} products with images\n")

        return products

    def create_recommendation_agent(
        self,
        products: list[JewelryProduct],
        model: Optional[str] = None
    ) -> JewelryRecommendationAgent:
        """
        Create a recommendation agent with in-memory products.

        Args:
            products: List of JewelryProduct objects
            model: Optional Gemini model to use

        Returns:
            Configured JewelryRecommendationAgent
        """
        # Create agent without file loading
        agent = JewelryRecommendationAgent.__new__(JewelryRecommendationAgent)

        # Initialize agent attributes
        from app.config import settings
        import google.genai as genai

        agent.client = genai.Client(api_key=settings.gemini_api_key)
        agent.model = model or settings.chat_model
        agent.products_file = None  # Not using file
        agent.products = products

        return agent


def load_and_initialize_recommendation_agent(
    db: Session,
    products_dir: str = "data/processed_products",
    limit: Optional[int] = None,
    overwrite_images: bool = False,
    model: Optional[str] = None
) -> tuple[JewelryRecommendationAgent, list[JewelryProduct]]:
    """
    Convenience function to load products and create recommendation agent.

    This is the main entry point for initializing the recommendation system
    with database-backed images.

    Args:
        db: Database session
        products_dir: Directory containing processed product JSON files
        limit: Optional limit on number of products to load
        overwrite_images: If True, recreate all images
        model: Optional Gemini model to use

    Returns:
        Tuple of (JewelryRecommendationAgent, list of JewelryProduct objects)

    Example:
        >>> from app.db.database import SessionLocal
        >>> from app.services.product_factory import load_and_initialize_recommendation_agent
        >>>
        >>> db = SessionLocal()
        >>> try:
        >>>     agent, products = load_and_initialize_recommendation_agent(db)
        >>>     recommendations = await agent.recommend(my_design)
        >>> finally:
        >>>     db.close()
    """
    factory = ProductFactory(products_dir=products_dir)

    # Load products and save images to database
    products = factory.load_products_with_db_images(
        db=db,
        limit=limit,
        overwrite_images=overwrite_images
    )

    # Create recommendation agent
    agent = factory.create_recommendation_agent(
        products=products,
        model=model
    )

    return agent, products


def load_products_simple(
    products_dir: str = "data/processed_products",
    limit: Optional[int] = None
) -> list[JewelryProduct]:
    """
    Simple function to load products from files without database.

    This keeps images as data URLs and doesn't interact with the database.
    Useful for testing or simple use cases.

    Args:
        products_dir: Directory containing processed product JSON files
        limit: Optional limit on number of products to load

    Returns:
        List of JewelryProduct objects with images as data URLs

    Example:
        >>> from app.services.product_factory import load_products_simple
        >>> products = load_products_simple(limit=10)
        >>> print(f"Loaded {len(products)} products")
    """
    factory = ProductFactory(products_dir=products_dir)
    return factory.load_products_from_files(limit=limit)


def create_agent_from_json(
    products_json_path: str,
    model: Optional[str] = None
) -> JewelryRecommendationAgent:
    """
    Create recommendation agent directly from a JSON file.

    Useful when all products are in a single file (like mock_products.json).

    Args:
        products_json_path: Path to JSON file containing array of products
        model: Optional Gemini model to use

    Returns:
        JewelryRecommendationAgent

    Example:
        >>> agent = create_agent_from_json("data/mock_products.json")
        >>> recommendations = await agent.recommend(design)
    """
    with open(products_json_path, 'r', encoding='utf-8') as f:
        products_data = json.load(f)

    products = [JewelryProduct(**p) for p in products_data]

    factory = ProductFactory()
    return factory.create_recommendation_agent(products=products, model=model)
