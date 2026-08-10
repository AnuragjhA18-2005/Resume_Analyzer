from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware

from api.routes.analyze import router as analyze_router
from core.config import APP_NAME, APP_VERSION, DEFAULT_CORS_ORIGINS

app = FastAPI(title=APP_NAME, version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEFAULT_CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router, prefix="/api")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=APP_NAME,
        version=APP_VERSION,
        routes=app.routes,
    )

    analyze_post = openapi_schema.get("paths", {}).get("/api/analyze", {}).get("post", {})
    request_body = analyze_post.get("requestBody", {})
    multipart = request_body.get("content", {}).get("multipart/form-data", {})
    schema_ref = multipart.get("schema", {}).get("$ref")

    if schema_ref:
        schema_name = schema_ref.rsplit("/", 1)[-1]
        body_schema = openapi_schema.get("components", {}).get("schemas", {}).get(schema_name)
        if body_schema and "properties" in body_schema and "files" in body_schema["properties"]:
            body_schema["properties"]["files"] = {
                "title": "Files",
                "type": "array",
                "description": "Resume files to upload",
                "items": {
                    "type": "string",
                    "format": "binary",
                },
            }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
