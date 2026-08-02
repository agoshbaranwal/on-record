-- On Record v2 — foundation schema.
--
-- The point of this file: in v1 the honesty charter was a discipline, enforced by build-time greps
-- and by remembering. Here it is enforced by the database. A claim cannot exist without a source.
-- An image cannot assert causation without an attribution study. A generated image cannot be
-- inserted at all, because there is no enum value for one.
--
-- Everything a reader sees traces back through these tables to a named, dated, licensed origin.

create extension if not exists "pgcrypto";

-- ─────────────────────────────────────────────────────────────────────────────
-- SOURCES — nothing on this site may be stated without one of these
-- ─────────────────────────────────────────────────────────────────────────────
create table sources (
  id            uuid primary key default gen_random_uuid(),
  slug          text not null unique,
  name          text not null,                    -- "ERA5 reanalysis"
  organisation  text not null,                    -- "ECMWF, via Open-Meteo"
  url           text not null,
  licence       text not null,                    -- "CC BY 4.0", "public domain"
  citation      text not null,                    -- a pasteable citation line
  accessed_at   date not null,
  -- how far the source itself claims to be authoritative; used to render honest hedging
  kind          text not null check (kind in ('dataset','paper','survey','agency','study','book')),
  created_at    timestamptz not null default now()
);
comment on table sources is 'Every number, claim and image on the site resolves to a row here.';

-- ─────────────────────────────────────────────────────────────────────────────
-- ATTRIBUTION STUDIES — the ONLY thing that licenses a causal statement
-- ─────────────────────────────────────────────────────────────────────────────
create table attribution_studies (
  id          uuid primary key default gen_random_uuid(),
  event       text not null,                      -- "Pacific North-West heat dome, June 2021"
  occurred_on daterange not null,
  place       text not null,
  publisher   text not null,                      -- "World Weather Attribution"
  doi         text,
  url         text not null,
  finding     text not null,                      -- the study's OWN words for what it concluded
  source_id   uuid not null references sources(id),
  created_at  timestamptz not null default now()
);
comment on table attribution_studies is
  'The site never says an event was caused by climate change on its own authority. It quotes one of these.';

-- ─────────────────────────────────────────────────────────────────────────────
-- IMAGES — provenance is mandatory, causation is gated, AI is unrepresentable
-- ─────────────────────────────────────────────────────────────────────────────
-- NOTE: there is deliberately no 'generated' value. A generated image has no photographer, no date
-- and no place; on a site whose whole claim is that everything traces to an origin, it is the visual
-- equivalent of an invented number. Making it unrepresentable is stronger than a policy.
create type image_origin as enum ('photograph','satellite','repeat_pair','archival','diagram');
create type image_mode   as enum ('illustrative','evidentiary');

create table images (
  id            uuid primary key default gen_random_uuid(),
  origin        image_origin not null,
  mode          image_mode not null default 'illustrative',
  storage_path  text not null,
  width         int not null check (width > 0),
  height        int not null check (height > 0),

  -- provenance: every field here is required, exactly as a number's source is required
  photographer  text not null,
  agency        text,
  captured_on   date not null,
  location      text not null,                    -- "Sonoma County, California"
  lat           double precision check (lat between -89 and 89),
  lon           double precision check (lon between -180 and 180),
  licence       text not null,
  credit        text not null,                    -- the visible credit line, rendered with the image

  -- caption must describe WHAT IS DEPICTED — a named event at a named place and date.
  -- It must never say "climate change"; that is the job of an attached study, if there is one.
  caption       text not null check (length(caption) between 12 and 400),

  attribution_study_id uuid references attribution_studies(id),
  source_id     uuid not null references sources(id),

  -- for repeat photography: the earlier frame of the same viewpoint
  pairs_with_id uuid references images(id),
  created_at    timestamptz not null default now(),

  -- ── THE CAUSATION GATE ──────────────────────────────────────────────────────
  -- An image may only be evidentiary if a published attribution study is attached.
  constraint evidentiary_requires_study
    check (mode = 'illustrative' or attribution_study_id is not null),
  -- A repeat pair must actually have a pair, or it proves nothing.
  constraint repeat_pair_needs_partner
    check (origin <> 'repeat_pair' or pairs_with_id is not null)
);
comment on constraint evidentiary_requires_study on images is
  'A photograph of a flood implies causation the data may not support. Illustrative by default; only a published study promotes it.';

