# 服务器部署指南

## 1. 前置条件
- **操作系统**：Linux（推荐）或 Windows。
- **运行时**：Go 1.23+。
- **数据库**：MySQL 5.7 或 8.0。

## 2. 配置
编辑 `config.yaml`（或确保环境变量已设置）：

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

## 3. 构建
```bash
go build -o sql_server_app main.go
```

## 4. 运行（Systemd）
创建 `/etc/systemd/system/sql_server.service`：

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

启用并启动：
```bash
systemctl daemon-reload
systemctl enable sql_server
systemctl start sql_server
```

## 5. Docker 部署（可选）
创建 `Dockerfile`：
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

构建并运行：
```bash
docker build -t sql_server .
docker run -d -p 9090:9090 --name sql_server sql_server
```
