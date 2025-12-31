package config

type Mysql struct {
	Port     string `mapstructure:"port"`     // 数据库端口
	Config   string `mapstructure:"config"`   // 高级配置
	Dbname   string `mapstructure:"db-name"`  // 数据库名
	Username string `mapstructure:"username"` // 数据库账号
	Password        string `mapstructure:"password"`          // 数据库密码
	Path            string `mapstructure:"path"`              // 数据库地址
	MaxIdleConns    int    `mapstructure:"max-idle-conns"`    // 空闲中的最大连接数
	MaxOpenConns    int    `mapstructure:"max-open-conns"`    // 打开到数据库的最大连接数
	ConnMaxLifetime int    `mapstructure:"conn-max-lifetime"` // 连接最大存活时间(秒)
}

func (m *Mysql) Dsn() string {
	return m.Username + ":" + m.Password + "@tcp(" + m.Path + ":" + m.Port + ")/" + m.Dbname + "?" + m.Config
}

func (m *Mysql) DataSourceName() string {
	return m.Username + ":" + m.Password + "@tcp(" + m.Path + ":" + m.Port + ")/"
}
