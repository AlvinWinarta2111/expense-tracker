-- Run this once in Supabase: Project -> SQL Editor -> New query -> paste -> Run

create table categories (
  id bigint generated always as identity primary key,
  name text not null unique,
  is_income boolean not null default false,
  color text not null default '#FF6600',
  archived boolean not null default false,
  sort_order int not null default 0
);

create table entries (
  id bigint generated always as identity primary key,
  item text not null,
  entry_date date not null default current_date,
  category_id bigint not null references categories(id),
  amount numeric(12,2) not null,  -- positive = income, negative = expense
  note text,
  created_at timestamptz not null default now()
);

create index entries_date_idx on entries(entry_date);

insert into categories (name, is_income, color, sort_order) values
  ('Income', true, '#639922', 0),
  ('Food & Beverages', false, '#D85A30', 1),
  ('Living Cost', false, '#378ADD', 2),
  ('Shopping', false, '#D4537E', 3),
  ('Transport', false, '#EF9F27', 4),
  ('Life & Entertainment', false, '#7F77DD', 5),
  ('Date', false, '#5DCAA5', 6);
