package service

import (
	"bufio"
	"context"
	"fmt"
	"log"
	"net"
	"sql_server/global"
	"sql_server/service/buffer"
	"sql_server/service/pool"
)

var WorkerPool *pool.WorkerPool

// 服务端
// 收包形式
// 包长 uint32   4bytes
// 命令 byte( 0:创建新表, 1: 新增, 2:更新, 3:查询, 4:清理喊话通道)
// 内容: json数据

func StartTcpServer() {
	// Initialize WorkerPool
	// 100 workers, 10000 queue size
	WorkerPool = pool.NewWorkerPool(100, 10000, func(data []byte) ([]byte, error) {
		return handlePack(data), nil
	})
	WorkerPool.Start()
	defer WorkerPool.Stop()

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
	// Context for cancellation
	ctx, cancel := context.WithCancel(context.Background())
	defer func() {
		cancel()
		conn.Close()
	}()

	// Response channel
	responses := make(chan pool.Result, 100)

	// Writer Goroutine
	go func() {
		for {
			select {
			case <-ctx.Done():
				return
			case res := <-responses:
				if res.Err != nil {
					log.Println("Processing error:", res.Err)
					continue
				}
				_, err := conn.Write(res.Data)
				if err != nil {
					log.Println("Error sending to client:", err)
					cancel() // Close connection
					return
				}
			}
		}
	}()

	// Reader Loop
	reader := bufio.NewReader(conn)
	buf := buffer.NewBuffer()
	read := make([]byte, 1024)
	for {
		n, err := reader.Read(read)
		if err != nil {
			// log.Println("Error reading:", err)
			return
		}
		buf.Write(read[:n])
		for {
			size := buf.GetPackageLength()
			if size == -1 {
				break
			}
			packet := buf.Pop(size)

			// Determine Job Type
			var jobType pool.JobType
			if len(packet) > 4 {
				cmd := packet[4]
				switch cmd {
				case Query:
					jobType = pool.JobTypeQuery
				case Insert:
					jobType = pool.JobTypeInsert
				case Update:
					jobType = pool.JobTypeUpdate
				default:
					jobType = pool.JobTypeOther
				}
			}

			// Create and Submit Job
			job := pool.Job{
				Ctx:    ctx,
				Data:   packet,
				Type:   jobType,
				Result: responses,
			}
			WorkerPool.Submit(job)
		}
	}
}
