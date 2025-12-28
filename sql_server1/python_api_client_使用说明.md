# Python API客户端使用说明

## 概述

Python API客户端是一个用于调用SQL Server HTTP接口的工具，它是基于原Lua API客户端的Python实现版本。该客户端提供了与原Lua版本相同的功能，但使用了更广泛使用的Python编程语言，具有更好的跨平台兼容性和更丰富的生态系统。

## 功能特性

1. **完整的API调用支持**
   - 创建新游戏
   - 插入数据
   - 查询数据
   - 清除聊天通道

2. **详细的调试功能**
   - 可开启/关闭的调试输出
   - 完整的请求和响应信息
   - JSON解析错误处理

3. **友好的命令行界面**
   - 使用argparse库提供专业的命令行参数解析
   - 支持帮助文档
   - 参数验证和提示

4. **完善的错误处理**
   - 网络请求异常捕获
   - JSON解析错误处理
   - 参数验证

## 安装与依赖

### 依赖库

Python API客户端需要安装以下依赖：

- `requests`: 用于发送HTTP请求

### 安装方法

使用pip安装依赖：

```bash
pip install requests
```

## 使用方法

### 基本用法

```bash
python python_api_client.py <命令> [参数]
```

### 可用命令

1. **创建新游戏**

```bash
python python_api_client.py create <game_name>
```

示例：
```bash
python python_api_client.py create test_game
```

2. **插入数据**

```bash
python python_api_client.py insert <game_name> <account> <b_zone> <s_zone> <rating>
```

参数说明：
- `game_name`: 游戏名称
- `account`: 账号
- `b_zone`: 大区号
- `s_zone`: 小区号
- `rating`: 评分（整数）

示例：
```bash
python python_api_client.py insert test_game user123 zone1 subzone1 100
```

3. **查询数据**

```bash
python python_api_client.py query <game_name> [online_duration] [talk_channel] [cnt]
```

参数说明：
- `game_name`: 游戏名称
- `online_duration`: 在线时长（分钟，默认：1）
- `talk_channel`: 聊天频道（默认：0）
- `cnt`: 查询数量（默认：100）

示例：
```bash
python python_api_client.py query test_game 60 1 10
```

4. **清除聊天通道**

```bash
python python_api_client.py clear <game_name> <talk_channel>
```

参数说明：
- `game_name`: 游戏名称
- `talk_channel`: 聊天频道

示例：
```bash
python python_api_client.py clear test_game 1
```

### 调试选项

- 启用调试模式：`--debug`
- 禁用调试模式：`--no-debug`

示例：
```bash
python python_api_client.py create test_game --debug
python python_api_client.py query test_game --no-debug
```

### 查看帮助

```bash
python python_api_client.py -h
```

或：

```bash
python python_api_client.py --help
```

## 配置

### 服务器配置

在脚本中可以修改服务器配置：

```python
# 服务器配置
SERVER_URL = "http://localhost:9091"
```

### 调试配置

脚本默认启用调试模式：

```python
# 调试配置
DEBUG = True  # 设置为True启用调试模式
```

也可以通过命令行选项临时启用或禁用调试模式。

## 与Lua版本的区别

| 特性 | Python版本 | Lua版本 |
|------|------------|---------|
| 编程语言 | Python 3 | Lua |
| HTTP库 | requests | luasocket |
| JSON库 | 内置json | lua-cjson |
| 命令行处理 | argparse | 手动解析 |
| 错误处理 | try-except | pcall |
| 跨平台性 | 更好 | 良好 |
| 生态系统 | 更丰富 | 较小 |
| 学习曲线 | 较低 | 中等 |

## 常见问题

### 1. 请求失败

**错误提示**：网络连接失败、超时等

**解决方案**：
- 检查服务器是否正在运行
- 验证服务器URL和端口是否正确
- 检查网络连接
- 开启调试模式查看详细错误信息

### 2. 参数错误

**错误提示**：参数缺失、类型错误等

**解决方案**：
- 检查参数数量和类型是否正确
- 使用`-h`选项查看帮助
- 确保所有必填参数都已提供

### 3. JSON解析错误

**错误提示**：JSON解析失败

**解决方案**：
- 检查服务器返回的响应是否为有效JSON格式
- 开启调试模式查看原始响应文本

### 4. 依赖库缺失

**错误提示**：`ModuleNotFoundError: No module named 'requests'`

**解决方案**：
- 安装缺失的依赖库：`pip install requests`

## 示例输出

### 成功示例

```bash
$ python python_api_client.py create test_game
=== 创建新游戏 ===
状态码: 200
响应: {
  "message": "create new game table success"
}
```

### 调试模式示例

```bash
$ python python_api_client.py create test_game --debug

[调试] 命令行参数: {'command': 'create', 'game_name': 'test_game', 'debug': True, 'no_debug': False}

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
=== 创建新游戏 ===
状态码: 200
响应: {
  "message": "create new game table success"
}
```

## 高级用法

### 作为模块使用

Python API客户端也可以作为模块导入到其他Python脚本中使用：

```python
from python_api_client import create_new_game, insert_data, query_data, clear_talk_channel

# 创建新游戏
create_new_game("test_game")

# 插入数据
insert_data("test_game", "user123", "zone1", "subzone1", 100)

# 查询数据
query_data("test_game", 60, 1, 10)

# 清除聊天通道
clear_talk_channel("test_game", 1)
```

### 自定义配置

可以在导入后修改配置：

```python
import python_api_client

# 修改服务器URL
python_api_client.SERVER_URL = "http://localhost:9092"

# 关闭调试模式
python_api_client.DEBUG = False
```

## 注意事项

1. 确保服务器正在运行且端口正确
2. 检查网络连接是否正常
3. 确保参数名称和格式与API要求一致
4. 使用调试模式可以帮助排查问题
5. 在生产环境中建议关闭调试模式

## 版本历史

- v1.0: 初始版本，完成所有基本功能

## 联系与支持

如果您在使用过程中遇到问题，请：
1. 查看帮助文档
2. 开启调试模式查看详细信息
3. 检查服务器日志
4. 与开发人员联系

## 许可证

本项目使用MIT许可证。