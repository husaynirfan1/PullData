# Web UI Support for Styled PDFs - Implementation Summary

## Overview

Styled PDF generation is now fully integrated into the PullData Web UI, allowing users to generate professional reports with 3 distinct visual styles directly from the browser.

---

## What Was Added

### 1. API Endpoint Updates

**File:** `pulldata/server/api.py`

#### QueryRequest Model
Added new parameter:
```python
pdf_style: Optional[str] = Field("executive",
    description="PDF style for styled_pdf format (executive, modernist, academic)")
```

#### Query Endpoint
Updated to pass `pdf_style` to the orchestrator:
```python
result = pd.query(
    query=request.query,
    k=request.k,
    filters=request.filters,
    generate_answer=request.generate_answer,
    output_format=request.output_format,
    pdf_style=request.pdf_style,  # NEW
)
```

### 2. Orchestrator Updates

**File:** `pulldata/pipeline/orchestrator.py`

#### Query Method Signature
```python
def query(
    self,
    query: str,
    k: Optional[int] = None,
    filters: Optional[Dict[str, Any]] = None,
    generate_answer: bool = True,
    output_format: Optional[Literal["excel", "markdown", "json", "powerpoint", "pdf", "styled_pdf"]] = None,
    pdf_style: Optional[Literal["executive", "modernist", "academic"]] = "executive",  # NEW
    **llm_kwargs,
) -> Union[QueryResult, OutputData]:
```

#### _get_formatter Method
Added support for `styled_pdf` format:
```python
def _get_formatter(
    self,
    format_type: str,
    pdf_style: Optional[str] = "executive",  # NEW
) -> OutputFormatter:
    # Handle styled_pdf format specially
    if format_type == "styled_pdf":
        from pulldata.synthesis.formatters.styled_pdf import StyledPDFFormatter
        return StyledPDFFormatter(style=pdf_style, llm=self._llm)
    # ... existing formats ...
```

### 3. Web UI HTML Updates

**File:** `pulldata/server/static/index.html`

#### Added Styled PDF Option
```html
<select id="outputFormat" class="input">
    <option value="">None (JSON only)</option>
    <option value="excel">Excel (.xlsx)</option>
    <option value="markdown">Markdown (.md)</option>
    <option value="json">JSON (.json)</option>
    <option value="powerpoint">PowerPoint (.pptx)</option>
    <option value="pdf">PDF (.pdf)</option>
    <option value="styled_pdf">Styled PDF (.pdf) ✨</option>  <!-- NEW -->
</select>
```

#### Added PDF Style Selector
```html
<div class="form-group" id="pdfStyleGroup" style="display: none;">
    <label for="pdfStyle">PDF Style:</label>
    <select id="pdfStyle" class="input">
        <option value="executive">Executive (Clean & Minimal)</option>
        <option value="modernist">Modernist (Bold & Impactful)</option>
        <option value="academic">Academic (Traditional & Formal)</option>
    </select>
    <small style="color: #999; display: block; margin-top: 4px;">
        Styled PDFs use LLM to structure content into professional reports
    </small>
</div>
```

### 4. Web UI JavaScript Updates

**File:** `pulldata/server/static/app.js`

#### Show/Hide Style Selector
```javascript
// Show/hide PDF style selector based on output format
elements.outputFormat.addEventListener('change', function() {
    const pdfStyleGroup = document.getElementById('pdfStyleGroup');
    if (this.value === 'styled_pdf') {
        pdfStyleGroup.style.display = 'block';
    } else {
        pdfStyleGroup.style.display = 'none';
    }
});
```

#### Include pdf_style in Request
```javascript
async function queryDocuments() {
    const pdfStyle = document.getElementById('pdfStyle').value;

    const requestBody = {
        project,
        query,
        k: 5,
        generate_answer: generateAnswer,
        output_format: outputFormat,
    };

    // Add pdf_style if styled_pdf format is selected
    if (outputFormat === 'styled_pdf') {
        requestBody.pdf_style = pdfStyle;
    }
    // ... rest of function ...
}
```

### 5. Documentation Updates

**File:** `docs/WEB_UI_GUIDE.md`

- Added **Styled PDF Reports** section
- Updated output format list
- Added visual style comparison table
- Added example workflow
- Added tips for style selection
- Updated REST API documentation with `pdf_style` parameter

---

## How to Use (Web UI)

### Step-by-Step

1. **Start the server**:
   ```bash
   python run_server.py
   ```

2. **Open Web UI**: http://localhost:8000/ui/

3. **Create/Select Project**

4. **Ingest Documents** (if not already done)

5. **Navigate to Query section**

6. **Enter your query**

7. **Select Output Format**: Choose "Styled PDF (.pdf) ✨"

8. **Choose PDF Style**:
   - **Executive** - Clean & minimal (best for executives)
   - **Modernist** - Bold & impactful (great for presentations)
   - **Academic** - Traditional & formal (ideal for research)

9. **Click "Query"**

