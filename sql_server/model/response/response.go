package response

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"sql_server/model"
)

// 服务端回报形式
// 包长: uint32 4bytes
// 内容: json

type ResponseResult []byte

type Response struct {
	Code   byte              `json:"code"`
	Game   []*model.BaseInfo `json:"game"`
	ErrMsg string            `json:"err_msg"`
}

const (
	Success byte = 0
	Error   byte = 1
)

func Result(res *Response) ResponseResult {
	buf := bytes.NewBuffer(nil)
	b, _ := json.Marshal(res)
	binary.Write(buf, binary.LittleEndian, uint32(len(b)+4))
	binary.Write(buf, binary.LittleEndian, b)
	return buf.Bytes()
}

func OK() ResponseResult {
	return Result(&Response{Code: Success})
}

func OkWithData(game []*model.BaseInfo) ResponseResult {
	return Result(&Response{Code: Success, Game: game})
}

func Fail(msg string) ResponseResult {
	return Result(&Response{Code: Error, ErrMsg: msg})
}
