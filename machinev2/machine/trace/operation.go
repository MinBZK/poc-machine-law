package trace

import (
	"context"
	"encoding/hex"
	"fmt"
	"net/http"
	"strings"
	"time"

	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/trace"
)

const (
	traceparentHeader = "traceparent"
)

var (
	emptyProcessingOperation = ProcessingContext{}
	currentProcessingKey     ctxKey
)

type ctxKey int

func Extract(ctx context.Context, h http.Header) context.Context {
	traceID, parentID, err := extract(h)
	if err != nil {
		return ctx
	}

	op := ProcessingContext{
		traceID: traceID,
		spanID:  parentID,
		foreign: true,
	}

	return ContextWithProcessingOperation(ctx, &op)
}

func extract(h http.Header) (TraceID, SpanID, error) {
	tp := h.Get(traceparentHeader)
	if tp == "" {
		return traceIDNil, spanIDNil, fmt.Errorf("traceparent header empty")
	}

	parts := strings.SplitN(tp, "-", 4)
	version := parts[0]
	if len(version) != 2 {
		return traceIDNil, spanIDNil, fmt.Errorf("traceparent invalid format")
	}

	traceID, err := hex.DecodeString(parts[1])
	if err != nil {
		return traceIDNil, spanIDNil, fmt.Errorf("traceID hex decode string failed: %w", err)
	}

	if len(traceID) != 16 {
		return traceIDNil, spanIDNil, fmt.Errorf("trace ID invalid length")
	}

	parentID, err := hex.DecodeString(parts[2])
	if err != nil {
		return traceIDNil, spanIDNil, fmt.Errorf("parentID hex decode string failed: %w", err)
	}

	if len(parentID) != 8 {
		return traceIDNil, spanIDNil, fmt.Errorf("parent ID invalid length")
	}

	return TraceID(traceID), SpanID(parentID), nil
}
func Inject(ctx context.Context, h http.Header) {
	span := trace.SpanFromContext(ctx)
	if span == nil {
		return
	}

	spanctx := span.SpanContext()
	if !spanctx.IsValid() {
		return
	}

	x := spanctx.TraceID()
	a := [16]byte(x)

	y := spanctx.SpanID()
	b := [8]byte(y)

	v := fmt.Sprintf("00-%x-%x-01", a[:], b[:])

	h.Set(traceparentHeader, v)
}

func ContextWithProcessingOperation(ctx context.Context, op *ProcessingContext) context.Context {
	return context.WithValue(ctx, currentProcessingKey, op)
}

func ProcessingOperationFromContext(ctx context.Context) *ProcessingContext {
	if ctx == nil {
		return &emptyProcessingOperation
	}

	op, ok := ctx.Value(currentProcessingKey).(*ProcessingContext)
	if !ok {
		return &emptyProcessingOperation
	}

	return op
}

func DataProcessingStart(ctx context.Context, tracer trace.Tracer, name string, opts ...trace.SpanStartOption) (context.Context, trace.Span) {
	return Action(ctx, tracer, name, append(opts, trace.WithNewRoot())...)
}

func Action(ctx context.Context, tracer trace.Tracer, name string, opts ...trace.SpanStartOption) (context.Context, trace.Span) {
	var parent ProcessingContext
	if p := ProcessingOperationFromContext(ctx); p.IsValid() {
		parent = *p
	}

	if opts == nil {
		opts = make([]trace.SpanStartOption, 0, 1)
	}

	opts = append(opts,
		trace.WithTimestamp(time.Now()),
	)

	if parent.IsValid() && parent.Foreign() {
		opts = append(opts, trace.WithAttributes(
			attribute.String("dpl.core.foreign_operation.trace_id", parent.TraceID().String()),
			attribute.String("dpl.core.foreign_operation.span_id", parent.SpanID().String()),
		))
	}

	ctx, span := tracer.Start(ctx, name, opts...)

	return ctx, span
}

func SetAttributeActivityID(activityID string) trace.SpanStartEventOption {
	return trace.WithAttributes(
		attribute.String("dpl.core.processing_activity_id", activityID),
	)
}

func SetAttributeBSN(bsn string) trace.SpanStartEventOption {
	return trace.WithAttributes(
		attribute.String("dpl.core.data_subject_id", bsn),
		attribute.String("dpl.core.data_subject_id_type", "BSN"),
	)
}

func SetAlgorithmID(algorithmID string) trace.SpanStartEventOption {
	return trace.WithAttributes(
		attribute.String("dpl.lac.algorithm_id", algorithmID),
	)
}
