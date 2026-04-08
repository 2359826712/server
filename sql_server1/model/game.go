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
	EmailAccount   string `json:"email_account"`
	EmailPassword  string `json:"email_password"`
	Status         int    `json:"status"`
	InUse          string `json:"in_use"`
	Address        string `json:"address"`
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
	    email_account VARCHAR(255),
	    email_password VARCHAR(255),
	    status INT,
	    in_use VARCHAR(5) NOT NULL DEFAULT 'false',
	    address VARCHAR(255),
	    computer_number VARCHAR(255));`, gameName)
	if err := global.DB.Exec(createTableSQL).Error; err != nil {
		return fmt.Errorf("Failed to create table %s: %v", gameName, err)
	}
	columnCnt := func(columnName string) (int, error) {
		var cnt int
		if err := global.DB.Raw("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND COLUMN_NAME = ?", global.Config.Mysql.Dbname, gameName, columnName).Scan(&cnt).Error; err != nil {
			return 0, err
		}
		return cnt, nil
	}
	ensureRenameOrAdd := func(oldCol, newCol, afterCol string) (int, error) {
		newCnt, err := columnCnt(newCol)
		if err != nil {
			return 0, err
		}
		oldCnt, err := columnCnt(oldCol)
		if err != nil {
			return 0, err
		}
		if newCnt == 0 && oldCnt > 0 {
			if err := global.DB.Exec(fmt.Sprintf("ALTER TABLE `%s` CHANGE COLUMN `%s` `%s` VARCHAR(255)", gameName, oldCol, newCol)).Error; err != nil {
				return 0, err
			}
			return 1, nil
		}
		if newCnt == 0 {
			if err := global.DB.Exec(fmt.Sprintf("ALTER TABLE `%s` ADD COLUMN `%s` VARCHAR(255) AFTER `%s`", gameName, newCol, afterCol)).Error; err != nil {
				return 0, err
			}
			return 1, nil
		}
		if oldCnt > 0 {
			if err := global.DB.Exec(fmt.Sprintf("UPDATE `%s` SET `%s` = `%s` WHERE (`%s` IS NULL OR `%s` = '') AND (`%s` IS NOT NULL AND `%s` <> '')", gameName, newCol, oldCol, newCol, newCol, oldCol, oldCol)).Error; err != nil {
				return newCnt, err
			}
		}
		return newCnt, nil
	}
	if _, err := ensureRenameOrAdd("b_zone", "email_account", "password"); err != nil {
		return err
	}
	if _, err := ensureRenameOrAdd("s_zone", "email_password", "email_account"); err != nil {
		return err
	}
	addressCnt, err := ensureRenameOrAdd("level", "address", "in_use")
	if err != nil {
		return err
	}
	var computerCnt int
	if err := global.DB.Raw("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND COLUMN_NAME = 'computer_number'", global.Config.Mysql.Dbname, gameName).Scan(&computerCnt).Error; err != nil {
		return err
	}
	if computerCnt == 0 {
		afterCol := "in_use"
		if addressCnt > 0 {
			afterCol = "address"
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
