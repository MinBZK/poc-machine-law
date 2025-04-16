package model

type Profile struct {
	BSN         string
	Name        string
	Description string
	Sources     map[string]Source
}
