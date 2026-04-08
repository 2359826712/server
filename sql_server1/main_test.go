package main

import (
	"fmt"
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
			EmailAccount:  "b",
			EmailPassword: "s",
			Address:       fmt.Sprintf("addr%d", i),
		})
		if err != nil {
			t.Fatal(err)
		}
	}
	err = client.Query(request.QueryReq{
		BaseInfo: model.BaseInfo{
			GameName: "fifa",
			Account:  "fifa1",
		},
	})
	if err != nil {
		t.Fatal(err)
	}

	err = client.ClearStatus("fifa3")
	if err != nil {
		t.Fatal(err)
	}

	time.Sleep(10 * time.Second)
}
