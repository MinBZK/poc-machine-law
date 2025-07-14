package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"os"
	"strings"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	_ "github.com/lib/pq"
	"gopkg.in/yaml.v3"
)

// Custom Null types for JSON marshaling
type NullString struct {
	sql.NullString
}

func (ns NullString) MarshalJSON() ([]byte, error) {
	if !ns.Valid {
		return []byte("null"), nil
	}
	return json.Marshal(ns.String)
}

func (ns *NullString) UnmarshalJSON(data []byte) error {
	if string(data) == "null" {
		ns.Valid = false
		ns.String = ""
		return nil
	}
	if err := json.Unmarshal(data, &ns.String); err != nil {
		return err
	}
	ns.Valid = true
	return nil
}

type NullInt64 struct {
	sql.NullInt64
}

func (ni NullInt64) MarshalJSON() ([]byte, error) {
	if !ni.Valid {
		return []byte("null"), nil
	}
	return json.Marshal(ni.Int64)
}

func (ni *NullInt64) UnmarshalJSON(data []byte) error {
	if string(data) == "null" {
		ni.Valid = false
		ni.Int64 = 0
		return nil
	}
	if err := json.Unmarshal(data, &ni.Int64); err != nil {
		return err
	}
	ni.Valid = true
	return nil
}

type RVVAEndpoint struct {
	RVVAEndpoint string `yaml:"rvva_endpoint"`
	GrantHash    string `yaml:"grant_hash"`
	RVVAID       string `yaml:"rvva_id"`
}

type RVVAMapping struct {
	Organization string                    `yaml:"organization"`
	Endpoints    map[string][]RVVAEndpoint `yaml:"endpoints"`
}

var db *sql.DB
var rvvaMapping RVVAMapping
var tableMetadata = make(map[string]map[string]bool)

func main() {
	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		log.Fatal("DATABASE_URL env var required")
	}
	var err error
	db, err = sql.Open("postgres", dsn)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	migrationSQL, err := os.ReadFile("migrations/0001_create_tables.sql")
	if err != nil {
		log.Fatalf("Failed to read migration file: %v", err)
	}
	if _, err := db.Exec(string(migrationSQL)); err != nil {
		log.Fatalf("Failed to execute migration: %v", err)
	}

	if rvvaData, err := os.ReadFile("rvva_mapping.yaml"); err == nil {
		if err := yaml.Unmarshal(rvvaData, &rvvaMapping); err != nil {
			log.Printf("Warning: Failed to parse rvva_mapping.yaml: %v", err)
		}
	}

	// Populate table metadata
	tableMetadata["box1"] = make(map[string]bool)
	tableMetadata["box1"]["id"] = true
	tableMetadata["box1"]["bsn"] = true
	tableMetadata["box1"]["loon_uit_dienstbetrekking"] = true
	tableMetadata["box1"]["uitkeringen_en_pensioenen"] = true
	tableMetadata["box1"]["winst_uit_onderneming"] = true
	tableMetadata["box1"]["resultaat_overige_werkzaamheden"] = true
	tableMetadata["box1"]["eigen_woning"] = true
	tableMetadata["box1"]["created_at"] = true
	tableMetadata["box2"] = make(map[string]bool)
	tableMetadata["box2"]["id"] = true
	tableMetadata["box2"]["bsn"] = true
	tableMetadata["box2"]["reguliere_voordelen"] = true
	tableMetadata["box2"]["vervreemdingsvoordelen"] = true
	tableMetadata["box3"] = make(map[string]bool)
	tableMetadata["box3"]["id"] = true
	tableMetadata["box3"]["bsn"] = true
	tableMetadata["box3"]["spaargeld"] = true
	tableMetadata["box3"]["beleggingen"] = true
	tableMetadata["box3"]["onroerend_goed"] = true
	tableMetadata["box3"]["schulden"] = true
	tableMetadata["aftrekposten"] = make(map[string]bool)
	tableMetadata["aftrekposten"]["id"] = true
	tableMetadata["aftrekposten"]["bsn"] = true
	tableMetadata["aftrekposten"]["persoonsgebonden_aftrek"] = true
	tableMetadata["buitenlands"] = make(map[string]bool)
	tableMetadata["buitenlands"]["id"] = true
	tableMetadata["buitenlands"]["bsn"] = true
	tableMetadata["buitenlands"]["inkomen"] = true

	r := chi.NewRouter()
	r.Use(middleware.Logger)
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
	r.Route("/aftrekposten", func(r chi.Router) {
		r.Get("/", listAftrekposten)
		r.Get("/{id}", getAftrekposten)
		r.Post("/", createAftrekposten)
		r.Put("/{id}", updateAftrekposten)
		r.Delete("/{id}", deleteAftrekposten)
	})
	r.Route("/buitenlands", func(r chi.Router) {
		r.Get("/", listBuitenlands)
		r.Get("/{id}", getBuitenlands)
		r.Post("/", createBuitenlands)
		r.Put("/{id}", updateBuitenlands)
		r.Delete("/{id}", deleteBuitenlands)
	})

	log.Println("Listening on :8080")
	http.ListenAndServe(":8080", r)
}

