package model

type Service struct {
	Name string
	Laws []Law
}

type Law struct {
	Name           string
	Discoverableby []string
}
