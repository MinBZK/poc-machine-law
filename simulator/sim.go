package main

import (
	"context"
	"encoding/csv"
	"fmt"
	"log"
	"math"
	"math/rand"
	"os"
	"sort"
	"strconv"
	"sync"
	"time"

	"github.com/gammazero/workerpool"
	"github.com/schollz/progressbar/v3"

	"github.com/minbzk/poc-machine-law/machinev2/machine/dataframe"
	"github.com/minbzk/poc-machine-law/machinev2/machine/service"
)

// Person represents an individual in the simulation
type Person struct {
	BSN            string
	BirthDate      time.Time
	Age            int
	AnnualIncome   int
	NetWorth       int
	WorkYears      float64
	ResidenceYears float64
	IsStudent      bool
	StudyGrant     int
	PartnerBSN     string
}

// SimulationResult represents the outcome of a person's simulation
type SimulationResult struct {
	BSN                 string
	Age                 int
	HasPartner          bool
	Income              float64
	NetWorth            float64
	WorkYears           float64
	ResidenceYears      float64
	IsStudent           bool
	StudyGrant          float64
	ZorgtoeslagEligible bool
	ZorgtoeslagAmount   float64
	AOWEligible         bool
	AOWAmount           float64
	AOWAccrual          float64
}

// ServiceResult represents the result of a service evaluation
type ServiceResult struct {
	RequirementsMet bool
	Output          map[string]any
}

// lognormal generates a random number from a lognormal distribution
func lognormal(mean, sigma float64) float64 {
	return math.Exp(rand.NormFloat64()*sigma + mean)
}

// LawSimulator is the main simulation engine
type LawSimulator struct {
	SimulationDate time.Time
	Services       *service.Services
	Results        []SimulationResult
	UsedBSNs       map[string]bool
	mutex          sync.Mutex
}

// NewLawSimulator creates a new LawSimulator instance
func NewLawSimulator(simulationDate time.Time) *LawSimulator {
	return &LawSimulator{
		SimulationDate: simulationDate,
		Services:       service.NewServices(simulationDate),
		Results:        make([]SimulationResult, 0),
		UsedBSNs:       make(map[string]bool),
	}
}

// GenerateBSN generates a unique BSN (citizen identification number)
func (ls *LawSimulator) GenerateBSN() string {
	ls.mutex.Lock()
	defer ls.mutex.Unlock()

	for {
		bsn := fmt.Sprintf("999%06d", rand.Intn(900000)+100000)
		if !ls.UsedBSNs[bsn] {
			ls.UsedBSNs[bsn] = true
			return bsn
		}
	}
}

// GeneratePerson creates a random person for the simulation
func (ls *LawSimulator) GeneratePerson(birthYearMin, birthYearMax int) Person {
	year := rand.Intn(birthYearMax-birthYearMin+1) + birthYearMin
	month := rand.Intn(12) + 1
	day := rand.Intn(28) + 1

	birthDate := time.Date(year, time.Month(month), day, 0, 0, 0, 0, time.UTC)

	ageInDays := int(ls.SimulationDate.Sub(birthDate).Hours() / 24)
	ageInYears := ageInDays / 365

	// Determine if person is a student (more likely for younger people)
	isStudent := ageInYears < 30 && rand.Float64() < 0.6

	// Generate random income with lognormal distribution (capped at 200,000)
	income := int(math.Min(math.Max(lognormal(10.8, 0.4), 0), 200000)) * 100

	// Generate random net worth with lognormal distribution
	netWorth := int(math.Min(math.Max(lognormal(11, 1), 0), 1000000)) * 100

	// Calculate work and residence years based on age
	workYears := math.Min(math.Max(0, float64(ageInYears-15)*rand.Float64()*0.4+0.5), 50)
	residenceYears := math.Min(math.Max(0, float64(ageInYears-15)*rand.Float64()*0.2+0.8), 50)

	// Study grant for students
	studyGrant := 0
	if isStudent {
		studyGrant = (rand.Intn(2500) + 2000) * 100
	}

	return Person{
		BSN:            ls.GenerateBSN(),
		BirthDate:      birthDate,
		Age:            ageInYears,
		AnnualIncome:   income,
		NetWorth:       netWorth,
		WorkYears:      workYears,
		ResidenceYears: residenceYears,
		IsStudent:      isStudent,
		StudyGrant:     studyGrant,
		PartnerBSN:     "",
	}
}

