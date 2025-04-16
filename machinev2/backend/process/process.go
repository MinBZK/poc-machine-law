package process

import (
	"context"
	"os"
	"os/signal"
	"syscall"
)

type Process struct {
	ctx    context.Context
	cancel context.CancelFunc
}

func New() *Process {
	ctx, cancel := context.WithCancel(context.Background())

	proc := &Process{
		ctx:    ctx,
		cancel: cancel,
	}

	proc.start()

	return proc
}

func (p *Process) start() {
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGTERM, syscall.SIGINT, syscall.SIGQUIT)

	go func() {
		<-sigChan
		p.cancel()
	}()
}

func (p *Process) Wait() {
	<-p.ctx.Done()
}
