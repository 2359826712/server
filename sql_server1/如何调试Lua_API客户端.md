# 如何调试 Lua API 客户端

## 一、环境准备

### 1. 安装 Lua

如果你的系统中没有安装 Lua，可以通过以下方式安装：

#### Windows 用户
1. 访问 [Lua 官网](https://www.lua.org/download.html) 下载最新的 Windows 版本（lua-5.4.x_Win64_bin.zip）
2. 解压到任意目录，例如 `C:\lua\`
3. 将 `C:\lua\` 添加到系统环境变量 PATH 中

#### 或使用 Chocolatey 安装
```powershell
choco install lua
```

### 2. 安装依赖库

需要安装以下 Lua 库：
- `lua-cjson`：用于 JSON 解析
- `luasocket`：用于 HTTP 请求

使用 LuaRocks 安装：
```powershell
luarocks install lua-cjson luasocket
```

## 二、调试功能说明

我已经为 `lua_api_client.lua` 添加了详细的调试功能，包括：

### 1. 调试开关

在脚本顶部有一个调试开关：
```lua
local DEBUG = true -- 设置为true启用调试模式
```

- 设置为 `true` 启用调试输出
- 设置为 `false` 禁用调试输出

### 2. 调试信息内容

启用调试模式后，脚本会输出以下信息：

- 请求 URL 和端点
- 请求数据的详细内容
- 转换后的 JSON 请求体
- 请求头信息
- 响应状态码
- 响应头信息
- 原始响应文本
- JSON 解析结果（成功或失败）

### 3. 调试输出示例

```
[调试] 发送请求到: /createNewGame
[调试] 请求数据: "game_name" = "test_game",

[调试] JSON请求: {"game_name":"test_game"}
[调试] 请求头: "Content-Type" = "application/json",
"Content-Length" = "20",

[调试] 请求URL: http://localhost:9091/createNewGame
[调试] 状态码: 200
[调试] 响应头: "connection" = "close",
"content-length" = "43",
"content-type" = "application/json",

[调试] 响应文本: {"message":"create new game table success"}
[调试] 解析JSON成功
```

## 三、常见问题调试

### 1. 连接问题

**错误提示**：连接失败或超时

**调试步骤**：
- 检查服务器是否正在运行
- 验证服务器 URL 和端口是否正确
- 检查网络连接
- 查看调试输出中的请求 URL

### 2. 参数错误

**错误提示**：游戏名不能为空、在线时长不能为 0 等

**调试步骤**：
- 查看调试输出中的请求数据
- 确认参数名称是否正确（例如 `game_name` 而不是 `gameName`）
- 检查参数值是否符合要求

### 3. JSON 解析错误

**错误提示**：JSON 解析失败

**调试步骤**：
- 查看调试输出中的原始响应文本
- 检查响应是否是有效的 JSON 格式
- 检查服务器返回的错误信息

### 4. 依赖库问题

**错误提示**：找不到模块 "cjson" 或 "socket.http"

**调试步骤**：
- 确认已安装所需的依赖库
- 检查 LuaRocks 安装路径是否在环境变量中
- 尝试重新安装依赖库

## 四、使用示例

### 1. 启用调试模式运行

```powershell
lua lua_api_client.lua create test_game
```

### 2. 检查服务器状态

确保服务器正在运行：

```powershell
# 查看服务器进程
Get-Process -Name sql_server_windows

# 或检查端口是否被监听
netstat -an | findstr :9091
```

### 3. 使用其他工具测试 API

可以使用 curl 或 Postman 测试 API 是否正常工作：

```powershell
# 使用 curl 测试
curl -X POST http://localhost:9091/createNewGame -H "Content-Type: application/json" -d '{"game_name":"test_game"}'
```

## 五、高级调试技巧

### 1. 使用 Lua 调试器

可以使用 Lua 调试器（如 `luadebug`）进行更深入的调试：

```powershell
luarocks install luadebug
lua -ldebug lua_api_client.lua create test_game
```

### 2. 逐行调试

在关键位置添加断点和调试语句：

```lua
-- 在关键函数入口添加
print("[断点] 进入 create_new_game 函数")

-- 打印变量值
print("[变量] game_name = ", game_name)
```

### 3. 捕获异常

使用 pcall 捕获可能的异常并打印详细信息：

```lua
local success, result = pcall(function()
    -- 可能出错的代码
    return create_new_game(game_name)
end)

if not success then
    print("[错误] 执行失败:", result)
    print("[堆栈] ", debug.traceback())
end
```

## 六、注意事项

1. 确保服务器正在运行且端口正确
2. 检查参数名称和格式是否与 API 要求一致
3. 查看调试输出以获取详细的请求和响应信息
4. 如果遇到问题，先检查服务器日志
5. 可以使用其他 HTTP 客户端工具验证 API 是否正常工作

## 七、进一步帮助

如果仍然无法解决问题，可以：
1. 查看服务器端的日志文件
2. 检查 API 文档确认参数要求
3. 使用网络抓包工具（如 Wireshark）分析 HTTP 请求和响应
4. 尝试使用简单的测试用例逐步排查问题