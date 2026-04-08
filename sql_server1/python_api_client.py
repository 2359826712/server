import requests
import json
import argparse
import sys

# 服务器配置
SERVER_URL = "http://localhost:9091"

# 调试配置
DEBUG = True


def debug_print(*args, **kwargs):
    if DEBUG:
        print("[调试]", *args, **kwargs)


def send_post_request(endpoint, data):
    url = f"{SERVER_URL}{endpoint}"
    debug_print(f"发送请求到: {url}")
    debug_print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")

    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=data, headers=headers, timeout=10)

        status_code = response.status_code
        try:
            response_data = response.json()
            debug_print("解析JSON成功")
        except json.JSONDecodeError as e:
            response_data = {"raw_text": response.text, "parse_error": str(e)}
            debug_print(f"JSON解析失败: {e}")

        return status_code, response_data
    except requests.exceptions.RequestException as e:
        debug_print(f"请求失败: {e}")
        return 500, {"error": str(e)}


# 1. 创建新游戏
def create_new_game(game_name):
    data = {"game_name": game_name}
    status_code, response = send_post_request("/createNewGame", data)

    print("=== 创建新游戏 ===")
    print(f"状态码: {status_code}")
    print(f"响应: {json.dumps(response, ensure_ascii=False, indent=2)}\n")
    return status_code, response


# 2. 插入数据
def insert_data(game_name, account, password, email_account, email_password, address):
    data = {
        "game_name": game_name,
        "account": account,
        "password": password,
        "email_account": email_account,
        "email_password": email_password,
        "address": address,
    }
    status_code, response = send_post_request("/insert", data)

    print("=== 插入数据 ===")
    print(f"状态码: {status_code}")
    print(f"响应: {json.dumps(response, ensure_ascii=False, indent=2)}\n")
    return status_code, response


# 3. 更新数据
def update_data(
    game_name,
    account,
    password=None,
    email_account=None,
    email_password=None,
    address=None,
    computer_number=None,
    status=None,
    in_use=None,
):
    data = {
        "game_name": game_name,
        "account": account,
    }
    if password:
        data["password"] = password
    if email_account:
        data["email_account"] = email_account
    if email_password:
        data["email_password"] = email_password
    if address:
        data["address"] = address
    if computer_number:
        data["computer_number"] = computer_number
    if status is not None:
        data["status"] = status
    if in_use is not None:
        data["in_use"] = "true" if in_use else "false"

    status_code, response = send_post_request("/update", data)

    print("=== 更新数据 ===")
    print(f"状态码: {status_code}")
    print(f"响应: {json.dumps(response, ensure_ascii=False, indent=2)}\n")
    return status_code, response


# 4. 删除数据
def delete_data(game_name, account):
    data = {
        "game_name": game_name,
        "account": account,
    }
    status_code, response = send_post_request("/delete", data)

    print("=== 删除数据 ===")
    print(f"状态码: {status_code}")
    print(f"响应: {json.dumps(response, ensure_ascii=False, indent=2)}\n")
    return status_code, response


# 5. 查询数据
def query_data(game_name, cnt=100):
    data = {"game_name": game_name, "cnt": cnt}
    status_code, response = send_post_request("/query", data)

    print("=== 查询数据 ===")
    print(f"状态码: {status_code}")
    print(f"响应: {json.dumps(response, ensure_ascii=False, indent=2)}\n")
    return status_code, response


# 6. 清空状态
def clear_status(game_name):
    data = {"game_name": game_name}
    status_code, response = send_post_request("/clearStatus", data)

    print("=== 清空状态 ===")
    print(f"状态码: {status_code}")
    print(f"响应: {json.dumps(response, ensure_ascii=False, indent=2)}\n")
    return status_code, response


def main():
    global DEBUG
    parser = argparse.ArgumentParser(description="SQL Server API 客户端")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # create 命令
    parser_create = subparsers.add_parser("create", help="创建新游戏")
    parser_create.add_argument("game_name", help="游戏名称")

    # insert 命令
    parser_insert = subparsers.add_parser("insert", help="插入数据")
    parser_insert.add_argument("game_name", help="游戏名称")
    parser_insert.add_argument("account", help="账号")
    parser_insert.add_argument("password", help="密码")
    parser_insert.add_argument("email_account", help="邮箱账号")
    parser_insert.add_argument("email_password", help="邮箱密码")
    parser_insert.add_argument("address", help="地址")

    # update 命令
    parser_update = subparsers.add_parser("update", help="更新数据")
    parser_update.add_argument("game_name", help="游戏名称")
    parser_update.add_argument("account", help="账号")
    parser_update.add_argument("--password", help="密码")
    parser_update.add_argument("--email_account", help="邮箱账号")
    parser_update.add_argument("--email_password", help="邮箱密码")
    parser_update.add_argument("--address", help="地址")
    parser_update.add_argument("--computer_number", help="机器号")
    parser_update.add_argument("--status", type=int, help="状态(整数)")
    parser_update.add_argument(
        "--in_use", action="store_true", help="设置为使用中(true)"
    )
    parser_update.add_argument(
        "--not_in_use", action="store_true", help="设置为未使用(false)"
    )

    # delete 命令
    parser_delete = subparsers.add_parser("delete", help="删除数据")
    parser_delete.add_argument("game_name", help="游戏名称")
    parser_delete.add_argument("account", help="账号")

    # query 命令
    parser_query = subparsers.add_parser("query", help="查询数据")
    parser_query.add_argument("game_name", help="游戏名称")
    parser_query.add_argument(
        "--cnt", type=int, default=100, help="查询数量 (默认: 100)"
    )

    # clearstatus 命令
    parser_clear = subparsers.add_parser("clearstatus", help="清空状态")
    parser_clear.add_argument("game_name", help="游戏名称")

    parser.add_argument(
        "--debug", action="store_true", default=True, help="启用调试模式 (默认开启)"
    )
    parser.add_argument(
        "--no-debug", action="store_false", dest="debug", help="禁用调试模式"
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    DEBUG = args.debug

    if args.command == "create":
        create_new_game(args.game_name)
    elif args.command == "insert":
        insert_data(
            args.game_name,
            args.account,
            args.password,
            args.email_account,
            args.email_password,
            args.address,
        )
    elif args.command == "update":
        if args.in_use and args.not_in_use:
            print("错误：--in_use 和 --not_in_use 不能同时使用")
            sys.exit(1)
        in_use_value = None
        if args.in_use:
            in_use_value = True
        elif args.not_in_use:
            in_use_value = False
        update_data(
            args.game_name,
            args.account,
            password=args.password,
            email_account=args.email_account,
            email_password=args.email_password,
            address=args.address,
            computer_number=args.computer_number,
            status=args.status,
            in_use=in_use_value,
        )
    elif args.command == "delete":
        delete_data(args.game_name, args.account)
    elif args.command == "query":
        query_data(args.game_name, args.cnt)
    elif args.command == "clearstatus":
        clear_status(args.game_name)


if __name__ == "__main__":
    main()
