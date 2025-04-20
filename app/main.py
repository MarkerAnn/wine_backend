from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from app.api.endpoints import wines, stats, bucket_wines  # Lägg till import för stats

# Create FastAPI application
app = FastAPI(
    title="Wine API", description="API for wine data visualization", version="0.1.0"
)

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    # allow_origins=origins,
    allow_origins=["http://localhost:5173"],  # eller ["*"] för att tillåta alla
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(wines.router, prefix="/api/wines", tags=["wines"])
app.include_router(stats.router, prefix="/api/stats", tags=["statistics"])
app.include_router(bucket_wines.router, prefix="/api/wines/bucket", tags=["wines"])


@app.get("/")
def read_root():
    """Root endpoint"""
    return {"message": "Welcome to the Wine API"}
