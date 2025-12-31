package service

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"log"
	"net/http"
	"sql_server/api"
	"sql_server/global"
	"time"
)

func StartHttpServer() {
	gin.SetMode(gin.ReleaseMode)
	router := gin.Default()
	router.POST("/createNewGame", api.CreateNewGameApi)
	router.POST("/insert", api.InsertApi)
	router.POST("/update", api.UpdateApi)
	router.POST("/query", api.QueryApi)

	router.POST("/clearTalkChannel", api.ClearTalkChannelApi)
	// 启动 HTTP 服务器
	log.Printf("start http server, port: %d\n", global.Config.Service.HttpPort)
	address := fmt.Sprintf(":%d", global.Config.Service.HttpPort)
	s := &http.Server{
		Addr:              address,
		Handler:           router,
		ReadTimeout:       20 * time.Second,
		ReadHeaderTimeout: 20 * time.Second,
		WriteTimeout:      20 * time.Second,
		MaxHeaderBytes:    1 << 20,
	}
	err := s.ListenAndServe()
	if err != nil {
		log.Fatalf("start http server error: %v", err)
	}
}
