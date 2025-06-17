"""
Multimodal capabilities for Gemini API client.
"""

import logging
from typing import List, Dict, Any, Optional

from shared.models.llm_request import LLMRequest
from shared.models.llm_response import LLMResponse

from .base_client import GeminiBaseClient
from .exceptions import wrap_gemini_call

logger = logging.getLogger(__name__)


class GeminiMultimodalClient(GeminiBaseClient):
    """
    Gemini client for multimodal operations.
    """

    @wrap_gemini_call
    def generate_from_image(
        self,
        image_data: bytes,
        prompt: str,
        image_format: str = "jpeg",
        **kwargs
    ) -> LLMResponse:
        """
        Generate text from image and prompt.

        Args:
            image_data: Raw image data
            prompt: Text prompt to accompany the image
            image_format: Image format (jpeg, png, etc.)
            **kwargs: Additional parameters

        Returns:
            LLMResponse with generated text based on image
        """
        # Rate limiting
        self.rate_limiter.wait_if_needed()

        try:
            client = self._get_genai_client()

            # Prepare image and text request
            request = LLMRequest(
                prompt=prompt,
                images=[{
                    'data': image_data,
                    'format': image_format,
                    'mime_type': f'image/{image_format}'
                }],
                **kwargs
            )

            # Map to Gemini format
            gemini_request = self.data_mapper.map_image_request(request)

            # Use vision-capable model
            model = self.config.vision_model or 'gemini-pro-vision'

            # Make API call
            response = client.models.generate_content(
                model=model,
                contents=gemini_request.get('contents', []),
                config=gemini_request.get('config', {})
            )

            # Convert response
            llm_response = self.data_mapper.map_gemini_response(
                response,
                model=model
            )

            # Update statistics
            self._stats['requests_made'] += 1
            if hasattr(llm_response, 'usage'):
                self._stats['total_tokens'] += llm_response.usage.get('total_tokens', 0)

            return llm_response

        except Exception as e:
            self._stats['errors'] += 1
            logger.error("Image generation failed: %s", str(e))
            raise

    def get_supported_image_formats(self) -> List[str]:
        """Get list of supported image formats."""
        return ["jpeg", "jpg", "png", "gif", "bmp", "webp"]

    @wrap_gemini_call
    def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate image from text prompt.

        Note: This is a placeholder - Gemini primarily handles image analysis,
        not generation. Image generation would require different API endpoint.

        Args:
            prompt: Text prompt for image generation
            size: Image size specification
            quality: Image quality setting
            **kwargs: Additional parameters

        Returns:
            Dictionary containing image data or error message
        """
        logger.warning(
            "Image generation not directly supported by Gemini API. "
            "This would require integration with a different service."
        )

        return {
            'error': 'Image generation not supported',
            'message': 'Gemini API is primarily for image analysis, not generation',
            'suggestion': 'Use DALL-E, Midjourney, or similar image generation APIs'
        }

    def analyze_multiple_images(
        self,
        images: List[Dict[str, Any]],
        prompt: str,
        **kwargs
    ) -> LLMResponse:
        """
        Analyze multiple images with a single prompt.

        Args:
            images: List of image dictionaries with 'data' and 'format' keys
            prompt: Analysis prompt
            **kwargs: Additional parameters

        Returns:
            LLMResponse with analysis of all images
        """
        try:
            client = self._get_genai_client()

            # Create request with multiple images
            request = LLMRequest(
                prompt=prompt,
                images=images,
                **kwargs
            )

            # Map to Gemini format
            gemini_request = self.data_mapper.map_image_request(request)

            # Use vision model
            model = self.config.vision_model or 'gemini-pro-vision'

            # Make API call
            response = client.models.generate_content(
                model=model,
                contents=gemini_request.get('contents', []),
                config=gemini_request.get('config', {})
            )

            # Convert response
            return self.data_mapper.map_gemini_response(response, model=model)

        except Exception as e:
            logger.error("Multiple image analysis failed: %s", str(e))
            raise

    def extract_text_from_image(
        self,
        image_data: bytes,
        image_format: str = "jpeg"
    ) -> str:
        """
        Extract text from image using OCR capabilities.

        Args:
            image_data: Raw image data
            image_format: Image format

        Returns:
            Extracted text string
        """
        try:
            response = self.generate_from_image(
                image_data=image_data,
                prompt="Extract and return only the text content from this image. "
                       "Do not add any commentary or formatting.",
                image_format=image_format
            )

            return response.content.strip()

        except Exception as e:
            logger.error("Text extraction from image failed: %s", str(e))
            raise

    def describe_image(
        self,
        image_data: bytes,
        detail_level: str = "medium",
        image_format: str = "jpeg"
    ) -> str:
        """
        Generate detailed description of an image.

        Args:
            image_data: Raw image data
            detail_level: Level of detail (basic, medium, detailed)
            image_format: Image format

        Returns:
            Image description string
        """
        # Adjust prompt based on detail level
        prompts = {
            "basic": "Briefly describe what you see in this image.",
            "medium": "Describe this image in detail, including objects, "
                     "people, colors, and setting.",
            "detailed": "Provide a comprehensive description of this image, "
                       "including all visible details, colors, composition, "
                       "mood, and any text or symbols present."
        }

        prompt = prompts.get(detail_level, prompts["medium"])

        try:
            response = self.generate_from_image(
                image_data=image_data,
                prompt=prompt,
                image_format=image_format
            )

            return response.content.strip()

        except Exception as e:
            logger.error("Image description failed: %s", str(e))
            raise