// GeneratePairedPeople creates a set of people, some with partners
func (ls *LawSimulator) GeneratePairedPeople(numPeople int, people chan Person) {
	count := 0

	for count < numPeople {

		person := ls.GeneratePerson(1940, 2007)
		people <- person

		// 60% chance of having a partner
		if rand.Float64() < 0.0 {
			// Age difference with Gaussian distribution (mean 0, std dev 5 years)
			ageDiff := int(rand.NormFloat64() * 5)

			// Partner birth year based on age difference
			partnerBirthYearMin := person.BirthDate.Year() + ageDiff - 1
			partnerBirthYearMax := person.BirthDate.Year() + ageDiff + 1

			partner := ls.GeneratePerson(partnerBirthYearMin, partnerBirthYearMax)

			// Link the partners
			person.PartnerBSN = partner.BSN
			partner.PartnerBSN = person.BSN

			people <- partner

			count += 2
		} else {
			count++
		}
	}

	close(people)
}

// SetupTestData prepares all the data sources for simulation
func (ls *LawSimulator) SetupTestData(people <-chan Person, data chan Person) {

	ls.Services.SetSourceDataFrame("CBS", "levensverwachting", dataframe.New([]map[string]any{
		{
			"jaar":           "2025",
			"verwachting_65": 20.5,
		},
	}))

	for person := range people {
		ls.Services.SetSourceDataFrame("RvIG", "personen", dataframe.New([]map[string]any{
			{
				"bsn":            person.BSN,
				"geboortedatum":  person.BirthDate.Format("2006-01-02"),
				"verblijfsadres": "Amsterdam",
				"land_verblijf":  "NEDERLAND",
			},
		}))

		partnershipType := "GEEN"
		if person.PartnerBSN != "" {
			partnershipType = "HUWELIJK"
		}

		ls.Services.SetSourceDataFrame("RvIG", "relaties", dataframe.New([]map[string]any{
			{
				"bsn":               person.BSN,
				"partnerschap_type": partnershipType,
				"partner_bsn":       person.PartnerBSN,
			},
		}))

		ls.Services.SetSourceDataFrame("BELASTINGDIENST", "inkomen", dataframe.New([]map[string]any{
			{
				"bsn":         person.BSN,
				"box1":        person.AnnualIncome,
				"box2":        0,
				"box3":        0,
				"buitenlands": 0,
			},
		}))

		ls.Services.SetSourceDataFrame("BELASTINGDIENST", "vermogen", dataframe.New([]map[string]any{
			{
				"bsn":         person.BSN,
				"bezittingen": person.NetWorth,
				"schulden":    0,
			},
		}))

		ls.Services.SetSourceDataFrame("BELASTINGDIENST", "dienstverbanden", dataframe.New([]map[string]any{
			{
				"bsn":        person.BSN,
				"start_date": person.BirthDate.Format("2006-01-02"),
				"end_date":   ls.SimulationDate,
			},
		}))

		ls.Services.SetSourceDataFrame("SVB", "verzekerde_tijdvakken", dataframe.New([]map[string]any{
			{
				"bsn":          person.BSN,
				"woonperiodes": person.ResidenceYears,
			},
		}))

		status := "ACTIEF"
		if rand.Float64() >= 0.95 {
			status = "INACTIEF"
		}

		ls.Services.SetSourceDataFrame("RVZ", "verzekeringen", dataframe.New([]map[string]any{
			{
				"bsn":          person.BSN,
				"polis_status": status,
			},
		}))

		ls.Services.SetSourceDataFrame("RVZ", "verdragsverzekeringen", dataframe.New([]map[string]any{
			{
				"bsn":         person.BSN,
				"registratie": "INACTIEF",
			},
		}))

		ls.Services.SetSourceDataFrame("DJI", "detenties", dataframe.New([]map[string]any{
			{
				"bsn":             person.BSN,
				"status":          "VRIJ",
				"inrichting_type": "GEEN",
			},
		}))

		ls.Services.SetSourceDataFrame("DJI", "forensische_zorg", dataframe.New([]map[string]any{
			{
				"bsn":              person.BSN,
				"zorgtype":         "GEEN",
				"juridische_titel": "GEEN",
			},
		}))

		onderwijstype := "GEEN"
		if person.IsStudent {
			onderwijstype = "HBO"
		}

		ls.Services.SetSourceDataFrame("DUO", "inschrijvingen", dataframe.New([]map[string]any{
			{
				"bsn":           person.BSN,
				"onderwijstype": onderwijstype,
			},
		}))

		aantalStuderend := 0
		if person.Age < 30 {
			aantalStuderend = rand.Intn(4)
		}

		ls.Services.SetSourceDataFrame("DUO", "studiefinanciering", dataframe.New([]map[string]any{
			{
				"bsn":                    person.BSN,
				"aantal_studerend_gezin": aantalStuderend,
			},
		}))

		data <- person
	}

	close(data)
}