-- ─────────────────────────────────────────────────────────────────────────────
-- PLACES and their records
-- ─────────────────────────────────────────────────────────────────────────────
create table places (
  id         uuid primary key default gen_random_uuid(),
  slug       text not null unique,
  name       text not null,                       -- "Lucknow"
  full_name  text not null,                       -- "Lucknow, India"
  country    text not null,
  iso3       char(3) not null,
  lat        double precision not null check (lat between -89 and 89),
  lon        double precision not null check (lon between -180 and 180),
  timezone   text not null,                       -- IANA
  population int check (population >= 0),
  in_picker  boolean not null default false,      -- the curated fallback bar
  created_at timestamptz not null default now()
);

-- A place's own baseline. The thresholds ARE the 1951-80 95th percentiles for that place,
-- which is why the baseline decade always yields ~5% of days and why the site must headline
-- the MULTIPLE rather than the pair (measured 18-21 across 20 cities — it is arithmetic, not a finding).
create table place_baselines (
  place_id        uuid primary key references places(id) on delete cascade,
  baseline_from   int not null default 1951,
  baseline_to     int not null default 1980,
  threshold_hot   numeric(4,1) not null,
  threshold_night numeric(4,1) not null,
  source_id       uuid not null references sources(id),
  computed_at     timestamptz not null default now(),
  check (baseline_to > baseline_from)
);

create table place_records (
  place_id    uuid not null references places(id) on delete cascade,
  year        int  not null check (year between 1940 and 2100),
  hot_days    int  not null check (hot_days between 0 and 366),
  warm_nights int  not null check (warm_nights between 0 and 366),
  mean_tmax   numeric(5,2),
  anomaly     numeric(5,2),
  primary key (place_id, year)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- INDICATORS — the global vitals, each with an "as of" so nothing is silently stale
-- ─────────────────────────────────────────────────────────────────────────────
create table indicators (
  slug       text primary key,                    -- 'co2_ppm', 'budget_gt_igcc', 'sea_level_mm'
  label      text not null,
  value      numeric not null,
  unit       text not null,
  as_of      date not null,
  -- fast-moving numbers must declare how long they may be trusted; the UI shows a staleness badge
  stale_after_days int not null default 40,
  source_id  uuid not null references sources(id),
  updated_at timestamptz not null default now()
);

-- ─────────────────────────────────────────────────────────────────────────────
-- EDITORIAL — articles, and the claims inside them
-- ─────────────────────────────────────────────────────────────────────────────
create type bucket as enum ('right_now','your_place','whats_coming','why_it_matters','whats_working','how_we_know');

create table articles (
  id            uuid primary key default gen_random_uuid(),
  slug          text not null unique,
  bucket        bucket not null,
  title         text not null,
  dek           text not null check (length(dek) <= 220),
  body_mdx      text not null,
  hero_image_id uuid references images(id),
  status        text not null default 'draft' check (status in ('draft','review','published')),
  published_at  timestamptz,
  reviewed_by   text,                             -- a named human, for the schools/NGO audience
  updated_at    timestamptz not null default now(),
  -- nothing reaches a reader without a named reviewer
  constraint published_needs_reviewer check (status <> 'published' or reviewed_by is not null),
  constraint published_needs_date     check (status <> 'published' or published_at is not null)
);

-- The v1 invariant "every claim maps to a source" as a foreign key rather than a grep.
create table claims (
  id         uuid primary key default gen_random_uuid(),
  article_id uuid not null references articles(id) on delete cascade,
  anchor     text not null,                       -- the id the figure renders with, for permalinks
  text       text not null,
  source_id  uuid not null references sources(id),
  created_at timestamptz not null default now(),
  unique (article_id, anchor)
);
comment on table claims is
  'Per-claim anchors are what make a citable permalink possible, which is what lets a student cite this site.';

create index on place_records (place_id, year);
create index on images (mode);
create index on articles (bucket, status);
create index on claims (source_id);
