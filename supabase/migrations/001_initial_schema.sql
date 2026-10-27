-- Supabase SQL Editor でこのファイル全体を実行してください。
-- 1アカウントごとに、試合記録・ヒーロー一覧・マップ一覧をまとめて保存します。
create table if not exists public.user_data (
  user_id uuid primary key references auth.users(id) on delete cascade,
  payload jsonb not null default '{"matches":[],"heroes":[],"maps":[]}'::jsonb,
  updated_at timestamptz not null default now()
);

alter table public.user_data enable row level security;

create policy "Users can read own data"
  on public.user_data for select
  to authenticated
  using (auth.uid() = user_id);

create policy "Users can insert own data"
  on public.user_data for insert
  to authenticated
  with check (auth.uid() = user_id);

create policy "Users can update own data"
  on public.user_data for update
  to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "Users can delete own data"
  on public.user_data for delete
  to authenticated
  using (auth.uid() = user_id);
