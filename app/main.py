# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers – prefix and tags are now managed in the router files
from app.api.endpoints import wines, bucket_wines, country_stats, price_rating

# Create FastAPI app instance
app = FastAPI(
    root_path="/wt2",
    title="Wine API",
    description="API for wine data visualization",
    version="0.1.0",
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


# Optional: root endpoint for checking server status
@app.get("/")
def read_root():
    """Basic API health check."""
    return {"message": "Welcome to the Wine API"}
