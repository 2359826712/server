#!/bin/bash
 if ! command -v screen &> /dev/null; then
   echo "====>screen 未安装，正在安装..."
   sudo apt install -y screen
 fi

 # 列出所有screen会话
 echo "====>先将screen中所有sql_server后台服务杀死"
 screen -ls
 # 使用循环杀死所有同名的screen会话
 for session in $(screen -ls | grep 'sql_server' | awk '{print $1}'); do
     screen -S $session -X quit
 done

 echo "====>在 screen 中运行 Go 程序..."
 chmod +x sql_server
 screen -mdSU sql_server ./sql_server

 # 检查 screen 会话是否成功启动
 sleep 2
 if screen -list | grep -q "sql_server"; then
     echo "====>screen 会话 'sql_server' 已成功启动。"
     screen -ls
 else
     echo "====>screen 会话 'sql_server' 启动失败。"
     exit 1
 fi