// SimulatePerson evaluates a single person in the simulation
func (ls *LawSimulator) SimulatePerson(person Person) error {
	hasPartner := person.PartnerBSN != ""

	// Create parameters for service calls
	params := map[string]any{
		"BSN": person.BSN,
	}

	// Call zorgtoeslag service
	zorgtoeslag, err := ls.Services.Evaluate(
		context.TODO(),
		"TOESLAGEN",
		"zorgtoeslagwet",
		params,
		ls.SimulationDate.Format("2006-01-02"),
		nil,
		"",
		false,
	)

	if err != nil {
		return fmt.Errorf("evaluate: %w", err)
	}

	// Call AOW service
	aow, err := ls.Services.Evaluate(
		context.TODO(),
		"SVB",
		"algemene_ouderdomswet",
		params,
		ls.SimulationDate.Format("2006-01-02"),
		nil,
		"",
		false,
	)

	if err != nil {
		return fmt.Errorf("evaluate: %w", err)
	}

	// Get zorgtoeslag amount
	var zorgtoeslagAmount float64
	if amount, ok := zorgtoeslag.Output["hoogte_toeslag"]; ok {
		zorgtoeslagAmount = float64(amount.(int)) / 100
	}

	// Get AOW amount and accrual
	var aowAmount, aowAccrual float64
	if amount, ok := aow.Output["pension_amount"]; ok {
		aowAmount = float64(amount.(int)) / 100
	}
	if accrual, ok := aow.Output["accrual_percentage"]; ok {
		aowAccrual = accrual.(float64)
	}

	// Create result
	result := SimulationResult{
		BSN:                 person.BSN,
		Age:                 person.Age,
		HasPartner:          hasPartner,
		Income:              float64(person.AnnualIncome) / 100,
		NetWorth:            float64(person.NetWorth) / 100,
		WorkYears:           person.WorkYears,
		ResidenceYears:      person.ResidenceYears,
		IsStudent:           person.IsStudent,
		StudyGrant:          float64(person.StudyGrant) / 100,
		ZorgtoeslagEligible: zorgtoeslag.RequirementsMet,
		ZorgtoeslagAmount:   zorgtoeslagAmount,
		AOWEligible:         aow.RequirementsMet,
		AOWAmount:           aowAmount,
		AOWAccrual:          aowAccrual,
	}

	ls.mutex.Lock()
	ls.Results = append(ls.Results, result)
	ls.mutex.Unlock()

	return nil
}

// RunSimulation runs the full simulation
func (ls *LawSimulator) RunSimulation(numPeople int) []SimulationResult {
	// Generate people with partnerships
	people := make(chan Person)
	go ls.GeneratePairedPeople(numPeople, people)

	// Set up test data
	data := make(chan Person)
	ls.SetupTestData(people, data)

	// Use a wait group to wait for all simulations to complete
	wp := workerpool.New(32)

	bar := progressbar.Default(int64(numPeople), "Simulating")

	// Run simulations for each person
	for person := range data {
		wp.Submit(func() {
			if err := ls.SimulatePerson(person); err != nil {
				fmt.Printf("simulate person: %v", err)
			}

			if err := bar.Add(1); err != nil {
				log.Fatalf("WOLLAH: %v\n", err)
			}
		})
	}

	// Wait for all simulations to complete
	wp.StopWait()

	return ls.Results
}

