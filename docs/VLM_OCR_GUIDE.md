# VLM-based OCR for Scanned PDFs

## Overview

PullData now supports **Vision Language Model (VLM) based OCR** for extracting text from scanned PDFs and images. This feature automatically detects when a PDF page has no text layer and uses a VLM to perform OCR.

## Features

✅ **Automatic Detection**: Detects scanned PDFs with minimal/no text layer  
✅ **LM Studio Integration**: Works with LM Studio running SmolVLM or other vision models  
✅ **Configurable**: Easily enable/disable and configure OCR settings  
✅ **Fallback Support**: Falls back to traditional text extraction for normal PDFs  
✅ **High Quality**: Uses vision models for better accuracy than traditional OCR  

## Quick Start

### 1. Start LM Studio with a Vision Model

1. Download **SmolVLM-500M-Instruct** (or another vision model)
2. Load the model in LM Studio
3. Start the server on `localhost:1234`

### 2. Use the OCR-Enabled Config

```bash
# Use the pre-configured OCR config
python -c "
from pulldata import PullData

pd = PullData(
    project='scanned_docs',
    config_path='configs/lm_studio_with_ocr.yaml'
)

# Ingest scanned PDFs - OCR will automatically run
pd.ingest('path/to/scanned_pdfs/*.pdf')

# Query as normal
result = pd.query('What is the main topic?')
print(result.llm_response.text)
"
```

### 3. Or Enable OCR in Your Config

```yaml
# your_config.yaml
parsing:
  pdf:
    ocr:
      enabled: true  # Enable VLM OCR
      base_url: http://localhost:1234/v1
      model: smolvlm-500m-instruct
      use_for_scanned_pdfs: true
      min_text_threshold: 50  # Min chars to consider PDF has text
```

## How It Works

1. **Text Extraction Attempt**: PullData first tries to extract text from PDF using PyMuPDF
2. **Detection**: If extracted text is below `min_text_threshold` (default: 50 chars), page is considered scanned
3. **OCR with VLM**: Page is rendered as an image and sent to VLM for text extraction
4. **Processing**: Extracted OCR text is used for chunking and embedding

```
PDF Page → Check Text Layer
    ├─→ Has Text (>50 chars) → Use PyMuPDF extraction
    └─→ No Text (<50 chars) → Render as Image → VLM OCR → Use OCR text
```

## Configuration Reference

```yaml
parsing:
  pdf:
    ocr:
      # Main Settings
      enabled: true                    # Enable/disable OCR
      provider: api                    # Only 'api' supported currently
      
      # VLM API Settings
      base_url: http://localhost:1234/v1
      api_key: sk-dummy
      model: smolvlm-500m-instruct
      timeout: 120                     # Longer timeout for VLM
      max_retries: 3
      
      # OCR Behavior
      use_for_scanned_pdfs: true       # Auto-detect scanned PDFs
      min_text_threshold: 50           # Min chars to trigger OCR
      ocr_prompt: "Extract all text from this image..."  # Custom prompt
```

## Supported Vision Models

| Model | Size | Performance | LM Studio Support |
|-------|------|-------------|-------------------|
| **SmolVLM-500M-Instruct** | 500MB | Fast, Good | ✅ Yes |
| LLaVA-1.5-7B | 7GB | Slower, Better | ✅ Yes |
| GPT-4 Vision (OpenAI) | API | Best | ✅ Yes (change base_url) |

### Using Different Models

**SmolVLM (Recommended for Local)**:
```yaml
model: smolvlm-500m-instruct
base_url: http://localhost:1234/v1
```

**GPT-4 Vision (OpenAI)**:
```yaml
model: gpt-4-vision-preview
base_url: https://api.openai.com/v1
api_key: sk-your-actual-openai-key
```

**LLaVA**:
```yaml
model: llava-v1.5-7b
base_url: http://localhost:1234/v1
```

