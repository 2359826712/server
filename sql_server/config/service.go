package config

type Service struct {
	TcpPort  int `mapstructure:"tcp_port"`
	HttpPort int `mapstructure:"http_port"`
}