// WriteResultsToCSV writes simulation results to a CSV file
func WriteResultsToCSV(results []SimulationResult, filename string) error {
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	// Write header
	header := []string{
		"bsn", "age", "has_partner", "income", "net_worth",
		"work_years", "residence_years", "is_student", "study_grant",
		"zorgtoeslag_eligible", "zorgtoeslag_amount",
		"aow_eligible", "aow_amount", "aow_accrual",
	}

	if err := writer.Write(header); err != nil {
		return err
	}

	// Write each row
	for _, result := range results {
		hasPartner := "false"
		if result.HasPartner {
			hasPartner = "true"
		}

		isStudent := "false"
		if result.IsStudent {
			isStudent = "true"
		}

		zorgtoeslagEligible := "false"
		if result.ZorgtoeslagEligible {
			zorgtoeslagEligible = "true"
		}

		aowEligible := "false"
		if result.AOWEligible {
			aowEligible = "true"
		}

		row := []string{
			result.BSN,
			strconv.Itoa(result.Age),
			hasPartner,
			fmt.Sprintf("%.2f", result.Income),
			fmt.Sprintf("%.2f", result.NetWorth),
			fmt.Sprintf("%.2f", result.WorkYears),
			fmt.Sprintf("%.2f", result.ResidenceYears),
			isStudent,
			fmt.Sprintf("%.2f", result.StudyGrant),
			zorgtoeslagEligible,
			fmt.Sprintf("%.2f", result.ZorgtoeslagAmount),
			aowEligible,
			fmt.Sprintf("%.2f", result.AOWAmount),
			fmt.Sprintf("%.2f", result.AOWAccrual),
		}

		if err := writer.Write(row); err != nil {
			return err
		}
	}

	return nil
}

