package main

import (
	"context"
	"flag"
	"fmt"
	"time"
)

func main() {
	numPeople := flag.Int("num_people", 1000, "number of people to process")

	flag.Parse()

	// Create a new law simulator with simulation date
	simulator, err := NewLawSimulator(time.Date(2025, 03, 01, 0, 0, 0, 0, time.UTC))
	if err != nil {
		fmt.Printf("Error creating new law simulator: %v\n", err)
		return
	}

	// Run the simulation for 1000 people
	fmt.Printf("Running simulation on: %d people\n", *numPeople)
	results := simulator.RunSimulation(context.Background(), *numPeople)

	// Write results to CSV file

	if err := WriteResultsToCSV(results, "simulation_results.csv"); err != nil {
		fmt.Printf("Error writing CSV: %v\n", err)
		return
	}

	fmt.Println("Results written to simulation_results.csv")

	// Print statistics
	CalculateStatistics(results)
}
