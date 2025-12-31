package pool

import (
	"context"
	"log"
	"sync"
)

type JobType int

const (
	JobTypeQuery JobType = iota
	JobTypeUpdate
	JobTypeInsert
	JobTypeOther
)

type Job struct {
	Ctx      context.Context
	Data     []byte
	Type     JobType
	Result   chan Result
}

type Result struct {
	Data []byte
	Err  error
}

type HandlerFunc func(data []byte) ([]byte, error)

type WorkerPool struct {
	HighPriorityQueue   chan Job
	NormalPriorityQueue chan Job
	Quit                chan bool
	wg                  sync.WaitGroup
	WorkerCount         int
	Handler             HandlerFunc
}

func NewWorkerPool(workerCount int, queueSize int, handler HandlerFunc) *WorkerPool {
	return &WorkerPool{
		HighPriorityQueue:   make(chan Job, queueSize),
		NormalPriorityQueue: make(chan Job, queueSize),
		Quit:                make(chan bool),
		WorkerCount:         workerCount,
		Handler:             handler,
	}
}

func (wp *WorkerPool) Start() {
	for i := 0; i < wp.WorkerCount; i++ {
		wp.wg.Add(1)
		go wp.worker()
	}
	log.Printf("Worker pool started with %d workers", wp.WorkerCount)
}

func (wp *WorkerPool) Stop() {
	close(wp.Quit)
	wp.wg.Wait()
}

func (wp *WorkerPool) worker() {
	defer wp.wg.Done()
	for {
		select {
		case job := <-wp.HighPriorityQueue:
			wp.process(job)
		case <-wp.Quit:
			return
		default:
			// Non-blocking check for high priority first, then block on both
			select {
			case job := <-wp.HighPriorityQueue:
				wp.process(job)
			case job := <-wp.NormalPriorityQueue:
				wp.process(job)
			case <-wp.Quit:
				return
			}
		}
	}
}

func (wp *WorkerPool) process(job Job) {
	// Check for cancellation
	select {
	case <-job.Ctx.Done():
		job.Result <- Result{Err: job.Ctx.Err()}
		return
	default:
	}

	res, err := wp.Handler(job.Data)
	job.Result <- Result{Data: res, Err: err}
}

func (wp *WorkerPool) Submit(job Job) {
	if job.Type == JobTypeQuery {
		select {
		case wp.HighPriorityQueue <- job:
		default:
			// If high priority queue is full, try normal
			wp.NormalPriorityQueue <- job
		}
	} else {
		wp.NormalPriorityQueue <- job
	}
}
