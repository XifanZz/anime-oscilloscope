begin;

alter table anime
  add column episode_count integer check (episode_count is null or episode_count >= 0);

create table mapping_candidate (
  id bigint generated always as identity primary key,
  anime_id uuid not null references anime(id) on delete cascade,
  source text not null check (source in ('mal', 'douban', 'filmarks')),
  external_id text not null,
  title text not null,
  confidence numeric(5,4) not null check (confidence between 0 and 1),
  disposition text not null check (disposition in ('automatic', 'review', 'reject')),
  evidence jsonb not null,
  generated_at timestamptz not null default now(),
  resolved_at timestamptz,
  unique (anime_id, source, external_id)
);

create index mapping_candidate_review_idx
  on mapping_candidate (source, disposition, confidence desc, generated_at desc);

update source_connector
set enabled = true,
    disabled_reason = null,
    updated_at = now()
where code = 'bangumi';

commit;
