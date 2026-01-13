package global

import (
	"sql_server/config"
	"sql_server/utils/timer"

	"gorm.io/gorm"
)

var (
	DB     *gorm.DB
	Config config.Config
	Timer  timer.Timer = timer.NewTimerTask()
)
