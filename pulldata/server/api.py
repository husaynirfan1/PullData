"""FastAPI server for PullData.

Provides REST API endpoints for document ingestion and querying.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import tempfile
import shutil

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from pulldata import PullData
from pulldata.core.datatypes import QueryResult
from pulldata.synthesis import strip_reasoning_tags


# Pydantic models for request/response
class ProjectConfig(BaseModel):
    """Project configuration."""
    project: str = Field(..., description="Project name")
    config_path: Optional[str] = Field(None, description="Path to config file")


class IngestRequest(BaseModel):
    """Document ingestion request."""
    project: str = Field(..., description="Project name")
    source_path: str = Field(..., description="Path to document(s)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")
    config_path: Optional[str] = Field(None, description="Path to config YAML file (relative to configs/)")


class QueryRequest(BaseModel):
    """Query request."""
    project: str = Field(..., description="Project name")
    query: str = Field(..., description="Query text")
    k: Optional[int] = Field(5, description="Number of results to retrieve")
    generate_answer: bool = Field(True, description="Whether to generate LLM answer")
    output_format: Optional[str] = Field(None, description="Output format (excel, markdown, json, powerpoint, pdf, styled_pdf)")
    pdf_style: Optional[str] = Field("executive", description="PDF style for styled_pdf format (executive, modernist, academic)")
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")
    config_path: Optional[str] = Field(None, description="Path to config YAML file (relative to configs/)")


class QueryResponse(BaseModel):
    """Query response."""
    query: str
    answer: Optional[str] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    output_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    """Ingestion response."""
    success: bool
    stats: Dict[str, Any]
    message: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str


# Initialize FastAPI app
app = FastAPI(
    title="PullData API",
    description="REST API for PullData - RAG system with deliverable outputs",
    version="0.1.0",
)

# Enable CORS for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for Web UI
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/ui", StaticFiles(directory=str(static_dir), html=True), name="static")

# Store active PullData instances (in-memory for now)
# In production, use proper state management
active_projects: Dict[str, PullData] = {}


def get_or_create_project(project: str, config_path: Optional[str] = None) -> PullData:
    """Get existing project or create new one."""
    if project not in active_projects:
        active_projects[project] = PullData(
            project=project,
            config_path=config_path,
        )
    if project not in active_projects:
        active_projects[project] = PullData(
            project=project,
            config_path=config_path,
        )
    return active_projects[project]


# Configure logging
import logging
logger = logging.getLogger("uvicorn.error")

def load_existing_projects():
    """Load existing projects from data directory."""
    # Use absolute path based on CWD
    data_dir = Path.cwd() / "data"
    
    msg = f"Checking for projects in: {data_dir.absolute()}"
    logger.info(msg)
    print(msg) # Ensure visibility
    
    if not data_dir.exists():
        msg = f"Data directory not found at: {data_dir.absolute()}"
        logger.warning(msg)
        print(msg)
        return

    print("Loading existing projects...")
    logger.info("Loading existing projects...")
    count = 0
    for item in data_dir.iterdir():
        if item.is_dir():
            project_name = item.name
            try:
                # Check if it looks like a project (has metadata.db)
                if (item / "metadata.db").exists():
                    msg = f"  • Loading project: {project_name}"
                    logger.info(msg)
                    print(msg)
                    
                    if project_name not in active_projects:
                        active_projects[project_name] = PullData(project=project_name)
                        count += 1
                    else:
                        logger.info(f"    (Project '{project_name}' already active)")
            except Exception as e:
                msg = f"  ❌ Failed to load project {project_name}: {e}"
                logger.error(msg)
                print(msg)
                
    msg = f"Loaded {count} existing projects. Total active: {len(active_projects)}"
    logger.info(msg)
    print(msg)


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    try:
        load_existing_projects()
    except Exception as e:
        logger.error(f"Error during startup project loading: {e}")
        print(f"Error during startup project loading: {e}")


@app.get("/")
async def root():
    """Root endpoint with HTML response."""
    return HTMLResponse("""
    <html>
        <head>
            <title>PullData API</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                h1 { color: #667eea; }
                .btn { display: inline-block; padding: 12px 24px; background: #667eea; color: white;
                       text-decoration: none; border-radius: 5px; margin: 10px 5px; }
                .btn:hover { background: #5568d3; }
            </style>
        </head>
        <body>
            <h1>🔍 PullData API Server</h1>
            <p><strong>Version:</strong> 0.1.0</p>
            <p><strong>Status:</strong> Running</p>

            <h2>Quick Links</h2>
            <a href="/ui/" class="btn">📊 Web UI</a>
            <a href="/docs" class="btn">📚 API Documentation</a>
            <a href="/health" class="btn">💚 Health Check</a>

            <h2>API Endpoints</h2>
            <ul>
                <li><code>POST /ingest</code> - Ingest documents</li>
                <li><code>POST /ingest/upload</code> - Upload and ingest files</li>
                <li><code>POST /query</code> - Query documents</li>
                <li><code>GET /projects</code> - List projects</li>
                <li><code>GET /projects/{project}/stats</code> - Get project statistics</li>
                <li><code>GET /output/{project}/{filename}</code> - Download output files</li>
            </ul>

            <p>Visit <a href="/docs">/docs</a> for interactive API documentation.</p>
        </body>
    </html>
    """)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0"
    }


@app.get("/configs")
async def list_configs():
    """List available configuration files."""
    try:
        config_dir = Path("./configs")
        if not config_dir.exists():
            return {"configs": [], "count": 0}

        # Find all YAML config files
        config_files = []
        for config_file in config_dir.glob("*.yaml"):
            config_files.append({
                "name": config_file.stem,
                "path": str(config_file),
                "filename": config_file.name,
            })

        return {
            "configs": sorted(config_files, key=lambda x: x["name"]),
            "count": len(config_files)
        }
    except Exception as e:
        return {"configs": [], "count": 0, "error": str(e)}


@app.get("/projects")
async def list_projects():
    """List active projects."""
    return {
        "projects": list(active_projects.keys()),
        "count": len(active_projects)
    }


@app.get("/projects/{project}/stats")
async def get_project_stats(project: str):
    """Get statistics for a project."""
    if project not in active_projects:
        raise HTTPException(status_code=404, detail=f"Project '{project}' not found")

    pd = active_projects[project]
    stats = pd.get_stats()

    return {
        "project": project,
        "stats": stats
    }


@app.get("/projects/{project}/documents")
async def list_project_documents(
    project: str,
    limit: Optional[int] = None,
    offset: int = 0
):
    """List all documents in a project.
    
    Args:
        project: Project name
        limit: Maximum number of documents to return (default: all)
        offset: Number of documents to skip (default: 0)
    
    Returns:
        List of documents with their metadata
    """
    if project not in active_projects:
        raise HTTPException(status_code=404, detail=f"Project '{project}' not found")
    
    pd = active_projects[project]
    
    try:
        # Get documents from metadata store
        documents = pd._metadata_store.list_documents(limit=limit, offset=offset)
        
        return {
            "project": project,
            "documents": [
                {
                    "id": doc.id,
                    "source": doc.source_path,
                    "title": doc.filename,
                    "file_type": doc.doc_type.value if doc.doc_type else "unknown",
                    "ingested_at": doc.ingested_at.isoformat() if doc.ingested_at else None,
                    "page_count": doc.num_pages,
                    "metadata": doc.metadata
                }
                for doc in documents
            ],
            "count": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@app.post("/ingest", response_model=IngestResponse)
async def ingest_documents(request: IngestRequest):
    """Ingest documents into a project."""
    try:
        # Use config if provided
        pd = get_or_create_project(request.project, config_path=request.config_path)

        # Ingest documents
        stats = pd.ingest(
            source=request.source_path,
            metadata=request.metadata or {},
        )

        return {
            "success": True,
            "stats": stats,
            "message": f"Successfully ingested {stats.get('processed_files', 0)} files"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/upload", response_model=IngestResponse)
async def upload_and_ingest(
    project: str,
    files: List[UploadFile] = File(...),
    config_path: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
):
    """Upload and ingest files."""
    try:
        pd = get_or_create_project(project, config_path=config_path)

        # Create temp directory for uploads
        temp_dir = Path(tempfile.mkdtemp())

        try:
            # Save uploaded files
            saved_files = []
            for file in files:
                file_path = temp_dir / file.filename
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                saved_files.append(str(file_path))

            # Ingest all files
            all_stats = {
                "total_files": 0,
                "processed_files": 0,
                "failed_files": 0,
                "new_chunks": 0,
            }

            for file_path in saved_files:
                stats = pd.ingest(source=file_path)
                all_stats["total_files"] += 1
                all_stats["processed_files"] += stats.get("processed_files", 0)
                all_stats["failed_files"] += stats.get("failed_files", 0)
                all_stats["new_chunks"] += stats.get("new_chunks", 0)

            return {
                "success": True,
                "stats": all_stats,
                "message": f"Successfully ingested {all_stats['processed_files']} files"
            }

        finally:
            # Schedule cleanup
            if background_tasks:
                background_tasks.add_task(shutil.rmtree, temp_dir, ignore_errors=True)
            else:
                shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query documents in a project."""
    try:
        # If project doesn't exist, create with config if provided
        if request.project not in active_projects:
            if request.config_path:
                # Create project with config for query-only scenarios
                pd = get_or_create_project(request.project, config_path=request.config_path)
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Project '{request.project}' not found. Please ingest documents first."
                )

        pd = active_projects[request.project]

        # Execute query
        result = pd.query(
            query=request.query,
            k=request.k,
            filters=request.filters,
            generate_answer=request.generate_answer,
            output_format=request.output_format,
            pdf_style=request.pdf_style,  # Pass PDF style for styled_pdf format
        )

        # Convert to response format
        # Strip reasoning tags from answer
        answer_text = result.llm_response.text if result.llm_response else None
        if answer_text:
            answer_text = strip_reasoning_tags(answer_text)

        return {
            "query": result.query,
            "answer": answer_text,
            "sources": [
                {
                    "document_id": chunk.chunk.document_id,
                    "chunk_id": chunk.chunk.id,
                    "text": chunk.chunk.text,
                    "score": chunk.score,
                    "page_number": chunk.chunk.start_page,
                }
                for chunk in result.retrieved_chunks
            ],
            "output_path": result.output_path,
            "metadata": result.metadata or {},
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/output/{project}/{filename}")
async def download_output(project: str, filename: str):
    """Download generated output file."""
    output_path = Path("./output") / filename

    if not output_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=output_path,
        filename=filename,
        media_type="application/octet-stream"
    )


@app.delete("/projects/{project}")
async def delete_project(project: str):
    """Close and remove a project."""
    if project not in active_projects:
        raise HTTPException(status_code=404, detail=f"Project '{project}' not found")

    pd = active_projects[project]
    pd.close()
    del active_projects[project]

    return {
        "success": True,
        "message": f"Project '{project}' closed and removed"
    }


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    for pd in active_projects.values():
        pd.close()
    active_projects.clear()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
