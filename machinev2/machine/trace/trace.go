package trace

import (
	"bytes"
	"fmt"
)

type TraceID [16]byte

var traceIDNil TraceID

func (id TraceID) Empty() bool {
	return bytes.Equal(id[:], traceIDNil[:])
}

func (id TraceID) String() string {
	return fmt.Sprintf("%032x", id[:])
}

type SpanID [8]byte

var spanIDNil SpanID

func (id SpanID) Empty() bool {
	return bytes.Equal(id[:], spanIDNil[:])
}

func (id SpanID) String() string {
	return fmt.Sprintf("%016x", id[:])
}

type ProcessingContext struct {
	traceID TraceID
	spanID  SpanID
	foreign bool
}

func New(traceID TraceID, spanID SpanID) *ProcessingContext {
	return &ProcessingContext{
		traceID: traceID,
		spanID:  spanID,
	}
}

func (p ProcessingContext) TraceID() TraceID {
	return p.traceID
}

func (p ProcessingContext) SpanID() SpanID {
	return p.spanID
}

func (p ProcessingContext) Foreign() bool {
	return p.foreign
}

func (p ProcessingContext) IsValid() bool {
	return !p.traceID.Empty() && !p.spanID.Empty()
}
