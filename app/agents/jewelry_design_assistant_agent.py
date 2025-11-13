"""Assistant agent with tool-use capabilities using Gemini API."""
from typing import Any, Callable
import json
import google.genai as genai
from google.genai import types

from app.config import settings
from app.schemas.message import Message

SYSTEM_PROMPT_TEMPLATE = """
You are a helpful AI assistant for PNJ Jewelry Designer.
You help users design jewelry, answer questions about jewelry,
and provide information about materials, styles, and pricing.

You have access to various tools to help you assist users better.
Use the appropriate tool when needed to provide accurate information.
""".strip()


class JewelryDesignAssistantAgent:
    """Assistant agent with tool-use capabilities."""

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        system_prompt: str | None = None,
        max_iterations: int = 10
    ):
        """
        Initialize the assistant agent.

        Args:
            model: Gemini model to use
            system_prompt: System prompt for the agent
            max_iterations: Maximum number of tool execution iterations
        """
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = model
        self.system_prompt = system_prompt or SYSTEM_PROMPT_TEMPLATE
        self.max_iterations = max_iterations

        # Tools registry: maps tool names to their definitions and implementations
        self.tools: dict[str, dict[str, Any]] = {}
        self.tool_implementations: dict[str, Callable] = {}

        # Register default tools
        self._register_default_tools()

    async def run(
        self,
        messages: list[Message],
        enable_tools: bool = True
    ) -> dict[str, Any]:
        """
        Run the assistant agent with tool-use capabilities.

        Args:
            messages: List of conversation messages
            enable_tools: Whether to enable tool calling

        Returns:
            Dictionary containing:
                - content: Final response text
                - tool_calls: List of tool calls made
                - iterations: Number of iterations
        """
        conversation_history = self._convert_messages_to_gemini_format(messages)

        # Add system instruction as first message if not present
        if not conversation_history or conversation_history[0].get("role") != "user":
            conversation_history.insert(0, {
                "role": "user",
                "parts": [{"text": self.system_prompt}]
            })

        all_tool_calls = []
        iterations = 0

        # Tool execution loop
        while iterations < self.max_iterations:
            iterations += 1

            # Prepare tools for API call
            tools = list(self.tools.values()) if enable_tools else None

            try:
                # Call Gemini API
                response = await self.client.aio.models.generate_content(
                    model=self.model,
                    contents=conversation_history,
                    config=types.GenerateContentConfig(
                        tools=tools,
                        temperature=0.7,
                    )
                )

                if not response.candidates or len(response.candidates) == 0:
                    return {
                        "content": "I apologize, but I couldn't generate a response.",
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

                # If no function calls, we're done
                if not has_function_calls:
                    return {
                        "content": text_content,
                        "tool_calls": all_tool_calls,
                        "iterations": iterations
                    }

                # Execute function calls
                function_responses = []
                for func_call in function_calls:
                    tool_name = func_call["name"]
                    tool_args = func_call["args"]

                    # Track tool call
                    all_tool_calls.append({
                        "name": tool_name,
                        "arguments": tool_args
                    })

                    # Execute tool
                    if tool_name in self.tool_implementations:
                        try:
                            result = self.tool_implementations[tool_name](**tool_args)
                        except Exception as e:
                            result = {
                                "success": False,
                                "error": f"Tool execution error: {str(e)}"
                            }
                    else:
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
                return {
                    "content": f"Error during execution: {str(e)}",
                    "tool_calls": all_tool_calls,
                    "iterations": iterations,
                    "error": str(e)
                }

        # Max iterations reached
        return {
            "content": "Maximum iterations reached. The task may be too complex.",
            "tool_calls": all_tool_calls,
            "iterations": iterations,
            "warning": "max_iterations_reached"
        }


    def _register_default_tools(self):
        """Register default tools for jewelry assistance."""

        # Jewelry price estimator
        # price_tool = self._get_price_estimator_tool_definition()
        # self.register_tool(
        #     name=price_tool["name"],
        #     description=price_tool["description"],
        #     parameters=price_tool["parameters"],
        #     implementation=self._estimate_price_tool
        # )

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
        self.tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters
        }
        self.tool_implementations[name] = implementation

    def _convert_messages_to_gemini_format(
        self,
        messages: list[Message]
    ) -> list[dict[str, Any]]:
        """Convert Message objects to Gemini format."""
        gemini_messages = []

        for msg in messages:
            role = "user" if msg.role == "user" else "model"
            content = {"role": role, "parts": []}

            # Add text content
            if msg.content:
                content["parts"].append({"text": msg.content})

            # Add tool results if present (for function responses)
            if hasattr(msg, 'tool_results') and msg.tool_results:
                for tool_result in msg.tool_results:
                    content["parts"].append({
                        "function_response": {
                            "name": tool_result["name"],
                            "response": tool_result["response"]
                        }
                    })

            gemini_messages.append(content)

        return gemini_messages
