package api

import (
	"errors"
	"net/http"
	"sql_server/model"
	"sql_server/model/request"
	"sql_server/mysql_server"
	"sql_server/utils"

	"github.com/gin-gonic/gin"
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
	if q.OnlineDuration == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "在线时长不能为0"})
		return
	}
	if list, err := mysql_server.MysqlService.Query(&q); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
	} else {
		c.JSON(http.StatusOK, gin.H{
			"message": "query success",
			"data":    list,
		})
	}
}

func QueryNoUpdateApi(c *gin.Context) {
	var q request.QueryReq
	if err := c.ShouldBindJSON(&q); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if err := validatorGameName(q.GameName); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if list, err := mysql_server.MysqlService.QueryNoUpdate(&q); err != nil {
		if errors.Is(err, mysql_server.QueryToEndErr) {
			// 双方约定， 401表示计数到最大值
			c.JSON(http.StatusUnauthorized, gin.H{"error": err.Error()})
			return
		}
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
	} else {
		c.JSON(http.StatusOK, gin.H{
			"message": "query success",
			"data":    list,
		})
	}
}

func ResetQueryCounterApi(c *gin.Context) {
	var q request.QueryReq
	if err := c.ShouldBindJSON(&q); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if err := validatorGameName(q.GameName); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	mysql_server.MysqlService.ResetQueryCounter(q.GameName)
	c.JSON(http.StatusOK, gin.H{
		"message": "reset query counter success",
	})
}

func ClearTalkChannelApi(c *gin.Context) {
	var q = &request.QueryReq{}
	if err := c.ShouldBindJSON(q); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if err := validatorGameName(q.GameName); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if err := mysql_server.MysqlService.ClearTalkTime(q.GameName, q.TalkChannel); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"message": "clear talk time channel success",
	})
}

func validatorGameName(gameName string) error {
	if gameName == "" {
		return errors.New("游戏名不能为空, 因为是通过游戏名来确认表名")
	}
	return nil
}
