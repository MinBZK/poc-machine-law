package main

import (
	"database/sql"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/go-chi/chi/v5"
	_ "github.com/lib/pq"
)

var db *sql.DB

func main() {
	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		log.Fatal("DATABASE_URL env var required")
	}

	print(dsn)

	var err error
	db, err = sql.Open("postgres", dsn)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	r := chi.NewRouter()
	r.Route("/box1", func(r chi.Router) {
		r.Get("/", listBox1)
		r.Get("/{id}", getBox1)
		r.Post("/", createBox1)
		r.Put("/{id}", updateBox1)
		r.Delete("/{id}", deleteBox1)
	})
	r.Route("/box2", func(r chi.Router) {
		r.Get("/", listBox2)
		r.Get("/{id}", getBox2)
		r.Post("/", createBox2)
		r.Put("/{id}", updateBox2)
		r.Delete("/{id}", deleteBox2)
	})
	r.Route("/box3", func(r chi.Router) {
		r.Get("/", listBox3)
		r.Get("/{id}", getBox3)
		r.Post("/", createBox3)
		r.Put("/{id}", updateBox3)
		r.Delete("/{id}", deleteBox3)
	})
	r.Route("/monthly_income", func(r chi.Router) {
		r.Get("/", listMonthly_income)
		r.Get("/{id}", getMonthly_income)
		r.Post("/", createMonthly_income)
		r.Put("/{id}", updateMonthly_income)
		r.Delete("/{id}", deleteMonthly_income)
	})

	log.Println("Listening on :8080")
	http.ListenAndServe(":8080", r)
}

type Box1 struct {
	Id                      int       `json:"id"`
	Bsn                     string    `json:"bsn"`
	Income_from_employment  int       `json:"income_from_employment"`
	Benefits_and_pensions   int       `json:"benefits_and_pensions"`
	Profit_from_enterprise  int       `json:"profit_from_enterprise"`
	Income_other_activities int       `json:"income_other_activities"`
	Eigen_woning            int       `json:"eigen_woning"`
	Created_at              time.Time `json:"created_at"`
}

type Box2 struct {
	Id                     int    `json:"id"`
	Bsn                    string `json:"bsn"`
	Reguliere_voordelen    int    `json:"reguliere_voordelen"`
	Vervreemdingsvoordelen int    `json:"vervreemdingsvoordelen"`
}

type Box3 struct {
	Id             int    `json:"id"`
	Bsn            string `json:"bsn"`
	Spaargeld      int    `json:"spaargeld"`
	Beleggingen    int    `json:"beleggingen"`
	Onroerend_goed int    `json:"onroerend_goed"`
	Schulden       int    `json:"schulden"`
}

type Monthly_income struct {
	Id     int    `json:"id"`
	Bsn    string `json:"bsn"`
	Amount int    `json:"amount"`
}

func listBox1(w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query("SELECT id, bsn, income_from_employment, benefits_and_pensions, profit_from_enterprise, income_other_activities, eigen_woning, created_at FROM public.\"box1\"")
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	defer rows.Close()
	var results []Box1
	for rows.Next() {
		var item Box1
		if err := rows.Scan(
			&item.Id,
			&item.Bsn,
			&item.Income_from_employment,
			&item.Benefits_and_pensions,
			&item.Profit_from_enterprise,
			&item.Income_other_activities,
			&item.Eigen_woning,
			&item.Created_at,
		); err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		results = append(results, item)
	}
	json.NewEncoder(w).Encode(results)
}

func getBox1(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	row := db.QueryRow("SELECT id, bsn, income_from_employment, benefits_and_pensions, profit_from_enterprise, income_other_activities, eigen_woning, created_at FROM public.\"box1\" WHERE id = $1", id)
	var item Box1
	if err := row.Scan(
		&item.Id,
		&item.Bsn,
		&item.Income_from_employment,
		&item.Benefits_and_pensions,
		&item.Profit_from_enterprise,
		&item.Income_other_activities,
		&item.Eigen_woning,
		&item.Created_at,
	); err != nil {
		http.Error(w, err.Error(), 404)
		return
	}
	json.NewEncoder(w).Encode(item)
}

