package mysql_server

import (
	"errors"
	"fmt"
	"sql_server/global"
	"sql_server/model"
	"sql_server/model/request"
	"sync"
	"time"
	"gorm.io/gorm"
)

var MysqlService = mysqlService{locker: &lockList{}}

type lockList struct {
	locks sync.Map
}

func (l *lockList) getLock(gameName string) *sync.Mutex {
	lock, loaded := l.locks.LoadOrStore(gameName, new(sync.Mutex))
	if !loaded {
		return lock.(*sync.Mutex)
	}
	return lock.(*sync.Mutex)
}

type mysqlService struct {
	locker *lockList
}

// 创建表
func (m *mysqlService) NewGame(gameName string) error {
	if gameName == "" {
		return errors.New("游戏名为空")
	}
	lock := m.locker.getLock(gameName)
	lock.Lock()
	defer lock.Unlock()
	return model.AutoMigrate(gameName)
}

// 新增数据
func (m *mysqlService) Insert(base *model.BaseInfo) error {
	if base == nil {
		return errors.New("数据为空")
	}
	if err := checkGameModel(base); err != nil {
		return err
	}
	lock := m.locker.getLock(base.GameName)
	lock.Lock()
	defer lock.Unlock()
	// 确保旧表补齐新列
	if err := model.AutoMigrate(base.GameName); err != nil {
		return err
	}
	// 默认 in_use 为 "false"
	if base.InUse == "" {
		base.InUse = "false"
	}
	acc := &model.Account{
		BaseInfo: *base,
	}
	var g = &model.Account{}
	err := global.DB.Table(base.GameName).Where("account = ?", base.Account).First(g).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return global.DB.Table(base.GameName).Create(acc).Error
	} else if err == nil {
		return m.update(base)
	} else {
		return err
	}
}

// 即再次采集
func (m *mysqlService) Update(game *model.BaseInfo) error {
	if game == nil {
		return errors.New("数据为空")
	}
	if err := checkGameModel(game); err != nil {
		return err
	}
	lock := m.locker.getLock(game.GameName)
	lock.Lock()
	defer lock.Unlock()
	// 确保旧表补齐新列
	if err := model.AutoMigrate(game.GameName); err != nil {
		return err
	}
	return m.update(game)
}

func (m *mysqlService) update(game *model.BaseInfo) error {
	if game == nil {
		return errors.New("数据为空")
	}
	db := global.DB.Table(game.GameName).Where("account = ?", game.Account)
	updates := map[string]interface{}{}
	if game.Level != "" {
		updates["level"] = game.Level
	}
	if game.ComputerNumber != "" {
		updates["computer_number"] = game.ComputerNumber
	}
	if game.Status != 0 {
		updates["status"] = game.Status
	}
	if len(updates) == 0 {
		return nil
	}
	return db.Updates(updates).Error
}

func (m *mysqlService) Delete(game *model.BaseInfo) error {
	if game == nil {
		return errors.New("数据为空")
	}
	if err := checkGameModel(game); err != nil {
		return err
	}
	lock := m.locker.getLock(game.GameName)
	lock.Lock()
	defer lock.Unlock()
	db := global.DB.Table(game.GameName).Where("account = ?", game.Account)
	return db.Delete(&model.Account{}).Error
}

func (m *mysqlService) updateTalkTime(list []*model.BaseInfo, talkChannel string) error {
	if talkChannel == "" {
		return errors.New("talk_channel is empty")
	}
	now := time.Now()
	for _, gm := range list {
		if err := global.DB.Table(gm.GameName).Where("id = ?", gm.ID).Update(talkChannel, now).Error; err != nil {
			return err
		}
	}
	return nil
}

func (m *mysqlService) ClearTalkTime(gameName string, talkChannel uint) error {
	if err := checkGameName(gameName); err != nil {
		return err
	}
	lock := m.locker.getLock(gameName)

	lock.Lock()
	defer lock.Unlock()
	field, err := getTalkChannel(talkChannel)
	if err != nil {
		return err
	}
	return global.DB.Table(gameName).Where("id >= 0").Update(field, "2000-01-01 00:00:00").Error
}

func (m *mysqlService) Query(query *request.QueryReq) (list []*model.BaseInfo, err error) {
	if query == nil {
		return nil, errors.New("查询数据为空")
	}
	if err = checkGameName(query.GameName); err != nil {
		return nil, err
	}
	lock := m.locker.getLock(query.GameName)
	lock.Lock()
	defer lock.Unlock()
	gm := query.BaseInfo
	list = make([]*model.BaseInfo, 0)
	err = global.DB.Transaction(func(tx *gorm.DB) error {
		db := tx.Table(gm.GameName).Select("*")
		if gm.Account != "" {
			db = db.Where("account = ?", gm.Account)
		}
		if gm.BZone != "" {
			db = db.Where("b_zone = ?", gm.BZone)
		}
		if gm.SZone != "" {
			db = db.Where("s_zone = ?", gm.SZone)
		}
		if gm.Level != "" {
			db = db.Where("level = ?", gm.Level)
		}
		if gm.ComputerNumber != "" {
			db = db.Where("computer_number = ?", gm.ComputerNumber)
		}
		if gm.InUse != "" {
			db = db.Where("in_use = ?", gm.InUse)
		}
		if query.Status != 0 {
			db = db.Where("status = ?", gm.Status)
		}
		var item model.BaseInfo
		if e := db.Order("created_at ASC").Limit(1).Take(&item).Error; e != nil {
			return e
		}
		list = append(list, &item)
		return nil
	})
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return list, nil
	}
	return list, err
}

func getTalkChannel(talkChannel uint) (string, error) {
	field := ""
	switch talkChannel {
	case 0:
		return "", nil
	case 1:
		field = "last_talk_time1"
	case 2:
		field = "last_talk_time2"
	case 3:
		field = "last_talk_time3"
	case 4:
		field = "last_talk_time4"
	case 5:
		field = "last_talk_time5"
	case 6:
		field = "last_talk_time6"
	default:
		return "", fmt.Errorf("喊话通道%d暂无", talkChannel)
	}
	return field, nil
}
