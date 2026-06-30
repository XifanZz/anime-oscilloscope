begin;

create extension if not exists pgcrypto;
create extension if not exists vector;

create table anime (
  id uuid primary key default gen_random_uuid(),
  bangumi_id bigint unique not null,
  canonical_name text not null,
  name_cn text,
  aliases text[] not null default '{}',
  summary text,
  image_url text,
  air_date date,
  end_date date,
  status text not null default 'unknown' check (status in ('upcoming', 'airing', 'finished', 'unknown')),
  media_type text not null check (media_type in ('tv', 'web', 'movie', 'ova', 'special', 'other')),
  regions text[] not null default '{}',
  is_nsfw boolean not null default false,
  is_excluded boolean not null default false,
  exclusion_reason text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table external_mapping (
  id bigint generated always as identity primary key,
  anime_id uuid not null references anime(id) on delete cascade,
  source text not null check (source in ('bangumi', 'mal', 'douban', 'filmarks')),
  external_id text not null,
  confidence numeric(5,4) check (confidence between 0 and 1),
  review_status text not null default 'pending' check (review_status in ('automatic', 'pending', 'approved', 'rejected')),
  match_evidence jsonb not null default '{}'::jsonb,
  reviewed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (source, external_id),
  unique (anime_id, source)
);

create table current_rating (
  anime_id uuid not null references anime(id) on delete cascade,
  source text not null check (source in ('bangumi', 'mal', 'douban', 'filmarks')),
  score numeric(4,2) not null check (score between 0 and 10),
  rating_count integer not null check (rating_count >= 0),
  source_rank integer check (source_rank is null or source_rank > 0),
  sampled_at timestamptz not null,
  primary key (anime_id, source)
);

create table rating_snapshot (
  id bigint generated always as identity primary key,
  anime_id uuid not null references anime(id) on delete cascade,
  source text not null check (source in ('bangumi', 'mal', 'douban', 'filmarks')),
  score numeric(4,2) not null check (score between 0 and 10),
  rating_count integer not null check (rating_count >= 0),
  source_rank integer check (source_rank is null or source_rank > 0),
  rating_distribution jsonb,
  sampled_at timestamptz not null,
  unique (anime_id, source, sampled_at)
);

create table episode (
  id bigint generated always as identity primary key,
  anime_id uuid not null references anime(id) on delete cascade,
  bangumi_episode_id bigint unique,
  episode_number numeric(8,2),
  title text,
  title_cn text,
  air_date timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table anime_embedding (
  anime_id uuid primary key references anime(id) on delete cascade,
  model_name text not null,
  content_hash text not null,
  embedding vector(512) not null,
  embedded_at timestamptz not null default now()
);

create table source_connector (
  code text primary key check (code in ('bangumi', 'mal', 'douban', 'filmarks')),
  label text not null,
  enabled boolean not null default false,
  disabled_reason text,
  last_success_at timestamptz,
  updated_at timestamptz not null default now()
);

create table sync_run (
  id uuid primary key default gen_random_uuid(),
  source text not null check (source in ('bangumi', 'mal', 'douban', 'filmarks')),
  job_type text not null,
  status text not null check (status in ('running', 'succeeded', 'partial', 'failed')),
  requested_count integer not null default 0,
  succeeded_count integer not null default 0,
  failed_count integer not null default 0,
  error_summary jsonb not null default '{}'::jsonb,
  started_at timestamptz not null default now(),
  finished_at timestamptz
);

create index anime_air_date_idx on anime (air_date desc);
create index anime_filter_idx on anime (status, media_type, is_nsfw, is_excluded);
create index external_mapping_review_idx on external_mapping (review_status, confidence);
create index rating_snapshot_series_idx on rating_snapshot (anime_id, source, sampled_at);
create index episode_timeline_idx on episode (anime_id, air_date);
create index sync_run_recent_idx on sync_run (source, started_at desc);

insert into source_connector (code, label, enabled, disabled_reason) values
  ('bangumi', 'Bangumi', false, 'Enabled in Phase 2'),
  ('mal', 'MyAnimeList', false, 'Enabled in Phase 2'),
  ('douban', '豆瓣', false, 'Requires written authorization'),
  ('filmarks', 'Filmarks', false, 'Requires written authorization');

commit;
