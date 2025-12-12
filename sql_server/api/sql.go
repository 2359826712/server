package api

import (
	"errors"
	"github.com/gin-gonic/gin"
	"net/http"
	"sql_server/model"
	"sql_server/model/request"
	"sql_server/mysql_server"
	"sql_server/utils"
)

func CreateNewGameApi(c *gin.Context) {
	var game model.BaseInfo
	if err := c.ShouldBindJSON(&game); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if err := validatorGameName(game.GameName); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if !utils.IsValid(game.GameName) {
		c.JSON(http.StatusBadRequest, gin.H{"error": "游戏名必须是字母数字或下划线且以字母开头"})
		return
	}
	if err := mysql_server.MysqlService.NewGame(game.GameName); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"message": "create new game table success",
	})
}

func InsertApi(c *gin.Context) {
	var game model.BaseInfo
	if err := c.ShouldBindJSON(&game); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if err := validatorGameName(game.GameName); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if err := mysql_server.MysqlService.Insert(&game); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"message": "insert success",
	})
}

func QueryApi(c *gin.Context) {
	var q request.QueryReq
	if err := c.ShouldBindJSON(&q); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if err := validatorGameName(q.GameName); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if list, err := mysql_server.MysqlService.Query(&q); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
	} else {
		var data interface{} = nil
		if len(list) > 0 {
			data = list[0]
		}
		c.JSON(http.StatusOK, gin.H{
			"message": "query success",
			"data":    data,
		})
	}
}

func UpdateApi(c *gin.Context) {
	var game model.BaseInfo
	if err := c.ShouldBindJSON(&game); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if err := validatorGameName(game.GameName); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if err := mysql_server.MysqlService.Update(&game); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"message": "update success",
	})
}

func DeleteApi(c *gin.Context) {
	var game model.BaseInfo
	if err := c.ShouldBindJSON(&game); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if err := validatorGameName(game.GameName); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if err := mysql_server.MysqlService.Delete(&game); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"message": "delete success",
	})
}

func validatorGameName(gameName string) error {
	if gameName == "" {
		return errors.New("游戏名不能为空, 因为是通过游戏名来确认表名")
	}
	return nil
}
