from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, preference, category, recommendation_router, destination, review

# For Monitoring
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import sys
import os

# Add monitor-source to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'monitor-source'))
from collector import start_metrics_collector, stop_metrics_collector

app = FastAPI(
    title="Swisstination API",
    description="Backend API for Swisstination application",
    version="1.0.0"
)

# For Monitoring - Set up instrumentator but don't expose yet
instrumentator = Instrumentator()
instrumentator.instrument(app)

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

# Startup and shutdown events for metrics collector
@app.on_event("startup")
async def startup_event():
    """Start metrics collection on application startup"""
    print("🔍 Starting metrics collector...")
    
    # Import metrics to register them with the default registry
    monitor_source_path = os.path.join(os.path.dirname(__file__), '..', 'monitor-source')
    print(f"📂 Looking for monitor-source at: {os.path.abspath(monitor_source_path)}")
    
    if os.path.exists(monitor_source_path):
        sys.path.insert(0, monitor_source_path)
        import metrics  # This registers all metrics with the default registry
        print("📊 Custom metrics module imported successfully")
        
        await start_metrics_collector(refresh_interval=30)
        print("✅ Metrics collector started")
    else:
        print("⚠️ monitor-source directory not found, metrics collector will not start")
        print("📊 Only FastAPI instrumentator metrics will be available")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop metrics collection on application shutdown"""
    print("🛑 Stopping metrics collector...")
    stop_metrics_collector()
    print("✅ Metrics collector stopped")

@app.get("/")
async def root():
    return {"message": "Welcome to Swisstination API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

@app.get("/metrics")
async def get_metrics():
    """Custom metrics endpoint that includes both instrumentator and custom metrics"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

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
