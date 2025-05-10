import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Import routers – prefix and tags are now managed in the router files
from app.api.endpoints import wines, bucket_wines, country_stats, price_rating, search_rag

# Create FastAPI app instance
app = FastAPI(
    root_path="/wt2",
    title="Wine API",
    description="API for wine data visualization",
    version="0.1.0",
)

# Exception handler for ValueError – used for business logic errors
@app.exception_handler(ValueError)
async def value_error_handler(
    request: Request,  # pylint: disable=unused-argument
    exc: ValueError
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )

# Exception handler for unexpected errors (500 Internal Server Error)
@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,  # pylint: disable=unused-argument
    exc: Exception
) -> JSONResponse:
    logging.error("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


# Enable CORS so frontend (e.g., Vite on port 5173) can access the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust for your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers – all of them now manage their own prefix and tags
app.include_router(wines.router)
app.include_router(bucket_wines.router)
app.include_router(country_stats.router)
app.include_router(price_rating.router)
app.include_router(search_rag.router)


# Optional: root endpoint for checking server status
@app.get("/")
def read_root():
    """Basic API health check."""
    return {"message": "Welcome to the Wine API"}
