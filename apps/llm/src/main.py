from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import travel_routes

app = FastAPI(
    title="Travel Gene LLM Service",
    description="LLM Service for Travel Gene application",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(travel_routes.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health_check():
    return {"status": 200}
