package mysql_server

import (
	"sql_server/global"
	"sql_server/model"
	"time"
)

type talkUpdateItem struct {
	game   string
	ids    []int
	field  string
	when   time.Time
}

var talkQueue = make(chan talkUpdateItem, 10000)

func StartTalkUpdater(worker int) {
	if worker <= 0 {
		worker = 4
	}
	for i := 0; i < worker; i++ {
		go func() {
			for it := range talkQueue {
				if len(it.ids) == 0 || it.field == "" || it.game == "" {
					continue
				}
				global.DB.Table(it.game).Where("id IN ?", it.ids).Update(it.field, it.when)
			}
		}()
	}
}

func enqueueTalkUpdate(list []*model.BaseInfo, talkChannel string) {
	if talkChannel == "" {
		return
	}
	if len(list) == 0 {
		return
	}
	ids := make([]int, 0, len(list))
	game := list[0].GameName
	for _, gm := range list {
		ids = append(ids, gm.ID)
	}
	talkQueue <- talkUpdateItem{
		game:  game,
		ids:   ids,
		field: talkChannel,
		when:  time.Now(),
	}
}
