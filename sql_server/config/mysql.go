package config

type Mysql struct {
	Port     string `mapstructure:"port"`     // 数据库端口
	Config   string `mapstructure:"config"`   // 高级配置
	Dbname   string `mapstructure:"db-name"`  // 数据库名
	Username string `mapstructure:"username"` // 数据库账号
	Password string `mapstructure:"password"` // 数据库密码
	Path     string `mapstructure:"path"`     // 数据库地址
}

func (m *Mysql) Dsn() string {
	return m.Username + ":" + m.Password + "@tcp(" + m.Path + ":" + m.Port + ")/" + m.Dbname + "?" + m.Config
}

func (m *Mysql) DataSourceName() string {
	return m.Username + ":" + m.Password + "@tcp(" + m.Path + ":" + m.Port + ")/"
}
