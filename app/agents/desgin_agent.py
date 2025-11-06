
from google import genai
from google.genai import types

from config import settings
from schemas.jewelry import JewelryDesign
from schemas.user import User


class JewelryDesignAgent:
    def __init__(
            self,
            model: str = "gemini-2.5-flash"
    ):
        self.model = model
        self.client = genai.Client(api_key=settings.gemini_api_key)

    async def run(
            self,
            description: str,
            images: list[str],
            context: str,
            user: User
    ) -> JewelryDesign:
        pass
