# Core OpenTelemetry monitoring setup
from prometheus_client import Counter

API_REQUESTS = Counter(
    "api_requests_total",
    "Total API requests processed",
    ["method", "endpoint"]
)
