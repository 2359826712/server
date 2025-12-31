# Client Integration Guide

## 1. Connection
Connect to the server via TCP:
- **Host**: Server IP
- **Port**: 9090 (default)

## 2. Protocol
The server uses a binary length-prefixed protocol with JSON payload.

**Packet Structure:**
| Offset | Size | Type | Description |
| :--- | :--- | :--- | :--- |
| 0 | 4 | uint32 | Total Packet Length (Header + Body) |
| 4 | 1 | byte | Command Code |
| 5 | N | bytes | JSON Payload |

**Endianness**: Little Endian for the length field.

## 3. Commands

| Command ID | Name | Payload (JSON) | Description |
| :--- | :--- | :--- | :--- |
| 1 | CreateNewGameTable | `{"game_name": "name"}` | Create a new game table |
| 2 | Insert | `BaseInfo` Object | Insert or Update account info |
| 3 | Update | `BaseInfo` Object | Update account info |
| 4 | Query | `QueryReq` Object | Query accounts |
| 5 | ClearTalkChannel | `QueryReq` Object | Clear talk time |

## 4. Example (Go)
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

## 5. Response Handling
The server sends back responses in the same format (Length + JSON).
- **Code**: 0 (Success), 1 (Error)
- **Game**: List of `BaseInfo` (for Query)
- **ErrMsg**: Error message string

**Note**: Requests are processed asynchronously. The order of responses is generally preserved per connection but high-priority requests (Query) might jump the queue ahead of Insert/Update requests if the backlog is high.
