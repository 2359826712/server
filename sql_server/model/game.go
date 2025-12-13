// 自动生成模板D2
package model

import (
	"fmt"
	"sql_server/global"
	"time"
)

type BaseInfo struct {
	ID             int    `json:"ID" gorm:"primaryKey"`
	GameName       string `json:"game_name"`
	Account        string `json:"account"`
	Password       string `json:"password"`
	BZone          string `json:"b_zone"`
	SZone          string `json:"s_zone"`
	Status         int    `json:"status"`
	InUse          string `json:"in_use"`
	Level          string `json:"level"`
	ComputerNumber string `json:"computer_number"`
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
	    in_use VARCHAR(5) NOT NULL DEFAULT 'false',
	    level VARCHAR(255),
	    computer_number VARCHAR(255));`, gameName)
	if err := global.DB.Exec(createTableSQL).Error; err != nil {
		return fmt.Errorf("Failed to create table %s: %v", gameName, err)
	}
	var levelCnt int
	if err := global.DB.Raw("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND COLUMN_NAME = 'level'", global.Config.Mysql.Dbname, gameName).Scan(&levelCnt).Error; err != nil {
		return err
	}
	if levelCnt == 0 {
		if err := global.DB.Exec(fmt.Sprintf("ALTER TABLE `%s` ADD COLUMN `level` VARCHAR(255) AFTER `in_use`", gameName)).Error; err != nil {
			return err
		}
	}
	var computerCnt int
	if err := global.DB.Raw("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND COLUMN_NAME = 'computer_number'", global.Config.Mysql.Dbname, gameName).Scan(&computerCnt).Error; err != nil {
		return err
	}
	if computerCnt == 0 {
		afterCol := "in_use"
		if levelCnt > 0 {
			afterCol = "level"
		}
		if err := global.DB.Exec(fmt.Sprintf("ALTER TABLE `%s` ADD COLUMN `computer_number` VARCHAR(255) AFTER `%s`", gameName, afterCol)).Error; err != nil {
			return err
		}
	}
	// ensure in_use column is VARCHAR(5) with 'false'/'true'
	var inUseType string
	if err := global.DB.Raw("SELECT DATA_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND COLUMN_NAME = 'in_use'", global.Config.Mysql.Dbname, gameName).Scan(&inUseType).Error; err != nil {
		return err
	}
	if inUseType != "varchar" {
		if err := global.DB.Exec(fmt.Sprintf("ALTER TABLE `%s` MODIFY COLUMN `in_use` VARCHAR(5) NOT NULL DEFAULT 'false'", gameName)).Error; err != nil {
			return err
		}
		// convert existing values to 'true'/'false'
		if err := global.DB.Exec(fmt.Sprintf("UPDATE `%s` SET `in_use` = CASE WHEN `in_use` IN ('1', 1, 'true') THEN 'true' ELSE 'false' END", gameName)).Error; err != nil {
			return err
		}
	}
	return nil
}
