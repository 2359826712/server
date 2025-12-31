# 客户端接入指南

## 1. 连接
通过 TCP 连接服务器：
- **主机**：服务器 IP
- **端口**：9090（默认）

## 2. 协议
服务器使用二进制长度前缀协议，负载为 JSON。

**数据包结构：**
| 偏移 | 大小 | 类型 | 描述 |
| :--- | :--- | :--- | :--- |
| 0 | 4 | uint32 | 数据包总长度（头 + 体） |
| 4 | 1 | byte | 命令码 |
| 5 | N | bytes | JSON 载荷 |

**字节序**：长度字段使用小端序。

## 3. 命令

| 命令 ID | 名称 | 载荷（JSON） | 描述 |
| :--- | :--- | :--- | :--- |
| 1 | CreateNewGameTable | `{"game_name": "name"}` | 创建新的游戏表 |
| 2 | Insert | `BaseInfo` 对象 | 插入或更新账号信息 |
| 3 | Update | `BaseInfo` 对象 | 更新账号信息 |
| 4 | Query | `QueryReq` 对象 | 查询账号 |
| 5 | ClearTalkChannel | `QueryReq` 对象 | 清空发言时间 |

## 4. 示例（Go）
```go
func SendRequest(conn net.Conn, cmd byte, data interface{}) error {
    payload, _ := json.Marshal(data)
    buf := new(bytes.Buffer)
    
    // Total Length = 4 (Length) + 1 (Cmd) + Payload Length
    totalLen := uint32(4 + 1 + len(payload))
    
    binary.Write(buf, binary.LittleEndian, totalLen)
    buf.WriteByte(cmd)
    buf.Write(payload)
    
    _, err := conn.Write(buf.Bytes())
    return err
}
```

## 5. 响应处理
服务器以相同格式返回（长度 + JSON）。
- **Code**：0（成功），1（错误）
- **Game**：`BaseInfo` 列表（用于查询）
- **ErrMsg**：错误信息字符串

**说明**：请求以异步方式处理。响应顺序通常在每个连接内保持，但当积压较高时，高优先级请求（查询）可能会在插入/更新请求之前插队处理。
