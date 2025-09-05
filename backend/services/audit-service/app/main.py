"""
Main FastAPI application for audit service
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.integrations.jira import router as jira_router

app = FastAPI(
    title="Audit Service API",
    description="API for audit logging and integrations",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jira_router, prefix="/api/v1/integrations/jira", tags=["jira-integration"])

@app.get("/")
async def root():
    return {"message": "Audit Service API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
