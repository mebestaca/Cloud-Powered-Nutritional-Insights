
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
    )


@app.route(
    route="health",
    methods=["GET"]
)
def health(req: func.HttpRequest) -> func.HttpResponse:
    return create_response(get_health())


@app.route(
    route="insights",
    methods=["GET"]
)
def insights(req: func.HttpRequest) -> func.HttpResponse:

    try:
        result = get_insights()
        return create_response(result)

    except Exception:
        logging.exception("Unable to generate nutritional insights.")

        return create_response(
            {
                "success": False,
                "error": "Unable to generate nutritional insights.",
            },
            500,
        )


@app.route(
    route="recipes",
    methods=["GET"]
)
def recipes(req: func.HttpRequest) -> func.HttpResponse:

    try:
        page = int(req.params.get("page", "1"))
        page_size = int(req.params.get("page_size", "10"))

        result = get_recipes(
            page=page,
            page_size=page_size,
        )

        return create_response(result)

    except ValueError as error:
        return create_response(
            {
                "success": False,
                "error": str(error),
            },
            400,
        )

    except Exception:
        logging.exception("Unable to retrieve recipes.")

        return create_response(
            {
                "success": False,
                "error": "Unable to retrieve recipes.",
            },
            500,
        )

@app.route(
    route="clusters",
    methods=["GET"]
)
def clusters(req: func.HttpRequest) -> func.HttpResponse:

    try:
        k = int(req.params.get("k", "3"))
        diet = req.params.get("diet", "all")
        search = req.params.get("search", "")

        result = get_clusters(
            k=k,
            diet=diet,
            search=search
        )

        return create_response(result)

    except ValueError as error:
        return create_response(
            {
                "success": False,
                "error": str(error),
            },
            400,
        )

    except Exception:
        logging.exception("Unable to generate nutritional clusters.")

        return create_response(
            {
                "success": False,
                "error": "Unable to generate nutritional clusters.",
            },
            500,
        )