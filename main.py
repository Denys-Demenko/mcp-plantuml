# main.py
from typing import Annotated
import argparse
import threading

import httpx
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI, Body
from pydantic import BaseModel, AnyHttpUrl
from starlette.responses import StreamingResponse

from plant_uml import plantuml_url

# ---------- HTTP ----------
http_app = FastAPI(
    title="PlantUML Encoder",
    version="1.0.0",
    description="Encode PlantUML text into PlantUML/PlantText rendering URLs.",
    docs_url="/docs",         # Swagger UI
    redoc_url="/redoc",       # ReDoc UI
    openapi_url="/openapi.json"
)


class EncodeReq(BaseModel):
    text: str
    server_url: AnyHttpUrl | None = "https://uml.planttext.com/plantuml/png"


class EncodeRes(BaseModel):
    url: AnyHttpUrl


@http_app.get("/health")
def health():
    return {"status": "ok"}


@http_app.post("/png_url", response_model=EncodeRes)
def encode(req: EncodeReq):
    return {"url": plantuml_url(req.text, str(req.server_url))}


@http_app.post("/png_url_raw", response_model=EncodeRes)
def encode_raw(body: str = Body(..., media_type="text/plain")):
    return {"url": plantuml_url(body, "https://uml.planttext.com/plantuml/png")}


@http_app.post("/png", responses={200: {"content": {"image/png": {}}}})
def png_bytes(req: EncodeReq):
    url = plantuml_url(req.text, str(req.server_url))
    r = httpx.get(url)
    return StreamingResponse(iter([r.content]), media_type="image/png")


@http_app.post("/png_raw", responses={200: {"content": {"image/png": {}}}})
def png_bytes_raw(body: str = Body(..., media_type="text/plain")):
    url = plantuml_url(body, "https://uml.planttext.com/plantuml/png")
    r = httpx.get(url)
    return StreamingResponse(iter([r.content]), media_type="image/png")


def run_http(host: str, port: int):
    import asyncio
    import uvicorn

    config = uvicorn.Config(http_app, host=host, port=port, loop="asyncio", http="h11")
    server = uvicorn.Server(config)

    asyncio.run(server.serve())


# ---------- MCP ----------
mcp_app = FastMCP("plantuml-encoder")


def encode_plantuml(
        text: Annotated[str, "PlantUML source code"],
        server_url: Annotated[str, "PlantUML server URL"] = "https://uml.planttext.com/plantuml/png",
) -> Annotated[str, "PlantUML encoded URL"]:
    return plantuml_url(text, server_url)


mcp_app.add_tool(
    encode_plantuml,
    name="encode_plantuml",
    description="Encode PlantUML text into a PlantUML/PlantText URL."
)


def run_mcp_stdio():
    mcp_app.run("stdio")


def run_mcp_sse(host: str, port: int):
    mcp_app.run("sse")


# ---------- MAIN ----------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["http", "mcp-stdio", "mcp-sse", "both"], default="both")
    p.add_argument("--http-host", default="0.0.0.0")
    p.add_argument("--http-port", type=int, default=8111)
    p.add_argument("--mcp-host", default="0.0.0.0")
    p.add_argument("--mcp-port", type=int, default=9111)
    args = p.parse_args()

    if args.mode == "http":
        run_http(args.http_host, args.http_port)
    elif args.mode == "mcp-stdio":
        run_mcp_stdio()
    elif args.mode == "mcp-sse":
        run_mcp_sse(args.mcp_host, args.mcp_port)
    else:  # both = HTTP + MCP(TCP)
        t = threading.Thread(target=run_http, args=(args.http_host, args.http_port), daemon=True)
        t.start()
        run_mcp_stdio()


if __name__ == "__main__":
    main()
