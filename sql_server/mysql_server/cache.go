package mysql_server

import (
	"errors"
	"fmt"
	"sql_server/global"
	"sql_server/model"
	"sql_server/model/request"
	"time"
)

var (
	locker        *lockList
	inserts       map[string]map[string]*model.Account
	aescQueryList map[string][]*model.BaseInfo
	descQueryList map[string][]*model.BaseInfo
	counter       map[string]*model.Counter
	ticker        *time.Ticker
)

func init() {
	locker = &lockList{}
	inserts = make(map[string]map[string]*model.Account)
	aescQueryList = make(map[string][]*model.BaseInfo)
	descQueryList = make(map[string][]*model.BaseInfo)
	counter = make(map[string]*model.Counter)
	ticker = time.NewTicker(5 * time.Minute)
	fmt.Println("初始化缓存")
}

func Insert(base *model.BaseInfo) ([]*model.Account, error) {
	if base == nil {
		return nil, errors.New("数据为空")
	}
	if err := checkGameModel(base); err != nil {
		return nil, err
	}
	res := Refresh(base)
	if res != nil {
		return res, nil
	}
	// 表锁, 使得单张表锁住
	tableLock := locker.getLock(base.GameName + "_cacha_insert")
	tableLock.Lock()
	defer tableLock.Unlock()

	mu := locker.getLock("cacha_insert")
	mu.Lock()
	insertList := inserts[base.GameName]
	if insertList == nil {
		insertList = make(map[string]*model.Account)
	}
	mu.Unlock()

	insertList[base.Account] = &model.Account{
		BaseInfo:   *base,
		OnlineTime: time.Now(),
	}
	res = []*model.Account{}
	if len(insertList) >= global.Config.Cache.InsertCount {
		for _, v := range insertList {
			res = append(res, v)
		}
		clear(insertList)
	}
	// 更新内存
	mu.Lock()
	inserts[base.GameName] = insertList
	mu.Unlock()
	return res, nil
}

func Query(query *request.QueryReq) []*model.BaseInfo {
	tableLock := locker.getLock(query.GameName + "_cacha_insert")
	tableLock.Lock()
	defer tableLock.Unlock()

	mu := locker.getLock("cacha_insert")
	mu.Lock()
	insertList := inserts[query.GameName]
	if insertList == nil {
		insertList = make(map[string]*model.Account)
		return nil
	}
	mu.Unlock()

	list := make([]*model.BaseInfo, 0)
	now := time.Now()
	for _, v := range insertList {
		if query.Account != "" && query.Account != v.Account {
			continue
		}
		if query.BZone != "" && query.BZone != v.BZone {
			continue
		}
		if query.SZone != "" && query.SZone != v.SZone {
			continue
		}
		if query.Rating != 0 && query.Rating != v.Rating {
			continue
		}
		if query.OnlineDuration != 0 && uint(now.Sub(v.OnlineTime).Minutes()) > query.OnlineDuration {
			continue
		}
		switch query.TalkChannel {
		case 1:
			if !v.LastTalkTime1.IsZero() && uint(now.Sub(v.LastTalkTime1).Minutes()) > query.OnlineDuration {
				break
			} else {
				list = append(list, &v.BaseInfo)
				v.LastTalkTime1 = now
			}
		case 2:
			if !v.LastTalkTime2.IsZero() && uint(now.Sub(v.LastTalkTime2).Minutes()) > query.OnlineDuration {
				break
			} else {
				list = append(list, &v.BaseInfo)
				v.LastTalkTime1 = now
			}
		case 3:
			if !v.LastTalkTime3.IsZero() && uint(now.Sub(v.LastTalkTime3).Minutes()) > query.OnlineDuration {
				break
			} else {
				list = append(list, &v.BaseInfo)
				v.LastTalkTime1 = now
			}
		case 4:
			if !v.LastTalkTime4.IsZero() && uint(now.Sub(v.LastTalkTime4).Minutes()) > query.OnlineDuration {
				break
			} else {
				list = append(list, &v.BaseInfo)
				v.LastTalkTime1 = now
			}
		case 5:
			if !v.LastTalkTime5.IsZero() && uint(now.Sub(v.LastTalkTime5).Minutes()) > query.OnlineDuration {
				break
			} else {
				list = append(list, &v.BaseInfo)
				v.LastTalkTime1 = now
			}
		case 6:
			if !v.LastTalkTime6.IsZero() && uint(now.Sub(v.LastTalkTime6).Minutes()) > query.OnlineDuration {
				break
			} else {
				list = append(list, &v.BaseInfo)
				v.LastTalkTime1 = now
			}
		}
	}
	return list
}

// 每隔一段时间就全部保存
func Refresh(base *model.BaseInfo) []*model.Account {
	mu := locker.getLock("cacha_insert")
	mu.Lock()
	defer mu.Unlock()

	select {
	case <-ticker.C:
		fmt.Println("更新所有插入")
		if inserts[base.GameName] == nil {
			inserts[base.GameName] = make(map[string]*model.Account)
		}
		inserts[base.GameName][base.Account] = &model.Account{
			BaseInfo:   *base,
			OnlineTime: time.Now(),
		}
		res := []*model.Account{}
		for _, insertList := range inserts {
			for _, v := range insertList {
				res = append(res, v)
			}
		}
		clear(inserts)
		return res
	default:
		return nil
	}
}

