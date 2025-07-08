CREATE TABLE IF NOT EXISTS public."box1" (
  id serial PRIMARY KEY,
  bsn text,
  income_from_employment integer,
  benefits_and_pensions integer,
  profit_from_enterprise integer,
  income_other_activities integer,
  eigen_woning integer,
  created_at timestamp
);

CREATE TABLE IF NOT EXISTS public."box2" (
  id serial PRIMARY KEY,
  bsn text,
  reguliere_voordelen integer,
  vervreemdingsvoordelen integer
);

CREATE TABLE IF NOT EXISTS public."box3" (
  id serial PRIMARY KEY,
  bsn text,
  spaargeld integer,
  beleggingen integer,
  onroerend_goed integer,
  schulden integer
);

CREATE TABLE IF NOT EXISTS public."monthly_income" (
  id serial PRIMARY KEY,
  bsn text,
  amount integer
);
