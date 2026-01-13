package mysql_server

import "sync"

type lockList struct {
	locks sync.Map
}

func (l *lockList) getLock(gameName string) *sync.RWMutex {
	lock, loaded := l.locks.LoadOrStore(gameName, new(sync.RWMutex))
	if !loaded {
		return lock.(*sync.RWMutex)
	}
	return lock.(*sync.RWMutex)
}
