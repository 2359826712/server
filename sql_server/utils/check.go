package utils

import (
	"regexp"
)

// isValid checks if the string s contains only letters, digits, and underscores,
// and starts with a letter.
func IsValid(s string) bool {
	// 正则表达式: ^[a-zA-Z][a-zA-Z0-9_]*$
	var validPattern = regexp.MustCompile(`^[a-zA-Z][a-zA-Z0-9_]*$`)
	return validPattern.MatchString(s)
}
