
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from api import get_health, get_insights, get_recipes


class APIHandler(BaseHTTPRequestHandler):

    def send_json(self, data, status_code=200):

        response = json.dumps(
            data,
            allow_nan=False
        ).encode("utf-8")

        self.send_response(status_code)

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(response))
        )

        self.end_headers()
        self.wfile.write(response)

    def do_GET(self):

        parsed_url = urlparse(self.path)
        route = parsed_url.path.rstrip("/")

        params = parse_qs(parsed_url.query)

        try:

            if route == "/api/health":

                self.send_json(get_health())
                return

            if route == "/api/insights":

                self.send_json(get_insights())
                return

            if route == "/api/recipes":

                page = int(params.get("page", ["1"])[0])

                page_size = int(
                    params.get("page_size", ["10"])[0]
                )

                result = get_recipes(
                    page=page,
                    page_size=page_size
                )

                self.send_json(result)
                return

            self.send_json(
                {"error": "Endpoint not found."},
                404
            )

        except ValueError as error:

            self.send_json(
                {"error": str(error)},
                400
            )

        except Exception:

            self.send_json(
                {"error": "Internal server error."},
                500
            )


if __name__ == "__main__":

    server = HTTPServer(
        ("127.0.0.1", 7071),
        APIHandler
    )

    print("Nutritional Insights API running.")
    print("Address: http://127.0.0.1:7071")

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print("\nStopping development server.")

    finally:
        server.server_close()
