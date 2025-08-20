# services/catalog-analysis/src/services/catalog_analysis_service.py
import time
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from sklearn.cluster import KMeans

from shared.utils.logger import ServiceLogger

from ..config import ServiceConfig
from ..schemas.catalog_item import CatalogItemAnalysisRequest, CatalogItemAnalysisResult


class CatalogAnalysisService:
    """Core business logic for catalog item apparel analysis and color extraction"""

    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        self._segmenter = None

        # Validate model file exists
        model_path = Path(config.model_path)
        if not model_path.is_file():
            raise SystemExit(f"❌ Model file missing at {model_path}")

    async def analyze_catalog_item(self, request: CatalogItemAnalysisRequest) -> CatalogItemAnalysisResult:
        """Main catalog item analysis pipeline for apparel color extraction"""
        t0 = time.perf_counter()

        try:
            self.logger.info(f"Analyzing catalog item {request.shop_id}/{request.product_id}/{request.variant_id}")

            # Build file paths
            variant_dir = (
                Path(self.config.products_base_path) / request.shop_id / request.product_id / request.variant_id
            )
            product_path = variant_dir / "product.png"
            analysis_dir = variant_dir / self.config.analysis_dir_name
            analysis_dir.mkdir(parents=True, exist_ok=True)

            # Validate input file exists
            if not product_path.exists():
                raise FileNotFoundError(f"{product_path} not found - upstream step missing?")

            # Load and validate image
            image = cv2.imread(str(product_path))
            if image is None:
                raise ValueError("Unable to read image (corrupt or unsupported format)")

            # Perform apparel segmentation
            coloured_mask, apparel_mask, apparel_crop, bound_crop, bound_mask = self._segment_apparel(image)

            if bound_crop is None or bound_mask is None:
                self.logger.warning("No apparel detected in catalog item")
                return CatalogItemAnalysisResult(
                    status="success",  # Keep original behavior: return success with empty colours
                    colours=[],
                    latency_ms=int((time.perf_counter() - t0) * 1000),
                    shop_id=request.shop_id,
                    product_id=request.product_id,
                    variant_id=request.variant_id,
                )

            # Extract apparel color palette
            dominant_colours = self._extract_apparel_palette_lab(
                mask=bound_mask,
                image=bound_crop,
                n_colors=self.config.default_colors,
                sample_size=self.config.sample_size,
                min_chroma=self.config.min_chroma,
            )

            # Save analysis artifacts
            cv2.imwrite(str(analysis_dir / "colored_mask.png"), coloured_mask)
            cv2.imwrite(str(analysis_dir / "clothes_crop.png"), apparel_crop)
            cv2.imwrite(str(analysis_dir / "clothes_crop_bound.png"), bound_crop)

            latency = int((time.perf_counter() - t0) * 1000)

            self.logger.info(
                f"Catalog item analysis completed successfully in {latency}ms, found {len(dominant_colours)} colors"
            )

            return CatalogItemAnalysisResult(
                status="success",
                colours=dominant_colours,
                latency_ms=latency,
                shop_id=request.shop_id,
                product_id=request.product_id,
                variant_id=request.variant_id,
            )

        except Exception as e:
            latency = int((time.perf_counter() - t0) * 1000)
            self.logger.error(f"Catalog item analysis failed: {e!s}", exc_info=True)

            return CatalogItemAnalysisResult(
                status="error",
                colours=None,
                latency_ms=latency,
                error=str(e),
                shop_id=request.shop_id,
                product_id=request.product_id,
                variant_id=request.variant_id,
            )

    def _get_segmenter(self):
        """Create the ImageSegmenter once - tailored for mediapipe 0.10.21."""
        if self._segmenter is not None:
            return self._segmenter

        from mediapipe.tasks.python.core.base_options import BaseOptions
        from mediapipe.tasks.python.vision.image_segmenter import (
            ImageSegmenter,
            ImageSegmenterOptions,
            _RunningMode,
        )

        self.logger.info(f"Creating ImageSegmenter with model path: {self.config.model_path}")

        opts = ImageSegmenterOptions(
            base_options=BaseOptions(model_asset_path=str(self.config.model_path)),
            running_mode=_RunningMode.IMAGE,
            output_category_mask=True,
        )
        self._segmenter = ImageSegmenter.create_from_options(opts)
        return self._segmenter

    def _make_colour_mask(self, segment_mask: np.ndarray):
        """Create colored visualization mask for catalog item analysis"""
        lut = np.zeros((256, 1, 3), dtype=np.uint8)
        lut[0] = (0, 0, 0)  # bg
        lut[1] = (255, 255, 0)  # hair
        lut[2] = (255, 0, 0)  # body-skin
        lut[3] = (0, 0, 255)  # face-skin
        lut[4] = (0, 255, 0)  # apparel/clothes
        lut[5] = (255, 0, 255)  # other
        return cv2.applyColorMap(segment_mask, lut)

    def _segment_apparel(
        self, image: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray | None, np.ndarray | None, np.ndarray | None]:
        """
        Run Mediapipe segmentation and extract apparel regions from catalog item.

        Returns:
            coloured_mask: HxWx3 BGR viz of all classes
            apparel_mask: HxW uint8 binary mask (255=apparel, 0=other)
            apparel_crop: HxWx3 BGR image where only apparel pixels survive
            bound_crop: H'xW'x3 BGR tight crop of apparel region
            bound_mask: H'xW' uint8 tight crop of binary mask
        """
        # Get segmenter
        segmenter = self._get_segmenter()

        # Wrap NumPy BGR in an mp.Image
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)

        # Run segmentation
        result = segmenter.segment(mp_img)
        class_mask = result.category_mask.numpy_view()  # HxW, values 0-5

        # Build binary apparel mask (class 4 = clothes/apparel)
        apparel_mask = np.where(class_mask == 4, 255, 0).astype(np.uint8)

        # Coloured viz mask (for debugging)
        coloured_mask = self._make_colour_mask(class_mask)

        # Raw crop: zero out non-apparel pixels
        apparel_crop = cv2.bitwise_and(image, image, mask=apparel_mask)

        # Find tight bounding box on the apparel region
        ys, xs = np.where(apparel_mask == 255)
        if xs.size == 0 or ys.size == 0:
            # No apparel detected in catalog item
            return coloured_mask, apparel_mask, None, None, None

        x0, x1 = xs.min(), xs.max() + 1
        y0, y1 = ys.min(), ys.max() + 1

        # Tight crops
        bound_crop = apparel_crop[y0:y1, x0:x1]
        bound_mask = apparel_mask[y0:y1, x0:x1]

        return coloured_mask, apparel_mask, apparel_crop, bound_crop, bound_mask

    def _extract_apparel_palette_lab(
        self,
        mask: np.ndarray,
        image: np.ndarray,
        n_colors: int = 5,
        sample_size: int = 20000,
        min_chroma: float = 5.0,
    ) -> list[list[int]]:
        """
        Extract color palette from apparel region in catalog item using LAB color space.

        Args:
            mask: HxW uint8 mask (255 = apparel, 0 = other)
            image: HxWx3 BGR image
            n_colors: Number of colors to extract
            sample_size: Maximum number of pixels to sample
            min_chroma: Minimum chroma threshold to filter grays

        Returns:
            List of [R,G,B] color values (0-255) representing dominant apparel colors
        """
        # Grab only the apparel-masked pixels
        coords = np.where(mask == 255)
        pixels = image[coords]  # NNx3 BGR

        if len(pixels) == 0:
            return []

        # Sample down if too many pixels
        if len(pixels) > sample_size:
            idx = np.random.choice(len(pixels), sample_size, replace=False)
            pixels = pixels[idx]

        # Convert BGR→RGB→Lab
        pixels_rgb = pixels[:, ::-1]
        pixels_lab = cv2.cvtColor(pixels_rgb.reshape(-1, 1, 3), cv2.COLOR_RGB2LAB).reshape(-1, 3)

        # K-Means clustering in Lab space
        km = KMeans(n_clusters=n_colors * 2, n_init=8, random_state=0)
        labels = km.fit_predict(pixels_lab)
        centers_lab = km.cluster_centers_

        # Compute counts & chroma, filter out low-chroma (near-gray)
        counts = np.bincount(labels)
        chroma = np.linalg.norm(centers_lab[:, 1:], axis=1)  # sqrt(a^2 + b^2)
        keep = [i for i in np.argsort(-counts) if chroma[i] >= min_chroma]

        # Take top n_colors valid clusters
        chosen = keep[:n_colors]
        palette_rgb = []
        for i in chosen:
            # Convert Lab center back to RGB
            lab = np.uint8(centers_lab[i].reshape(1, 1, 3))
            rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB).reshape(
                3,
            )
            palette_rgb.append([int(c) for c in rgb])

        return palette_rgb
