from app import http_app
from mangum import Mangum

handler = Mangum(http_app)
