"""
OpenAI multimodal client for vision and image processing.
Handles image analysis, DALL-E image generation, and multimodal interactions.
"""

import base64
import io
from typing import List, Dict, Any, Optional, Union
from PIL import Image

from .base_client import BaseOpenAIClient
from .data_mapper import OpenAIDataMapper
from shared.models.llm_response import LLMResponse


class OpenAIMultimodalClient(BaseOpenAIClient):
    """
    OpenAI client for multimodal tasks including vision and image generation.
    Supports GPT-4 Vision and DALL-E image generation.
    """

    def generate_from_image(
        self,
        image_data: bytes,
        prompt: str,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text description or analysis from an image.
        
        Args:
            image_data: Raw image bytes
            prompt: Text prompt describing what to analyze
            **kwargs: Additional parameters (model, max_tokens, etc.)
            
        Returns:
            Shared LLM response with image analysis
        """
        model = kwargs.get('model', 'gpt-4o')  # Default to vision-capable model
        
        self.logger.info(f"Analyzing image with model: {model}")
        
        # Validate model supports vision
        if not self._model_supports_vision(model):
            raise ValueError(f"Model {model} does not support vision capabilities")
        
        # Prepare image data
        image_format = kwargs.get('image_format', 'png')
        detail_level = kwargs.get('detail', 'auto')
        
        # Map request to OpenAI vision format
        openai_request = OpenAIDataMapper.map_image_request_to_openai(
            prompt=prompt,
            image_data=image_data,
            model=model,
            detail=detail_level,
            image_format=image_format,
            **kwargs
        )
        
        # Estimate tokens (vision requests use more tokens)
        estimated_tokens = self._estimate_vision_tokens(prompt, image_data, detail_level)
        if kwargs.get('max_tokens'):
            estimated_tokens += kwargs['max_tokens']
        
        # Generate cache key if caching is enabled
        cache_key = None
        if self.config.enable_response_cache and not kwargs.get('no_cache', False):
            # Include image hash in cache key for vision requests
            image_hash = str(hash(image_data))
            cache_key = f"vision:{model}:{hash(prompt)}:{image_hash}"
        
        self.logger.debug("Making vision API request")
        
        # Make API call
        try:
            response = self._make_api_call(
                api_method=self.client.chat.completions.create,
                request_data=openai_request,
                estimated_tokens=estimated_tokens,
                cache_key=cache_key
            )
        except Exception as e:
            self.logger.error(f"Vision analysis failed: {e}")
            raise
        
        # Convert response to shared format
        llm_response = OpenAIDataMapper.map_openai_response_to_llm_response(
            response,
            model,
            kwargs.get('request_id')
        )
        
        self.logger.info(
            f"Vision analysis completed: {llm_response.usage.total_tokens} tokens"
        )
        
        return llm_response

    def generate_from_multiple_images(
        self,
        images: List[bytes],
        prompt: str,
        **kwargs
    ) -> LLMResponse:
        """
        Analyze multiple images in a single request.
        
        Args:
            images: List of image byte arrays
            prompt: Text prompt for analysis
            **kwargs: Additional parameters
            
        Returns:
            Shared LLM response with multi-image analysis
        """
        model = kwargs.get('model', 'gpt-4o')
        
        self.logger.info(f"Analyzing {len(images)} images with model: {model}")
        
        if not self._model_supports_vision(model):
            raise ValueError(f"Model {model} does not support vision capabilities")
        
        # Build message content with multiple images
        content = [{'type': 'text', 'text': prompt}]
        
        for i, image_data in enumerate(images):
            image_format = kwargs.get('image_format', 'png')
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            content.append({
                'type': 'image_url',
                'image_url': {
                    'url': f'data:image/{image_format};base64,{image_base64}',
                    'detail': kwargs.get('detail', 'auto')
                }
            })
        
        # Create request
        openai_request = {
            'model': model,
            'messages': [{'role': 'user', 'content': content}],
            'max_tokens': kwargs.get('max_tokens', 1500),
            'temperature': kwargs.get('temperature', 0.7)
        }
        
        # Estimate tokens for multiple images
        estimated_tokens = sum(
            self._estimate_vision_tokens("", image_data, kwargs.get('detail', 'auto'))
            for image_data in images
        )
        estimated_tokens += self.estimate_tokens(prompt)
        if kwargs.get('max_tokens'):
            estimated_tokens += kwargs['max_tokens']
        
        self.logger.debug(f"Making multi-image vision request for {len(images)} images")
        
        # Make API call
        try:
            response = self._make_api_call(
                api_method=self.client.chat.completions.create,
                request_data=openai_request,
                estimated_tokens=estimated_tokens
            )
        except Exception as e:
            self.logger.error(f"Multi-image analysis failed: {e}")
            raise
        
        # Convert response
        llm_response = OpenAIDataMapper.map_openai_response_to_llm_response(
            response,
            model,
            kwargs.get('request_id')
        )
        
        self.logger.info(
            f"Multi-image analysis completed: {llm_response.usage.total_tokens} tokens"
        )
        
        return llm_response

    def generate_image(
        self,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate image using DALL-E.
        
        Args:
            prompt: Text description of image to generate
            **kwargs: Additional parameters (size, quality, style, etc.)
            
        Returns:
            Dictionary with image data and metadata
        """
        model = kwargs.get('model', 'dall-e-3')
        size = kwargs.get('size', '1024x1024')
        quality = kwargs.get('quality', 'standard')
        style = kwargs.get('style', 'vivid')
        n = kwargs.get('n', 1)
        
        self.logger.info(f"Generating image with {model}: {prompt[:50]}...")
        
        # Validate model
        if model not in ['dall-e-2', 'dall-e-3']:
            raise ValueError(f"Model {model} is not a valid DALL-E model")
        
        # Prepare request
        dalle_request = {
            'model': model,
            'prompt': prompt,
            'size': size,
            'n': n
        }
        
        # DALL-E 3 specific parameters
        if model == 'dall-e-3':
            dalle_request['quality'] = quality
            dalle_request['style'] = style
        
        # Response format
        response_format = kwargs.get('response_format', 'url')
        dalle_request['response_format'] = response_format
        
        self.logger.debug(f"Making DALL-E image generation request: {dalle_request}")
        
        # Make API call
        try:
            response = self._make_api_call(
                api_method=self.client.images.generate,
                request_data=dalle_request,
                estimated_tokens=0  # Image generation doesn't use completion tokens
            )
        except Exception as e:
            self.logger.error(f"Image generation failed: {e}")
            raise
        
        # Process response
        result = {
            'model': model,
            'prompt': prompt,
            'images': [],
            'created': response.get('created'),
            'provider': 'openai'
        }
        
        for image_data in response.get('data', []):
            image_info = {
                'url': image_data.get('url'),
                'b64_json': image_data.get('b64_json'),
                'revised_prompt': image_data.get('revised_prompt')
            }
            result['images'].append(image_info)
        
        # Calculate cost
        model_config = self.config.get_model_config(model)
        if model_config:
            cost_per_image = model_config.get('cost_per_image', 0)
            result['estimated_cost'] = cost_per_image * n
        
        self.logger.info(f"Image generation completed: {len(result['images'])} images")
        
        return result

    def edit_image(
        self,
        image_data: bytes,
        mask_data: Optional[bytes],
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Edit an existing image using DALL-E.
        
        Args:
            image_data: Original image bytes (PNG required)
            mask_data: Mask image bytes (optional)
            prompt: Description of desired edit
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with edited image data
        """
        self.logger.info(f"Editing image: {prompt[:50]}...")
        
        # Prepare files for upload
        files = {'image': ('image.png', image_data, 'image/png')}
        if mask_data:
            files['mask'] = ('mask.png', mask_data, 'image/png')
        
        # Prepare data
        edit_data = {
            'prompt': prompt,
            'n': kwargs.get('n', 1),
            'size': kwargs.get('size', '1024x1024'),
            'response_format': kwargs.get('response_format', 'url')
        }
        
        self.logger.debug("Making DALL-E image edit request")
        
        # Make API call (note: different method for edits)
        try:
            response = self.client.images.edit(**edit_data, **files)
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else dict(response)
        except Exception as e:
            self.logger.error(f"Image editing failed: {e}")
            raise
        
        # Process response
        result = {
            'prompt': prompt,
            'images': [],
            'created': response_dict.get('created'),
            'provider': 'openai',
            'operation': 'edit'
        }
        
        for image_data in response_dict.get('data', []):
            image_info = {
                'url': image_data.get('url'),
                'b64_json': image_data.get('b64_json')
            }
            result['images'].append(image_info)
        
        self.logger.info(f"Image editing completed: {len(result['images'])} images")
        
        return result

    def create_image_variation(
        self,
        image_data: bytes,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create variations of an existing image.
        
        Args:
            image_data: Original image bytes (PNG required)
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with image variations
        """
        self.logger.info("Creating image variations")
        
        # Prepare request
        variation_data = {
            'image': ('image.png', image_data, 'image/png'),
            'n': kwargs.get('n', 1),
            'size': kwargs.get('size', '1024x1024'),
            'response_format': kwargs.get('response_format', 'url')
        }
        
        self.logger.debug("Making DALL-E image variation request")
        
        # Make API call
        try:
            response = self.client.images.create_variation(**variation_data)
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else dict(response)
        except Exception as e:
            self.logger.error(f"Image variation creation failed: {e}")
            raise
        
        # Process response
        result = {
            'images': [],
            'created': response_dict.get('created'),
            'provider': 'openai',
            'operation': 'variation'
        }
        
        for image_data in response_dict.get('data', []):
            image_info = {
                'url': image_data.get('url'),
                'b64_json': image_data.get('b64_json')
            }
            result['images'].append(image_info)
        
        self.logger.info(f"Image variation creation completed: {len(result['images'])} images")
        
        return result

    def get_supported_image_formats(self) -> List[str]:
        """
        Get list of supported image formats.
        
        Returns:
            List of supported image format strings
        """
        return ['png', 'jpeg', 'jpg', 'webp', 'gif']

    def validate_image_data(self, image_data: bytes) -> Dict[str, Any]:
        """
        Validate image data and get metadata.
        
        Args:
            image_data: Image bytes to validate
            
        Returns:
            Dictionary with validation results and metadata
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            
            return {
                'valid': True,
                'format': image.format.lower() if image.format else 'unknown',
                'size': image.size,
                'mode': image.mode,
                'file_size_bytes': len(image_data),
                'supported': image.format.lower() in self.get_supported_image_formats()
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'file_size_bytes': len(image_data)
            }

    def _model_supports_vision(self, model: str) -> bool:
        """Check if model supports vision capabilities."""
        vision_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4-vision-preview']
        return model in vision_models

    def _estimate_vision_tokens(
        self,
        text_prompt: str,
        image_data: bytes,
        detail_level: str = 'auto'
    ) -> int:
        """
        Estimate tokens for vision request.
        
        Args:
            text_prompt: Text portion
            image_data: Image bytes
            detail_level: Detail level ('low', 'high', 'auto')
            
        Returns:
            Estimated token count
        """
        # Base text tokens
        text_tokens = self.estimate_tokens(text_prompt)
        
        # Image tokens depend on detail level and size
        try:
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            
            if detail_level == 'low':
                image_tokens = 85  # Fixed cost for low detail
            else:
                # High detail calculation
                # Scale to fit 2048x2048, then divide into 512x512 tiles
                scale = min(2048 / width, 2048 / height)
                scaled_width = int(width * scale)
                scaled_height = int(height * scale)
                
                tiles_x = (scaled_width + 511) // 512
                tiles_y = (scaled_height + 511) // 512
                num_tiles = tiles_x * tiles_y
                
                image_tokens = 85 + (170 * num_tiles)
            
        except Exception:
            # Fallback estimation
            image_tokens = 255  # Conservative estimate
        
        return text_tokens + image_tokens

    def get_vision_capabilities(self) -> Dict[str, Any]:
        """Get information about vision capabilities."""
        return {
            'supported_models': ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'],
            'supported_formats': self.get_supported_image_formats(),
            'max_images_per_request': 10,  # OpenAI limit
            'max_image_size_mb': 20,
            'detail_levels': ['low', 'high', 'auto'],
            'features': [
                'image_analysis',
                'text_extraction',
                'object_detection',
                'scene_description',
                'multi_image_comparison'
            ]
        }

    def get_image_generation_capabilities(self) -> Dict[str, Any]:
        """Get information about image generation capabilities."""
        return {
            'models': ['dall-e-2', 'dall-e-3'],
            'sizes': {
                'dall-e-2': ['256x256', '512x512', '1024x1024'],
                'dall-e-3': ['1024x1024', '1024x1792', '1792x1024']
            },
            'quality_levels': ['standard', 'hd'],  # DALL-E 3 only
            'style_options': ['vivid', 'natural'],  # DALL-E 3 only
            'max_images_per_request': {
                'dall-e-2': 10,
                'dall-e-3': 1
            },
            'features': [
                'text_to_image',
                'image_editing',
                'image_variations',
                'prompt_revision'
            ]
        }