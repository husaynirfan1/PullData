"""Launch PullData API Server with Web UI.

Usage:
    python run_server.py

The server will start on http://localhost:8000
- Web UI: http://localhost:8000/ui/
- API Docs: http://localhost:8000/docs
"""

import uvicorn
from pulldata.server import app


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting PullData API Server")
    print("=" * 60)
    print()
    print("Server will start on: http://localhost:8000")
    print()
    print("Quick Links:")
    print("  • Web UI:    http://localhost:8000/ui/")
    print("  • API Docs:  http://localhost:8000/docs")
    print("  • Health:    http://localhost:8000/health")
    print()
    print("Press CTRL+C to stop the server")
    print("=" * 60)
    print()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
