"""
OpenTelemetry setup for the RAG pipeline: traces export via OTLP to Jaeger,
metrics are exposed in Prometheus format on the API's /metrics endpoint.

Usage: import `tracer` for spans, and the metric instruments below for
custom RAG-specific measurements (stage latency, retrieval confidence,
token usage).
"""
import os

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

SERVICE_NAME = "rag-pipeline"
OTLP_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")

resource = Resource.create({"service.name": SERVICE_NAME})

# --- Tracing: spans exported to Jaeger via OTLP/HTTP ---
tracer_provider = TracerProvider(resource=resource)
tracer_provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{OTLP_ENDPOINT}/v1/traces"))
)
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(SERVICE_NAME)

# --- Metrics: exposed in Prometheus format (scraped, not pushed) ---
prometheus_reader = PrometheusMetricReader()
meter_provider = MeterProvider(resource=resource, metric_readers=[prometheus_reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(SERVICE_NAME)

request_counter = meter.create_counter(
    "rag_requests_total", description="Total /query requests, labeled by status"
)
retrieval_latency = meter.create_histogram(
    "rag_retrieval_latency_seconds", description="FAISS vector search latency"
)
rerank_latency = meter.create_histogram(
    "rag_rerank_latency_seconds", description="Cross-encoder rerank latency"
)
generation_latency = meter.create_histogram(
    "rag_generation_latency_seconds", description="OpenAI chat completion latency"
)
retrieval_top_score = meter.create_histogram(
    "rag_retrieval_top_score", description="Top reranked chunk score (retrieval confidence proxy)"
)
tokens_counter = meter.create_counter(
    "rag_tokens_total", description="OpenAI tokens used, labeled by type (prompt/completion)"
)


def instrument_fastapi(app):
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)