func logRVVAInfo(endpoint string) {
	if endpoints, exists := rvvaMapping.Endpoints[endpoint]; exists && len(endpoints) > 0 {
		ep := endpoints[0]
		log.Printf("rvva_endpoint: %s", ep.RVVAEndpoint)
		log.Printf("grant_hash: %s", ep.GrantHash)
		log.Printf("rvva_id: %s", ep.RVVAID)
	}
}

type Box1 struct {
	Id                              int64      `json:"id"`
	Bsn                             NullString `json:"bsn"`
	Loon_uit_dienstbetrekking       NullInt64  `json:"loon_uit_dienstbetrekking"`
	Uitkeringen_en_pensioenen       NullInt64  `json:"uitkeringen_en_pensioenen"`
	Winst_uit_onderneming           NullInt64  `json:"winst_uit_onderneming"`
	Resultaat_overige_werkzaamheden NullInt64  `json:"resultaat_overige_werkzaamheden"`
	Eigen_woning                    NullInt64  `json:"eigen_woning"`
	Created_at                      NullString `json:"created_at"`
}

type Box2 struct {
	Id                     int64      `json:"id"`
	Bsn                    NullString `json:"bsn"`
	Reguliere_voordelen    NullInt64  `json:"reguliere_voordelen"`
	Vervreemdingsvoordelen NullInt64  `json:"vervreemdingsvoordelen"`
}

type Box3 struct {
	Id             int64      `json:"id"`
	Bsn            NullString `json:"bsn"`
	Spaargeld      NullInt64  `json:"spaargeld"`
	Beleggingen    NullInt64  `json:"beleggingen"`
	Onroerend_goed NullInt64  `json:"onroerend_goed"`
	Schulden       NullInt64  `json:"schulden"`
}

type Aftrekposten struct {
	Id                      int64      `json:"id"`
	Bsn                     NullString `json:"bsn"`
	Persoonsgebonden_aftrek NullInt64  `json:"persoonsgebonden_aftrek"`
}

type Buitenlands struct {
	Id      int64      `json:"id"`
	Bsn     NullString `json:"bsn"`
	Inkomen NullInt64  `json:"inkomen"`
}

func listBox1(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("listBox1")
	handleList(w, r, "box1", []string{"id", "bsn", "loon_uit_dienstbetrekking", "uitkeringen_en_pensioenen", "winst_uit_onderneming", "resultaat_overige_werkzaamheden", "eigen_woning", "created_at"}, "", nil)
}

func getBox1(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("getBox1")
	id := chi.URLParam(r, "id")
	handleGet(w, r, "box1", []string{"id", "bsn", "loon_uit_dienstbetrekking", "uitkeringen_en_pensioenen", "winst_uit_onderneming", "resultaat_overige_werkzaamheden", "eigen_woning", "created_at"}, id)
}

