import json
import asyncio
import socket
import struct
from typing import Tuple, Dict, Any, Optional

# Protocol Constants
CMD_CREATE_NEW_GAME = 1
CMD_INSERT = 2
CMD_UPDATE = 3
CMD_QUERY = 4
CMD_CLEAR_TALK_CHANNEL = 5

class ApiClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 9090):
        # Support passing a URL string for backward compatibility (parse host/port)
        if isinstance(host, str) and (host.startswith("http://") or host.startswith("https://")):
            from urllib.parse import urlparse
            parsed = urlparse(host)
            self.host = parsed.hostname or "127.0.0.1"
            # If port is not specified in URL, use default 9090 (assuming user meant the new server)
            # or parsed.port if available.
            self.port = parsed.port or port
        else:
            self.host = host
            self.port = port

    def _pack_request(self, cmd: int, data: dict) -> bytes:
        json_bytes = json.dumps(data).encode("utf-8")
        # Total Length = 4 (Header) + 1 (Cmd) + Len(JSON)
        total_len = 4 + 1 + len(json_bytes)
        # Pack: Length (uint32 LE), Cmd (byte), JSON
        return struct.pack("<IB", total_len, cmd) + json_bytes

    def _unpack_response(self, data: bytes) -> Tuple[int, Dict[str, Any]]:
        if not data:
            return 0, {"error": "Empty response"}
        
        try:
            # Response: [Length (4 bytes)] [JSON]
            # We assume the caller handles the length framing, so 'data' here is just the JSON part?
            # No, let's handle framing in the receive loop.
            # This helper just parses JSON.
            resp_obj = json.loads(data.decode("utf-8"))
            code = resp_obj.get("code", 1)
            # Map server code: 0=Success, 1=Error
            # The original client returned (status_code, dict).
            # HTTP 200 is success. Server returns code 0 for success.
            # Let's map code 0 -> 200, others -> 500?
            # Or just return the code as is? The original client returned HTTP status codes (200, 404, etc).
            # To maintain compatibility with existing logic (which likely checks == 200),
            # I should map success to 200.
            status = 200 if code == 0 else 500
            return status, resp_obj
        except json.JSONDecodeError as e:
            return 500, {"parse_error": str(e), "raw": data.decode("utf-8", errors="ignore")}

    async def _send_tcp_request_async(self, cmd: int, data: dict) -> Tuple[int, Dict[str, Any]]:
        payload = self._pack_request(cmd, data)
        
        try:
            reader, writer = await asyncio.open_connection(self.host, self.port)
            
            writer.write(payload)
            await writer.drain()
            
            # Read Length (4 bytes)
            head_data = await reader.readexactly(4)
            (total_len,) = struct.unpack("<I", head_data)
            
            # Read Body (Total Len - 4)
            body_len = total_len - 4
            body_data = await reader.readexactly(body_len)
            
            writer.close()
            await writer.wait_closed()
            
            return self._unpack_response(body_data)
            
        except (ConnectionRefusedError, asyncio.TimeoutError, OSError) as e:
            return 0, {"error": str(e)}
        except Exception as e:
            return 0, {"error": f"Unexpected: {str(e)}"}

    def _send_tcp_request_sync(self, cmd: int, data: dict) -> Tuple[int, Dict[str, Any]]:
        payload = self._pack_request(cmd, data)
        
        try:
            with socket.create_connection((self.host, self.port), timeout=10) as sock:
                sock.sendall(payload)
                
                # Read Length
                head_data = self._recv_exact(sock, 4)
                if not head_data:
                    return 0, {"error": "Closed prematurely"}
                
                (total_len,) = struct.unpack("<I", head_data)
                
                # Read Body
                body_len = total_len - 4
                body_data = self._recv_exact(sock, body_len)
                
                return self._unpack_response(body_data)
                
        except (ConnectionRefusedError, socket.timeout, OSError) as e:
            return 0, {"error": str(e)}
        except Exception as e:
            return 0, {"error": f"Unexpected: {str(e)}"}

    def _recv_exact(self, sock: socket.socket, n: int) -> bytes:
        data = b""
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                break
            data += packet
        return data

    # Async Interfaces
    async def create_new_game_async(self, game_name: str) -> Tuple[int, Dict[str, Any]]:
        return await self._send_tcp_request_async(CMD_CREATE_NEW_GAME, {"game_name": game_name})

    async def insert_data_async(self, game_name: str, account: str, b_zone: str, s_zone: str, rating: int) -> Tuple[int, Dict[str, Any]]:
        data = {
            "game_name": game_name,
            "account": account,
            "b_zone": b_zone,
            "s_zone": s_zone,
            "rating": rating,
        }
        return await self._send_tcp_request_async(CMD_INSERT, data)

    async def query_data_async(self, game_name: str, online_duration: Optional[int] = 1, talk_channel: Optional[int] = 0, cnt: Optional[int] = 100) -> Tuple[int, Dict[str, Any]]:
        data = {
            "game_name": game_name,
            "online_duration": online_duration or 1,
            "talk_channel": talk_channel or 0,
            "cnt": cnt or 100,
        }
        return await self._send_tcp_request_async(CMD_QUERY, data)

    async def clear_talk_channel_async(self, game_name: str, talk_channel: int) -> Tuple[int, Dict[str, Any]]:
        data = {"game_name": game_name, "talk_channel": talk_channel}
        return await self._send_tcp_request_async(CMD_CLEAR_TALK_CHANNEL, data)

    async def update_data_async(self, game_name: str, account: str, b_zone: str, s_zone: str, rating: int) -> Tuple[int, Dict[str, Any]]:
        data = {
            "game_name": game_name,
            "account": account,
            "b_zone": b_zone,
            "s_zone": s_zone or "1",
            "rating": rating or 50,
        }
        return await self._send_tcp_request_async(CMD_UPDATE, data)

    # Sync Interfaces
    def create_new_game(self, game_name: str) -> Tuple[int, Dict[str, Any]]:
        return self._send_tcp_request_sync(CMD_CREATE_NEW_GAME, {"game_name": game_name})

    def insert_data(self, game_name: str, account: str, b_zone: str, s_zone: str, rating: int) -> Tuple[int, Dict[str, Any]]:
        return self._send_tcp_request_sync(CMD_INSERT, {
            "game_name": game_name,
            "account": account,
            "b_zone": b_zone,
            "s_zone": s_zone,
            "rating": rating,
        })

    def query_data(self, game_name: str, online_duration: Optional[int] = 1, talk_channel: Optional[int] = 0, cnt: Optional[int] = 100) -> Tuple[int, Dict[str, Any]]:
        return self._send_tcp_request_sync(CMD_QUERY, {
            "game_name": game_name,
            "online_duration": online_duration or 1,
            "talk_channel": talk_channel or 0,
            "cnt": cnt or 100,
        })

    def clear_talk_channel(self, game_name: str, talk_channel: int) -> Tuple[int, Dict[str, Any]]:
        return self._send_tcp_request_sync(CMD_CLEAR_TALK_CHANNEL, {"game_name": game_name, "talk_channel": talk_channel})

    def update_data(self, game_name: str, account: str, b_zone: str, s_zone: str, rating: int) -> Tuple[int, Dict[str, Any]]:
        return self._send_tcp_request_sync(CMD_UPDATE, {
            "game_name": game_name,
            "account": account,
            "b_zone": b_zone,
            "s_zone": s_zone or "1",
            "rating": rating or 50,
        })
