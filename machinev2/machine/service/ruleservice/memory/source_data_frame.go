package memory

import (
	"fmt"
	"sync"

	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
)

var _ model.SourceDataFrame = &SourceDataFrame{}

type SourceDataFrame struct {
	source map[string]model.DataFrame
	mu     sync.RWMutex
}

func NewSourceDataFrame() *SourceDataFrame {
	return &SourceDataFrame{
		source: map[string]model.DataFrame{},
		mu:     sync.RWMutex{},
	}
}

func (s *SourceDataFrame) Get(table string) (model.DataFrame, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	data, ok := s.source[table]
	return data, ok
}

func (s *SourceDataFrame) Set(table string, df model.DataFrame) {
	s.mu.Lock()
	defer s.mu.Unlock()

	df1, ok := s.source[table]
	if ok {
		var err error
		df, err = df1.Append(df)
		if err != nil {
			fmt.Printf("err: %v\n", err)
		}
	}

	s.source[table] = df
}

func (s *SourceDataFrame) Reset() {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.source = make(map[string]model.DataFrame)
}
