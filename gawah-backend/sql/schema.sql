-- Gawah Supabase / Postgres schema (MVP)

create extension if not exists "pgcrypto";

create table if not exists cases (
  id uuid primary key default gen_random_uuid(),
  case_id text unique not null,
  status text not null default 'open',
  station_id text,
  title text,
  description text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists statements (
  id uuid primary key default gen_random_uuid(),
  case_id text not null references cases(case_id) on delete cascade,
  call_sid text,
  witness_language text not null default 'urdu',
  raw_transcript text not null default '',
  structured_statement jsonb not null default '{}'::jsonb,
  inconsistencies jsonb not null default '[]'::jsonb,
  confirmed boolean not null default false,
  officer_confirmed boolean not null default false,
  readback_text text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_statements_case_id on statements(case_id);
create index if not exists idx_statements_call_sid on statements(call_sid);
create index if not exists idx_cases_status on cases(status);
