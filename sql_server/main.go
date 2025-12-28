package main

import (
	"sql_server/global"
	"sql_server/initialize"
	"sql_server/service"
)

func main() {
	initialize.Viper()
	global.DB = initialize.InitGormDb(global.Config.Mysql)
	if global.DB != nil {
		db, _ := global.DB.DB()
		defer db.Close()
	}
	//service.StartTcpServer()
	service.StartHttpServer()

}
