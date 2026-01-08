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
	acc := &model.Account{
		BaseInfo:   *base,
		OnlineTime: time.Now(),
	}
	var g = &model.Account{}
	err := global.DB.Table(base.GameName).Where("account", base.Account).First(g).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return global.DB.Table(base.GameName).Create(acc).Error
	} else if g.GameName != "" {
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
	return m.update(game)
}

func (m *mysqlService) update(game *model.BaseInfo) error {
	if game == nil {
		return errors.New("数据为空")
	}
	db := global.DB.Table(game.GameName).Where("account = ?", game.Account)
	acc := &model.Account{
		BaseInfo:   *game,
		OnlineTime: time.Now(),
	}
	return db.Select("b_zone", "s_zone", "rating", "online_time").Updates(acc).Error
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

func (m *mysqlService) ResetQueryCounter(gameName string) error {
	var total int64
	if err := global.DB.Table(gameName).Count(&total).Error; err != nil {
		return err
	}
	return global.DB.Table("counters_esc").Where("game_name = ?", gameName).Updates(
		map[string]interface{}{
			"counter":      0,
			"desc_counter": total,
		},
	).Error
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
	db := global.DB.Table(gm.GameName).Select("*")
	now := time.Now()
	// 默认至少一条
	if query.Cnt == 0 {
		query.Cnt = 1
	}
	if gm.Account != "" {
		db = db.Where("account = ?", gm.Account)
	}
	if gm.BZone != "" {
		db = db.Where("b_zone = ?", gm.BZone)
	}
	if gm.SZone != "" {
		db = db.Where("s_zone = ?", gm.SZone)
	}
	if gm.Rating != 0 {
		db = db.Where("rating = ?", gm.Rating)
	}
	if query.OnlineDuration != 0 {
		db = db.Where("TIMESTAMPDIFF(MINUTE, online_time, ?) < ?", now, query.OnlineDuration)
	}
	talkChannel, err := getTalkChannel(query.TalkChannel)
	if err != nil {
		return nil, err
	}
	if query.TalkChannel != 0 {
		db = db.Where(fmt.Sprintf("TIMESTAMPDIFF(MINUTE, %s, ?) > ?", talkChannel), now, query.OnlineDuration)
	}
	list = make([]*model.BaseInfo, 0)
	if err = db.Limit(int(query.Cnt)).Where("game_name = ?", query.GameName).Find(&list).Error; err != nil {
		return nil, err
	}
	if err = m.updateTalkTime(list, talkChannel); err != nil {
		return nil, err
	}
	return list, err
}

func (m *mysqlService) QueryNoUpdate(query *request.QueryReq) (list []*model.BaseInfo, err error) {
	if query == nil {
		return nil, errors.New("查询数据为空")
	}
	if err = checkGameName(query.GameName); err != nil {
		return nil, err
	}
	lock := m.locker.getLock(query.GameName + "counter")
	// 先计数
	lock.Lock()
	var cter = model.Counter{
		GameName: query.GameName,
	}
	err = global.DB.Table("counters_esc").Where("game_name = ?", query.GameName).FirstOrCreate(&cter).Error
	if err != nil {
		lock.Unlock()
		return nil, err
	}
	if cter.DescCounter == 0 {
		global.DB.Table(query.GameName).Count(&cter.DescCounter)
	}
	if query.IsDesc {
		err = global.DB.Table("counters_esc").Where("game_name = ?", query.GameName).Update("desc_counter", cter.DescCounter-int64(query.Cnt)).Error
	} else {
		err = global.DB.Table("counters_esc").Where("game_name = ?", query.GameName).Update("counter", cter.Counter+int64(query.Cnt)).Error
	}
	lock.Unlock()
	if err != nil {
		return nil, err
	}
	gm := query.BaseInfo
	db := global.DB.Table(gm.GameName).Select("*")
	// 默认至少一条
	if query.Cnt == 0 {
		query.Cnt = 1
	}
	list = make([]*model.BaseInfo, 0)
	if query.IsDesc {
		if cter.DescCounter-int64(query.Cnt) < 0 {
			return nil, QueryToEndErr
		}
		if err = db.Limit(int(query.Cnt)).Where("game_name = ? and id < ? and id >= ?", query.GameName, cter.DescCounter, cter.DescCounter-int64(query.Cnt)).Find(&list).Error; err != nil {
			return nil, err
		}
	} else {
		if err = db.Limit(int(query.Cnt)).Where("game_name = ? and id > ?", query.GameName, cter.Counter).Find(&list).Error; err != nil {
			return nil, err
		}
	}
	if len(list) == 0 {
		return nil, QueryToEndErr
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
