CREATE TABLE IF NOT EXISTS public."box1" (
  "id" serial PRIMARY KEY,
  "bsn" text,
  "loon_uit_dienstbetrekking" integer,
  "uitkeringen_en_pensioenen" integer,
  "winst_uit_onderneming" integer,
  "resultaat_overige_werkzaamheden" integer,
  "eigen_woning" integer,
  "created_at" timestamp
);

CREATE TABLE IF NOT EXISTS public."box2" (
  "id" serial PRIMARY KEY,
  "bsn" text,
  "reguliere_voordelen" integer,
  "vervreemdingsvoordelen" integer
);

CREATE TABLE IF NOT EXISTS public."box3" (
  "id" serial PRIMARY KEY,
  "bsn" text,
  "spaargeld" integer,
  "beleggingen" integer,
  "onroerend_goed" integer,
  "schulden" integer
);

CREATE TABLE IF NOT EXISTS public."aftrekposten" (
  "id" serial PRIMARY KEY,
  "bsn" text,
  "persoonsgebonden_aftrek" integer
);

CREATE TABLE IF NOT EXISTS public."buitenlands" (
  "id" serial PRIMARY KEY,
  "bsn" text,
  "inkomen" integer
);