10. **Download** the generated styled PDF from results

---

## How to Use (REST API)

### Endpoint

**POST** `http://localhost:8000/query`

### Request Body

```json
{
  "project": "my_project",
  "query": "What are the key findings from Q3?",
  "generate_answer": true,
  "output_format": "styled_pdf",
  "pdf_style": "executive"
}
```

### Parameters

- `output_format`: Set to `"styled_pdf"`
- `pdf_style`: Choose from `"executive"`, `"modernist"`, or `"academic"` (default: `"executive"`)

### Example with cURL

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "project": "financial_reports",
    "query": "Summarize Q3 2024 performance",
    "output_format": "styled_pdf",
    "pdf_style": "modernist"
  }'
```

### Response

```json
{
  "query": "Summarize Q3 2024 performance",
  "answer": "Q3 2024 showed strong performance...",
  "sources": [...],
  "output_path": "./output/financial_reports_query_1234567890.pdf",
  "metadata": {}
}
```

---

## Visual Style Examples

### Executive Style
- **Design**: Clean, minimalist
- **Colors**: Blue (#0ea5e9) and grey
- **Layout**: Single column with generous whitespace
- **Metrics**: 3-column grid with cards
- **Best for**: Board presentations, executive summaries

### Modernist Style
- **Design**: Bold, high contrast
- **Colors**: Orange (#f59e0b), red (#ef4444), dark navy
- **Layout**: Asymmetric with bold typography
- **Metrics**: 2-column colored blocks
- **Best for**: Marketing materials, innovation reports

### Academic Style
- **Design**: Traditional, scholarly
- **Colors**: Black text, minimal color
- **Layout**: Two-column body text
- **Metrics**: Table format
- **Best for**: Research papers, white papers, technical docs

---

## Features

✅ **LLM-Powered Structuring**: Automatically organizes content into:
- Title and summary
- Key metrics extraction
- Logical sections with headings
- Source citations

✅ **Three Visual Styles**: Choose the best style for your audience

✅ **Web UI Integration**: Easy selection via dropdowns

✅ **REST API Support**: Programmatic access

✅ **Markdown Support**: Content can include markdown formatting

✅ **Page Break Control**: Intelligent pagination

✅ **Source Citations**: Automatic reference list generation

---

## Requirements

- **LLM Configuration**: Styled PDFs require an LLM to be configured
  - Works with: OpenAI, LM Studio, Ollama, Groq, etc.
  - Configured in `configs/default.yaml` or custom config

- **Dependencies**:
  ```bash
  pip install weasyprint jinja2 markdown2
  ```

---

## Testing

### Quick Test

1. Ingest a sample document
2. Query it with styled PDF output
3. Try all 3 styles to compare
4. Download and review the PDFs

### Example Query

```
Project: financial_reports
Query: "What were the main highlights of Q3 2024?"
Format: Styled PDF
Style: Executive
```

Expected result: A professional PDF report with:
- Title: "Q3 2024 Highlights"
- Summary paragraph
- Key metrics (if present in data)
- Organized findings
- Source references

---

## Troubleshooting

### Style Selector Not Showing

**Issue**: PDF style dropdown doesn't appear when selecting "Styled PDF"

**Solution**:
- Clear browser cache
- Hard refresh (Ctrl+F5)
- Check browser console for JavaScript errors

### PDF Generation Fails

**Issue**: Error when generating styled PDF

**Common causes**:
1. **No LLM configured**: Check `configs/default.yaml`
2. **WeasyPrint not installed**: Run `pip install weasyprint`
3. **LLM structuring fails**: Check LLM temperature and model capability

### Empty PDF or Missing Content

**Issue**: PDF generates but has minimal content

**Solution**:
- Ensure `generate_answer` is set to `true`
- Check that documents were properly ingested
- Verify k value is sufficient (default: 5)

---

## Files Modified

1. `pulldata/server/api.py` - Added pdf_style parameter
2. `pulldata/pipeline/orchestrator.py` - Updated query method and _get_formatter
3. `pulldata/server/static/index.html` - Added styled PDF option and style selector
4. `pulldata/server/static/app.js` - Added show/hide logic and pdf_style handling
5. `docs/WEB_UI_GUIDE.md` - Added styled PDF documentation

---

## Next Steps

### Optional Enhancements

1. **Preview Mode**: Add PDF preview in Web UI
2. **Style Customization**: Allow users to modify CSS
3. **Template Library**: Pre-built templates for common use cases
4. **Batch Generation**: Generate multiple PDFs at once
5. **Custom Fonts**: User-uploaded fonts
6. **Cover Pages**: Customizable cover page templates

---

## Support

- **Documentation**: `docs/STYLED_PDF_GUIDE.md`
- **Examples**: `examples/styled_pdf_example.py`
- **Web UI Guide**: `docs/WEB_UI_GUIDE.md`

---

**Status**: ✅ Complete and ready for use

**Created**: 2024-12-18

**Version**: 1.0
