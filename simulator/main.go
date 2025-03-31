package main

import (
	"fmt"
	"time"
)

func main() {
	// Create a new law simulator with simulation date
	simulator := NewLawSimulator(time.Date(2025, 03, 01, 0, 0, 0, 0, time.UTC))

	// Run the simulation for 1000 people
	fmt.Println("Running simulation...")
	results := simulator.RunSimulation(1000)

	// Write results to CSV file
	err := WriteResultsToCSV(results, "simulation_results.csv")
	if err != nil {
		fmt.Printf("Error writing CSV: %v\n", err)
	} else {
		fmt.Println("Results written to simulation_results.csv")
	}

	// Print statistics
	CalculateStatistics(results)
}
