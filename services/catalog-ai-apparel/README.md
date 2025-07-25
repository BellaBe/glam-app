# ================================================================================================
# services/catalog-analysis/README.md
# ================================================================================================

# Catalog Analysis Service

AI-powered catalog item analysis and color extraction service for apparel using MediaPipe and computer vision.

## Overview

This service processes catalog item images to:
- Segment apparel items from background/person  
- Extract dominant color palettes from apparel regions
- Save analysis artifacts for review
- Publish results via event-driven architecture

The service maintains the **exact same output format** as the original API implementation:
```json
{
  "status": "success",
  "colours": [[255, 0, 0], [0, 255, 0], [0, 0, 255]],
  "latency_ms": 1250
}
```

## Features

- **MediaPipe Integration**: Uses Google's MediaPipe for accurate human/apparel segmentation
- **Color Analysis**: LAB color space analysis with chroma filtering to avoid grays
- **Event-Driven**: Consumes analysis requests and publishes results via NATS
- **Artifact Storage**: Saves visualization masks and cropped regions
- **Production Ready**: Comprehensive error handling, logging, and monitoring

## Event Contracts

### Input Events
**Subject**: `evt.catalog.item.analysis.requested`
```json
{
  "subject": "evt.catalog.item.analysis.requested",
  "payload": {
    "shop_id": "70931710194",
    "product_id": "8526062977266",
    "variant_id": "46547096469746"
  },
  "correlation_id": "unique-request-id"
}
```

### Output Events

**Success**: `evt.catalog.item.analysis.completed`
```json
{
  "subject": "evt.catalog.item.analysis.completed", 
  "payload": {
    "status": "success",
    "colours": [[255, 0, 0], [0, 255, 0], [0, 0, 255]],
    "latency_ms": 1250,
    "shop_id": "70931710194",
    "product_id": "8526062977266", 
    "variant_id": "46547096469746"
  },
  "correlation_id": "unique-request-id"
}
```

**Failure**: `evt.catalog.item.analysis.failed`
```json
{
  "subject": "evt.catalog.item.analysis.failed",
  "payload": {
    "status": "error",
    "error": "Product image not found",
    "latency_ms": 50,
    "shop_id": "70931710194",
    "product_id": "8526062977266",
    "variant_id": "46547096469746"
  },
  "correlation_id": "unique-request-id"
}
```

## Development

### Setup
```bash
# Install dependencies
make setup-dev

# Run tests
make test

# Start with Docker
make docker-run

# View logs
make docker-logs
```

### Testing
```bash
# Unit tests
pytest tests/unit/

# Integration tests  
pytest tests/integration/

# Manual testing
python scripts/test_catalog_analysis.py publish
python scripts/test_catalog_analysis.py listen
```

## Algorithm Details

### Apparel Segmentation Pipeline
1. **MediaPipe Processing**: Segments image into 6 classes (background, hair, body-skin, face-skin, clothes, other)
2. **Apparel Extraction**: Isolates clothing pixels (class 4) from other regions
3. **Bounding Box**: Finds tight bounds around apparel region
4. **Color Sampling**: Randomly samples up to 20,000 pixels from apparel area

### Color Analysis
1. **Color Space**: Converts BGR → RGB → LAB for perceptually uniform clustering
2. **K-Means Clustering**: Groups colors into 2×requested clusters
3. **Chroma Filtering**: Removes low-chroma colors (grays) using threshold
4. **Ranking**: Orders by cluster size, returns top N colors
5. **Format**: Converts back to RGB integers (0-255)

## Dependencies

### Core
- **mediapipe** (≥0.10.16): Human segmentation model
- **opencv-python**: Image processing and color space conversion
- **scikit-learn**: K-means clustering for color analysis
- **numpy**: Numerical operations

### Infrastructure  
- **shared**: Internal shared package for events, config, logging
- **nats-py**: Event streaming via NATS JetStream
- **redis**: Caching (optional)
- **pydantic**: Data validation and configuration

## Configuration

Service configuration follows the three-tier hierarchy:

### Service Configuration (config/services/catalog-analysis.yml)
```yaml
service:
  name: "catalog-analysis"
catalog_analysis:
  model_path: "services/cv_cloth/models/selfie_multiclass_256x256.tflite"
  products_base_path: "selfie/products" 
  default_colors: 5
  sample_size: 20000
  min_chroma: 8.0
```

### Environment Variables (.env)
```bash
# No database required for this service
REDIS_URL=redis://localhost:6379
NATS_URL=nats://localhost:4222

# Optional service secrets
CATALOG_ANALYSIS_API_KEY=your_api_key_here
```

## Performance

Typical processing times:
- **Small images** (< 500px): 200-500ms
- **Medium images** (500-1000px): 500-1000ms  
- **Large images** (> 1000px): 1000-2000ms

Memory usage scales with image size and color complexity.