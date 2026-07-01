begin;

alter table anime
  add column if not exists tags text[] not null default '{}';

alter table source_connector
  add column if not exists last_attempt_at timestamptz,
  add column if not exists last_error text;

create index if not exists current_rating_source_idx
  on current_rating (source, sampled_at desc);

commit;
