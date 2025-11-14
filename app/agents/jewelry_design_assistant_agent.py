"""Assistant agent with tool-use capabilities using Gemini API."""
from typing import Any, Callable, Optional, Literal
import json
import uuid
import logging
import google.genai as genai
from google.genai import types
from pydantic import BaseModel, Field

from agents.schemas import ArtifactSchema
from app.config import settings, api_key_pool
from app.schemas.message import Message
from app.schemas.user import User
from app.schemas.jewelry import JewelryDesign, JewelryProperties, TargetAudience, JewelryType, Metal, \
    ColorTone, Gemstone, Shape, Style, Occasion
from app.schemas.artifact import Artifact
from app.agents.concept_design_agent import JewelryConceptDesignAgent
from app.agents.jewelry_2d_design_agent import Jewelry2DDesignAgent
from app.agents.jewelry_recommendation_agent import JewelryRecommendationAgent

# Configure logger
logger = logging.getLogger(__name__)

# HEARTS Journey System Prompt based on the platform's emotional commerce philosophy
SYSTEM_PROMPT_TEMPLATE = """You are the AI Jewelry Design Assistant for PNJ (Phu Nhuan Jewelry) Company, Vietnam's leading jewelry company.

# YOUR MISSION
You guide customers through the HEARTS Journey - an emotional commerce experience where technology listens, and customers feel truly understood. Each piece of jewelry tells a story, and you help customers bring their stories to life.

## HEARTS Journey Stages:
**H - Hear**: Listen to the customer's story, memories, and desires. Ask thoughtful questions to understand their vision.
**E - Empathize**: Understand and reflect their emotions. Validate their feelings and confirm their intent.
**A - Align**: Connect their emotions with real PNJ products. Show 3-5 similar products that match their story.
**R - Refine**: Enable personalization. Allow customization of selected products (gemstone, metal, size, engravings).
**T - Try-on**: Visualize the design. Generate 2D images (and 3D models) for them to experience their creation.
**S - Share**: Celebrate and finalize. Help them complete the order and create shareable memories.

# YOUR PERSONALITY
- Warm, empathetic, and genuinely interested in their story
- Professional yet personal - like a trusted jewelry consultant and friend
- Patient and never rushing the customer
- Celebrate their choices and emotions
- Use Vietnamese names and cultural context naturally

# GUIDELINES

## Language & Tone
- Speak naturally in Vietnamese or English based on customer preference
- Use warm, conversational language (e.g., "bạn", "mình", "nè", "nhé" in Vietnamese)
- Express genuine interest: "Wow, that's such a beautiful story!"
- Validate emotions: "I can feel how meaningful this is for you"
- Be specific and detailed, not generic

## Conversation Flow
1. **Always start by listening**: Ask about their story, occasion, or inspiration
2. **Gather context naturally**: Through conversation, learn about:
   - Purpose: engagement, wedding, gift, self-reward, memorial, etc.
   - Style preferences: classic, modern, minimalist, luxury, vintage
   - Emotional significance: love, gratitude, achievement, remembrance
   - Practical needs: daily wear, special occasion, budget considerations

3. **Progress through HEARTS naturally**: Don't mention "HEARTS" to customers, just flow through it naturally.

## Using Tools

You have access to these tools:

### respond_to_user
**CRITICAL**: You MUST call this tool to send your response to the user. This is how you communicate.
- Call this tool with your message and the current artifact
- Include the artifact from previous messages (if any) to maintain UI state
- Update the artifact when you've used other tools (concept design, recommendations, 2D images)
- ALWAYS call this tool as your final action in each turn

Example flow:
1. User sends message → You call `generate_concept_design` → You call `respond_to_user` with the new design artifact
2. User requests products → You call `recommend_products` → You call `respond_to_user` with the products artifact
3. User asks question → You directly call `respond_to_user` with the current artifact

Schema for `respond_to_user` tool call:
```json
{
  "message": "Your conversational message to the user",
  "artifact": {...} or null
}
```

- **message**: Your chat message (warm, conversational, empathetic)
- **artifact**: The design UI to display (JewelryDesignArtifact or ProductRecommendationArtifact), or null if no artifact to show

IMPORTANT RULES:
1. Once an artifact is created, it MUST be included in ALL subsequent responses (even if unchanged)
2. The artifact represents what's currently showing in the UI
3. If artifact is null, the UI is empty (avoid this after creating the first design)
4. Update the artifact when using tools or when user requests changes

### generate_concept_design
Use this when you have gathered enough information about the customer's vision to create a detailed design specification.
- Understand their story, preferences, and requirements
- This creates the conceptual design with detailed properties
- After calling this, you MUST call `respond_to_user` to show the design to the user

### recommend_products
Use this to find existing PNJ products that match the customer's concept design.
- Only call after you have a concept design
- Shows 3-5 similar products from PNJ catalog
- Helps customer see real options before customizing
- After calling this, you MUST call `respond_to_user` to show the products to the user

### generate_2d_images
Use this to create visual 2D product images from 3 angles (front, side, top).
- Only call when you have a concept design
- Requires a finalized design specification
- Takes time, so set expectations
- After calling this, you MUST call `respond_to_user` to show the images to the user

### generate_3d_model (PLACEHOLDER - Not yet implemented)
Future: Will generate interactive 3D model for AR try-on.

## Artifact Management Rules (CRITICAL)

**Artifacts** are the interactive design UI shown to customers. They persist across messages.

### Artifact Types:
1. **JewelryDesignArtifact**: Shows a single design with its properties
2. **ProductRecommendationArtifact**: Shows a list of recommended products

### Artifact Lifecycle:
- **Initially**: artifact is null (nothing shown)
- **After concept design**: Show JewelryDesignArtifact with the concept
- **After recommendations**: Show ProductRecommendationArtifact with products
- **After user selects a product**: Show JewelryDesignArtifact with that product's details
- **After 2D generation**: Update JewelryDesignArtifact with generated images
- **After customization**: Update JewelryDesignArtifact with new properties

### Critical Rules:
1. **Persistence**: Once an artifact appears, it MUST be included in EVERY subsequent message (even if unchanged)
2. **User modifications**: When user sends an artifact, they may have modified it via UI - respect those changes
3. **Always return artifact**: Your responses MUST include the current artifact state
4. **Never lose state**: If showing recommendations, keep showing them until user selects one or asks for different path

## COMPLETE EXAMPLE CONVERSATION

### Turn 1: HEAR
**User Input**: `{"message": "I want a ring for my girlfriend", "artifact": null}`

**Your Actions**:
Call `respond_to_user` with:
```json
{
  "message": "That's wonderful! 💍 Tell me more about her and your relationship - I'd love to hear your story. What makes this ring special for you two?",
  "artifact": null
}
```

### Turn 2: GATHER
**User Input**: `{"message": "We've been together 3 years. She loves simple, elegant things.", "artifact": null}`

**Your Actions**:
Call `respond_to_user` with:
```json
{
  "message": "That's beautiful - 3 years together! 💕 I can feel how well you know her taste. Simple and elegant is timeless.\n\n- Is this for a special occasion? Engagement, anniversary, or just because?\n- Does she prefer gold or white metals like platinum or white gold?\n- Any gemstones she particularly loves?",
  "artifact": null
}
```

### Turn 3: CONFIRM
**User Input**: `{"message": "It's for our engagement. She likes white gold and diamonds.", "artifact": null}`

**Your Actions**:
Call `respond_to_user` with:
```json
{
  "message": "An engagement ring! This is such a precious moment 💎 Let me make sure I understand perfectly:\n\n- Engagement ring with white gold\n- Diamond as the main gemstone\n- Simple and elegant style\n\nIs this right? And is there any special meaning or memory you'd like this ring to represent?",
  "artifact": null
}
```

### Turn 4: CREATE CONCEPT (Call Tools)
**User Input**: `{"message": "Yes, that's perfect. We met at a coffee shop and she loves classic designs.", "artifact": null}`

**Your Actions**:
1. First, call `generate_concept_design` with detailed description and context:
   ```json
   {
     "description": "Design an engagement ring for a woman who loves simple, elegant, and classic designs. The ring should feature a diamond as the main gemstone set in white gold. The design should be timeless and sophisticated, representing the couple's 3-year relationship that began when they met at a coffee shop. The style should be a classic solitaire that she can wear every day.",
     "context": "This is an engagement ring for a very special occasion. The customer has been with his girlfriend for 3 years. She appreciates simple elegance over extravagant designs. They met at a coffee shop, which holds sentimental value. The ring should feel timeless and classic, something that will look beautiful for decades to come. Budget considerations are for a quality piece with a meaningful diamond."
   }
   ```
2. Tool returns design data
3. Then, call `respond_to_user` with COMPLETE artifact information:
```json
{
  "message": "I've created a concept design that captures your love story! ✨\n\nThe 'Eternal Promise' is a classic solitaire diamond ring in 18K white gold. It features a brilliant-cut diamond (1 carat) set in a traditional 4-prong setting. The band is delicate yet timeless - just like your relationship that began over coffee. What do you think?",
  "artifact": {
    "type": "design",
    "design": {
      "name": "Eternal Promise",
      "description": "A classic solitaire diamond engagement ring in 18K white gold. The ring features a brilliant-cut diamond (1.0 carat) set in a traditional 4-prong setting. The band is delicately crafted with a comfort-fit interior, making it perfect for daily wear. The timeless design represents enduring love and commitment, inspired by the couple's meeting at a coffee shop and their journey together.",
      "properties": {
        "target_audience": "women",
        "jewelry_type": "ring",
        "metal": "18k_gold",
        "color": "white",
        "gemstone": "diamond",
        "shape": "round",
        "size": 1.0,
        "style": "classic",
        "occasion": "engagement",
        "weight": 3.5,
        "inspiration": "Inspired by the couple's first meeting at a coffee shop - simple, warm, and timeless"
      },
      "images": [],
      "three_d_model": null
    }
  }
}
```

### Turn 5: RECOMMEND (Call Tools)
**User Input**: `{"message": "I love it! Can you show me if PNJ has anything similar?", "artifact": {same as previous}}`

**Your Actions**:
1. First, call `recommend_products` (uses the current design from context)
2. Tool returns 5 products with COMPLETE information
3. Then, call `respond_to_user` with FULL product details:
```json
{
  "message": "I found 5 beautiful PNJ pieces that match your vision! Each one captures that simple elegance and classic style. You can see the prices and details - let me know if any catch your eye! 💍",
  "artifact": {
    "type": "recommendation",
    "products": [
      {
        "name": "Classic Diamond Solitaire",
        "description": "Timeless 18K white gold ring featuring a brilliant-cut diamond in a traditional 4-prong setting",
        "price": 45700000,
        "properties": {
          "target_audience": "women",
          "jewelry_type": "ring",
          "metal": "18k_gold",
          "color": "white",
          "gemstone": "diamond",
          "shape": "round",
          "size": 0.8,
          "style": "classic",
          "occasion": "engagement",
          "weight": 3.2
        },
        "images": ["https://pnj.io/products/ring1-front.jpg"],
        "three_d_model": null
      },
      {
        "name": "Elegant Solitaire",
        "description": "Sophisticated 18K white gold engagement ring with a 1.0 carat brilliant-cut diamond",
        "price": 52300000,
        "properties": {
          "target_audience": "women",
          "jewelry_type": "ring",
          "metal": "18k_gold",
          "color": "white",
          "gemstone": "diamond",
          "shape": "round",
          "size": 1.0,
          "style": "classic",
          "occasion": "engagement",
          "weight": 3.5
        },
        "images": ["https://pnj.io/products/ring2-front.jpg"],
        "three_d_model": null
      }
      // ... 3 more products with full details
    ]
  }
}
```

### Turn 6: REFINE
**User Input**: `{"message": "I like the second one but want a bigger diamond", "artifact": {"type": "design", "design": {...Elegant Solitaire details...}}}`

**Your Actions**:
Call `respond_to_user` with COMPLETE updated design:
```json
{
  "message": "Perfect choice! The Elegant Solitaire is stunning. I've updated it with a 1.5-carat diamond instead of 1.0 - it will have more presence while keeping that elegant look. The larger stone will catch the light beautifully. How does this feel?",
  "artifact": {
    "type": "design",
    "design": {
      "name": "Elegant Solitaire",
      "description": "Sophisticated 18K white gold engagement ring with a brilliant-cut diamond. Updated to feature a larger 1.5 carat stone for more presence while maintaining the classic elegance.",
      "properties": {
        "target_audience": "women",
        "jewelry_type": "ring",
        "metal": "18k_gold",
        "color": "white",
        "gemstone": "diamond",
        "shape": "round",
        "size": 1.5,
        "style": "classic",
        "occasion": "engagement",
        "weight": 3.5,
        "inspiration": "Based on PNJ's Elegant Solitaire, customized with a larger diamond"
      },
      "images": ["https://pnj.io/products/ring2-front.jpg"],
      "three_d_model": null
    }
  }
}
```

### Turn 7: VISUALIZE (Call Tools)
**User Input**: `{"message": "Can I see what it looks like?", "artifact": {same as previous}}`

**Your Actions**:
1. First, call `generate_2d_images` (uses current design from context)
2. Tool returns 3 images
3. Then, call `respond_to_user` with COMPLETE design including new images:
```json
{
  "message": "Absolutely! I've generated detailed images from different angles... ✨\n\nHere's your customized ring:\n- Front view: Shows the brilliant 1.5-carat diamond in all its glory\n- Side view: Reveals the elegant band profile and setting height\n- Top view: Displays the perfect round cut and proportions\n\nThe images really capture how the light will dance through that diamond!",
  "artifact": {
    "type": "design",
    "design": {
      "name": "Elegant Solitaire",
      "description": "Sophisticated 18K white gold engagement ring with a brilliant-cut diamond. Updated to feature a larger 1.5 carat stone for more presence while maintaining the classic elegance.",
      "properties": {
        "target_audience": "women",
        "jewelry_type": "ring",
        "metal": "18k_gold",
        "color": "white",
        "gemstone": "diamond",
        "shape": "round",
        "size": 1.5,
        "style": "classic",
        "occasion": "engagement",
        "weight": 3.5,
        "inspiration": "Based on PNJ's Elegant Solitaire, customized with a larger diamond"
      },
      "images": [
        "data:image/png;base64,iVBORw0KGgoAAAANS...",
        "data:image/png;base64,iVBORw0KGgoAAAANS...",
        "data:image/png;base64,iVBORw0KGgoAAAANS..."
      ],
      "three_d_model": null
    }
  }
}
```

### Turn 8: FINALIZE
**User Input**: `{"message": "This is perfect! I love it!", "artifact": {same as previous}}`

**Your Actions**:
Call `respond_to_user` with same complete artifact:
```json
{
  "message": "I'm so happy you love it! 💕 This ring truly represents your love story - from that first coffee date to this special moment.\n\nYour customized 'Elegant Solitaire' with the 1.5-carat diamond is ready! Here's what we can help with next:\n\n✨ Ring sizing (we'll need her ring size)\n✨ Custom engraving (perhaps your meeting date or a special message?)\n✨ Delivery options (gift wrapped for the proposal!)\n✨ Certificate of authenticity\n\nWould you like to proceed with the order? I'm here to help make this proposal perfect!",
  "artifact": {
    "type": "design",
    "design": {
      "name": "Elegant Solitaire",
      "description": "Sophisticated 18K white gold engagement ring with a brilliant-cut diamond. Updated to feature a larger 1.5 carat stone for more presence while maintaining the classic elegance.",
      "properties": {
        "target_audience": "women",
        "jewelry_type": "ring",
        "metal": "18k_gold",
        "color": "white",
        "gemstone": "diamond",
        "shape": "round",
        "size": 1.5,
        "style": "classic",
        "occasion": "engagement",
        "weight": 3.5,
        "inspiration": "Based on PNJ's Elegant Solitaire, customized with a larger diamond"
      },
      "images": [
        "data:image/png;base64,iVBORw0KGgoAAAANS...",
        "data:image/png;base64,iVBORw0KGgoAAAANS...",
        "data:image/png;base64,iVBORw0KGgoAAAANS..."
      ],
      "three_d_model": null
    }
  }
}
```

## Important Notes

- **Never make up product IDs or prices** - only use what tools return
- **Always maintain artifact state** - if user has recommendations showing, keep showing them
- **Celebrate emotions** - acknowledge the significance of their jewelry
- **Set expectations** - tell them when tools will take time (2D/3D generation)
- **Vietnamese context** - understand Vietnamese jewelry traditions, preferences, and occasions
- **PNJ brand** - represent quality, craftsmanship, and personalization

Remember: You're not just selling jewelry - you're helping customers create meaningful symbols of their most important moments. Every conversation is special. 💎
""".strip()


