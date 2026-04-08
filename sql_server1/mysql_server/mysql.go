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
	if game.Password != "" {
		updates["password"] = game.Password
	}
	if game.EmailAccount != "" {
		updates["email_account"] = game.EmailAccount
	}
	if game.EmailPassword != "" {
		updates["email_password"] = game.EmailPassword
	}
	if game.Address != "" {
		updates["address"] = game.Address
	}
	if game.ComputerNumber != "" {
		updates["computer_number"] = game.ComputerNumber
	}
	if game.Status != 0 {
		updates["status"] = game.Status
	}
	if game.InUse != "" {
		updates["in_use"] = game.InUse
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

func (m *mysqlService) ClearStatus(gameName string) error {
	if err := checkGameName(gameName); err != nil {
		return err
	}
	lock := m.locker.getLock(gameName)
	lock.Lock()
	defer lock.Unlock()
	updates := map[string]interface{}{
		"computer_number": "",
		"in_use":          "false",
		"status":          0,
	}
	return global.DB.Table(gameName).Where("id >= 0").Updates(updates).Error
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
		if gm.EmailAccount != "" {
			db = db.Where("email_account = ?", gm.EmailAccount)
		}
		if gm.EmailPassword != "" {
			db = db.Where("email_password = ?", gm.EmailPassword)
		}
		if gm.Address != "" {
			db = db.Where("address = ?", gm.Address)
		}
		if gm.ComputerNumber != "" {
			db = db.Where("computer_number = ?", gm.ComputerNumber)
		}
		if gm.InUse != "" {
			db = db.Where("in_use = ?", gm.InUse)
		}
		if query.Status != 0 || query.Status == 0 {
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
