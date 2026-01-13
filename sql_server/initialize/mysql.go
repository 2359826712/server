package initialize

import (
	"database/sql"
	"fmt"
	"log"
	"sql_server/config"
	"time"

	"gorm.io/driver/mysql"
	"gorm.io/gorm"
)

func InitGormDb(ms config.Mysql) *gorm.DB {
	// 检查库是否已经存在
	exists := checkDatabaseExists(ms)
	if !exists {
		log.Printf("数据库%s不存在, 创建数据库\n", ms.Dbname)
		if err := createDatabase(ms); err != nil {
			panic(err)
		}
	} else {
		log.Printf("数据库%s已经存在\n", ms.Dbname)
	}
	mysqlConfig := mysql.Config{
		DriverName:    "",
		ServerVersion: "",
		DSN:           ms.Dsn(), // DSN data source name
	}
	db, err := gorm.Open(mysql.New(mysqlConfig))
	if err != nil {
		panic(err)
	}
	sqlDB, _ := db.DB()
	sqlDB.SetMaxIdleConns(50)
	sqlDB.SetMaxOpenConns(2000)
	sqlDB.SetConnMaxLifetime(time.Hour)
	sqlDB.SetConnMaxIdleTime(30 * time.Minute)
	return db
}

func createDatabase(ms config.Mysql) error {
	createSql := fmt.Sprintf("CREATE DATABASE IF NOT EXISTS `%s` DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_general_ci;", ms.Dbname)
	db, err := sql.Open("mysql", ms.DataSourceName())
	if err != nil {
		return err
	}
	defer func(db *sql.DB) {
		err = db.Close()
		if err != nil {
			log.Println(err)
		}
	}(db)
	if err = db.Ping(); err != nil {
		return err
	}
	_, err = db.Exec(createSql)
	return err
}

// checkDatabaseExists 检查数据库是否存在
func checkDatabaseExists(ms config.Mysql) bool {
	db, err := sql.Open("mysql", ms.DataSourceName())
	if err != nil {
		panic(err)
	}
	var exists bool
	query := "SELECT COUNT(*) > 0 FROM information_schema.schemata WHERE schema_name = ?"
	if err = db.QueryRow(query, ms.Dbname).Scan(&exists); err != nil {
		panic(err)
	}
	return exists
}
