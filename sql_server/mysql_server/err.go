package mysql_server

import (
	"errors"
	"sql_server/model"
)

var (
	NoGameNameErr = errors.New("游戏名不能为空")
	NoAccountErr  = errors.New("账号名不能为空")
	QueryToEndErr = errors.New("查询计数已到末尾")
)

func checkGameModel(game *model.BaseInfo) error {
	if game.GameName == "" {
		return NoGameNameErr
	}
	if game.Account == "" {
		return NoAccountErr
	}
	return nil
}

func checkGameName(gameName string) error {
	if gameName == "" {
		return NoGameNameErr
	}
	return nil
}