## Example: Processing Scanned Documents

```python
from pulldata import PullData

# Initialize with OCR enabled
pd = PullData(
    project="medical_records",
    config_path="configs/lm_studio_with_ocr.yaml"
)

# Ingest scanned medical records
stats = pd.ingest("./scanned_records/*.pdf")
print(f"Processed {stats['processed_files']} files")
print(f"Created {stats['new_chunks']} chunks")

# Query the scanned documents
result = pd.query(
    "What medications were prescribed?",
    output_format="markdown"
)
```

## Performance Tips

1. **Batch Processing**: OCR is slower than text extraction (5-10s per page)
2. **Use Smaller Models**: SmolVLM is much faster than larger models
3. **Adjust Threshold**: Increase `min_text_threshold` if you have PDFs with minimal headers
4. **GPU Acceleration**: Run LM Studio on a machine with GPU for faster OCR

## Troubleshooting

### OCR Not Running

**Check if OCR is enabled:**
```python
from pulldata.core.config import load_config
config = load_config("configs/lm_studio_with_ocr.yaml")
print(f"OCR Enabled: {config.parsing.pdf.ocr.enabled}")
```

### VLM Connection Fails

**Test VLM connection:**
```python
from pulldata.vlm import VLMClient
from PIL import Image

vlm = VLMClient(
    model_name="smolvlm-500m-instruct",
    base_url="http://localhost:1234/v1"
)

# Test with a simple image
test_img = Image.new("RGB", (100, 100), color="white")
result = vlm.analyze_image(test_img, "What color is this?")
print(result)  # Should return something about "white"
```

### Check Which Pages Used OCR

OCR events are logged:
```
INFO: Using VLM OCR for page 3 (text layer too small)
INFO: Using VLM OCR for page 7 (text layer too small)
```

Enable DEBUG logging to see more details:
```yaml
logging:
  level: DEBUG
```

## API Reference

### VLMClient

```python
from pulldata.vlm import VLMClient

client = VLMClient(
    model_name="smolvlm-500m-instruct",
    base_url="http://localhost:1234/v1",
    api_key="sk-dummy",
    timeout=120,
)

# OCR a PDF page
text = client.ocr_pdf_page(page_image, page_number=1)

# General image analysis
result = client.analyze_image(
    image=my_image,
    prompt="Describe this image",
)
```

### Configuration

```python
from pulldata.core.config import VLMConfig

vlm_config = VLMConfig(
    enabled=True,
    model="smolvlm-500m-instruct",
    base_url="http://localhost:1234/v1",
    min_text_threshold=50,
)
```

## Cost Considerations

| Provider | Cost | Speed |
|----------|------|-------|
| **LM Studio (Local)** | Free | Fast (with GPU) |
| OpenAI GPT-4 Vision | $0.01-0.03/image | Very Fast |
| Self-hosted | Free | Hardware dependent |

**For production**: Consider using a local model (SmolVLM) to avoid API costs.

## Limitations

1. **Speed**: OCR is slower than text extraction (5-10s per page with VLM)
2. **Accuracy**: Depends on VLM model quality and image quality
3. **API Dependency**: Requires a running VLM server
4. **Memory**: Higher resolution images use more memory

## Future Enhancements

- [ ] Support for local VLM models (without API)
- [ ] Batch OCR processing for multiple pages
- [ ] OCR caching to avoid re-processing
- [ ] Support for more OCR backends (Tesseract, EasyOCR)
- [ ] Image preprocessing for better OCR quality

## See Also

- [LM Studio Documentation](https://lmstudio.ai/docs)
- [SmolVLM Model Card](https://huggingface.co/HuggingFaceTB/SmolVLM-500M-Instruct)
- [Configuration Guide](CONFIG_GUIDE.md)
- [PDF Parsing Documentation](docs/PDF_PARSING.md)

---

**Last Updated**: 2024-12-19  
**Version**: 0.2.0