// CalculateStatistics computes and prints statistics on simulation results
func CalculateStatistics(results []SimulationResult) {
	fmt.Println("\nPopulation Statistics:")
	fmt.Printf("Total people: %d\n", len(results))

	// Count partners
	partnerCount := 0
	for _, result := range results {
		if result.HasPartner {
			partnerCount++
		}
	}
	partnerPercentage := float64(partnerCount) / float64(len(results)) * 100
	fmt.Printf("With partners: %.1f%%\n", partnerPercentage)

	// Count students
	studentCount := 0
	for _, result := range results {
		if result.IsStudent {
			studentCount++
		}
	}
	studentPercentage := float64(studentCount) / float64(len(results)) * 100
	fmt.Printf("Students: %.1f%%\n", studentPercentage)

	// Calculate age statistics
	ageSum := 0
	ageMin := 999
	ageMax := 0
	for _, result := range results {
		ageSum += result.Age
		if result.Age < ageMin {
			ageMin = result.Age
		}
		if result.Age > ageMax {
			ageMax = result.Age
		}
	}
	ageAvg := float64(ageSum) / float64(len(results))
	fmt.Printf("Average age: %.1f years\n", ageAvg)
	fmt.Printf("Age range: %d-%d years\n", ageMin, ageMax)

	// Calculate income statistics
	incomeSum := 0.0
	incomes := make([]float64, len(results))
	for i, result := range results {
		incomeSum += result.Income
		incomes[i] = result.Income
	}
	incomeAvg := incomeSum / float64(len(results))
	fmt.Printf("\nIncome Statistics:\n")
	fmt.Printf("Average income: €%.2f\n", incomeAvg)

	// Calculate income percentiles
	sort.Float64s(incomes)
	fmt.Println("Income percentiles:")
	for _, p := range []int{10, 25, 50, 75, 90} {
		percentile := float64(p) / 100.0
		index := int(percentile * float64(len(incomes)))
		if index >= len(incomes) {
			index = len(incomes) - 1
		}
		fmt.Printf("  %dth: €%.2f\n", p, incomes[index])
	}

	// Calculate zorgtoeslag statistics
	eligible := make([]SimulationResult, 0)
	for _, result := range results {
		if result.ZorgtoeslagEligible {
			eligible = append(eligible, result)
		}
	}

	fmt.Printf("\nZorgtoeslag Statistics:\n")
	eligiblePercentage := float64(len(eligible)) / float64(len(results)) * 100
	fmt.Printf("Eligible: %.1f%%\n", eligiblePercentage)

	if len(eligible) > 0 {
		// Calculate average zorgtoeslag amount
		zorgtoeslagSum := 0.0
		zorgtoeslagMin := 999999.0
		zorgtoeslagMax := 0.0
		for _, result := range eligible {
			zorgtoeslagSum += result.ZorgtoeslagAmount
			if result.ZorgtoeslagAmount < zorgtoeslagMin {
				zorgtoeslagMin = result.ZorgtoeslagAmount
			}
			if result.ZorgtoeslagAmount > zorgtoeslagMax {
				zorgtoeslagMax = result.ZorgtoeslagAmount
			}
		}
		zorgtoeslagAvg := zorgtoeslagSum / float64(len(eligible))
		fmt.Printf("Average amount: €%.2f\n", zorgtoeslagAvg)
		fmt.Printf("Amount range: €%.2f-€%.2f\n", zorgtoeslagMin, zorgtoeslagMax)
	}

	// Zorgtoeslag by income quartile
	sort.Slice(results, func(i, j int) bool {
		return results[i].Income < results[j].Income
	})

	if len(results) >= 4 {
		quartileSize := len(results) / 4
		fmt.Println("By income quartile (eligible %):")
		for i := range 4 {
			start := i * quartileSize
			end := (i + 1) * quartileSize
			if i == 3 {
				end = len(results) // Last quartile includes remainder
			}

			quartile := results[start:end]
			eligibleCount := 0
			for _, result := range quartile {
				if result.ZorgtoeslagEligible {
					eligibleCount++
				}
			}

			eligiblePct := float64(eligibleCount) / float64(len(quartile)) * 100
			lowerBound := quartile[0].Income
			upperBound := quartile[len(quartile)-1].Income

			fmt.Printf("  Q%d (€%.0f-€%.0f): %.1f%%\n", i+1, lowerBound, upperBound, eligiblePct)
		}
	} else {
		fmt.Println("Income quartile cant be calculated, not enough results")
	}

	// Calculate AOW statistics
	aowEligible := make([]SimulationResult, 0)
	for _, result := range results {
		if result.AOWEligible {
			aowEligible = append(aowEligible, result)
		}
	}

	fmt.Printf("\nAOW Statistics:\n")
	aowEligiblePct := float64(len(aowEligible)) / float64(len(results)) * 100
	fmt.Printf("Eligible: %.1f%%\n", aowEligiblePct)

	if len(aowEligible) > 0 {
		// Calculate average AOW amount
		aowSum := 0.0
		for _, result := range aowEligible {
			aowSum += result.AOWAmount
		}
		aowAvg := aowSum / float64(len(aowEligible))
		fmt.Printf("Average amount: €%.2f\n", aowAvg)
	}

	// Calculate average accrual
	accrualSum := 0.0
	for _, result := range results {
		accrualSum += result.AOWAccrual
	}
	accrualAvg := accrualSum / float64(len(results)) * 100
	fmt.Printf("Average accrual: %.1f%%\n", accrualAvg)

	// AOW by age group
	fmt.Println("By age group (eligible %):")
	ageBins := []int{0, 50, 60, 65, 67, 150}
	ageLabels := []string{"<50", "50-60", "60-65", "65-67", "67+"}

	for i := 0; i < len(ageBins)-1; i++ {
		lower := ageBins[i]
		upper := ageBins[i+1]

		// Filter by age group
		group := make([]SimulationResult, 0)
		for _, result := range results {
			if result.Age >= lower && result.Age < upper {
				group = append(group, result)
			}
		}

		if len(group) > 0 {
			eligibleCount := 0
			for _, result := range group {
				if result.AOWEligible {
					eligibleCount++
				}
			}

			eligiblePct := float64(eligibleCount) / float64(len(group)) * 100
			fmt.Printf("  %s: %.1f%%\n", ageLabels[i], eligiblePct)
		}
	}
}
