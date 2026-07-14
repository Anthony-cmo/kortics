-- ============================================================
--  KORTICS — Schéma Supabase (tables + sécurité RLS)
--  À coller dans Supabase → SQL Editor → Run.
-- ============================================================

-- 0) REPARTIR PROPRE : on supprime l'ancien avant de recréer.
--    (Supprime les données existantes de ces tables — c'est voulu.)
drop trigger if exists on_auth_user_created on auth.users;
drop function if exists public.handle_new_user() cascade;
drop table if exists public.historical_predictions cascade;
drop table if exists public.profiles cascade;

-- 1) TABLE DES MATCHS (les "fiches" affichées sur le site)
create table if not exists public.historical_predictions (
  id             text primary key,          -- event_key de l'API Tennis
  circuit        text not null,             -- 'ATP' ou 'WTA'
  match_date     date not null,
  match_time     text,
  tournament     text,
  surface        text,                       -- déduite via notre table tournoi->surface
  round          text,
  player_a       text not null,
  player_b       text not null,
  player_a_key   text,                        -- clés joueurs de l'API (pour le H2H)
  player_b_key   text,
  rank_a         int,   rank_b        int,    -- classement ATP/WTA
  elo_a          numeric, elo_b       numeric, -- niveau global
  elo_surf_a     numeric, elo_surf_b  numeric, -- niveau sur la surface
  form_a         numeric, form_b      numeric, -- forme 12 mois (%)
  surf_pct_a     numeric, surf_pct_b  numeric, -- % victoires sur la surface
  h2h_a          int,     h2h_b       int,     -- face-à-face
  proba_ia       numeric,                       -- notre proba que le joueur A gagne (%)
  odds_bookmaker numeric,                        -- meilleure cote marché
  odds_ia        numeric,                        -- notre cote "juste valeur"
  is_value       boolean default false,          -- notre estimation s'écarte du marché ?
  match_status   text default 'upcoming',        -- upcoming / Gagné / Perdu / Finished
  winner         text,                            -- 'A' ou 'B' (le gagnant)
  final_result   text,                            -- résultat en sets, ex. "2 - 0"
  score          text,                            -- score détaillé par set, ex. "6-4 6-2 7-6(4)"
  profit_loss    numeric,                         -- résultat (transparence, matchs passés)
  updated_at     timestamptz default now()
);

-- Index pour charger vite les matchs d'un jour / circuit
create index if not exists idx_hp_date_circ on public.historical_predictions (match_date, circuit);

-- 2) TABLE DES PROFILS (statut Premium)
create table if not exists public.profiles (
  id         uuid primary key references auth.users(id) on delete cascade,
  email      text,
  is_vip     boolean not null default false,   -- Premium ? (activé UNIQUEMENT par Stripe/Zapier)
  created_at timestamptz default now()
);

-- ============================================================
-- 3) SÉCURITÉ (Row Level Security) — le point crucial
-- ============================================================
alter table public.historical_predictions enable row level security;
alter table public.profiles                enable row level security;

-- Les matchs = contenu public du produit -> lecture autorisée à tous.
-- (Aucune écriture publique : seul le pipeline, avec la clé service_role, écrit.)
drop policy if exists "matchs lisibles par tous" on public.historical_predictions;
create policy "matchs lisibles par tous"
  on public.historical_predictions for select using (true);

-- Chaque utilisateur ne lit QUE sa propre ligne de profil.
drop policy if exists "profil: lecture de soi" on public.profiles;
create policy "profil: lecture de soi"
  on public.profiles for select using (auth.uid() = id);

-- ⚠️ IMPORTANT : aucune policy UPDATE pour les utilisateurs.
-- => un utilisateur ne peut PAS se mettre "is_vip = true" tout seul.
--    Seul Stripe/Zapier (via la clé service_role) peut activer le Premium.

-- 4) Création automatique du profil à l'inscription (is_vip = false)
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, email, is_vip)
  values (new.id, new.email, false)
  on conflict (id) do nothing;
  return new;
end; $$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
