package service

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"log"
	"net"
	"os"
	"sql_server/global"
	"sql_server/model"
	"sql_server/model/request"
	"sql_server/model/response"
	"sql_server/service/buffer"
	"sync"
)

type Client struct {
	conn net.Conn
	once sync.Once
}

func newConn() net.Conn {
	conn, err := net.Dial("tcp", fmt.Sprintf("127.0.0.1:%d", global.Config.Service.TcpPort))
	if err != nil {
		log.Println("连接失败:", err)
		os.Exit(1)
	}
	return conn
}

func InitClient() *Client {
	c := &Client{
		conn: newConn(),
	}
	go c.recv()
	return c
}

func (c *Client) recv() {
	defer c.Close()
	read := make([]byte, 1024)
	buf := buffer.NewBuffer()
	for {
		if c.conn == nil {
			log.Println("收包结束")
			return
		}
		n, err := c.conn.Read(read)
		if err != nil {
			continue
		}
		buf.Write(read[:n])
		for {
			size := buf.GetPackageLength()
			if size == -1 {
				break
			}
			res := &response.Response{}
			if err = json.Unmarshal(buf.Pop(size)[4:], res); err != nil {
				log.Println(err)
				return
			}
			if res.Code == response.Success {
				log.Println("发包成功")
				if res.Game != nil {
					for _, v := range res.Game {
						log.Println(v)
					}
				}
			} else {
				log.Println("发包失败, 原因: ", res.ErrMsg)
			}
		}
	}

}

func (c *Client) Close() {
	go func() {
		c.once.Do(func() {
			if c.conn != nil {
				c.conn.Close()
			}
		})
	}()
}

// 客户端
// 发包形式
// 包长 uint32   4bytes
// 命令 byte( 0:创建新表, 1: 新增, 2:更新, 3:查询, 4:清理喊话通道)
// 内容: json数据
// 字段名:
// GameName string `json:"game_name"` // 用作表名
// BaseInfo  string `json:"account"`
// BZone    string `json:"b_zone"` //大区
// SZone    string `json:"s_zone"` //小区
// Rating   int    `json:"rating"` //等级
// OnlineDuration int `json:"online_duration"` // 在线时长, 单位分钟
// TalkChannel    int `json:"talk_channel"` // 1-6

func (c *Client) sendPack(data any, cmd byte) error {
	pack, err := json.Marshal(&data)
	if err != nil {
		return err
	}
	buf := bytes.NewBuffer(nil)
	binary.Write(buf, binary.LittleEndian, uint32(len(pack)+1+4))
	buf.WriteByte(cmd)
	buf.Write(pack)
	_, err = c.conn.Write(buf.Bytes())
	return err
}

func (c *Client) CreateNewTable(gameName string) error {
	game := model.BaseInfo{
		GameName: gameName,
	}
	return c.sendPack(game, CreateNewGameTable)
}

func (c *Client) Insert(game model.BaseInfo) error {
	return c.sendPack(game, Insert)
}

func (c *Client) Update(game model.BaseInfo) error {
	return c.sendPack(game, Update)
}

func (c *Client) Query(query request.QueryReq) error {
	return c.sendPack(query, Query)
}

func (c *Client) ClearTalkChannel(query request.QueryReq) error {
	return c.sendPack(query, ClearTalkChannel)
}
