begin;

create table if not exists catalog_backfill_state (
  source text primary key references source_connector(code),
  start_year integer not null check (start_year between 1900 and 2100),
  end_year integer not null check (end_year between start_year and 2100),
  next_year integer not null check (next_year between 1900 and 2101),
  next_offset integer not null default 0 check (next_offset >= 0),
  processed_pages integer not null default 0 check (processed_pages >= 0),
  discovered_count integer not null default 0 check (discovered_count >= 0),
  completed boolean not null default false,
  last_error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

commit;
