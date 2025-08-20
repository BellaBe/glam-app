# services/catalog-ai-analyzer/src/utils/image_downloader.py
import asyncio
from typing import Optional
import httpx
from shared.utils.logger import ServiceLogger
from shared.utils.exceptions import ValidationError, RequestTimeoutError, InfrastructureError

class ImageDownloader:
    """Utility for downloading and validating product images"""
    
    # Supported image formats
    SUPPORTED_FORMATS = {
        'image/jpeg', 'image/jpg', 'image/png', 
        'image/webp', 'image/gif', 'image/bmp'
    }
    
    # Maximum file size (10MB)
    MAX_SIZE_BYTES = 10 * 1024 * 1024
    
    def __init__(
        self, 
        timeout: int = 10,
        max_retries: int = 3,
        logger: Optional[ServiceLogger] = None
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logger
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=10)
        )
    
    async def download(self, url: str) -> bytes:
        """
        Download image with validation and retry logic
        
        Args:
            url: Image URL to download
            
        Returns:
            Image bytes
            
        Raises:
            ValidationError: Invalid URL or image format
            RequestTimeoutError: Download timeout
            InfrastructureError: Network/server errors
        """
        if not url or not url.startswith(('http://', 'https://')):
            raise ValidationError(
                message="Invalid image URL",
                field="image_url",
                value=url
            )
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                if self.logger:
                    self.logger.debug(f"Downloading image (attempt {attempt + 1}): {url}")
                
                # Make request
                response = await self.client.get(url)
                
                # Check status
                if response.status_code == 404:
                    raise ValidationError(
                        message=f"Image not found: {url}",
                        field="image_url",
                        value=url
                    )
                
                response.raise_for_status()
                
                # Validate content type
                content_type = response.headers.get('content-type', '').lower()
                if content_type and not any(fmt in content_type for fmt in self.SUPPORTED_FORMATS):
                    raise ValidationError(
                        message=f"Unsupported image format: {content_type}",
                        field="content_type",
                        value=content_type
                    )
                
                # Check size
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > self.MAX_SIZE_BYTES:
                    raise ValidationError(
                        message=f"Image too large: {int(content_length)} bytes (max {self.MAX_SIZE_BYTES})",
                        field="content_length",
                        value=content_length
                    )
                
                # Get content
                content = response.content
                
                # Validate actual size
                if len(content) > self.MAX_SIZE_BYTES:
                    raise ValidationError(
                        message=f"Image too large: {len(content)} bytes",
                        field="image_size",
                        value=len(content)
                    )
                
                # Validate it's actually an image (check magic bytes)
                if not self._validate_image_bytes(content):
                    raise ValidationError(
                        message="Invalid image data",
                        field="image_data"
                    )
                
                if self.logger:
                    self.logger.debug(f"Successfully downloaded {len(content)} bytes from {url}")
                
                return content
                
            except httpx.TimeoutException as e:
                last_error = RequestTimeoutError(
                    message=f"Image download timeout after {self.timeout}s",
                    timeout_seconds=self.timeout,
                    operation="image_download"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500:
                    last_error = InfrastructureError(
                        message=f"Server error downloading image: {e.response.status_code}",
                        service="image_server",
                        retryable=True
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                else:
                    raise ValidationError(
                        message=f"Failed to download image: HTTP {e.response.status_code}",
                        field="image_url",
                        value=url
                    )
                    
            except httpx.RequestError as e:
                last_error = InfrastructureError(
                    message=f"Network error downloading image: {str(e)}",
                    service="network",
                    retryable=True
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    
            except ValidationError:
                raise  # Don't retry validation errors
                
            except Exception as e:
                last_error = InfrastructureError(
                    message=f"Unexpected error downloading image: {str(e)}",
                    service="image_download"
                )
                if self.logger:
                    self.logger.error(f"Unexpected download error: {e}", exc_info=True)
                break
        
        # All retries exhausted
        if last_error:
            raise last_error
        
        raise InfrastructureError(
            message="Failed to download image after all retries",
            service="image_download"
        )
    
    def _validate_image_bytes(self, data: bytes) -> bool:
        """Validate image data by checking magic bytes"""
        if len(data) < 8:
            return False
        
        # Check common image format signatures
        signatures = {
            b'\xff\xd8\xff': 'jpeg',  # JPEG
            b'\x89PNG\r\n\x1a\n': 'png',  # PNG
            b'GIF87a': 'gif',  # GIF87a
            b'GIF89a': 'gif',  # GIF89a
            b'RIFF': 'webp',  # WebP (need more checks)
            b'BM': 'bmp',  # BMP
        }
        
        for signature, format_name in signatures.items():
            if data.startswith(signature):
                # Special case for WebP
                if format_name == 'webp' and len(data) > 12:
                    return data[8:12] == b'WEBP'
                return True
        
        return False
    
    async def download_batch(
        self, 
        urls: list[str], 
        max_concurrent: int = 5
    ) -> list[tuple[str, Optional[bytes], Optional[Exception]]]:
        """
        Download multiple images concurrently
        
        Returns:
            List of (url, image_bytes, error) tuples
        """
        results = []
        
        for chunk in self._chunk_urls(urls, max_concurrent):
            tasks = [self._download_safe(url) for url in chunk]
            chunk_results = await asyncio.gather(*tasks)
            results.extend(chunk_results)
        
        return results
    
    async def _download_safe(self, url: str) -> tuple[str, Optional[bytes], Optional[Exception]]:
        """Safe download that returns error instead of raising"""
        try:
            image_bytes = await self.download(url)
            return (url, image_bytes, None)
        except Exception as e:
            return (url, None, e)
    
    def _chunk_urls(self, urls: list[str], chunk_size: int):
        """Split URLs into chunks"""
        for i in range(0, len(urls), chunk_size):
            yield urls[i:i + chunk_size]
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()