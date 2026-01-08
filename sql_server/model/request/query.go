package request

import "sql_server/model"

type QueryReq struct {
	OnlineDuration uint `json:"online_duration"` // 在线时长, 单位分钟
	TalkChannel    uint `json:"talk_channel"`
	Cnt            uint `json:"cnt"`     // 返回最多多少条
	IsDesc         bool `json:"is_desc"` // 是否降序查询
	model.BaseInfo
}
