package service

import (
	"encoding/json"
	"fmt"
	"sql_server/model"
	"sql_server/model/request"
	"sql_server/model/response"
	"sql_server/mysql_server"
)

// 此时传进来的是一个完整的包
func handlePack(buf []byte) response.ResponseResult {
	buf = buf[4:]
	cmd := buf[0]
	buf = buf[1:]
	switch cmd {
	case CreateNewGameTable:
		return createNewGameTable(buf)
	case Insert:
		return insert(buf)
	case Update:
		return update(buf)
	case Query:
		return query(buf)
	}
	return response.Fail(fmt.Sprintf("命令%d暂无", cmd))
}

func createNewGameTable(buf []byte) response.ResponseResult {
	g := &model.BaseInfo{}
	if err := json.Unmarshal(buf, g); err != nil {
		return response.Fail(err.Error())
	}
	if err := mysql_server.MysqlService.NewGame(g.GameName); err != nil {
		return response.Fail(err.Error())
	}
	return response.OK()
}

func insert(buf []byte) response.ResponseResult {
	g := &model.BaseInfo{}
	if err := json.Unmarshal(buf, g); err != nil {
		return response.Fail(err.Error())
	}
	if err := mysql_server.MysqlService.Insert(g); err != nil {
		return response.Fail(err.Error())
	}
	return response.OK()
}

func update(buf []byte) response.ResponseResult {
	g := &model.BaseInfo{}
	if err := json.Unmarshal(buf, g); err != nil {
		return response.Fail(err.Error())
	}
	if err := mysql_server.MysqlService.Update(g); err != nil {
		return response.Fail(err.Error())
	}
	return response.OK()
}

func query(buf []byte) response.ResponseResult {
	q := &request.QueryReq{}
	if err := json.Unmarshal(buf, q); err != nil {
		return response.Fail(err.Error())
	}
	if list, err := mysql_server.MysqlService.Query(q); err != nil {
		return response.Fail(err.Error())
	} else {
		return response.OkWithData(list)
	}
}

