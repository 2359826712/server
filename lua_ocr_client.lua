local http = require("socket.http")
local ltn12 = require("ltn12")
local mime = require("mime")
local cjson = require("cjson")

-- 配置 OCR 服务器地址
local OCR_SERVER_URL = os.getenv("OCR_SERVER_URL") or "http://127.0.0.1:8000"

-- 读取文件内容
local function read_file(path)
    local f = io.open(path, "rb")
    if not f then return nil, "无法打开文件: " .. path end
    local content = f:read("*a")
    f:close()
    return content
end

-- 获取文件的 Base64 编码
local function get_base64_from_file(path)
    local content, err = read_file(path)
    if not content then return nil, err end
    return mime.b64(content)
end

-- 调用 OCR 接口
-- @param image_path: 图片路径
-- @param target_text: (可选) 目标文本
-- @param max_side: (可选) 最大边长，默认 720
-- @param use_angle_cls: (可选) 是否使用角度分类，默认 false
local function ocr_predict(image_path, target_text, max_side, use_angle_cls)
    local img_base64, err = get_base64_from_file(image_path)
    if not img_base64 then
        return nil, err
    end

    local req_body = {
        image_base64 = img_base64,
        target_text = target_text or "",
        max_side = max_side or 720,
        use_angle_cls = use_angle_cls or false
    }

    local req_json = cjson.encode(req_body)
    local resp_body = {}

    local res, code, headers, status = http.request{
        url = OCR_SERVER_URL .. "/ocr/predict",
        method = "POST",
        headers = {
            ["Content-Type"] = "application/json",
            ["Content-Length"] = #req_json
        },
        source = ltn12.source.string(req_json),
        sink = ltn12.sink.table(resp_body)
    }

    if code ~= 200 then
        return nil, "HTTP 请求失败，状态码: " .. tostring(code)
    end

    local resp_str = table.concat(resp_body)
    local success, resp_data = pcall(cjson.decode, resp_str)
    
    if not success then
        return nil, "JSON 解析失败: " .. tostring(resp_data)
    end

    if resp_data.code == 0 then
        return resp_data.data
    else
        return nil, "OCR 识别错误: " .. tostring(resp_data.msg)
    end
end

-- 导出模块函数
local M = {
    ocr_predict = ocr_predict
}

-- 如果直接运行此脚本 (非 require 引用)，则执行测试
-- 注意：Lua 没有直接的 "if __name__ == '__main__'"，这里简单判断一下 arg
if arg and arg[0] and string.find(arg[0], "lua_ocr_client.lua") then
    if #arg < 1 then
        print("用法: lua lua_ocr_client.lua <image_path> [target_text]")
        return
    end

    local img_path = arg[1]
    local target = arg[2]

    print("正在识别图片: " .. img_path)
    local res, err = ocr_predict(img_path, target)
    if res then
        print("识别成功:")
        print(cjson.encode(res))
    else
        print("识别失败:", err)
    end
end

return M
