package global

import (
	"gorm.io/gorm"
	"sql_server/config"
)

var (
	DB     *gorm.DB
	Config config.Config
)
