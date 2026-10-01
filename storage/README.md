# storage/

Local-development file storage. Only used when `STORAGE_BACKEND` resolves
to `local` — i.e. when `SUPABASE_URL` / `SUPABASE_KEY` are not set.

**Do not rely on this folder for production data.** Most free hosting
platforms (including Render's free tier) wipe local disk contents on
every redeploy and restart. In production, files are written to
Supabase Storage instead — see the main README, "Deploying to Render +
Supabase (free, public, persistent)".
