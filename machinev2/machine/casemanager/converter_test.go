package casemanager

import (
	"encoding/json"
	"fmt"
	"testing"

	"github.com/stretchr/testify/require"
)

type SampleStruct struct {
	Name string `json:"name"`
	ID   string `json:"id"`
}

type EmbededStruct struct {
	FieldStruct `json:"field"`
	Hello       string `json:"hello"`
}

type FieldStruct struct {
	OnePoint string        `json:"one_point"`
	Sample   *SampleStruct `json:"sample"`
}

type FieldStruct2 struct {
	OnePoint string        `json:"one_point"`
	Sample   *SampleStruct `json:"sample,omitempty"`
}

func TestStructToMap_Normal(t *testing.T) {
	sample := SampleStruct{
		Name: "John Doe",
		ID:   "12121",
	}

	res := structToMap(sample)
	require.NotNil(t, res)

	fmt.Printf("%+v \n", res)
	// Output: map[name:John Doe id:12121]
	jbyt, err := json.Marshal(res)
	require.NoError(t, err)
	fmt.Println(string(jbyt))
	// Output: {"id":"12121","name":"John Doe"}
}
func TestStructToMap_FieldStruct(t *testing.T) {

	sample := &SampleStruct{
		Name: "John Doe",
		ID:   "12121",
	}
	field := FieldStruct{
		Sample:   sample,
		OnePoint: "yuhuhuu",
	}

	res := structToMap(field)
	require.NotNil(t, res)
	fmt.Printf("%+v \n", res)
	// Output: map[sample:0xc4200f04a0 one_point:yuhuhuu]
	jbyt, err := json.Marshal(res)
	require.NoError(t, err)
	fmt.Println(string(jbyt))
	// Output: {"one_point":"yuhuhuu","sample":{"name":"John Doe","id":"12121"}}

}

func TestStructToMap_EmbeddedStruct(t *testing.T) {

	sample := &SampleStruct{
		Name: "John Doe",
		ID:   "12121",
	}
	field := FieldStruct{
		Sample:   sample,
		OnePoint: "yuhuhuu",
	}

	embed := EmbededStruct{
		FieldStruct: field,
		Hello:       "WORLD!!!!",
	}

	res := structToMap(embed)
	require.NotNil(t, res)
	fmt.Printf("%+v \n", res)
	//Output: map[field:map[one_point:yuhuhuu sample:0xc420106420] hello:WORLD!!!!]

	jbyt, err := json.Marshal(res)
	require.NoError(t, err)
	fmt.Println(string(jbyt))
	// Output: {"field":{"one_point":"yuhuhuu","sample":{"name":"John Doe","id":"12121"}},"hello":"WORLD!!!!"}
}

func TestStructToMap_FieldStruct2(t *testing.T) {

	field := FieldStruct2{
		OnePoint: "yuhuhuu",
	}

	res := structToMap(field)
	require.NotNil(t, res)
	fmt.Printf("%+v \n", res)
	// Output: map[sample:nil one_point:yuhuhuu]
	jbyt, err := json.Marshal(res)
	require.NoError(t, err)
	fmt.Println(string(jbyt))
	// Output: {"one_point":"yuhuhuu"}

}