func createBox1(w http.ResponseWriter, r *http.Request) {
	var item Box1
	if err := json.NewDecoder(r.Body).Decode(&item); err != nil {
		http.Error(w, err.Error(), 400)
		return
	}

	item.Created_at = time.Now()

	_, err := db.Exec("INSERT INTO public.\"box1\" (bsn, income_from_employment, benefits_and_pensions, profit_from_enterprise, income_other_activities, eigen_woning, created_at) VALUES ($1, $2, $3, $4, $5, $6, $7)",
		item.Bsn,
		item.Income_from_employment,
		item.Benefits_and_pensions,
		item.Profit_from_enterprise,
		item.Income_other_activities,
		item.Eigen_woning,
		item.Created_at,
	)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(201)
}

func updateBox1(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	var item Box1
	if err := json.NewDecoder(r.Body).Decode(&item); err != nil {
		http.Error(w, err.Error(), 400)
		return
	}
	_, err := db.Exec("UPDATE public.\"box1\" SET bsn = $1, income_from_employment = $2, benefits_and_pensions = $3, profit_from_enterprise = $4, income_other_activities = $5, eigen_woning = $6, created_at = $7 WHERE id = $8",
		item.Bsn,
		item.Income_from_employment,
		item.Benefits_and_pensions,
		item.Profit_from_enterprise,
		item.Income_other_activities,
		item.Eigen_woning,
		item.Created_at,
		id,
	)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(204)
}

func deleteBox1(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	_, err := db.Exec("DELETE FROM public.\"box1\" WHERE id = $1", id)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(204)
}

func listBox2(w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query("SELECT id, bsn, reguliere_voordelen, vervreemdingsvoordelen FROM public.\"box2\"")
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	defer rows.Close()
	var results []Box2
	for rows.Next() {
		var item Box2
		if err := rows.Scan(
			&item.Id,
			&item.Bsn,
			&item.Reguliere_voordelen,
			&item.Vervreemdingsvoordelen,
		); err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		results = append(results, item)
	}
	json.NewEncoder(w).Encode(results)
}

func getBox2(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	row := db.QueryRow("SELECT id, bsn, reguliere_voordelen, vervreemdingsvoordelen FROM public.\"box2\" WHERE id = $1", id)
	var item Box2
	if err := row.Scan(
		&item.Id,
		&item.Bsn,
		&item.Reguliere_voordelen,
		&item.Vervreemdingsvoordelen,
	); err != nil {
		http.Error(w, err.Error(), 404)
		return
	}
	json.NewEncoder(w).Encode(item)
}

func createBox2(w http.ResponseWriter, r *http.Request) {
	var item Box2
	if err := json.NewDecoder(r.Body).Decode(&item); err != nil {
		http.Error(w, err.Error(), 400)
		return
	}
	_, err := db.Exec("INSERT INTO public.\"box2\" (bsn, reguliere_voordelen, vervreemdingsvoordelen) VALUES ($1, $2, $3)",
		item.Bsn,
		item.Reguliere_voordelen,
		item.Vervreemdingsvoordelen,
	)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(201)
}

func updateBox2(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	var item Box2
	if err := json.NewDecoder(r.Body).Decode(&item); err != nil {
		http.Error(w, err.Error(), 400)
		return
	}
	_, err := db.Exec("UPDATE public.\"box2\" SET bsn = $1, reguliere_voordelen = $2, vervreemdingsvoordelen = $3 WHERE id = $4",
		item.Bsn,
		item.Reguliere_voordelen,
		item.Vervreemdingsvoordelen,
		id,
	)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(204)
}

func deleteBox2(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	_, err := db.Exec("DELETE FROM public.\"box2\" WHERE id = $1", id)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(204)
}

