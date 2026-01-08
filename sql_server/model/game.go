// 自动生成模板D2
package model

import (
	"fmt"
	"sql_server/global"
	"time"
)

type BaseInfo struct {
	ID       int    `json:"ID" gorm:"primaryKey"`
	GameName string `json:"game_name"` // 用作表名
	Account  string `json:"account"`
	BZone    string `json:"b_zone"` //大区
	SZone    string `json:"s_zone"` //小区
	Rating   int    `json:"rating"` //等级
}

type Account struct {
	BaseInfo
	CreatedAt     time.Time `json:"created_at"`                                           //首次插入时间
	OnlineTime    time.Time `json:"online_time"`                                          //在线时间
	LastTalkTime1 time.Time `json:"last_talk_time1" gorm:"default:'2000-01-01 00:00:00'"` //最后喊话时间1
	LastTalkTime2 time.Time `json:"last_talk_time2" gorm:"default:'2000-01-01 00:00:00'"` //最后喊话时间2
	LastTalkTime3 time.Time `json:"last_talk_time3" gorm:"default:'2000-01-01 00:00:00'"` //最后喊话时间3
	LastTalkTime4 time.Time `json:"last_talk_time4" gorm:"default:'2000-01-01 00:00:00'"` //最后喊话时间4
	LastTalkTime5 time.Time `json:"last_talk_time5" gorm:"default:'2000-01-01 00:00:00'"` //最后喊话时间5
	LastTalkTime6 time.Time `json:"last_talk_time6" gorm:"default:'2000-01-01 00:00:00'"` //最后喊话时间6
}

type Counter struct {
	ID          int    `json:"ID" gorm:"primaryKey"`
	GameName    string `json:"game_name"`
	Counter     int64  `json:"counter"`
	DescCounter int64  `json:"desc_counter"`
}

// D2迁移到数据库
func AutoMigrate(gameName string) error {
	createTableSQL := fmt.Sprintf(`CREATE TABLE IF NOT EXISTS `+`%s`+`(
    id INT PRIMARY KEY AUTO_INCREMENT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,  
    online_time DATETIME,                                  
	game_name VARCHAR(255),
    account VARCHAR(255),                                  
    b_zone VARCHAR(255),                                   
    s_zone VARCHAR(255),                                    
    rating INT,                                          
    last_talk_time1 DATETIME DEFAULT '2000-01-01 00:00:00',                               
    last_talk_time2 DATETIME DEFAULT '2000-01-01 00:00:00',                               
    last_talk_time3 DATETIME DEFAULT '2000-01-01 00:00:00',                               
    last_talk_time4 DATETIME DEFAULT '2000-01-01 00:00:00',                               
    last_talk_time5 DATETIME DEFAULT '2000-01-01 00:00:00',                                
    last_talk_time6 DATETIME DEFAULT '2000-01-01 00:00:00');`, gameName)
	if err := global.DB.Exec(createTableSQL).Error; err != nil {
		return fmt.Errorf("Failed to create table %s: %v", gameName, err)
	}
	return nil
}

func AutoMigrateCounters() error {
	createTableSql := `CREATE TABLE IF NOT EXISTS counters_esc (id INT PRIMARY KEY AUTO_INCREMENT,game_name VARCHAR(255),counter INT, desc_counter INT)`
	if err := global.DB.Exec(createTableSql).Error; err != nil {
		return fmt.Errorf("Failed to create table counters_esc: %v", err)
	}
	return nil
}
