package mysql_server

import (
	"fmt"
	"testing"
	"time"
)

var mA map[string]map[string]int

func m(tableName string, val int) {
	lockTable := locker.getLock(tableName)
	lockTable.Lock()
	defer lockTable.Unlock()

	lock := locker.getLock("global")
	lock.Lock()
	mB := mA[tableName]
	if mB == nil {
		mB = make(map[string]int)
	}
	lock.Unlock()

	mB[tableName] = val
	for k, v := range mB {
		if tableName == "b" {
			fmt.Println(k, v)
		}
	}
	clear(mB)

	lock.Lock()
	mA[tableName] = mB
	lock.Unlock()
}

func TestMap(t *testing.T) {
	mA = make(map[string]map[string]int)
	for i := 0; i < 100; i++ {
		go m("a", i)
		go m("b", i)
		go m("b", i)
		go m("b", i)
		go m("e", i)
		go m("d", i)
	}
	time.Sleep(10 * time.Second)
}

func TestList(t *testing.T) {
	now := time.Now()
	time.Sleep(time.Second)
	var a time.Time
	t.Log(a.IsZero())
	t.Log(int(now.Sub(a).Seconds()))
}
