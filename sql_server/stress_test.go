package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"net"
	"sql_server/global"
	"sql_server/initialize"
	"sql_server/model"
	"sql_server/model/request"
	"sql_server/service"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

// Define constants from service/const.go locally to avoid import cycle if needed,
// but since this is package main, I can import sql_server/service.
// service/const.go exports them.
const (
	CreateNewGameTable = 1
	Insert             = 2
	Update             = 3
	Query              = 4
	ClearTalkChannel   = 5
)

func TestPerformance(t *testing.T) {
	// 1. Initialize Server
	initialize.Viper()
	global.DB = initialize.InitGormDb(global.Config.Mysql)
	
	// Ensure table exists
	model.AutoMigrate("benchmark_game")

	go service.StartTcpServer()
	time.Sleep(2 * time.Second) // Wait for server startup

	// 2. Benchmark Config
	concurrency := 200 // Number of concurrent clients
	requestsPerConn := 50 // Requests per client
	
	fmt.Printf("Starting Stress Test with %d connections, %d requests each...\n", concurrency, requestsPerConn)

	var (
		totalSuccess int64
		totalFail    int64
		latencies    []time.Duration
		latencyLock  sync.Mutex
	)

	wg := sync.WaitGroup{}
	wg.Add(concurrency)

	start := time.Now()

	for i := 0; i < concurrency; i++ {
		go func(id int) {
			defer wg.Done()
			conn, err := net.Dial("tcp", fmt.Sprintf("127.0.0.1:%d", global.Config.Service.TcpPort))
			if err != nil {
				atomic.AddInt64(&totalFail, int64(requestsPerConn))
				t.Logf("Connection failed: %v", err)
				return
			}
			defer conn.Close()

			// Timestamp queue for latency measurement
			timestamps := make(chan time.Time, requestsPerConn + 10)

			// Reader Goroutine
			readDone := make(chan bool)
			go func() {
				buf := make([]byte, 4096) // Larger buffer
				msgBuf := make([]byte, 0)
				for {
					n, err := conn.Read(buf)
					if err != nil {
						close(readDone)
						return
					}
					msgBuf = append(msgBuf, buf[:n]...)
					
					// Parse packets
					for len(msgBuf) >= 4 {
						pkgLen := binary.LittleEndian.Uint32(msgBuf[:4])
						if len(msgBuf) < int(pkgLen) {
							break
						}
						
						// One response received
						// _ := msgBuf[4:pkgLen] // Payload
						msgBuf = msgBuf[pkgLen:]
						
						// Calculate latency
						select {
						case ts := <-timestamps:
							lat := time.Since(ts)
							latencyLock.Lock()
							latencies = append(latencies, lat)
							latencyLock.Unlock()
							atomic.AddInt64(&totalSuccess, 1)
						default:
							// Should not happen if protocol is 1:1
						}
					}
				}
			}()

			// Sender Loop
			for j := 0; j < requestsPerConn; j++ {
				// Mix of Insert and Query
				var reqData any
				var cmd byte
				
				if j%2 == 0 {
					// Query
					cmd = Query
					reqData = request.QueryReq{
						BaseInfo: model.BaseInfo{
							GameName: "benchmark_game",
							Account:  fmt.Sprintf("user_%d", id),
						},
						Cnt: 1,
					}
				} else {
					// Insert
					cmd = Insert
					reqData = model.BaseInfo{
						GameName: "benchmark_game",
						Account:  fmt.Sprintf("user_%d", id),
						Rating:   j,
					}
				}

				pack, _ := json.Marshal(reqData)
				buf := bytes.NewBuffer(nil)
				binary.Write(buf, binary.LittleEndian, uint32(len(pack)+1+4))
				buf.WriteByte(cmd)
				buf.Write(pack)
				
				timestamps <- time.Now()
				_, err := conn.Write(buf.Bytes())
				if err != nil {
					t.Logf("Write failed: %v", err)
					break
				}
			}
			
			// Wait for responses
			timeout := time.After(10 * time.Second)
			ticker := time.NewTicker(100 * time.Millisecond)
			defer ticker.Stop()
			
			for {
				select {
				case <-timeout:
					return
				case <-readDone:
					return
				case <-ticker.C:
					if len(timestamps) == 0 {
						return
					}
				}
			}
		}(i)
	}

	wg.Wait()
	totalTime := time.Since(start)

	// Stats
	fmt.Printf("Total Time: %v\n", totalTime)
	fmt.Printf("Total Requests: %d\n", totalSuccess)
	fmt.Printf("QPS: %.2f\n", float64(totalSuccess)/totalTime.Seconds())
	
	// Latency Stats
	var totalLat time.Duration
	var maxLat time.Duration
	count95 := 0
	
	latencyLock.Lock() // Use lock for read as well just in case
	for _, l := range latencies {
		totalLat += l
		if l > maxLat {
			maxLat = l
		}
		if l < 100*time.Millisecond {
			count95++
		}
	}
	count := len(latencies)
	latencyLock.Unlock()
	
	avgLat := time.Duration(0)
	if count > 0 {
		avgLat = totalLat / time.Duration(count)
	}
	
	percent95 := 0.0
	if count > 0 {
		percent95 = float64(count95) / float64(count) * 100
	}

	fmt.Printf("Avg Latency: %v\n", avgLat)
	fmt.Printf("Max Latency: %v\n", maxLat)
	fmt.Printf("Requests < 100ms: %.2f%%\n", percent95)

	if percent95 < 95.0 {
		t.Logf("Warning: 95%% latency target not met (got %.2f%%)", percent95)
	}
	if float64(totalSuccess)/totalTime.Seconds() < 1000 {
		t.Logf("Warning: 1000 QPS target not met")
	}
}
