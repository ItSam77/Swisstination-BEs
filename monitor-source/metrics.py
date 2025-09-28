from prometheus_client import Gauge, Counter, Histogram
import time

# Database metrics
db_connections_total = Gauge(
    'db_connections_total',
    'Total number of database connections'
)

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Time spent on database queries',
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

db_queries_total = Counter(
    'db_queries_total',
    'Total number of database queries',
    ['table', 'operation']
)

# Application metrics
active_users_total = Gauge(
    'active_users_total',
    'Total number of active users'
)

destinations_total = Gauge(
    'destinations_total',
    'Total number of destinations in database'
)

reviews_total = Gauge(
    'reviews_total',
    'Total number of reviews in database'
)

recommendations_generated = Counter(
    'recommendations_generated_total',
    'Total number of recommendations generated',
    ['user_id']
)

# API metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status_code']
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'Time spent processing API requests',
    ['method', 'endpoint'],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Authentication metrics
login_attempts_total = Counter(
    'login_attempts_total',
    'Total number of login attempts',
    ['status']
)

signup_attempts_total = Counter(
    'signup_attempts_total',
    'Total number of signup attempts',
    ['status']
)

# System metrics
app_uptime_seconds = Gauge(
    'app_uptime_seconds',
    'Application uptime in seconds'
)

memory_usage_bytes = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes'
)

# Business metrics
user_preferences_total = Gauge(
    'user_preferences_total',
    'Total number of user preferences set'
)

categories_total = Gauge(
    'categories_total',
    'Total number of destination categories'
)

# Error metrics
errors_total = Counter(
    'errors_total',
    'Total number of errors',
    ['type', 'severity']
)

# Custom metrics helper functions
def record_db_query(table: str, operation: str, duration: float):
    """Record database query metrics"""
    db_queries_total.labels(table=table, operation=operation).inc()
    db_query_duration.observe(duration)

def record_api_request(method: str, endpoint: str, status_code: int, duration: float):
    """Record API request metrics"""
    api_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    api_request_duration.labels(method=method, endpoint=endpoint).observe(duration)

def record_login_attempt(success: bool):
    """Record login attempt metrics"""
    status = "success" if success else "failure"
    login_attempts_total.labels(status=status).inc()

def record_signup_attempt(success: bool):
    """Record signup attempt metrics"""
    status = "success" if success else "failure"
    signup_attempts_total.labels(status=status).inc()

def record_error(error_type: str, severity: str = "error"):
    """Record error metrics"""
    errors_total.labels(type=error_type, severity=severity).inc()

def update_app_uptime(start_time: float):
    """Update application uptime"""
    uptime = time.time() - start_time
    app_uptime_seconds.set(uptime)

# Initialize some metrics with default values so they appear immediately
def initialize_metrics():
    """Initialize metrics with default values"""
    # Set initial values for gauges
    active_users_total.set(0)
    destinations_total.set(0)
    reviews_total.set(0)
    user_preferences_total.set(0)
    categories_total.set(0)
    db_connections_total.set(0)
    memory_usage_bytes.set(0)
    app_uptime_seconds.set(0)
    
    print("📊 Custom metrics initialized with default values")

# Initialize metrics when module is imported
initialize_metrics()