func listBox3(w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query("SELECT id, bsn, spaargeld, beleggingen, onroerend_goed, schulden FROM public.\"box3\"")
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	defer rows.Close()
	var results []Box3
	for rows.Next() {
		var item Box3
		if err := rows.Scan(
			&item.Id,
			&item.Bsn,
			&item.Spaargeld,
			&item.Beleggingen,
			&item.Onroerend_goed,
			&item.Schulden,
		); err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		results = append(results, item)
	}
	json.NewEncoder(w).Encode(results)
}

func getBox3(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	row := db.QueryRow("SELECT id, bsn, spaargeld, beleggingen, onroerend_goed, schulden FROM public.\"box3\" WHERE id = $1", id)
	var item Box3
	if err := row.Scan(
		&item.Id,
		&item.Bsn,
		&item.Spaargeld,
		&item.Beleggingen,
		&item.Onroerend_goed,
		&item.Schulden,
	); err != nil {
		http.Error(w, err.Error(), 404)
		return
	}
	json.NewEncoder(w).Encode(item)
}

func createBox3(w http.ResponseWriter, r *http.Request) {
	var item Box3
	if err := json.NewDecoder(r.Body).Decode(&item); err != nil {
		http.Error(w, err.Error(), 400)
		return
	}
	_, err := db.Exec("INSERT INTO public.\"box3\" (bsn, spaargeld, beleggingen, onroerend_goed, schulden) VALUES ($1, $2, $3, $4, $5)",
		item.Bsn,
		item.Spaargeld,
		item.Beleggingen,
		item.Onroerend_goed,
		item.Schulden,
	)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(201)
}

func updateBox3(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	var item Box3
	if err := json.NewDecoder(r.Body).Decode(&item); err != nil {
		http.Error(w, err.Error(), 400)
		return
	}
	_, err := db.Exec("UPDATE public.\"box3\" SET bsn = $1, spaargeld = $2, beleggingen = $3, onroerend_goed = $4, schulden = $5 WHERE id = $6",
		item.Bsn,
		item.Spaargeld,
		item.Beleggingen,
		item.Onroerend_goed,
		item.Schulden,
		id,
	)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(204)
}

func deleteBox3(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	_, err := db.Exec("DELETE FROM public.\"box3\" WHERE id = $1", id)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(204)
}

func listMonthly_income(w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query("SELECT id, bsn, amount FROM public.\"monthly_income\"")
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	defer rows.Close()
	var results []Monthly_income
	for rows.Next() {
		var item Monthly_income
		if err := rows.Scan(
			&item.Id,
			&item.Bsn,
			&item.Amount,
		); err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		results = append(results, item)
	}
	json.NewEncoder(w).Encode(results)
}

func getMonthly_income(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	row := db.QueryRow("SELECT id, bsn, amount FROM public.\"monthly_income\" WHERE id = $1", id)
	var item Monthly_income
	if err := row.Scan(
		&item.Id,
		&item.Bsn,
		&item.Amount,
	); err != nil {
		http.Error(w, err.Error(), 404)
		return
	}
	json.NewEncoder(w).Encode(item)
}

func createMonthly_income(w http.ResponseWriter, r *http.Request) {
	var item Monthly_income
	if err := json.NewDecoder(r.Body).Decode(&item); err != nil {
		http.Error(w, err.Error(), 400)
		return
	}
	_, err := db.Exec("INSERT INTO public.\"monthly_income\" (bsn, amount) VALUES ($1, $2)",
		item.Bsn,
		item.Amount,
	)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(201)
}

func updateMonthly_income(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	var item Monthly_income
	if err := json.NewDecoder(r.Body).Decode(&item); err != nil {
		http.Error(w, err.Error(), 400)
		return
	}
	_, err := db.Exec("UPDATE public.\"monthly_income\" SET bsn = $1, amount = $2 WHERE id = $3",
		item.Bsn,
		item.Amount,
		id,
	)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(204)
}

func deleteMonthly_income(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	_, err := db.Exec("DELETE FROM public.\"monthly_income\" WHERE id = $1", id)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(204)
}
