### http
```go
// 字段名:
// GameName string `json:"game_name"` // 用作表名
// Account  string `json:"account"`
// BZone    string `json:"b_zone"` //大区
// SZone    string `json:"s_zone"` //小区
// Rating   int    `json:"rating"` //等级
// OnlineDuration int `json:"online_duration"` // 在线时长, 单位分钟
// TalkChannel    int `json:"talk_channel"` // 1-6
```
```http request
POST http://192.168.2.99:9091/createNewGame
Content-Type: application/json

{
  "game_name": "fsjs"
}

###
POST http://192.168.2.99:9091/insert
Content-Type: application/json

{
  "game_name": "fsjs",
  "account": "hao123.com",
  "b_zone": "b",
  "s_zone": "s",
  "rating": 10
}

###
POST http://192.168.2.99:9091/query
Content-Type: application/json

{
  "game_name": "fsjs",
  "online_duration": 50,
  "talk_channel": 1,
  "cnt": 2
}

###
POST http://192.168.2.99:9091/clearTalkChannel
Content-Type: application/json

{
  "game_name": "fsjs",
  "talk_channel": 1
}
```


### tcp 客户端

- 发包格式(小端序)
 1. 包长 uint32   4bytes, 总长包含包长的4字节
 2. cmd命令 byte( 1:创建新表, 2: 新增, 3:更新, 4:查询, 5:清理喊话通道)
 3. 数据内容json格式
```go
// 字段名:
// GameName string `json:"game_name"` // 用作表名
// Account  string `json:"account"`
// BZone    string `json:"b_zone"` //大区
// SZone    string `json:"s_zone"` //小区
// Rating   int    `json:"rating"` //等级
// OnlineDuration int `json:"online_duration"` // 在线时长, 单位分钟
// TalkChannel    int `json:"talk_channel"` // 1-6
```
4. 建表
```go
包长(包长4字节+cmd 1字节+len(json->bytes))+cmd(创建新表1)+game_name(json格式)
```
5. 新增
```go
包长(包长4字节+cmd 1字节+len(json->bytes))+cmd(新增2)+struct:game_name, account, bzone, szone, rating(json格式)
更新也可以用
```
6. 查询
```go
包长(包长4字节+cmd 1字节+len(json->bytes))+cmd(新增2)+struct:game_name, account, bzone, szone, rating, online_duration, talk_channel(json格式)
```


### mysql
```mysql

sudo docker volume create mysql-data
sudo docker volume create mysql-config

##MYSQL_ROOT_PASSWORD=fsjs636119 这是用户名root, 密码自己给定, 同时config.yaml中记得改密码 
sudo docker run --name my-mysql \
-e MYSQL_ROOT_PASSWORD=fsjs636119 \
-d \
-p 3306:3306 \
-v mysql-data:/var/lib/mysql \
-v mysql-config:/etc/mysql/conf.d \
mysql:latest
```

### 部署
#### window版
1. 将config.yaml, sql_server_windows.exe放在同一文件夹下
2. 运行sql_server_windows.exe即可
#### ubuntu版
1. 需要先用docker启动上面的mysql服务, 记得mysql密码与config.yaml统一
2. 编译为linux环境的sql_server
  - set GOOS=linux(这是在windows环境编译linux文件, 如果本身就是linux, 可忽略)
  - go build -o sql_server
3. 将config.yaml, sql_server_script.sh, sql_server三个文件拷贝到服务器
4. 运行bash sql_server_script.sh脚本即可(注意: ubuntu是apt,centos是yum, 主要是检测服务器有没有安装screen, 已安装可忽略)