func createBox1(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("createBox1")
	var item Box1
	if err := json.NewDecoder(r.Body).Decode(&item); err != nil {
		http.Error(w, err.Error(), 400)
		return
	}
	sql := `INSERT INTO public."box1" ("bsn", "loon_uit_dienstbetrekking", "uitkeringen_en_pensioenen", "winst_uit_onderneming", "resultaat_overige_werkzaamheden", "eigen_woning", "created_at") VALUES ($1, $2, $3, $4, $5, $6, $7)`
	_, err := db.Exec(sql, item.Bsn, item.Loon_uit_dienstbetrekking, item.Uitkeringen_en_pensioenen, item.Winst_uit_onderneming, item.Resultaat_overige_werkzaamheden, item.Eigen_woning, item.Created_at)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(201)
}

func updateBox1(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("updateBox1")
	id := chi.URLParam(r, "id")
	var item Box1
	if err := json.NewDecoder(r.Body).Decode(&item); err != nil {
		http.Error(w, err.Error(), 400)
		return
	}
	sql := `UPDATE public."box1" SET "bsn"=$1, "loon_uit_dienstbetrekking"=$2, "uitkeringen_en_pensioenen"=$3, "winst_uit_onderneming"=$4, "resultaat_overige_werkzaamheden"=$5, "eigen_woning"=$6, "created_at"=$7 WHERE id = $8`
	_, err := db.Exec(sql, item.Bsn, item.Loon_uit_dienstbetrekking, item.Uitkeringen_en_pensioenen, item.Winst_uit_onderneming, item.Resultaat_overige_werkzaamheden, item.Eigen_woning, item.Created_at, id)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(204)
}

func deleteBox1(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("deleteBox1")
	id := chi.URLParam(r, "id")
	_, err := db.Exec("DELETE FROM public.\"box1\" WHERE id = $1", id)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(204)
}

func listBox2(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("listBox2")
	handleList(w, r, "box2", []string{"id", "bsn", "reguliere_voordelen", "vervreemdingsvoordelen"}, "", nil)
}

func getBox2(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("getBox2")
	id := chi.URLParam(r, "id")
	handleGet(w, r, "box2", []string{"id", "bsn", "reguliere_voordelen", "vervreemdingsvoordelen"}, id)
}

func createBox2(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("createBox2")
	var item Box2
	if err := json.NewDecoder(r.Body).Decode(&item); err != nil {
		http.Error(w, err.Error(), 400)
		return
	}
	sql := `INSERT INTO public."box2" ("bsn", "reguliere_voordelen", "vervreemdingsvoordelen") VALUES ($1, $2, $3)`
	_, err := db.Exec(sql, item.Bsn, item.Reguliere_voordelen, item.Vervreemdingsvoordelen)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(201)
}

func updateBox2(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("updateBox2")
	id := chi.URLParam(r, "id")
	var item Box2
	if err := json.NewDecoder(r.Body).Decode(&item); err != nil {
		http.Error(w, err.Error(), 400)
		return
	}
	sql := `UPDATE public."box2" SET "bsn"=$1, "reguliere_voordelen"=$2, "vervreemdingsvoordelen"=$3 WHERE id = $4`
	_, err := db.Exec(sql, item.Bsn, item.Reguliere_voordelen, item.Vervreemdingsvoordelen, id)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(204)
}

func deleteBox2(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("deleteBox2")
	id := chi.URLParam(r, "id")
	_, err := db.Exec("DELETE FROM public.\"box2\" WHERE id = $1", id)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(204)
}

func listBox3(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("listBox3")
	handleList(w, r, "box3", []string{"id", "bsn", "spaargeld", "beleggingen", "onroerend_goed", "schulden"}, "", nil)
}

func getBox3(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("getBox3")
	id := chi.URLParam(r, "id")
	handleGet(w, r, "box3", []string{"id", "bsn", "spaargeld", "beleggingen", "onroerend_goed", "schulden"}, id)
}

func createBox3(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("createBox3")
	var item Box3
	if err := json.NewDecoder(r.Body).Decode(&item); err != nil {
		http.Error(w, err.Error(), 400)
		return
	}
	sql := `INSERT INTO public."box3" ("bsn", "spaargeld", "beleggingen", "onroerend_goed", "schulden") VALUES ($1, $2, $3, $4, $5)`
	_, err := db.Exec(sql, item.Bsn, item.Spaargeld, item.Beleggingen, item.Onroerend_goed, item.Schulden)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(201)
}

