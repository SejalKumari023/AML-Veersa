# Backend 2 - Image Authenticity Verification API

Backend service for comprehensive image authenticity verification, AI detection, tampering analysis, and reverse image search.

## Features

### 🔍 Authenticity Verification
Detect stolen images using reverse image search via **SerpAPI Google Reverse Image Search**. The system:
- Automatically uploads images to Imgur for public URL generation
- Performs web-wide reverse image search to find duplicate instances
- Identifies potential copyright infringement and stolen content
- Provides match confidence scores and source links
- Flags images as potentially stolen if found on other websites

**Integration:** SerpAPI Google Reverse Image Search API

### 🤖 AI-Generated Detection
Identify AI-generated or synthetic images using **Sightengine API**. The system:
- Analyzes images for AI generation indicators using advanced ML models
- Provides probability scores (0.0 - 1.0) for AI generation likelihood
- Detects common AI artifacts like:
  - Unnatural textures and patterns
  - Inconsistent lighting or shadows
  - Unusual artifacts or distortions
  - Over-perfect or uniform elements
  - Unnatural perspective or proportions
- High accuracy detection with 90%+ confidence for Sightengine results

**Integration:** Sightengine API (genai model)

### 🔎 Tampering Detection
Analyze metadata and pixel-level anomalies to detect image manipulation:
- **Metadata Analysis:**
  - EXIF data extraction and validation
  - GPS location verification
  - Camera information cross-checking
  - Timestamp consistency analysis
  - Software editing detection
  
- **Pixel-Level Analysis:**
  - Copy-move forgery detection
  - Splicing detection
  - Resampling detection
  - Compression artifacts analysis
  - Statistical anomaly detection

**Technologies:** PIL, scikit-image, OpenCV, EXIF analysis

### 🔬 Forensic Analysis
Deep inspection for manipulation indicators using multiple forensic techniques:
- Error Level Analysis (ELA)
- JPEG compression analysis
- Noise pattern analysis
- Color channel consistency checks
- Blocking artifact detection
- Manipulation probability scoring

**Technologies:** NumPy, scikit-image, image processing algorithms

## API Endpoints

### Image Upload
```
POST /api/images/upload
```
Upload an image for analysis. Returns image ID for subsequent verification.

### Image Analysis
```
GET /api/images/analysis/{image_id}
```
Get comprehensive analysis results for an uploaded image.

### Verify Authenticity
```
POST /api/images/verify/{image_id}
```
Perform complete authenticity verification including:
- AI generation detection
- Tampering detection
- Forensic analysis
- Metadata analysis

Returns authenticity score (0.0 - 1.0) with detailed findings.

### Reverse Image Search
```
POST /api/images/reverse-search/{image_id}?limit=10
```
Search for duplicate/stolen images on the web. Returns:
- Web matches with source URLs
- Match confidence scores
- Stolen image indicators
- Similarity rankings

## Configuration

### Required Environment Variables

#### SerpAPI (Reverse Image Search)
```bash
SERPAPI_API_KEY=your_serpapi_key
```
Get your key at: https://serpapi.com/

#### Sightengine (AI Detection)
```bash
SIGHTENGINE_API_USER=your_user_id
SIGHTENGINE_API_SECRET=your_secret
```
Get your credentials at: https://sightengine.com/

### Optional Configuration
```bash
GROQ_API_KEY=your_groq_key  # Optional, secondary AI detection
```

## Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
python app.py
```

Server runs on `http://0.0.0.0:8000` by default.

## Technical Stack

- **Framework:** FastAPI
- **Image Processing:** PIL, OpenCV, scikit-image
- **AI Detection:** Sightengine API
- **Reverse Search:** SerpAPI
- **Storage:** In-memory database (configurable)
- **File Storage:** Local disk storage

## Response Structure

### Verification Response
```json
{
  "authenticity_score": 0.85,
  "tampering_detected": false,
  "ai_generated_probability": 0.15,
  "metadata_analysis": {...},
  "pixel_analysis": {...},
  "forensic_analysis": {...},
  "ai_detection": {...}
}
```

### Reverse Search Response
```json
{
  "matches_found": 3,
  "similar_images": [...],
  "potentially_stolen": true,
  "stolen_confidence": 0.75,
  "stolen_indicators": [...],
  "web_search": {...}
}
```

## Notes

- Images are temporarily uploaded to Imgur for reverse image search (public URL required)
- All analyses run asynchronously for better performance
- Results are cached in the database for quick retrieval
- Multiple detection methods are combined for higher accuracy
