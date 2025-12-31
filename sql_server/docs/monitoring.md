# System Monitoring Guide

## 1. Key Metrics to Monitor

### System Metrics
- **CPU Usage**: High usage is expected under load, but should not stay at 100% continuously.
- **Memory Usage**: Monitor for leaks. The worker pool limits concurrency, so memory should be stable.
- **Network I/O**: Throughput (MB/s) and Packet rate.

### Application Metrics (To be implemented via Prometheus/Log parsing)
- **Worker Pool Depth**:
    -   `HighPriorityQueue` Length
    -   `NormalPriorityQueue` Length
    -   *Alert*: If queue is full (blocking), scale up workers.
- **Latency**:
    -   P95 Response Time.
    -   *Target*: < 100ms for Queries.
- **Throughput (QPS)**:
    -   Requests per second.
- **Error Rate**:
    -   DB Connection Errors.
    -   JSON Parse Errors.

## 2. Logging
- **Standard Output**: The server logs important events (New Connection, Errors) to stdout.
- **Log Rotation**: Ensure stdout is captured and rotated (e.g., via Docker logs or logrotate).

## 3. Health Check
- **TCP Port Check**: Monitor if port 9090 is accepting connections.
- **HTTP Health Endpoint** (Optional): The server starts an HTTP server on port 9091. You can add a `/health` endpoint to `service/http_server.go` for load balancers.

## 4. Database Monitoring
- **Connections**: Monitor active vs idle connections. (Max configured: 100).
- **Slow Queries**: Enable MySQL slow query log to identify unoptimized SQL.
