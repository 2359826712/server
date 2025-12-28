-- Lua API客户端：用于调用SQL Server的HTTP接口
-- 依赖：需要安装lua-cjson和luasocket库
-- 安装方法：luarocks install lua-cjson luasocket
-- 手动把 LuaRocks 的路径加进去

local appdata = os.getenv("APPDATA")  -- 一般是 C:\Users\admin\AppData\Roaming
local lr_root = appdata .. [[\luarocks]]

-- 告诉 Lua 去 LuaRocks 安装目录里找模块
package.path = package.path
    .. ";" .. lr_root .. [[\share\lua\5.3\?.lua]]
    .. ";" .. lr_root .. [[\share\lua\5.3\?\init.lua]]

package.cpath = package.cpath
    .. ";" .. lr_root .. [[\lib\lua\5.3\?.dll]]

-- 现在再 require 就能找到了
-- local http = require "socket.http"
-- require("socket")
local http = require("socket.http")
local ltn12 = require("ltn12")
local json = require 'script.lualib.json'
-- local json = require("cjson")

-- 调试配置
local DEBUG = true -- 设置为true启用调试模式

-- 服务器配置
local server_url = "http://localhost:9096"

-- 辅助函数：调试输出
local function debug_print(...) 
    if DEBUG then
        print(...) 
    end
end

-- 辅助函数：格式化表格为字符串
local function table_to_string(tbl, indent)
    indent = indent or 0
    local result = ""
    local spaces = string.rep("  ", indent)
    
    for k, v in pairs(tbl) do
        local key = type(k) == "string" and "\"" .. k .. "\"" or tostring(k)
        if type(v) == "table" then
            result = result .. spaces .. key .. " = {\n" .. table_to_string(v, indent + 1) .. spaces .. "},\n"
        else
            local value = type(v) == "string" and "\"" .. v .. "\"" or tostring(v)
            result = result .. spaces .. key .. " = " .. value .. ",\n"
        end
    end
    
    return result
end

