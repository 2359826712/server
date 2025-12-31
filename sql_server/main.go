package main

import (
	"sql_server/global"
	"sql_server/initialize"
	"sql_server/service"
	"sql_server/mysql_server"
)

func main() {
	initialize.Viper()
	global.DB = initialize.InitGormDb(global.Config.Mysql)
	if global.DB != nil {
		db, _ := global.DB.DB()
		defer db.Close()
	}
	mysql_server.StartTalkUpdater(4)
	go service.StartTcpServer()
	service.StartHttpServer()
}