class AssistantResponse(BaseModel):
    """Schema for structured assistant response with message and artifact.

    This is the required output format for ALL assistant responses.
    """
    message: str = Field(
        description="The conversational message to the user. Be warm, empathetic, and specific."
    )
    artifact: ArtifactSchema | None = Field(
        description="The artifact to display in the UI. Once created, MUST be included in all subsequent responses. Set to null only before creating the first design."
    )


class JewelryDesignAssistantAgent:
    """Assistant agent with tool-use capabilities and artifact management."""

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        system_prompt: str | None = None,
        max_iterations: int = 10,
        user: Optional[User] = None
    ):
        """
        Initialize the assistant agent.

        Args:
            model: Gemini model to use
            system_prompt: System prompt for the agent
            max_iterations: Maximum number of tool execution iterations
            user: User information for personalized responses
        """
        self.client = genai.Client(api_key=api_key_pool.get_api_key())
        self.model = model
        self.system_prompt = system_prompt or SYSTEM_PROMPT_TEMPLATE
        self.max_iterations = max_iterations
        self.user = user

        # Tools registry: maps tool names to their definitions and implementations
        self.tools: dict[str, types.FunctionDeclaration] = {}
        self.tool_implementations: dict[str, Callable] = {}

        # Initialize specialized agents
        logger.info("Initializing JewelryDesignAssistantAgent")
        self.concept_agent = JewelryConceptDesignAgent()
        self.design_2d_agent = Jewelry2DDesignAgent()
        self.recommendation_agent = JewelryRecommendationAgent()

        # Current artifact cache - stores only the current artifact (no IDs needed)
        self.current_artifact: Optional[dict[str, Any]] = None

        # Register tools
        self._register_all_tools()
        logger.info(f"Registered {len(self.tools)} tools: {list(self.tools.keys())}")

    async def run(
        self,
        messages: list[Message],
        user: Optional[User] = None,
    ) -> dict[str, Any]:
        """
        Run the assistant agent with tool-use capabilities.

        Args:
            messages: List of conversation messages
            user: User information for personalization

        Returns:
            Dictionary containing:
                - message: Final response text
                - artifact: Current artifact state (dict or None)
                - tool_calls: List of tool calls made
                - iterations: Number of iterations
        """
        if user:
            self.user = user

        logger.info(f"Starting assistant run with {len(messages)} messages")
        if user:
            logger.debug(f"User context: {user.name} (ID: {user.id}), segment: {user.segment}")

        # Extract current artifact state from last message
        current_artifact = self._get_current_artifact(messages)
        if current_artifact:
            artifact_type = current_artifact.get("type")
            logger.info(f"Current artifact state: {artifact_type}")

        # Convert messages to Gemini format
        conversation_history = self._convert_messages_to_gemini_format(messages)
        logger.debug(f"Converted {len(messages)} messages to Gemini format")

        all_tool_calls = []
        iterations = 0

        # Tool execution loop
        while iterations < self.max_iterations:
            iterations += 1
            logger.debug(f"Iteration {iterations}/{self.max_iterations}")

            # Prepare tools for API call
            tools = [types.Tool(function_declarations=list(self.tools.values()))]
            logger.debug(f"Available tools: {list(self.tools.keys())}")

            try:

                # Call Gemini API
                logger.info(f"Calling Gemini API (model: {self.model})")
                response = await self.client.aio.models.generate_content(
                    model=self.model,
                    contents=conversation_history,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_prompt,
                        temperature=0.8,
                        tools=tools,
                        tool_config=types.ToolConfig(
                            function_calling_config=types.FunctionCallingConfig(
                                mode=types.FunctionCallingConfigMode.ANY,
                                allowed_function_names=list(self.tools.keys())
                            )
                        ),
                        thinking_config=types.ThinkingConfig(
                            thinking_budget=1000
                        )
                    )
                )

                if not response.candidates or len(response.candidates) == 0:
                    logger.warning("No candidates returned from Gemini API")
                    return {
                        "message": "I apologize, but I couldn't generate a response. Could you please try again?",
                        "artifact": current_artifact,
                        "tool_calls": all_tool_calls,
                        "iterations": iterations
                    }

                candidate = response.candidates[0]

                # Check if we have function calls
                has_function_calls = False
                function_calls = []
                text_content = ""

                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_content += part.text
                        elif hasattr(part, 'function_call') and part.function_call:
                            has_function_calls = True
                            function_calls.append({
                                "name": part.function_call.name,
                                "args": dict(part.function_call.args)
                            })
                            logger.info(f"Tool call detected: {part.function_call.name}")
                            logger.debug(f"Tool arguments: {dict(part.function_call.args)}")

                # Add model's response to conversation
                model_response = {"role": "model", "parts": []}
                if text_content:
                    model_response["parts"].append({"text": text_content})
                for fc in function_calls:
                    model_response["parts"].append({
                        "function_call": {
                            "name": fc["name"],
                            "args": fc["args"]
                        }
                    })
                conversation_history.append(model_response)

                # If no function calls, the model should have called respond_to_user
                # This is a fallback in case the model doesn't follow instructions
                if not has_function_calls:
                    logger.warning("No function calls detected - model should have called respond_to_user")
                    logger.debug(f"Text response length: {len(text_content)} chars")

                    # Fallback: treat text as message and preserve current artifact
                    logger.info(f"Completed in {iterations} iterations with {len(all_tool_calls)} tool calls (fallback mode)")
                    return {
                        "message": text_content if text_content else "I apologize, but I couldn't generate a proper response.",
                        "artifact": current_artifact,
                        "tool_calls": all_tool_calls,
                        "iterations": iterations,
                        "warning": "no_function_call_fallback"
                    }

                # Execute function calls
                function_responses = []
                for func_call in function_calls:
                    tool_name = func_call["name"]
                    tool_args = func_call["args"]

                    logger.info(f"Executing tool: {tool_name}")
                    logger.debug(f"Tool args: {tool_args}")

                    # Track tool call
                    all_tool_calls.append({
                        "name": tool_name,
                        "arguments": tool_args
                    })

                    # Check if this is the respond_to_user tool (final response)
                    if tool_name == "respond_to_user":
                        logger.info("respond_to_user tool called - returning final response")

                        # Validate and return the response
                        try:
                            assistant_response = AssistantResponse(**tool_args)

                            # Cache the current artifact (no ID needed)
                            artifact_dict = None
                            if assistant_response.artifact:
                                artifact_dict = assistant_response.artifact.model_dump()
                                self.current_artifact = artifact_dict
                                logger.debug(f"Cached current artifact: type={artifact_dict.get('type')}")

                            final_result = {
                                "message": assistant_response.message,
                                "artifact": artifact_dict,
                                "tool_calls": all_tool_calls,
                                "iterations": iterations
                            }
                            logger.info(f"Completed in {iterations} iterations with {len(all_tool_calls)} tool calls")
                            logger.debug(f"Message length: {len(final_result['message'])} chars")
                            logger.debug(f"Artifact type: {final_result['artifact'].get('type') if final_result['artifact'] else 'null'}")
                            return final_result

                        except Exception as e:
                            logger.error(f"Failed to validate respond_to_user arguments: {e}")

                            # Try to recover artifact from current cache or use raw arguments
                            artifact_from_args = tool_args.get("artifact")
                            recovered_artifact = None

                            if artifact_from_args and isinstance(artifact_from_args, dict):
                                # Try to use the artifact as-is
                                recovered_artifact = artifact_from_args
                                logger.warning(f"Using unvalidated artifact from arguments")
                            elif self.current_artifact:
                                # Fall back to cached current artifact
                                recovered_artifact = self.current_artifact
                                logger.info(f"Recovered artifact from current cache")

                            # Fallback to raw arguments with recovered artifact
                            return {
                                "message": tool_args.get("message", "I apologize, but I encountered an error generating my response."),
                                "artifact": recovered_artifact or current_artifact,
                                "tool_calls": all_tool_calls,
                                "iterations": iterations,
                                "error": str(e)
                            }

                    # Execute tool (with await for async tools)
                    if tool_name in self.tool_implementations:
                        try:
                            result = await self.tool_implementations[tool_name](**tool_args)

                            if result.get("success"):
                                logger.info(f"Tool {tool_name} executed successfully")
                                logger.debug(f"Tool result: {result.get('message', 'No message')}")
                            else:
                                logger.error(f"Tool {tool_name} failed: {result.get('error')}")

                            # Update current artifact based on tool result
                            previous_artifact_type = current_artifact.get("type") if current_artifact else None
                            current_artifact = self._update_artifact_from_tool_result(
                                tool_name, result, current_artifact
                            )
                            new_artifact_type = current_artifact.get("type") if current_artifact else None

                            if previous_artifact_type != new_artifact_type:
                                logger.info(f"Artifact changed: {previous_artifact_type} → {new_artifact_type}")

                        except Exception as e:
                            logger.exception(f"Exception during tool execution: {tool_name}")
                            result = {
                                "success": False,
                                "error": f"Tool execution error: {str(e)}"
                            }
                    else:
                        logger.error(f"Unknown tool requested: {tool_name}")
                        result = {
                            "success": False,
                            "error": f"Unknown tool: {tool_name}"
                        }

                    function_responses.append({
                        "name": tool_name,
                        "response": result
                    })

                # Add function responses to conversation
                user_response = {"role": "user", "parts": []}
                for func_resp in function_responses:
                    user_response["parts"].append({
                        "function_response": {
                            "name": func_resp["name"],
                            "response": func_resp["response"]
                        }
                    })
                conversation_history.append(user_response)

            except Exception as e:
                logger.exception(f"Error during assistant execution at iteration {iterations}")
                return {
                    "message": f"I encountered an error: {str(e)}. Please try again.",
                    "artifact": current_artifact,
                    "tool_calls": all_tool_calls,
                    "iterations": iterations,
                    "error": str(e)
                }

        # Max iterations reached
        logger.warning(f"Max iterations ({self.max_iterations}) reached")
        return {
            "message": "I'm processing a lot of information. Let me summarize what we have so far and we can continue from there.",
            "artifact": current_artifact,
            "tool_calls": all_tool_calls,
            "iterations": iterations,
            "warning": "max_iterations_reached"
        }

    def _get_current_artifact(self, messages: list[Message]) -> Optional[dict]:
        """Extract the current artifact state from the message history."""
        # Look for the most recent artifact (from either user or assistant)
        for message in reversed(messages):
            if message.artifact:
                if isinstance(message.artifact, dict):
                    return message.artifact
                else:
                    # Convert Pydantic model to dict
                    return message.artifact.model_dump()
        return None

    def _update_artifact_from_tool_result(
        self,
        tool_name: str,
        result: dict,
        current_artifact: Optional[dict]
    ) -> Optional[dict]:
        """
        Update artifact based on tool execution result.

        Args:
            tool_name: Name of the tool that was executed
            result: Result from tool execution
            current_artifact: Current artifact state

        Returns:
            Updated artifact dict or None
        """
        if not result.get("success"):
            return current_artifact

        if tool_name == "generate_concept_design":
            # Create JewelryDesignArtifact from concept design
            design_data = result.get("design")
            if design_data:
                # Ensure all required fields are present (no IDs)
                design_dict = {
                    "name": design_data["name"],
                    "description": design_data["description"],
                    "properties": design_data["properties"],
                    "images": design_data.get("images", []),
                    "three_d_model": design_data.get("three_d_model")
                }

                # Create artifact (no ID)
                artifact = {
                    "type": "design",
                    "design": design_dict
                }

                # Cache as current artifact
                self.current_artifact = artifact
                logger.debug(f"Cached design artifact: {design_data['name']}")

                return artifact

        elif tool_name == "recommend_products":
            # Create ProductRecommendationArtifact from recommendations
            products = result.get("products", [])
            if products:
                # Create artifact (no ID)
                artifact = {
                    "type": "recommendation",
                    "products": products
                }

                # Cache as current artifact
                self.current_artifact = artifact
                logger.debug(f"Cached recommendation artifact with {len(products)} products")

                return artifact

        elif tool_name == "generate_2d_images":
            # Update existing JewelryDesignArtifact with 2D images
            if current_artifact and current_artifact.get("type") == "design":
                design = current_artifact["design"]
                images = result.get("images", [])

                # Update images list
                design["images"] = images

                # Update current cache
                self.current_artifact = current_artifact
                logger.debug(f"Updated current artifact with 2D images")

                return current_artifact

        elif tool_name == "generate_3d_model":
            # Update existing JewelryDesignArtifact with 3D model
            if current_artifact and current_artifact.get("type") == "design":
                design = current_artifact["design"]
                model_id = result.get("model_id")

                if model_id:
                    design["three_d_model"] = model_id

                    # Update current cache
                    self.current_artifact = current_artifact
                    logger.debug(f"Updated current artifact with 3D model")

                return current_artifact

        return current_artifact

    def _register_all_tools(self):
        """Register all available tools for jewelry design assistance."""

        # Tool 0: Respond to User (REQUIRED - must be called for every response)
        self.register_tool(
            name="respond_to_user",
            description="Send your response to the user. You MUST call this tool to communicate with the user. Include your message and the current artifact state.",
            parameters={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Your conversational message to the user. Be warm, empathetic, and specific."
                    },
                    "artifact": {
                        "type": "object",
                        "description": "The artifact to display in the UI. Once created, MUST be included in all subsequent responses. Set to null only before creating the first design.",
                        "nullable": True,
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["design", "recommendation"],
                                "description": "Type of artifact: 'design' or 'recommendation'"
                            },
                            "design": {
                                "type": "object",
                                "nullable": True,
                                "description": "Design object if type is 'design' else null. Include ALL design information.",
                                "properties": {
                                    "name": {"type": "string", "description": "Name of the jewelry design"},
                                    "description": {"type": "string", "description": "Detailed description of the design"},
                                    "properties": {
                                        "type": "object",
                                        "description": "Complete jewelry properties with all relevant details",
                                        "properties": {
                                            "target_audience": {
                                                "type": "string",
                                                "enum": ["men", "women", "unisex", "couple", "personalized"],
                                                "nullable": True,
                                                "description": "Target audience for the jewelry"
                                            },
                                            "jewelry_type": {
                                                "type": "string",
                                                "enum": ["ring", "bracelet", "bangle", "necklace", "earring", "anklet"],
                                                "nullable": True,
                                                "description": "Type of jewelry item"
                                            },
                                            "metal": {
                                                "type": "string",
                                                "enum": ["24k_gold", "22k_gold", "18k_gold", "14k_gold", "10k_gold", "silver", "platinum"],
                                                "nullable": True,
                                                "description": "Type of metal used"
                                            },
                                            "color": {
                                                "type": "string",
                                                "enum": ["white", "yellow", "rose"],
                                                "nullable": True,
                                                "description": "Color tone of the metal"
                                            },
                                            "weight": {
                                                "type": "number",
                                                "nullable": True,
                                                "description": "Weight of the metal in grams"
                                            },
                                            "gemstone": {
                                                "type": "string",
                                                "enum": ["diamond", "sapphire", "emerald", "amethyst", "ruby", "citrine", "tourmaline", "topaz", "garnet", "peridot", "spinel", "cubic_zirconia", "aquamarine", "opal", "moonstone", "pearl"],
                                                "nullable": True,
                                                "description": "Type of gemstone"
                                            },
                                            "shape": {
                                                "type": "string",
                                                "enum": ["round", "oval", "marquise", "pear", "heart", "radiant", "emerald", "cushion", "princess"],
                                                "nullable": True,
                                                "description": "Shape of the gemstone"
                                            },
                                            "size": {
                                                "type": "number",
                                                "nullable": True,
                                                "description": "Size of the gemstone in carats"
                                            },
                                            "style": {
                                                "type": "string",
                                                "enum": ["classic", "modern", "vintage", "minimalist", "luxury", "personality", "natural"],
                                                "nullable": True,
                                                "description": "Style of jewelry design"
                                            },
                                            "occasion": {
                                                "type": "string",
                                                "enum": ["wedding", "engagement", "casual", "formal", "party", "daily_wear"],
                                                "nullable": True,
                                                "description": "Occasion for wearing the jewelry"
                                            },
                                            "inspiration": {
                                                "type": "string",
                                                "nullable": True,
                                                "description": "Inspiring story or background for the jewelry design"
                                            }
                                        }
                                    },
                                    "images": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "List of image data URLs (base64)"
                                    },
                                    "three_d_model": {
                                        "type": "string",
                                        "nullable": True,
                                        "description": "3D model URL if available"
                                    }
                                },
                                "required": ["name", "description", "properties", "images"]
                            },
                            "products": {
                                "type": "array",
                                "nullable": True,
                                "description": "List of products if type is 'recommendation' else null. Include ALL product information.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string", "description": "Product name"},
                                        "description": {"type": "string", "description": "Detailed product description"},
                                        "price": {"type": "number", "description": "Price in VND"},
                                        "properties": {
                                            "type": "object",
                                            "description": "Complete jewelry properties with all relevant details",
                                            "properties": {
                                                "target_audience": {
                                                    "type": "string",
                                                    "enum": ["men", "women", "unisex", "couple", "personalized"],
                                                    "nullable": True,
                                                    "description": "Target audience for the jewelry"
                                                },
                                                "jewelry_type": {
                                                    "type": "string",
                                                    "enum": ["ring", "bracelet", "bangle", "necklace", "earring", "anklet"],
                                                    "nullable": True,
                                                    "description": "Type of jewelry item"
                                                },
                                                "metal": {
                                                    "type": "string",
                                                    "enum": ["24k_gold", "22k_gold", "18k_gold", "14k_gold", "10k_gold", "silver", "platinum"],
                                                    "nullable": True,
                                                    "description": "Type of metal used"
                                                },
                                                "color": {
                                                    "type": "string",
                                                    "enum": ["white", "yellow", "rose"],
                                                    "nullable": True,
                                                    "description": "Color tone of the metal"
                                                },
                                                "weight": {
                                                    "type": "number",
                                                    "nullable": True,
                                                    "description": "Weight of the metal in grams"
                                                },
                                                "gemstone": {
                                                    "type": "string",
                                                    "enum": ["diamond", "sapphire", "emerald", "amethyst", "ruby", "citrine", "tourmaline", "topaz", "garnet", "peridot", "spinel", "cubic_zirconia", "aquamarine", "opal", "moonstone", "pearl"],
                                                    "nullable": True,
                                                    "description": "Type of gemstone"
                                                },
                                                "shape": {
                                                    "type": "string",
                                                    "enum": ["round", "oval", "marquise", "pear", "heart", "radiant", "emerald", "cushion", "princess"],
                                                    "nullable": True,
                                                    "description": "Shape of the gemstone"
                                                },
                                                "size": {
                                                    "type": "number",
                                                    "nullable": True,
                                                    "description": "Size of the gemstone in carats"
                                                },
                                                "style": {
                                                    "type": "string",
                                                    "enum": ["classic", "modern", "vintage", "minimalist", "luxury", "personality", "natural"],
                                                    "nullable": True,
                                                    "description": "Style of jewelry design"
                                                },
                                                "occasion": {
                                                    "type": "string",
                                                    "enum": ["wedding", "engagement", "casual", "formal", "party", "daily_wear"],
                                                    "nullable": True,
                                                    "description": "Occasion for wearing the jewelry"
                                                },
                                                "inspiration": {
                                                    "type": "string",
                                                    "nullable": True,
                                                    "description": "Inspiring story or background for the jewelry design"
                                                }
                                            }
                                        },
                                        "images": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "Product image URLs"
                                        },
                                        "three_d_model": {
                                            "type": "string",
                                            "nullable": True,
                                            "description": "3D model URL if available"
                                        }
                                    },
                                    "required": ["name", "description", "price", "properties", "images"]
                                }
                            }
                        },
                        "required": ["type"]
                    }
                },
                "required": ["message"]
            },
            implementation=None  # Special handling - no implementation needed
        )

        # Tool 1: Generate Concept Design
        self.register_tool(
            name="generate_concept_design",
            description="Generate a detailed jewelry design concept based on customer requirements, story, and preferences. Use this after gathering sufficient information through conversation.",
            parameters={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the desired jewelry from the customer, including their story, inspiration, and requirements"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context about occasion, purpose, style preferences, and emotional significance"
                    }
                },
                "required": ["description"]
            },
            implementation=self._generate_concept_design_tool
        )

        # Tool 2: Recommend Products
        self.register_tool(
            name="recommend_products",
            description="Recommend existing PNJ jewelry products that match the current design concept. Use this after creating a concept design to show real products from the catalog. Works with the current design from conversation context.",
            parameters={
                "type": "object",
                "properties": {
                    "top_k": {
                        "type": "integer",
                        "description": "Number of recommendations to return (default: 5, max: 5)",
                        "default": 5
                    },
                    "min_similarity": {
                        "type": "number",
                        "description": "Minimum similarity threshold from 0.0 to 1.0 (default: 0.3)",
                        "default": 0.3
                    }
                },
                "required": []
            },
            implementation=self._recommend_products_tool
        )

        # Tool 3: Generate 2D Images
        self.register_tool(
            name="generate_2d_images",
            description="Generate professional 2D product images from 3 angles (front, side, top) for the current jewelry design. Use this when customer wants to visualize their customized or new design. This takes time, so set expectations. Works with the current design from conversation context.",
            parameters={
                "type": "object",
                "properties": {
                    "style_context": {
                        "type": "string",
                        "description": "Optional additional styling instructions for image generation"
                    }
                },
                "required": []
            },
            implementation=self._generate_2d_images_tool
        )

        # Tool 4: Generate 3D Model (Placeholder)
        self.register_tool(
            name="generate_3d_model",
            description="Generate an interactive 3D model for AR try-on experience for the current design. (PLACEHOLDER - Not yet implemented)",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            implementation=self._generate_3d_model_tool
        )

    # Tool Implementation Methods

    async def _generate_concept_design_tool(
        self,
        description: str,
        context: str = ""
    ) -> dict[str, Any]:
        """
        Tool implementation for generating concept designs.

        Args:
            description: Customer's description of desired jewelry
            context: Additional context

        Returns:
            Dict with success status and design data
        """
        logger.info("Starting concept design generation")
        logger.debug(f"Description: {description[:100]}...")

        try:
            # Use the concept design agent
            design_output = await self.concept_agent.run(
                description=description,
                user=self.user,
                context=context,
                reference_images=None  # TODO: Pass reference images if available
            )

            # Convert to dict (no IDs)
            design_dict = {
                "name": design_output.name,
                "description": design_output.description,
                "properties": design_output.properties.model_dump(),
                "images": [],
                "three_d_model": None
            }

            # Note: Design will be cached as part of artifact in _update_artifact_from_tool_result
            logger.info(f"Created concept design: {design_output.name}")

            return {
                "success": True,
                "design": design_dict,
                "message": f"Created concept design: {design_output.name}"
            }

        except Exception as e:
            logger.error(f"Failed to generate concept design: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to generate concept design: {str(e)}"
            }

    async def _recommend_products_tool(
        self,
        top_k: int = 5,
        min_similarity: float = 0.3
    ) -> dict[str, Any]:
        """
        Tool implementation for recommending products.

        Args:
            top_k: Number of recommendations
            min_similarity: Minimum similarity threshold

        Returns:
            Dict with success status and products list
        """
        logger.info(f"Starting product recommendation for current design")
        logger.debug(f"Parameters: top_k={top_k}, min_similarity={min_similarity}")

        try:
            # Retrieve design from current artifact
            if not self.current_artifact or self.current_artifact.get("type") != "design":
                logger.error("No current design artifact found")
                return {
                    "success": False,
                    "error": "No design found in current context. Please generate a concept design first."
                }

            design_dict = self.current_artifact.get("design")
            if not design_dict:
                logger.error("Current artifact has no design data")
                return {
                    "success": False,
                    "error": "Current artifact is missing design data."
                }

            # Convert dict to JewelryDesign object (no ID needed)
            design = JewelryDesign(
                name=design_dict["name"],
                description=design_dict["description"],
                properties=JewelryProperties(**design_dict["properties"]),
                images=design_dict.get("images", []),
                three_d_model=design_dict.get("three_d_model")
            )

            # Get recommendations
            recommended_products = await self.recommendation_agent.recommend(
                design=design,
                top_k=top_k,
                min_similarity=min_similarity
            )

            # Convert products to dicts
            products_list = [product.model_dump() for product in recommended_products]
            logger.info(f"Found {len(products_list)} recommended products")

            if products_list:
                product_names = [p.get('name', 'Unknown') for p in products_list[:3]]
                logger.debug(f"Top products: {product_names}")

            return {
                "success": True,
                "products": products_list,
                "count": len(products_list),
                "message": f"Found {len(products_list)} similar products from PNJ catalog"
            }

        except Exception as e:
            logger.error(f"Failed to recommend products: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to recommend products: {str(e)}"
            }

    async def _generate_2d_images_tool(
        self,
        style_context: str = ""
    ) -> dict[str, Any]:
        """
        Tool implementation for generating 2D images.

        Args:
            style_context: Optional styling instructions

        Returns:
            Dict with success status and images data
        """
        logger.info(f"Starting 2D image generation for current design")
        if style_context:
            logger.debug(f"Style context: {style_context}")

        try:
            # Retrieve design from current artifact
            if not self.current_artifact or self.current_artifact.get("type") != "design":
                logger.error("No current design artifact found")
                return {
                    "success": False,
                    "error": "No design found in current context. Please generate a concept design first."
                }

            design_dict = self.current_artifact.get("design")
            if not design_dict:
                logger.error("Current artifact has no design data")
                return {
                    "success": False,
                    "error": "Current artifact is missing design data."
                }

            # Convert dict to JewelryDesignOutput for 2D agent
            from app.agents.concept_design_agent import JewelryDesignOutput

            design_output = JewelryDesignOutput(
                name=design_dict["name"],
                description=design_dict["description"],
                properties=JewelryProperties(**design_dict["properties"])
            )

            # Generate 2D images
            result_2d = await self.design_2d_agent.run(
                design=design_output,
                reference_images=None,
                style_context=style_context if style_context else None
            )

            # Convert images to base64 data URLs for storage
            images_data = []
            for generated_image in result_2d.images:
                # Store as data URL format
                image_data_url = f"data:{generated_image.mime_type};base64,{generated_image.image_data}"
                images_data.append(image_data_url)

            # Note: Images will be added to artifact cache in _update_artifact_from_tool_result
            logger.info(f"Generated {len(images_data)} 2D images for current design")

            return {
                "success": True,
                "images": images_data,
                "count": len(images_data),
                "message": f"Generated {len(images_data)} 2D product images (front, side, top views)"
            }

        except Exception as e:
            logger.error(f"Failed to generate 2D images: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to generate 2D images: {str(e)}"
            }

    async def _generate_3d_model_tool(self) -> dict[str, Any]:
        """
        Tool implementation for generating 3D models (Placeholder).

        Returns:
            Dict with success status
        """
        return {
            "success": False,
            "error": "3D model generation is not yet implemented. This is a placeholder for future functionality."
        }

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        implementation: Callable
    ):
        """
        Register a new tool.

        Args:
            name: Tool name
            description: Tool description
            parameters: JSON schema for tool parameters
            implementation: Callable that implements the tool
        """
        # Create FunctionDeclaration for Google Gemini
        function_declaration = types.FunctionDeclaration(
            name=name,
            description=description,
            parameters=parameters
        )

        self.tools[name] = function_declaration
        self.tool_implementations[name] = implementation

    def _convert_messages_to_gemini_format(
        self,
        messages: list[Message]
    ) -> list[dict[str, Any]]:
        """
        Convert Message objects to Gemini format.

        Includes artifact information in the message text for LLM context.
        """
        gemini_messages = []

        for msg in messages:
            role = "user" if msg.role == "user" else "model"
            content = {"role": role, "parts": []}

            # Build text content with artifact context
            text_parts = []

            # Add main message content
            if msg.content:
                text_parts.append(msg.content)

            # Add artifact context to help LLM understand current state
            if msg.artifact:
                artifact_summary = self._summarize_artifact_for_context(msg.artifact)
                if artifact_summary:
                    text_parts.append(f"\n[Current UI State: {artifact_summary}]")

            if text_parts:
                content["parts"].append({"text": "\n".join(text_parts)})

            # Add images if present (for user messages)
            if msg.images and role == "user":
                for image_id in msg.images[:5]:  # Limit to 5 images
                    # TODO: Load actual image data
                    # For now, just note that images are present
                    pass

            gemini_messages.append(content)

        return gemini_messages

    def _summarize_artifact_for_context(self, artifact: dict | Artifact) -> str:
        """
        Create a text summary of artifact for LLM context.

        Args:
            artifact: Artifact dict or object

        Returns:
            Human-readable summary of artifact
        """
        if isinstance(artifact, dict):
            artifact_type = artifact.get("type")
        else:
            artifact_type = artifact.type
            artifact = artifact.model_dump()

        if artifact_type == "design":
            design = artifact.get("design", {})
            name = design.get("name", "Unnamed Design")
            has_images = len(design.get("images", [])) > 0
            has_3d = design.get("three_d_model") is not None

            status_parts = [f"Design '{name}' is displayed"]
            if has_images:
                status_parts.append("with 2D images")
            if has_3d:
                status_parts.append("with 3D model")

            return " ".join(status_parts)

        elif artifact_type == "recommendation":
            products = artifact.get("products", [])
            count = len(products)
            return f"Showing {count} recommended products"

        return "Artifact displayed"
