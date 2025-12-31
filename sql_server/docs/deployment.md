# Server Deployment Guide

## 1. Prerequisites
- **OS**: Linux (Recommended) or Windows.
- **Runtime**: Go 1.23+.
- **Database**: MySQL 5.7 or 8.0.

## 2. Configuration
Edit `config.yaml` (or ensure environment variables are set):

```yaml
mysql:
  path: "127.0.0.1"
  port: "3306"
  db-name: "sql_server"
  username: "root"
  password: "your_password"
  max-idle-conns: 10
  max-open-conns: 100
  conn-max-lifetime: 3600

service:
  tcp-port: 9090
```

## 3. Build
```bash
go build -o sql_server_app main.go
```

## 4. Run (Systemd)
Create `/etc/systemd/system/sql_server.service`:

```ini
[Unit]
Description=Go SQL Server
After=network.target mysql.service

[Service]
Type=simple
User=root
ExecStart=/path/to/sql_server_app
Restart=on-failure
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
systemctl daemon-reload
systemctl enable sql_server
systemctl start sql_server
```

## 5. Docker Deployment (Alternative)
Create `Dockerfile`:
```dockerfile
FROM golang:1.23 AS builder
WORKDIR /app
COPY . .
RUN go build -o server main.go

FROM debian:buster-slim
WORKDIR /app
COPY --from=builder /app/server .
COPY config.yaml .
EXPOSE 9090
CMD ["./server"]
```

Build and Run:
```bash
docker build -t sql_server .
docker run -d -p 9090:9090 --name sql_server sql_server
```
