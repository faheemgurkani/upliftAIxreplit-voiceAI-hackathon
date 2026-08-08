-- Gawah full schema (Supabase / Postgres) — FULL_SPEC §5

create extension if not exists "pgcrypto";

create table if not exists sessions (
  id uuid primary key default gen_random_uuid(),
  room_name text,
  status text default 'active',
  created_at timestamptz default now()
);

create table if not exists incident_clusters (
  id uuid primary key default gen_random_uuid(),
  cluster_label text,
  incident_date_range text,
  incident_location text,
  statement_count integer default 0,
  consensus_summary jsonb default '{}'::jsonb,
  conflict_map jsonb default '[]'::jsonb,
  cluster_status varchar(30) default 'open',
  composite_score numeric(4,3),
  collusion_warning boolean default false,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists statements (
  id uuid primary key default gen_random_uuid(),
  ref_code varchar(6) unique not null,
  session_id text,

  time_of_incident text,
  location text not null,
  persons_present text[] default '{}',
  sequence_of_events text not null,
  relationship_to_accused text,
  temporal_uncertainty boolean default false,
  language_of_call varchar(10) default 'ur',

  witness_type varchar(30),
  corroboration_sources_mentioned text[] default '{}',

  statement_delay_days integer,
  statement_delay_explanation text,
  delayed_statement_high_risk boolean default false,

  privacy_mode boolean default false,
  intimidation_flag boolean default false,
  intimidation_text text,
  inconsistency_flags jsonb default '[]',

  offence_category varchar(50),
  witness_age_under_16 boolean default false,
  witness_is_victim boolean default false,
  protection_referral_generated boolean default false,
  protection_referral_url text,
  applicable_protection_act text,
  preferred_contact_method varchar(50) default 'phone',
  safe_contact_time text,

  corrections_count integer default 0,
  confirmed_by_witness boolean default false,
  confirmation_audio_url text,

  background_noise_flagged boolean default false,
  third_party_presence_flagged boolean default false,
  call_phase_at_disconnect varchar(30),

  incident_cluster_id uuid references incident_clusters(id),
  corroboration_score numeric(4,3),
  corroboration_detail jsonb default '{}',

  status varchar(50) default 'pending_review',
  created_at timestamptz default now(),
  reviewed_at timestamptz,
  reviewed_by text,
  reviewer_notes text,

  readback_text text,
  readback_audio_url text,
  call_recording_url text,
  raw_transcript text
);

create index if not exists idx_ref_code on statements(ref_code);
create index if not exists idx_status on statements(status, created_at desc);
create index if not exists idx_cluster on statements(incident_cluster_id);

create table if not exists kpi_events (
  id uuid primary key default gen_random_uuid(),
  type text not null,
  meta jsonb default '{}'::jsonb,
  at timestamptz default now()
);

create or replace function append_inconsistency_flag(
  p_session_id text,
  p_flag jsonb
) returns void as $$
begin
  update statements
  set inconsistency_flags = inconsistency_flags || p_flag
  where session_id = p_session_id;
end;
$$ language plpgsql security definer;
