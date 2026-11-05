import json
import logging

import azure.functions as func

from api import get_health, get_insights, get_recipes, get_clusters


app = func.FunctionApp(
    http_auth_level=func.AuthLevel.ANONYMOUS
)


def create_response(data, status_code=200):
    """Convert a Python dictionary into an HTTP JSON response."""

    return func.HttpResponse(
        json.dumps(data, allow_nan=False),
        status_code=status_code,
        mimetype="application/json",
        headers={"Cache-Control": "no-store"},
    )


def error_response(message, status_code):
    return create_response({"success": False, "error": message}, status_code)


def filter_params(req: func.HttpRequest) -> dict:
    """Query parameters every data endpoint accepts."""

    return {
        "diet": req.params.get("diet", "all"),
        "search": req.params.get("search", ""),
        "refresh": req.params.get("refresh", ""),
    }


def int_param(req: func.HttpRequest, *names, default: int) -> int:
    """Read the first present integer parameter (accepts camelCase or snake_case)."""

    for name in names:
        value = req.params.get(name)
        if value not in (None, ""):
            try:
                return int(value)
            except ValueError:
                raise ValueError(f"'{name}' must be a whole number.")
    return default


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return create_response(get_health())


@app.route(route="insights", methods=["GET"])
def insights(req: func.HttpRequest) -> func.HttpResponse:
    try:
        return create_response(get_insights(**filter_params(req)))

    except ValueError as error:
        return error_response(str(error), 400)

    except Exception:
        logging.exception("Unable to generate nutritional insights.")
        return error_response("Unable to generate nutritional insights.", 500)


@app.route(route="recipes", methods=["GET"])
def recipes(req: func.HttpRequest) -> func.HttpResponse:
    try:
        result = get_recipes(
            page=int_param(req, "page", default=1),
            page_size=int_param(req, "pageSize", "page_size", default=10),
            sort=req.params.get("sort", "protein"),
            order=req.params.get("order", "desc"),
            **filter_params(req),
        )
        return create_response(result)

    except ValueError as error:
        return error_response(str(error), 400)

    except Exception:
        logging.exception("Unable to retrieve recipes.")
        return error_response("Unable to retrieve recipes.", 500)


@app.route(route="clusters", methods=["GET"])
def clusters(req: func.HttpRequest) -> func.HttpResponse:
    try:
        result = get_clusters(
            k=int_param(req, "k", default=3),
            **filter_params(req),
        )
        return create_response(result)

    except ValueError as error:
        return error_response(str(error), 400)

    except Exception:
        logging.exception("Unable to generate nutritional clusters.")
        return error_response("Unable to generate nutritional clusters.", 500)
