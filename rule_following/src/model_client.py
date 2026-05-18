"""
Model client interfaces for querying VLMs
Includes base class and OpenAI-compatible clients
send images as base64-encoded data URLs
"""

from abc import ABC, abstractmethod
from typing import Optional, Union, List
import base64
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ModelClient(ABC):
    """Base class for model clients"""

    def __init__(self, model_name: str = "test_model"):
        self.model_name = model_name

    @abstractmethod
    def query(self, prompt: str, image_path: Union[str, List[str]]) -> str:
        """
        Query the model with text and image(s)

        Args:
            prompt: Text prompt
            image_path: Path to image file, or list of paths for multiple images

        Returns:
            Model response as string
        """
        pass

    def query_text_only(self, prompt: str) -> str:
        """
        Query the model with text only (no images).

        Args:
            prompt: Text prompt

        Returns:
            Model response as string
        """
        raise NotImplementedError("Subclass must implement query_text_only")


class OpenAICompatibleModelClient(ModelClient):
    """
    Base class for OpenAI-compatible API clients
    Supports any service that uses OpenAI's API format
    """

    # Subclasses should override these
    DEFAULT_BASE_URL = None
    ENV_API_KEY = None
    ENV_BASE_URL = None
    ENV_MODEL = None
    SERVICE_NAME = "OpenAI-compatible"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize OpenAI-compatible client

        Args:
            api_key: API key (if None, reads from environment variable)
            base_url: API base URL (if None, reads from environment variable)
            model_name: Model name (if None, reads from environment variable)
            **kwargs: Additional parameters to pass to the API
        """
        # Get configuration from env vars if not provided
        self.api_key = api_key or os.getenv(self.ENV_API_KEY)
        self.base_url = base_url or os.getenv(
            self.ENV_BASE_URL, self.DEFAULT_BASE_URL)
        model = model_name or os.getenv(self.ENV_MODEL)

        # Validate required parameters
        if not self.api_key:
            raise ValueError(
                f"{self.SERVICE_NAME} API key not found. "
                f"Please set {self.ENV_API_KEY} environment variable or pass api_key parameter."
            )

        if not model:
            raise ValueError(
                f"{self.SERVICE_NAME} model name not found. "
                f"Please set {self.ENV_MODEL} environment variable or pass model_name parameter."
            )

        if not self.base_url:
            raise ValueError(
                f"{self.SERVICE_NAME} base URL not found. "
                f"Please set {self.ENV_BASE_URL} environment variable or pass base_url parameter."
            )

        super().__init__(model_name=model)

        # Store any additional parameters
        self.extra_params = kwargs

        # Initialize OpenAI client
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            print(f"✓ {self.SERVICE_NAME} client initialized")
            print(f"  Model: {self.model_name}")
            if self.extra_params:
                print(f"  Extra params: {self.extra_params}")
        except ImportError:
            raise ImportError(
                "openai package is required. Install it with: pip install 'openai>=1.0.0'"
            )

    def query(self, prompt: str, image_path: Union[str, List[str]]) -> str:
        """
        Call OpenAI-compatible API with image(s)

        Args:
            prompt: Text prompt
            image_path: Path to image file, or list of paths for multiple images

        Returns:
            Model response
        """
        # Handle both single image and multiple images
        if isinstance(image_path, str):
            image_paths = [image_path]
        else:
            image_paths = image_path

        # Build content array with images and text
        content = []

        # Add all images first
        for img_path in image_paths:
            # Read and encode image as base64
            with open(img_path, "rb") as image_file:
                image_data = base64.b64encode(
                    image_file.read()).decode("utf-8")

            # Determine image media type
            if img_path.lower().endswith('.png'):
                media_type = "image/png"
            elif img_path.lower().endswith(('.jpg', '.jpeg')):
                media_type = "image/jpeg"
            else:
                media_type = "image/png"  # default

            # Construct data URL
            image_url = f"data:{media_type};base64,{image_data}"

            content.append({
                "type": "image_url",
                "image_url": {
                    "url": image_url
                }
            })

        # Add text prompt at the end
        content.append({
            "type": "text",
            "text": prompt
        })

        try:
            # Prepare base parameters
            params = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ]
            }

            # Add any extra parameters if provided
            params.update(self.extra_params)

            # Call API
            chat_completion_res = self.client.chat.completions.create(**params)

            # Handle streaming vs non-streaming responses
            if self.extra_params.get('stream', False):
                # Collect streamed response
                response_text = ""
                for chunk in chat_completion_res:
                    if chunk.choices[0].delta.content:
                        response_text += chunk.choices[0].delta.content
                return response_text
            else:
                # Return non-streaming response
                return chat_completion_res.choices[0].message.content

        except Exception as e:
            raise Exception(f"{self.SERVICE_NAME} API call failed: {str(e)}")

    def query_text_only(self, prompt: str) -> str:
        """Query with text only, no images."""
        content = [{"type": "text", "text": prompt}]

        try:
            params = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": content}]
            }
            params.update(self.extra_params)

            chat_completion_res = self.client.chat.completions.create(**params)

            if self.extra_params.get('stream', False):
                response_text = ""
                for chunk in chat_completion_res:
                    if chunk.choices[0].delta.content:
                        response_text += chunk.choices[0].delta.content
                return response_text
            else:
                return chat_completion_res.choices[0].message.content

        except Exception as e:
            raise Exception(f"{self.SERVICE_NAME} API call failed: {str(e)}")


class NovitaModelClient(OpenAICompatibleModelClient):
    """Novita AI model client"""

    DEFAULT_BASE_URL = "https://api.novita.ai/openai"
    ENV_API_KEY = "NOVITA_API_KEY"
    ENV_BASE_URL = "NOVITA_BASE_URL"
    ENV_MODEL = "NOVITA_MODEL"
    SERVICE_NAME = "Novita"


class DashScopeModelClient(OpenAICompatibleModelClient):
    """Alibaba DashScope model client"""

    DEFAULT_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    ENV_API_KEY = "DASHSCOPE_API_KEY"
    ENV_BASE_URL = "DASHSCOPE_BASE_URL"
    ENV_MODEL = "DASHSCOPE_MODEL"
    SERVICE_NAME = "DashScope"


class XAIModelClient(OpenAICompatibleModelClient):
    """XAI model client"""

    DEFAULT_BASE_URL = "https://api.x.ai/v1"
    ENV_API_KEY = "XAI_API_KEY"
    ENV_BASE_URL = "XAI_BASE_URL"
    ENV_MODEL = "XAI_MODEL"
    SERVICE_NAME = "XAI"


class SiliconFlowModelClient(OpenAICompatibleModelClient):
    """SiliconFlow model client"""

    DEFAULT_BASE_URL = "https://api.siliconflow.com/v1"
    ENV_API_KEY = "SILICONFLOW_API_KEY"
    ENV_BASE_URL = "SILICONFLOW_BASE_URL"
    ENV_MODEL = "SILICONFLOW_MODEL"
    SERVICE_NAME = "SiliconFlow"


class GoogleModelClient(OpenAICompatibleModelClient):
    """Google Gemini (via OpenAI-compatible endpoint) model client"""

    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
    ENV_API_KEY = "GOOGLE_API_KEY"
    ENV_BASE_URL = "GOOGLE_BASE_URL"
    ENV_MODEL = "GOOGLE_MODEL"
    SERVICE_NAME = "Google"


class OpenRouterModelClient(OpenAICompatibleModelClient):
    """OpenRouter unified gateway (OpenAI-compatible)"""

    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
    ENV_API_KEY = "OPENROUTER_API_KEY"
    ENV_BASE_URL = "OPENROUTER_BASE_URL"
    ENV_MODEL = "OPENROUTER_MODEL"
    SERVICE_NAME = "OpenRouter"


class OpenAIModelClient(OpenAICompatibleModelClient):
    """OpenAI GPT model client with Reasoning support"""

    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    ENV_API_KEY = "OPENAI_API_KEY"
    ENV_BASE_URL = "OPENAI_BASE_URL"
    ENV_MODEL = "OPENAI_MODEL"
    SERVICE_NAME = "OpenAI"
    REASONING_EFFORT = "low"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name
        )
        print(f"  Reasoning: ON (effort: {self.REASONING_EFFORT})")

    def query(self, prompt: str, image_path: Union[str, List[str]]) -> str:
        image_paths = [image_path] if isinstance(
            image_path, str) else image_path
        content = []

        for img_path in image_paths:
            with open(img_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            ext = img_path.lower().split('.')[-1]
            media_type = {'png': 'image/png', 'jpg': 'image/jpeg',
                          'jpeg': 'image/jpeg', 'gif': 'image/gif',
                          'webp': 'image/webp'}.get(ext, 'image/png')
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{media_type};base64,{image_data}"}
            })

        content.append({"type": "text", "text": prompt})

        params = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": content}],
            "reasoning_effort": self.REASONING_EFFORT
        }

        try:
            response = self.client.chat.completions.create(**params)
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"{self.SERVICE_NAME} API error: {str(e)}")

    def query_text_only(self, prompt: str) -> str:
        """Query with text only, includes reasoning_effort."""
        content = [{"type": "text", "text": prompt}]

        params = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": content}],
            "reasoning_effort": self.REASONING_EFFORT
        }

        try:
            response = self.client.chat.completions.create(**params)
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"{self.SERVICE_NAME} API error: {str(e)}")


class AnthropicModelClient(ModelClient):
    """Anthropic Claude model client with Extended Thinking"""

    ENV_API_KEY = "ANTHROPIC_API_KEY"
    ENV_MODEL = "ANTHROPIC_MODEL"
    SERVICE_NAME = "Anthropic"
    DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
    THINKING_BUDGET = 1024

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv(self.ENV_API_KEY)
        model = model_name or os.getenv(self.ENV_MODEL, self.DEFAULT_MODEL)

        if not self.api_key:
            raise ValueError(f"Set {self.ENV_API_KEY} environment variable.")

        super().__init__(model_name=model)

        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
            print(f"✓ {self.SERVICE_NAME} client initialized")
            print(f"  Model: {self.model_name}")
            print(f"  Extended Thinking: ON (budget: {self.THINKING_BUDGET})")
        except ImportError:
            raise ImportError("pip install anthropic")

    def query(self, prompt: str, image_path: Union[str, List[str]]) -> str:
        image_paths = [image_path] if isinstance(
            image_path, str) else image_path
        content = []

        for img_path in image_paths:
            with open(img_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            ext = img_path.lower().split('.')[-1]
            media_type = {'png': 'image/png', 'jpg': 'image/jpeg',
                          'jpeg': 'image/jpeg', 'gif': 'image/gif',
                          'webp': 'image/webp'}.get(ext, 'image/png')
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": image_data}
            })

        content.append({"type": "text", "text": prompt})

        api_params = {
            "model": self.model_name,
            "max_tokens": 16000,
            "messages": [{"role": "user", "content": content}],
            "thinking": {
                "type": "enabled",
                "budget_tokens": self.THINKING_BUDGET
            }
        }

        try:
            message = self.client.messages.create(**api_params)
            return "".join(b.text for b in message.content if b.type == "text")
        except Exception as e:
            raise Exception(f"{self.SERVICE_NAME} API error: {str(e)}")

    def query_text_only(self, prompt: str) -> str:
        """Query with text only, uses Extended Thinking."""
        content = [{"type": "text", "text": prompt}]

        api_params = {
            "model": self.model_name,
            "max_tokens": 16000,
            "messages": [{"role": "user", "content": content}],
            "thinking": {
                "type": "enabled",
                "budget_tokens": self.THINKING_BUDGET
            }
        }

        try:
            message = self.client.messages.create(**api_params)
            return "".join(b.text for b in message.content if b.type == "text")
        except Exception as e:
            raise Exception(f"{self.SERVICE_NAME} API error: {str(e)}")


class DummyModelClient(ModelClient):
    """Dummy model client for testing the framework"""

    def __init__(self, verification_pass_rate: float = 0.7):
        """
        Initialize dummy model

        Args:
            verification_pass_rate: Probability of passing verification (0.0 to 1.0)
        """
        super().__init__(model_name="dummy_model")
        self.verification_pass_rate = verification_pass_rate
        self.test_cases_lookup = {}  # image_path -> case info

    def set_test_cases(self, test_cases: list):
        """
        Provide test cases to dummy model so it can "know" correct answers

        Args:
            test_cases: List of test case dictionaries
        """
        self.test_cases_lookup = {}
        for case in test_cases:
            # Handle both single image_path and multiple image_paths
            if 'image_paths' in case and case['image_paths']:
                # Use first image path as key for temporal tests
                key = case['image_paths'][0] if isinstance(
                    case['image_paths'], list) else case['image_paths']
                self.test_cases_lookup[key] = case
            elif 'image_path' in case:
                self.test_cases_lookup[case['image_path']] = case

        print(f"  Dummy model loaded {len(self.test_cases_lookup)} test cases")

    def query(self, prompt: str, image_path: Union[str, List[str]]) -> str:
        """
        Return simulated answer for testing

        Args:
            prompt: Text prompt
            image_path: Path to image file, or list of paths for multiple images

        Returns:
            Simulated response
        """
        import random

        # Get the first image path as lookup key
        if isinstance(image_path, list):
            lookup_key = image_path[0]
        else:
            lookup_key = image_path

        # Look up the case info
        case = self.test_cases_lookup.get(lookup_key)

        # Check if this is a combined prompt (verification + test)
        if "Verification:" in prompt and "Main answer:" in prompt:
            return self._generate_combined_response(prompt, case)
        else:
            # Single question - random answer
            return random.choice(["yes", "no", "unknown"])

    def query_text_only(self, prompt: str) -> str:
        """Return simulated answer for text-only testing."""
        import random
        return random.choice(["Main answer: yes", "Main answer: no"])

    def _generate_combined_response(self, prompt: str, case: dict = None) -> str:
        """Generate response for combined verification + test prompt"""
        import random

        # Generate verification response (using case info if available)
        if case:
            verification_response = self._generate_verification_response_with_case(
                case)
        else:
            verification_response = self._generate_random_verification()

        # Random answer for main question
        main_answer = random.choice(["yes", "no", "unknown"])

        # Format response
        response = f"""Verification: {verification_response}
