package config

type Cache struct {
	InsertCount int `mapstructure:"insert_count"` // 插入缓存数量限制
	QueryCount  int `mapstructure:"query_count"`  // 查询缓存数量限制
}
