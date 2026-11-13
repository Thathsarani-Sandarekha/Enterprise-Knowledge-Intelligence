
from fastapi import FastAPI
from pydantic import BaseModel

from app.routes.documents import router as documents_router
from app.routes.search import router as search_router
from app.routes.intelligence import router as intelligence_router

class HealthResponse(BaseModel):
    status: str
    service: str


def create_app() -> FastAPI:
    app = FastAPI(
        title="Enterprise Knowledge Intelligence API",
        description="Secure enterprise document search and RAG",
        version="0.1.0",
    )

    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["System"],
    )
    def health_check() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service="enterprise-knowledge-api",
        )

    app.include_router(documents_router)
    app.include_router(search_router)
    app.include_router(intelligence_router)

    return app


app = create_app()
