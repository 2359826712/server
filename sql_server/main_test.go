package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"sql_server/model"
	"sql_server/model/request"
	"sql_server/service"
	"testing"
	"time"
)

func TestClient(t *testing.T) {
	client := service.InitClient()
	err := client.CreateNewTable("fifa2")
	if err != nil {
		t.Fatal(err)
	}
	for i := 0; i < 50; i++ {
		err = client.Insert(model.BaseInfo{
			GameName: "fifa3",
			Account:  fmt.Sprintf("fifa%d", i),
			BZone:    "b",
			SZone:    "s",
			Rating:   i,
		})
		if err != nil {
			t.Fatal(err)
		}
	}
	err = client.Query(request.QueryReq{
		OnlineDuration: 1,
		TalkChannel:    1,
		BaseInfo: model.BaseInfo{
			GameName: "fifa",
			Account:  "fifa1",
		},
	})
	if err != nil {
		t.Fatal(err)
	}
	time.Sleep(10 * time.Second)
}

func TestHttpQuery(t *testing.T) {
	client := http.Client{}
	do := client.Do
	for i := 0; i < 3000; i++ {
		testQuery(i, do)
	}
	//testReset(do)
	time.Sleep(time.Minute)
}

func testReset(do func(req *http.Request) (*http.Response, error)) {
	url := "http://192.168.20.66:9096/resetQueryCounter"
	q := &request.QueryReq{
		BaseInfo: model.BaseInfo{
			GameName: "arc_game",
		},
	}
	b, _ := json.Marshal(q)
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(b))
	if err != nil {
		panic(fmt.Errorf("req err: %v", err))
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := do(req)
	if err != nil {
		panic(fmt.Errorf("client err: %v", err))
	}
	defer resp.Body.Close()
	data, err := io.ReadAll(resp.Body)
	if err != nil {
		panic(fmt.Errorf("read resp err: %v", err))
	}
	_, _ = data, err
}

func testQuery(index int, do func(req *http.Request) (*http.Response, error)) {
	//fmt.Println("开始请求", index)
	start := time.Now()
	url := "http://192.168.20.66:9096/query_no_update"
	q := &request.QueryReq{
		Cnt:    1,
		IsDesc: false,
		BaseInfo: model.BaseInfo{
			GameName: "arc_game",
		},
	}
	b, _ := json.Marshal(q)
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(b))
	if err != nil {
		panic(fmt.Errorf("req err: %v", err))
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := do(req)
	if err != nil {
		panic(fmt.Errorf("client err: %v", err))
	}
	defer resp.Body.Close()
	data, err := io.ReadAll(resp.Body)
	if err != nil {
		panic(fmt.Errorf("read body err: %v", err))
	}
	fmt.Println("用时： ", time.Since(start).Milliseconds(), "ms ", index, "--->>", string(data))
}
