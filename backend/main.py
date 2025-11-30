from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from app.database import init_db
from app.routers import emails, analysis, insights, oauth
from app.exceptions import MailMindException

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="Mail Mind API",
    description="Email Analysis and Classifier Tool",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler for structured errors
@app.exception_handler(MailMindException)
async def mailmind_exception_handler(request: Request, exc: MailMindException):
    """Handle MailMind exceptions with structured error format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code or "UNKNOWN_ERROR",
                "message": exc.detail,
                "metadata": exc.metadata
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    import traceback
    error_trace = traceback.format_exc()
    print(f"Unhandled exception: {exc}")
    print(error_trace)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"An unexpected error occurred: {str(exc)}",
                "metadata": {}
            }
        }
    )

# Routers
app.include_router(emails.router, prefix="/api/emails", tags=["emails"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(insights.router, prefix="/api/insights", tags=["insights"])
app.include_router(oauth.router, prefix="/api/oauth", tags=["oauth"])

@app.get("/")
async def root():
    return {"message": "Mail Mind API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

