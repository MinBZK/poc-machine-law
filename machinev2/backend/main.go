package main

import (
	"log"

	"github.com/minbzk/poc-machine-law/machinev2/backend/cmd"
)

func main() {
	if err := cmd.Run(); err != nil {
		log.Fatal(err)
	}
}
