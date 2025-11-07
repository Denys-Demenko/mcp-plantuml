from app import mcp_app
from mangum import Mangum

# Get the SSE Starlette app from MCP
sse_app = mcp_app.sse_app()
handler = Mangum(sse_app)
