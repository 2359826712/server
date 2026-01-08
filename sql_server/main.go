package main

import (
	"sql_server/global"
	"sql_server/initialize"
	"sql_server/model"
	"sql_server/service"
)

func main() {
	initialize.Viper()
	global.DB = initialize.InitGormDb(global.Config.Mysql)
	if global.DB != nil {
		db, _ := global.DB.DB()
		defer db.Close()
	}
	if err := model.AutoMigrateCounters(); err != nil {
		panic(err)
	}
	//service.StartTcpServer()
	service.StartHttpServer()

}
