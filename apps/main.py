from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, preference, category, recommendation_router, destination, review

# For Monitoring
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    title="Swisstination API",
    description="Backend API for Swisstination application",
    version="1.0.0"
)

# For Monitoring
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(preference.router)
app.include_router(category.router)
app.include_router(recommendation_router.router)
app.include_router(destination.router)
app.include_router(review.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Swisstination API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Swisstination Backend Server...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
