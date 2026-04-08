# PowerShell API 测试指南

## 1. 创建新游戏

```powershell
Invoke-WebRequest -Uri "http://localhost:9091/createNewGame" -Method POST -ContentType "application/json" -Body '{"game_name":"test_game"}'
```

## 2. 插入数据

```powershell
Invoke-WebRequest -Uri "http://localhost:9091/insert" -Method POST -ContentType "application/json" -Body '{"game_name":"test_game","account":"user123","email_account":"test@example.com","email_password":"password","address":"addr"}'
```

## 3. 查询数据

```powershell
Invoke-WebRequest -Uri "http://localhost:9091/query" -Method POST -ContentType "application/json" -Body '{"game_name":"test_game","onlineDuration":3600}'
```

## 参数说明

### 创建新游戏
- `game_name`: 游戏名称（必填，用作表名）

### 插入数据
- `game_name`: 游戏名称（必填）
- `account`: 账号（必填）
- `email_account`: 邮箱账号（必填）
- `email_password`: 邮箱密码（必填）
- `address`: 地址（必填）

### 查询数据
- `game_name`: 游戏名称（必填）
- `onlineDuration`: 在线时长（秒，选填）

## 响应处理

可以使用 `-UseBasicParsing` 参数避免HTML解析错误：

```powershell
Invoke-WebRequest -Uri "http://localhost:9091/createNewGame" -Method POST -ContentType "application/json" -Body '{"game_name":"test_game"}' -UseBasicParsing | Select-Object -ExpandProperty Content
```

或者使用 ConvertFrom-Json 解析JSON响应：

```powershell
$response = Invoke-WebRequest -Uri "http://localhost:9091/createNewGame" -Method POST -ContentType "application/json" -Body '{"game_name":"test_game"}' -UseBasicParsing
$response.Content | ConvertFrom-Json
```
