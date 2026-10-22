-- ============================================================
--  KORTICS — Suivi du CLV (closing line value)  → Supabase SQL Editor → Run
--
--  Pourquoi : le ROI demande des milliers de matchs pour trancher (au
--  22/10/2026, 2 148 matchs donnent une fourchette de −4 % à +3 %). Le CLV
--  mesure autre chose, beaucoup plus vite : la cote que nous publions
--  est-elle meilleure que la cote juste avant le match ? Un pronostic qui bat
--  régulièrement la clôture a de la valeur, quel que soit le résultat.
--
--  odds_bookmaker / odds_b restent la cote du DERNIER passage avant le match
--  (réécrite à chaque run tant que le match n'a pas commencé) : c'est notre
--  clôture. On ajoute la cote de la PREMIÈRE publication, jamais réécrite.
--
--  Sans danger : "add column if not exists" n'efface rien. Le pipeline
--  détecte ces colonnes tout seul et commence à les remplir au run suivant.
-- ============================================================

alter table public.historical_predictions
  -- meilleure cote vue à la première publication du pronostic
  add column if not exists cote_pub_a  numeric,
  add column if not exists cote_pub_b  numeric,
  add column if not exists pub_at      timestamptz,
  -- moment du dernier relevé de odds_bookmaker / odds_b avant le match
  add column if not exists cote_maj_at timestamptz;
