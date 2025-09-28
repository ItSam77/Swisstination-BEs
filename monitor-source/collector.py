import asyncio
import time
import logging
import psutil
import os
import sys
from typing import Optional

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to the path to import supabase_client
apps_path = os.path.join(os.path.dirname(__file__), '..', 'apps')
if not os.path.exists(apps_path):
    # Try Docker path structure
    apps_path = os.path.join(os.path.dirname(__file__), '..', 'app')
    if not os.path.exists(apps_path):
        # Try current directory (if running from apps directory)
        apps_path = os.path.dirname(__file__)

sys.path.insert(0, apps_path)

try:
    from supabase_client import supabase
    logger.info(f"✅ Supabase client imported successfully from {apps_path}")
except ImportError as e:
    logger.error(f"❌ Failed to import supabase_client: {e}")
    logger.error(f"📂 Tried path: {apps_path}")
    supabase = None

# Import metrics
from metrics import (
    active_users_total,
    destinations_total,
    reviews_total,
    user_preferences_total,
    categories_total,
    db_connections_total,
    memory_usage_bytes,
    update_app_uptime,
    record_error,
    record_db_query
)


class MetricsCollector:
    def __init__(self, refresh_interval: int = 30):
        """
        Initialize the metrics collector
        
        Args:
            refresh_interval: How often to refresh metrics in seconds
        """
        self.refresh_interval = refresh_interval
        self.start_time = time.time()
        self.is_running = False
        
    async def collect_user_metrics(self):
        """Collect user-related metrics from Supabase"""
        try:
            start_time = time.time()
            
            # Count total users
            result = supabase.table("custom_users").select("user_id", count="exact").execute()
            if result.data is not None:
                active_users_total.set(result.count or 0)
            
            # Count user preferences
            pref_result = supabase.table("preference").select("user_id", count="exact").execute()
            if pref_result.data is not None:
                user_preferences_total.set(pref_result.count or 0)
            
            duration = time.time() - start_time
            record_db_query("custom_users", "select", duration)
            record_db_query("preference", "select", duration)
            
            logger.info(f"Collected user metrics: {result.count or 0} users, {pref_result.count or 0} preferences")
            
        except Exception as e:
            logger.error(f"Error collecting user metrics: {e}")
            record_error("user_metrics_collection", "error")
    
    async def collect_destination_metrics(self):
        """Collect destination-related metrics from Supabase"""
        try:
            start_time = time.time()
            
            # Count total destinations
            dest_result = supabase.table("destinasi").select("destinasi_id", count="exact").execute()
            if dest_result.data is not None:
                destinations_total.set(dest_result.count or 0)
            
            # Count categories
            cat_result = supabase.table("category").select("kategori_id", count="exact").execute()
            if cat_result.data is not None:
                categories_total.set(cat_result.count or 0)
            
            duration = time.time() - start_time
            record_db_query("destinasi", "select", duration)
            record_db_query("category", "select", duration)
            
            logger.info(f"Collected destination metrics: {dest_result.count or 0} destinations, {cat_result.count or 0} categories")
            
        except Exception as e:
            logger.error(f"Error collecting destination metrics: {e}")
            record_error("destination_metrics_collection", "error")
    
    async def collect_review_metrics(self):
        """Collect review-related metrics from Supabase"""
        try:
            start_time = time.time()
            
            # Count total reviews/ratings
            review_result = supabase.table("ratings").select("rating_id", count="exact").execute()
            if review_result.data is not None:
                reviews_total.set(review_result.count or 0)
            
            duration = time.time() - start_time
            record_db_query("ratings", "select", duration)
            
            logger.info(f"Collected review metrics: {review_result.count or 0} reviews")
            
        except Exception as e:
            logger.error(f"Error collecting review metrics: {e}")
            record_error("review_metrics_collection", "error")
    
    async def collect_system_metrics(self):
        """Collect system-related metrics"""
        try:
            # Update memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_usage_bytes.set(memory_info.rss)
            
            # Update uptime
            update_app_uptime(self.start_time)
            
            # Simulate database connection count (you can implement actual connection pooling metrics)
            db_connections_total.set(1)  # For now, showing 1 active connection
            
            logger.info(f"Collected system metrics: {memory_info.rss} bytes memory")
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            record_error("system_metrics_collection", "error")
    
    async def collect_all_metrics(self):
        """Collect all metrics from various sources"""
        if supabase is None:
            logger.warning("Supabase client not available, skipping database metrics")
            await self.collect_system_metrics()
            return
        
        try:
            # Collect all metrics concurrently
            await asyncio.gather(
                self.collect_user_metrics(),
                self.collect_destination_metrics(),
                self.collect_review_metrics(),
                self.collect_system_metrics()
            )
            
        except Exception as e:
            logger.error(f"Error during metrics collection: {e}")
            record_error("metrics_collection", "critical")
    
    async def start_collection_loop(self):
        """Start the continuous metrics collection loop"""
        self.is_running = True
        logger.info(f"Starting metrics collection loop with {self.refresh_interval}s interval")
        
        while self.is_running:
            try:
                await self.collect_all_metrics()
                await asyncio.sleep(self.refresh_interval)
                
            except asyncio.CancelledError:
                logger.info("Metrics collection loop cancelled")
                break
            except Exception as e:
                logger.error(f"Unexpected error in collection loop: {e}")
                record_error("collection_loop", "critical")
                await asyncio.sleep(self.refresh_interval)
    
    def stop_collection(self):
        """Stop the metrics collection loop"""
        self.is_running = False
        logger.info("Stopping metrics collection loop")

# Global collector instance
collector_instance: Optional[MetricsCollector] = None

async def start_metrics_collector(refresh_interval: int = 30):
    """Start the metrics collector with specified refresh interval"""
    global collector_instance
    
    if collector_instance is not None:
        logger.warning("Metrics collector already running")
        return
    
    collector_instance = MetricsCollector(refresh_interval)
    
    # Start the collection loop as a background task
    asyncio.create_task(collector_instance.start_collection_loop())
    
    logger.info("Metrics collector started successfully")

def stop_metrics_collector():
    """Stop the metrics collector"""
    global collector_instance
    
    if collector_instance is not None:
        collector_instance.stop_collection()
        collector_instance = None
        logger.info("Metrics collector stopped")

# For testing purposes
async def collect_metrics_once():
    """Collect metrics once without starting the loop"""
    collector = MetricsCollector()
    await collector.collect_all_metrics()

if __name__ == "__main__":
    # Run collector for testing
    async def main():
        await collect_metrics_once()
    
    asyncio.run(main())
