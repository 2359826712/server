// 自动生成模板D2
package model

import (
	"fmt"
	"sql_server/global"
	"time"
)

type BaseInfo struct {
	ID       int    `json:"ID" gorm:"primaryKey"`
	GameName string `json:"game_name"`
	Account  string `json:"account"`
	Password string `json:"password"`
	BZone    string `json:"b_zone"`
	SZone    string `json:"s_zone"`
	Status   int    `json:"status"`
	InUse    bool   `json:"in_use"`
}

type Account struct {
	BaseInfo
	CreatedAt time.Time `json:"created_at"`
}

// D2迁移到数据库
func AutoMigrate(gameName string) error {
	createTableSQL := fmt.Sprintf(`CREATE TABLE IF NOT EXISTS `+`%s`+`(
	    id INT PRIMARY KEY AUTO_INCREMENT,
	    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		game_name VARCHAR(255),
	    account VARCHAR(255),
		password VARCHAR(255),
	    b_zone VARCHAR(255),
	    s_zone VARCHAR(255),
	    status INT,
	    in_use TINYINT(1) DEFAULT 0);`, gameName)
	if err := global.DB.Exec(createTableSQL).Error; err != nil {
		return fmt.Errorf("Failed to create table %s: %v", gameName, err)
	}
	return nil
}