func ResetCounter(gameName string, descCount int) {
	mu := locker.getLock("cache_aesc_query")
	mu.Lock()
	defer mu.Unlock()
	mu2 := locker.getLock("cache_desc_query")
	mu2.Lock()
	defer mu2.Unlock()

	ctr := counter[gameName]
	if ctr == nil {
		ctr = &model.Counter{
			GameName: gameName,
		}
	}
	ctr.Counter = 0
	ctr.DescCounter = int64(descCount)
	counter[gameName] = ctr
}

func QueryAesc(query *request.QueryReq) ([]*model.BaseInfo, error) {
	// 表锁
	tableLock := locker.getLock(query.GameName + "_cache_aesc_query")
	tableLock.Lock()
	defer tableLock.Unlock()

	// map锁
	mu := locker.getLock("cache_aesc_query")
	mu.Lock()
	queryList := aescQueryList[query.GameName]
	ctr := counter[query.GameName]
	mu.Unlock()

	if ctr == nil {
		var cter = model.Counter{
			GameName: query.GameName,
		}
		err := global.DB.Table("counters_esc").Where("game_name = ?", query.GameName).FirstOrCreate(&cter).Error
		if err != nil {
			return nil, err
		}
		if cter.DescCounter <= 0 {
			global.DB.Table(query.GameName).Count(&cter.DescCounter)
		}
		ctr = &cter
	}
	cnt := max(500, query.Cnt)
	if len(queryList) < int(cnt) {
		list := make([]*model.BaseInfo, 0)
		db := global.DB.Table(query.GameName).Select("*")
		if err := db.Limit(global.Config.Cache.QueryCount).Where("game_name = ? and id > ?", query.GameName, ctr.Counter).Find(&list).Error; err != nil {
			return nil, err
		}
		if len(list) == 0 {
			return nil, QueryToEndErr
		}
		queryList = append(queryList, list...)
	}
	if queryList == nil {
		return nil, nil
	}
	ctr.Counter += int64(query.Cnt)
	// 降低数据库更新频率
	if ctr.Counter%200 == 0 {
		if err := global.DB.Table("counters_esc").Where("game_name = ?", query.GameName).Update("counter", ctr.Counter+int64(query.Cnt)).Error; err != nil {
			return nil, err
		}
	}
	output := queryList[:query.Cnt]
	queryList = queryList[query.Cnt:]
	// 更新内存
	mu.Lock()
	aescQueryList[query.GameName] = queryList
	counter[query.GameName] = ctr
	mu.Unlock()
	return output, nil
}

func QueryDesc(query *request.QueryReq) ([]*model.BaseInfo, error) {
	// 表锁
	tableLock := locker.getLock(query.GameName + "_cache_desc_query")
	tableLock.Lock()
	defer tableLock.Unlock()

	// map锁
	mu := locker.getLock("cache_desc_query")
	mu.Lock()
	queryList := descQueryList[query.GameName]
	ctr := counter[query.GameName]
	mu.Unlock()

	if ctr == nil {
		var cter = model.Counter{
			GameName: query.GameName,
		}
		err := global.DB.Table("counters_esc").Where("game_name = ?", query.GameName).FirstOrCreate(&cter).Error
		if err != nil {
			return nil, err
		}
		if cter.DescCounter <= 0 {
			global.DB.Table(query.GameName).Count(&cter.DescCounter)
		}
		ctr = &cter
	}
	if ctr.DescCounter-int64(query.Cnt) <= 0 {
		return nil, QueryToEndErr
	}
	cnt := max(500, query.Cnt)
	if len(queryList) < int(cnt) {
		list := make([]*model.BaseInfo, 0)
		db := global.DB.Table(query.GameName).Select("*")
		if err := db.Limit(global.Config.Cache.QueryCount).Where("game_name = ? and id < ? and id >= ?", query.GameName, ctr.DescCounter, ctr.DescCounter-int64(query.Cnt)).Find(&list).Error; err != nil {
			return nil, err
		}
		if len(list) == 0 {
			return nil, QueryToEndErr
		}
		queryList = append(queryList, list...)
	}
	if queryList == nil {
		return nil, nil
	}
	ctr.Counter -= int64(query.Cnt)
	// 降低数据库更新频率
	if ctr.Counter%200 == 0 {
		if err := global.DB.Table("counters_esc").Where("game_name = ?", query.GameName).Update("desc_counter", ctr.DescCounter-int64(query.Cnt)).Error; err != nil {
			return nil, err
		}
	}
	tmp := queryList[len(queryList)-int(query.Cnt):]
	queryList = queryList[:len(queryList)-int(query.Cnt)]

	// 更新内存
	mu.Lock()
	descQueryList[query.GameName] = queryList
	counter[query.GameName] = ctr
	mu.Unlock()
	return tmp, nil
}
