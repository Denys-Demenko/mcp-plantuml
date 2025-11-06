import os
import sys
from pathlib import Path
from a2wsgi import ASGIMiddleware
import importlib

PROJECT = "/home/d0507002107/mcp-puml"
sys.path.insert(0, PROJECT)

from main import http_app

application = ASGIMiddleware(http_app.middleware_stack)
