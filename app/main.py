# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.api.endpoints import wines

# Create FastAPI application
app = FastAPI(
    title="Wine API",
    description="API for wine data visualization",
    version="0.1.0"
)

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(wines.router, prefix="/api/wines", tags=["wines"])

@app.get("/")
def read_root():
    """Root endpoint"""
    return {"message": "Welcome to the Wine API"}