-- 辅助函数：发送POST请求
local function send_post_request(endpoint, data)
    -- 调试：请求数据
    debug_print("\n[调试] 发送请求到:", endpoint)
    debug_print("[调试] 请求数据:", table_to_string(data))
    
    local json_data = json.encode(data)
    debug_print("[调试] JSON请求:", json_data)
    
    local response_body = {}
    
    local headers = {
        ["Content-Type"] = "application/json",
        ["Content-Length"] = tostring(#json_data)
    }
    
    debug_print("[调试] 请求:", table_to_string(headers))
    
    local request_url = server_url .. endpoint
    debug_print("[调试] 请求URL:", request_url)
    
    -- 尝试发送请求
    local _, status_code, response_headers = http.request{
        url = request_url,
        method = "POST",
        headers = headers,
        source = ltn12.source.string(json_data),
        sink = ltn12.sink.table(response_body)
    }
    
    -- 调试：响应状态
    debug_print("[调试] 状态码:", status_code)
    debug_print("[调试] 响应头:", table_to_string(response_headers))
    
    local response_text = table.concat(response_body)
    debug_print("[调试] 响应文本:", response_text)
    
    local response = {}
    
    -- 尝试解析JSON响应
    local success, result = pcall(json.decode, response_text)
    if success then
        response = result
        debug_print("[调试] 解析JSON成功")
    else
        response = { raw_text = response_text, parse_error = result }
        debug_print("[调试] JSON解析失败:", result)
    end
    
    return status_code, response
end

-- 1. 创建新游戏
local function create_new_game(game_name)
    local data = { game_name = game_name }
    local status_code, response = send_post_request("/createNewGame", data)
    
    print("=== 创建新游戏 ===")
    print("状态码:", status_code)
    print("响应:", json.encode(response))
    print()
    
    return status_code, response
end

-- 2. 插入数据
local function insert_data(game_name, account, b_zone, s_zone, rating)
    local data = {
        game_name = game_name,
        account = account,
        b_zone = b_zone,
        s_zone = s_zone,
        rating = rating
    }
    local status_code, response = send_post_request("/insert", data)
    
    print("=== 插入数据 ===")
    print("状态码:", status_code)
    print("响应:", json.encode(response))
    print()
    
    return status_code, response
end

-- 3. 查询数据
local function query_data(game_name, online_duration, talk_channel, cnt)
    local data = {
        game_name = game_name,
        online_duration = online_duration or 1,  -- 在线时长不能为0
        talk_channel = talk_channel or 0,
        cnt = cnt or 100
    }
    local status_code, response = send_post_request("/query", data)
    
    print("=== 查询数据 ===")
    print("状态码:", status_code)
    print("响应:", json.encode(response))
    print()
    
    return status_code, response
end

-- 4. 清除聊天通道
local function clear_talk_channel(game_name, talk_channel)
    local data = {
        game_name = game_name,
        talk_channel = talk_channel
    }
    local status_code, response = send_post_request("/clearTalkChannel", data)
    
    print("=== 清除聊天通道 ===")
    print("状态码:", status_code)
    print("响应:", json.encode(response))
    print()
    
    return status_code, response
end
create_new_game("test")
-- 使用示例
-- if arg[1] == "help" or arg[1] == nil then
--     print("使用方法:")
--     print("lua lua_api_client.lua create <game_name>           - 创建新游戏")
--     print("lua lua_api_client.lua insert <game_name> <account> <b_zone> <s_zone> <rating> - 插入数据")
--     print("lua lua_api_client.lua query <game_name> [online_duration] [talk_channel] [cnt] - 查询数据")
--     print("lua lua_api_client.lua clear <game_name> <talk_channel> - 清除聊天通道")
--     print()
--     print("示例:")
--     print("lua lua_api_client.lua create test_game")
--     print("lua lua_api_client.lua insert test_game user123 zone1 subzone1 100")
--     print("lua lua_api_client.lua query test_game 60 1 10")
--     print("lua lua_api_client.lua clear test_game 1")
--     os.exit()
-- end

-- -- 解析命令行参数
-- local command = arg[1]

-- if DEBUG then
--     debug_print("[调试] 命令行参数:", table_to_string(arg))
-- end

-- if command == "create" then
--     local game_name = arg[2]
--     if not game_name then
--         print("错误：请提供游戏名称")
--         os.exit(1)
--     end
--     create_new_game(game_name)
    
-- elseif command == "insert" then
--     local game_name = arg[2]
--     local account = arg[3]
--     local b_zone = arg[4]
--     local s_zone = arg[5]
--     local rating = tonumber(arg[6])
    
--     if not (game_name and account and b_zone and s_zone and rating) then
--         print("错误：请提供完整的参数：<game_name> <account> <b_zone> <s_zone> <rating>")
--         os.exit(1)
--     end
    
--     insert_data(game_name, account, b_zone, s_zone, rating)
    
-- elseif command == "query" then
--     local game_name = arg[2]
--     local online_duration = tonumber(arg[3]) or 1
--     local talk_channel = tonumber(arg[4]) or 0
--     local cnt = tonumber(arg[5]) or 100
    
--     if not game_name then
--         print("错误：请提供游戏名称")
--         os.exit(1)
--     end
    
--     query_data(game_name, online_duration, talk_channel, cnt)
    
-- elseif command == "clear" then
--     local game_name = arg[2]
--     local talk_channel = tonumber(arg[3])
    
--     if not (game_name and talk_channel) then
--         print("错误：请提供完整的参数：<game_name> <talk_channel>")
--         os.exit(1)
--     end
    
--     clear_talk_channel(game_name, talk_channel)
    
-- else
--     print("错误：未知命令", command)
--     print("使用 'lua lua_api_client.lua help' 查看帮助")
--     os.exit(1)
-- end