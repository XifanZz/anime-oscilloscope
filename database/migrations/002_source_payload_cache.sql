begin;

create table source_payload_cache (
  id bigint generated always as identity primary key,
  source text not null check (source in ('bangumi', 'mal', 'douban', 'filmarks')),
  resource_type text not null check (resource_type in ('subject', 'episode_page', 'search_page', 'rating')),
  external_id text not null,
  payload jsonb not null,
  payload_sha256 text not null,
  fetched_at timestamptz not null,
  expires_at timestamptz,
  unique (source, resource_type, external_id, payload_sha256)
);

create index source_payload_lookup_idx
  on source_payload_cache (source, resource_type, external_id, fetched_at desc);

commit;