func updateBox3(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("updateBox3")
	id := chi.URLParam(r, "id")
	var item Box3
	if err := json.NewDecoder(r.Body).Decode(&item); err != nil {
		http.Error(w, err.Error(), 400)
		return
	}
	sql := `UPDATE public."box3" SET "bsn"=$1, "spaargeld"=$2, "beleggingen"=$3, "onroerend_goed"=$4, "schulden"=$5 WHERE id = $6`
	_, err := db.Exec(sql, item.Bsn, item.Spaargeld, item.Beleggingen, item.Onroerend_goed, item.Schulden, id)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(204)
}

func deleteBox3(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("deleteBox3")
	id := chi.URLParam(r, "id")
	_, err := db.Exec("DELETE FROM public.\"box3\" WHERE id = $1", id)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(204)
}

func listAftrekposten(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("listAftrekposten")
	handleList(w, r, "aftrekposten", []string{"id", "bsn", "persoonsgebonden_aftrek"}, "", nil)
}

func getAftrekposten(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("getAftrekposten")
	id := chi.URLParam(r, "id")
	handleGet(w, r, "aftrekposten", []string{"id", "bsn", "persoonsgebonden_aftrek"}, id)
}

func createAftrekposten(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("createAftrekposten")
	var item Aftrekposten
	if err := json.NewDecoder(r.Body).Decode(&item); err != nil {
		http.Error(w, err.Error(), 400)
		return
	}
	sql := `INSERT INTO public."aftrekposten" ("bsn", "persoonsgebonden_aftrek") VALUES ($1, $2)`
	_, err := db.Exec(sql, item.Bsn, item.Persoonsgebonden_aftrek)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(201)
}

func updateAftrekposten(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("updateAftrekposten")
	id := chi.URLParam(r, "id")
	var item Aftrekposten
	if err := json.NewDecoder(r.Body).Decode(&item); err != nil {
		http.Error(w, err.Error(), 400)
		return
	}
	sql := `UPDATE public."aftrekposten" SET "bsn"=$1, "persoonsgebonden_aftrek"=$2 WHERE id = $3`
	_, err := db.Exec(sql, item.Bsn, item.Persoonsgebonden_aftrek, id)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(204)
}

func deleteAftrekposten(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("deleteAftrekposten")
	id := chi.URLParam(r, "id")
	_, err := db.Exec("DELETE FROM public.\"aftrekposten\" WHERE id = $1", id)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(204)
}

func listBuitenlands(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("listBuitenlands")
	handleList(w, r, "buitenlands", []string{"id", "bsn", "inkomen"}, "", nil)
}

func getBuitenlands(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("getBuitenlands")
	id := chi.URLParam(r, "id")
	handleGet(w, r, "buitenlands", []string{"id", "bsn", "inkomen"}, id)
}

func createBuitenlands(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("createBuitenlands")
	var item Buitenlands
	if err := json.NewDecoder(r.Body).Decode(&item); err != nil {
		http.Error(w, err.Error(), 400)
		return
	}
	sql := `INSERT INTO public."buitenlands" ("bsn", "inkomen") VALUES ($1, $2)`
	_, err := db.Exec(sql, item.Bsn, item.Inkomen)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(201)
}

func updateBuitenlands(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("updateBuitenlands")
	id := chi.URLParam(r, "id")
	var item Buitenlands
	if err := json.NewDecoder(r.Body).Decode(&item); err != nil {
		http.Error(w, err.Error(), 400)
		return
	}
	sql := `UPDATE public."buitenlands" SET "bsn"=$1, "inkomen"=$2 WHERE id = $3`
	_, err := db.Exec(sql, item.Bsn, item.Inkomen, id)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(204)
}

func deleteBuitenlands(w http.ResponseWriter, r *http.Request) {
	logRVVAInfo("deleteBuitenlands")
	id := chi.URLParam(r, "id")
	_, err := db.Exec("DELETE FROM public.\"buitenlands\" WHERE id = $1", id)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.WriteHeader(204)
}

type FilterCondition struct {
	Key       string      `json:"key"`
	Value     interface{} `json:"value"`
	Operation string      `json:"operation"`
}

