package mysql_server

import (
	"errors"
	"fmt"
	"sql_server/global"
	"sql_server/model"
	"sql_server/model/request"
	"time"

	"gorm.io/gorm"
)

var MysqlService = mysqlService{locker: &lockList{}}

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

func (m *mysqlService) Insert(base *model.BaseInfo) error {
	list, err := Insert(base)
	if err != nil {
		return err
	}
	go func() {
		for _, v := range list {
			_ = m.insert(v)
		}
	}()
	return nil
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
	acc := &model.Account{
		BaseInfo: *game,
	}
	return m.update(acc)
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
	ResetCounter(gameName, int(total))
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
	if len(list) == 0 {
		return Query(query), nil
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
	// 默认至少一条
	if query.Cnt == 0 {
		query.Cnt = 1
	}
	if query.IsDesc {
		return QueryDesc(query)
	}
	return QueryAesc(query)
}

// 新增数据
func (m *mysqlService) insert(acc *model.Account) error {
	if acc == nil {
		return errors.New("数据为空")
	}
	if err := checkGameModel(&acc.BaseInfo); err != nil {
		return err
	}
	lock := m.locker.getLock(acc.GameName)
	lock.Lock()
	defer lock.Unlock()

	var g = &model.Account{}
	err := global.DB.Table(acc.GameName).Where("account", acc.Account).First(g).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return global.DB.Table(acc.GameName).Create(acc).Error
	} else if g.GameName != "" {
		return m.update(acc)
	} else {
		return err
	}
}

func (m *mysqlService) update(acc *model.Account) error {
	if acc == nil {
		return errors.New("数据为空")
	}
	db := global.DB.Table(acc.GameName).Where("account = ?", acc.Account)
	var updateMap = map[string]interface{}{
		"b_zone":      acc.BZone,
		"s_zone":      acc.SZone,
		"rating":      acc.Rating,
		"online_time": time.Now(),
	}
	if !acc.LastTalkTime1.IsZero() {
		updateMap["last_talk_time1"] = acc.LastTalkTime1
	}
	if !acc.LastTalkTime2.IsZero() {
		updateMap["last_talk_time2"] = acc.LastTalkTime2
	}
	if !acc.LastTalkTime3.IsZero() {
		updateMap["last_talk_time3"] = acc.LastTalkTime3
	}
	if !acc.LastTalkTime4.IsZero() {
		updateMap["last_talk_time4"] = acc.LastTalkTime4
	}
	if !acc.LastTalkTime5.IsZero() {
		updateMap["last_talk_time5"] = acc.LastTalkTime5
	}
	if !acc.LastTalkTime6.IsZero() {
		updateMap["last_talk_time6"] = acc.LastTalkTime6
	}
	return db.Updates(updateMap).Error
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
