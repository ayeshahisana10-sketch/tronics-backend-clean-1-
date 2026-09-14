-- Run this once in Supabase SQL Editor.
create extension if not exists pgcrypto;

create table if not exists public.trace_reports (
  id uuid primary key default gen_random_uuid(),
  suspect_address text not null,
  confidence_tier text not null,
  confidence_reason text not null,
  final_destination text,
  final_destination_label text,
  cross_chain_flag boolean not null default false,
  cross_chain_note text,
  report_json jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists trace_reports_suspect_address_idx
  on public.trace_reports (suspect_address);
create index if not exists trace_reports_created_at_idx
  on public.trace_reports (created_at desc);

create table if not exists public.complaints (
  id uuid primary key default gen_random_uuid(),
  complaint_id text not null unique,
  reported_wallet text not null,
  blockchain text not null default 'TRON',
  token text not null default 'USDT-TRC20',
  victim_amount numeric,
  transaction_hash text,
  reported_at timestamptz,
  trace_report_json jsonb,
  created_at timestamptz not null default now()
);

alter table public.trace_reports enable row level security;
alter table public.complaints enable row level security;

-- No public policies are created intentionally. The backend uses the
-- server-side Supabase key and performs writes securely on the server.
