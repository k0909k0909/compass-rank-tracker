# コンパス戦績ノート（クラウド同期対応版）

#コンパスの試合結果・ランクポイントを記録する React + TypeScript + Vite アプリです。Supabase のメールアカウントでログインすると、試合記録・ヒーロー一覧・マップ一覧をクラウドに保存し、PC とスマートフォンで共有できます。

## 構成

- Web公開：Vercel などの静的ホスティング
- アカウント／データ保存：Supabase
- ローカル開発：Node.js LTS

## Supabase の設定

1. Supabase で新しいプロジェクトを作成します。
2. Supabase の SQL Editor を開き、`supabase/migrations/001_initial_schema.sql` の内容を貼り付けて実行します。
3. Authentication の設定でメール／パスワード認証を有効にします。
4. Project Connect / API Keys の画面から Project URL と Publishable key を確認します。
5. Vercel の Project Settings → Environment Variables に次を登録します。
   - `VITE_SUPABASE_URL` = Project URL
   - `VITE_SUPABASE_PUBLISHABLE_KEY` = Publishable key
6. 登録後、Vercel で再デプロイします。

**重要：** `service_role` や `secret` と書かれたキーはブラウザアプリに設定しないでください。Publishable key を使い、SQL の Row Level Security (RLS) ポリシーも有効なままにしてください。

## Vercel への公開

1. このプロジェクトを GitHub リポジトリにアップロードします。
2. Vercel で GitHub リポジトリを Import します。
3. Build Command は `npm run build`、Output Directory は `dist`（通常は自動検出）にします。
4. Supabase の環境変数を登録して Deploy します。
5. 公開URLをPCとスマートフォンの両方で開き、同じメールアドレスとパスワードでログインします。

## ローカル起動

```bash
npm install
npm run dev
```

表示された `http://localhost:5173` をブラウザで開きます。クラウド同期をローカルでも試す場合は、プロジェクト直下に `.env.local` を作成し、上記の Supabase 環境変数を設定してください。

## 注意事項

- 最初にログインした端末にローカルデータがある場合、クラウド側にデータが存在しなければ、そのデータを初回アップロードします。
- すでにクラウド側にデータがある場合は、ログイン時にクラウドのデータが読み込まれます。
- 端末を変える前に、念のため「設定・バックアップ」から JSON バックアップを保存してください。
- このアプリの初期版には、複数端末で同時編集した際の競合解決機能はありません。複数端末を同時に操作する場合は注意してください。