Main answer: {main_answer}"""

        return response

    def _generate_verification_response_with_case(self, case: dict) -> str:
        """
        Generate verification response using case information

        Pass with probability = verification_pass_rate
        """
        import random

        # Decide if this attempt passes
        if random.random() > self.verification_pass_rate:
            # Fail: return wrong answer
            return self._generate_wrong_verification()

        # Pass: return correct answer from case
        verification_expected = case.get('verification_expected', '')

        # If we have the expected answer, return it
        if verification_expected:
            return verification_expected

        # Otherwise try to construct from case data
        squares = case.get('squares', [])
        pieces = case.get('pieces', {})

        # Generate correct response based on verification question type
        verification_q = case.get('verification_question', '').lower()

        if "how many squares" in verification_q:
            return "64"

        elif "what square" in verification_q and len(squares) == 1:
            # Single square question
            return squares[0]

        elif "what two squares" in verification_q or ("what squares" in verification_q and len(squares) == 2):
            # Two squares question
            if len(squares) >= 2:
                return f"{squares[0]} and {squares[1]}"
            else:
                return self._generate_wrong_verification()

        elif "what squares" in verification_q and len(squares) >= 3:
            # Three or more squares
            return ", ".join(squares[:-1]) + " and " + squares[-1]

        elif "how many pieces" in verification_q:
            # Piece count question
            return str(len(pieces))

        elif "what square" in verification_q and "piece" in verification_q:
            # Piece position question
            if pieces:
                piece_sq = list(pieces.keys())[0]
                return piece_sq
            else:
                return self._generate_wrong_verification()

        else:
            # Default: return verification_expected if available
            return verification_expected if verification_expected else "I see the board"

    def _generate_random_verification(self) -> str:
        """Generate random verification response (when case info not available)"""
        import random

        responses = [
            "I see a chess board",
            f"{self._generate_square_name()}",
            f"{self._generate_square_name()} and {self._generate_square_name()}",
        ]
        return random.choice(responses)

    def _generate_square_name(self) -> str:
        """Generate a random valid square name"""
        import random
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        ranks = ['1', '2', '3', '4', '5', '6', '7', '8']
        return random.choice(files) + random.choice(ranks)

    def _generate_wrong_verification(self) -> str:
        """Generate intentionally wrong verification response"""
        import random

        wrong_responses = [
            "I see a chess board",
            "The board looks normal",
            f"{self._generate_square_name()}",  # Wrong square
            f"{self._generate_square_name()} and {self._generate_square_name()}",
            "I'm not sure",
            "c3 d4",  # Random squares
            "There are pieces on the board",
        ]

        return random.choice(wrong_responses)
