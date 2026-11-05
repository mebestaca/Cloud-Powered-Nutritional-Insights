"""
Tiny local stand-in for the Function App, for when `func start` isn't handy.

    python dev_server.py

Serves the same routes on http://localhost:7071/api/... and allows any
origin (CORS), so `npm run dev` in ../frontend can call it directly.
Reads Blob Storage settings from the environment, or set
LOCAL_DATASET_PATH=../phase1_reference/All_Diets.csv to work offline.
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from api import get_clusters, get_health, get_insights, get_recipes


def _int(params, *names, default):
    for name in names:
        if name in params and params[name] != "":
            try:
                return int(params[name])
            except ValueError:
                raise ValueError(f"'{name}' must be a whole number.")
    return default


class APIHandler(BaseHTTPRequestHandler):

    def send_json(self, data, status_code=200):
        body = json.dumps(data, allow_nan=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        route = url.path.rstrip("/")
        params = {k: v[0] for k, v in parse_qs(url.query).items()}
        filters = {
            "diet": params.get("diet", "all"),
            "search": params.get("search", ""),
            "refresh": params.get("refresh", ""),
        }

        try:
            if route == "/api/health":
                return self.send_json(get_health())

            if route == "/api/insights":
                return self.send_json(get_insights(**filters))

            if route == "/api/recipes":
                return self.send_json(get_recipes(
                    page=_int(params, "page", default=1),
                    page_size=_int(params, "pageSize", "page_size", default=10),
                    sort=params.get("sort", "protein"),
                    order=params.get("order", "desc"),
                    **filters,
                ))

            if route == "/api/clusters":
                return self.send_json(get_clusters(k=_int(params, "k", default=3), **filters))

            self.send_json({"success": False, "error": "Endpoint not found."}, 404)

        except ValueError as error:
            self.send_json({"success": False, "error": str(error)}, 400)

        except Exception as error:
            print(f"Error on {self.path}: {error!r}")
            self.send_json({"success": False, "error": "Internal server error."}, 500)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 7071), APIHandler)
    print("Nutritional Insights API running at http://127.0.0.1:7071/api")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping development server.")
    finally:
        server.server_close()
