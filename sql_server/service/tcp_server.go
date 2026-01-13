package service

import (
	"bufio"
	"fmt"
	"log"
	"net"
	"sql_server/global"
	"sql_server/service/buffer"
)

// 服务端
// 收包形式
// 包长 uint32   4bytes
// 命令 byte( 0:创建新表, 1: 新增, 2:更新, 3:查询, 4:清理喊话通道)
// 内容: json数据

func StartTcpServer() {
	// 监听指定的端口
	listener, er := net.Listen("tcp", fmt.Sprintf(":%d", global.Config.Service.TcpPort))
	if er != nil {
		panic(er)
	}
	defer listener.Close()
	log.Printf("TCP server listening on port %d\n", global.Config.Service.TcpPort)
	for {
		// 接受新的连接
		conn, err := listener.Accept()
		if err != nil {
			log.Println("Error accepting connection:", err)
			continue
		}
		log.Println("Accepted new connection")
		go handleConnection(conn)
	}
}

// 处理单个连接
func handleConnection(conn net.Conn) {
	defer conn.Close()
	// 创建一个 bufio.Reader 来读取客户端发送的数据
	reader := bufio.NewReader(conn)
	buf := buffer.NewBuffer()
	read := make([]byte, 1024)
	for {
		n, err := reader.Read(read)
		if err != nil {
			log.Println("Error reading:", err)
			return
		}
		buf.Write(read[:n])
		for {
			size := buf.GetPackageLength()
			if size == -1 {
				break
			}
			res := handlePack(buf.Pop(size))
			_, err = conn.Write(res)
			if err != nil {
				log.Println("Error sending to client:", err)
				return
			}
		}
	}
}