var allowedOperations = map[string]bool{
	"=": true, ">": true, "<": true, ">=": true, "<=": true,
	"<>": true, "!=": true, "LIKE": true, "ILIKE": true,
}

func handleList(w http.ResponseWriter, r *http.Request, tableName string, allFields []string, baseWhere string, baseArgs []interface{}) {
	fieldsParam := r.URL.Query().Get("fields")
	var selectedFields []string
	if fieldsParam != "" {
		selectedFields = strings.Split(fieldsParam, ",")
	} else {
		selectedFields = allFields
	}

	validCols := tableMetadata[tableName]
	for _, field := range selectedFields {
		if !validCols[field] {
			http.Error(w, fmt.Sprintf("invalid field: %s", field), 400)
			return
		}
	}

	var whereParts []string
	if baseWhere != "" {
		whereParts = append(whereParts, baseWhere)
	}
	args := baseArgs

	filterParam := r.URL.Query().Get("filter")
	if filterParam != "" {
		var filters []FilterCondition
		decoded, err := url.QueryUnescape(filterParam)
		if err != nil {
			http.Error(w, "invalid filter: could not decode", 400)
			return
		}
		if err := json.Unmarshal([]byte(decoded), &filters); err != nil {
			http.Error(w, "invalid filter: could not parse json", 400)
			return
		}

		for _, f := range filters {
			if !validCols[f.Key] {
				http.Error(w, fmt.Sprintf("invalid filter key: %s", f.Key), 400)
				return
			}
			if !allowedOperations[f.Operation] {
				http.Error(w, fmt.Sprintf("invalid filter operation: %s", f.Operation), 400)
				return
			}
			whereParts = append(whereParts, fmt.Sprintf("\"%s\" %s $%d", f.Key, f.Operation, len(args)+1))
			args = append(args, f.Value)
		}
	}

	query := fmt.Sprintf("SELECT %s FROM public.\"%s\"", strings.Join(selectedFields, ", "), tableName)
	if len(whereParts) > 0 {
		query += " WHERE " + strings.Join(whereParts, " AND ")
	}

	rows, err := db.Query(query, args...)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	defer rows.Close()

	results := make([]map[string]any, 0)
	for rows.Next() {
		columns := make([]interface{}, len(selectedFields))
		columnPointers := make([]interface{}, len(selectedFields))
		for i := range columns {
			columnPointers[i] = &columns[i]
		}

		if err := rows.Scan(columnPointers...); err != nil {
			http.Error(w, err.Error(), 500)
			return
		}

		m := make(map[string]interface{})
		for i, colName := range selectedFields {
			val := columnPointers[i].(*interface{})
			if b, ok := (*val).([]byte); ok {
				m[colName] = string(b)
			} else {
				m[colName] = *val
			}
		}
		results = append(results, m)
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(results)
}

func handleGet(w http.ResponseWriter, r *http.Request, tableName string, allFields []string, id string) {
	fieldsParam := r.URL.Query().Get("fields")
	var selectedFields []string
	if fieldsParam != "" {
		selectedFields = strings.Split(fieldsParam, ",")
	} else {
		selectedFields = allFields
	}

	validCols := tableMetadata[tableName]
	for _, field := range selectedFields {
		if !validCols[field] {
			http.Error(w, fmt.Sprintf("invalid field: %s", field), 400)
			return
		}
	}

	query := fmt.Sprintf("SELECT %s FROM public.\"%s\" WHERE id = $1", strings.Join(selectedFields, ", "), tableName)
	row := db.QueryRow(query, id)

	columns := make([]interface{}, len(selectedFields))
	columnPointers := make([]interface{}, len(selectedFields))
	for i := range columns {
		columnPointers[i] = &columns[i]
	}

	if err := row.Scan(columnPointers...); err != nil {
		if err == sql.ErrNoRows {
			http.Error(w, "not found", 404)
		} else {
			http.Error(w, err.Error(), 500)
		}
		return
	}

	m := make(map[string]interface{})
	for i, colName := range selectedFields {
		val := columnPointers[i].(*interface{})
		if b, ok := (*val).([]byte); ok {
			m[colName] = string(b)
		} else {
			m[colName] = *val
		}
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(m)
}
