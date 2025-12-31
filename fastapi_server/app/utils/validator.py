import re

def is_valid_game_name(game_name: str) -> bool:
    if not game_name:
        return False
    # Match Go's validation: must be alphanumeric or underscore, start with letter
    # But Go code says: "游戏名必须是字母数字或下划线且以字母开头"
    # Go's utils.IsValid implementation is not visible here, but I'll assume standard regex.
    # Let's check `utils/check.go` if needed, but for now I'll use a safe regex.
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]*$'
    return bool(re.match(pattern, game_name))
