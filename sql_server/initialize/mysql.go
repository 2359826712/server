package initialize

import (
	"database/sql"
	"fmt"
	"gorm.io/driver/mysql"
	"gorm.io/gorm"
	"log"
	"sql_server/config"
	"time"
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
	// SetMaxIdleConns 设置空闲连接池中连接的最大数量
	if ms.MaxIdleConns > 0 {
		sqlDB.SetMaxIdleConns(ms.MaxIdleConns)
	} else {
		sqlDB.SetMaxIdleConns(10)
	}

	// SetMaxOpenConns 设置打开数据库连接的最大数量
	if ms.MaxOpenConns > 0 {
		sqlDB.SetMaxOpenConns(ms.MaxOpenConns)
	} else {
		sqlDB.SetMaxOpenConns(100)
	}

	// SetConnMaxLifetime 设置了连接可复用的最大时间
	if ms.ConnMaxLifetime > 0 {
		sqlDB.SetConnMaxLifetime(time.Duration(ms.ConnMaxLifetime) * time.Second)
	} else {
		sqlDB.SetConnMaxLifetime(time.Hour)
	}
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
