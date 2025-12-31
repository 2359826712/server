package mysql_server

import (
	"errors"
	"fmt"
	"gorm.io/gorm/clause"
	"gorm.io/gorm"
	"sql_server/global"
	"sql_server/model"
	"sql_server/model/request"
	"time"
)

var MysqlService = mysqlService{}

type mysqlService struct {
}

// 创建表
func (m *mysqlService) NewGame(gameName string) error {
	if gameName == "" {
		return errors.New("游戏名为空")
	}
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

	acc := &model.Account{
		BaseInfo:   *base,
		OnlineTime: time.Now(),
	}

	return global.DB.Transaction(func(tx *gorm.DB) error {
		return tx.Table(base.GameName).
			Clauses(clause.OnConflict{
				Columns:   []clause.Column{{Name: "account"}},
				DoUpdates: clause.AssignmentColumns([]string{"b_zone", "s_zone", "rating", "online_time"}),
			}).
			Create(acc).Error
	})
}

// 即再次采集
func (m *mysqlService) Update(game *model.BaseInfo) error {
	if game == nil {
		return errors.New("数据为空")
	}
	if err := checkGameModel(game); err != nil {
		return err
	}
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
	if err = db.Limit(int(query.Cnt)).Find(&list).Error; err != nil {
		return nil, err
	}
	enqueueTalkUpdate(list, talkChannel)
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
