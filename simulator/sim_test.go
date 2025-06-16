package main

import (
	"context"
	"fmt"
	"testing"
	"time"
)

func TestBlah(t *testing.T) {
	numPeople := 10000

	// Create a new law simulator with simulation date
	simulator, err := NewLawSimulator(time.Date(2025, 03, 01, 0, 0, 0, 0, time.UTC))
	if err != nil {
		fmt.Printf("Error creating new law simulator: %v\n", err)
		return
	}

	// Run the simulation for 1000 people
	fmt.Printf("Running simulation on: %d people\n", numPeople)
	results := simulator.RunSimulation(context.Background(), numPeople)
	// Print statistics
	CalculateStatistics(results)
}
