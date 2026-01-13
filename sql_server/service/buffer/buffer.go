package buffer

import (
	"encoding/binary"
)

const headLen = 0x04

type Buffer interface {
	Write(p []byte)
	GetPackageLength() int
	Pop(size int) []byte
}

func NewBuffer() Buffer {
	return &buffer{}
}

type buffer struct {
	data []byte
}

func (b *buffer) GetPackageLength() int {
	dataLen := len(b.data)
	if dataLen < headLen {
		return -1
	}
	packageLen := int(binary.LittleEndian.Uint32(b.data))
	if dataLen < packageLen {
		return -1
	}
	return packageLen
}

func (b *buffer) Pop(size int) []byte {
	data := make([]byte, size)
	copy(data, b.data)
	b.data = b.data[size:]
	return data
}

func (b *buffer) Write(p []byte) {
	b.data = append(b.data, p...)
}
