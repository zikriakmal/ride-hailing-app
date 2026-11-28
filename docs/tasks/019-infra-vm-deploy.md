# 019: Set up the existing VPS and continuous deploy

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 017, 018
- **PRD flow:** none (infra; ADRs 0011, 0012)

## Goal

Merging to `main` builds the backend image in GitHub Actions, pushes it to GHCR, deploys it to our existing VPS behind its nginx, and checks `https://api.<domain>/health`. The database is backed up daily, and a restore has been tested.

## Scope

**In:**
- Set up the VPS per the `docs/INFRA.md` checklist (`deploy/provision.md`): capacity check, DNS, `deploy` user, Docker, `ufw`, `fail2ban`, `/opt/ride/.env`
- Create the `ride` role + database on the existing Postgres with `deploy/create-db.sql`; `~/.pgpass` for `deploy`
- Install the nginx server block, `nginx -t`, reload, `certbot --nginx -d api.<domain>`; other sites on the VPS keep working
- `.github/workflows/deploy.yml`: `workflow_run` after `ci` on `main` + `workflow_dispatch(tag)`; build + push `ghcr.io/<owner>/ride-hailing-api:<sha>` and `:latest`; SSH deploy (pull → migrate → up); smoke test with auto-rollback to the previous tag; `production` environment
- `deploy/backup.sh` + cron: daily `pg_dump -Fc`, `age`-encrypted to the owner + verify public keys, `.sha256`, retention 7 daily / 4 weekly / 3 monthly, 20% free-disk guard, `last-success` file — all on VPS storage (`/var/backups/ride-hailing`, `0700`), no bucket (ADR 0011)
- `deploy/backup-verify.sh` + weekly cron: checksum check and test restore into a throwaway `--network none` Postgres container
- Owner `age` key generated on the owner's machine and stored offline; never copied to the VPS
- Test one restore into a scratch database and record it in Notes

**Out (don't build here):**
- Managed DB, staging, monitoring (backlog)
- Mobile store builds

## API

- none

## Acceptance criteria

- [ ] `https://api.<domain>/health` → `200` envelope with a valid Let's Encrypt cert; `http://` redirects to `https://`; `certbot renew --dry-run` passes
- [ ] Other sites on the VPS still respond after the nginx change
- [ ] A phone on mobile data holds `wss://api.<domain>/ws` open > 5 min
- [ ] Merging a trivial change to `main` deploys it without manual steps; the running image tag equals the merge commit SHA
- [ ] A deliberately broken `/health` makes the smoke test fail and the previous tag is restored automatically
- [ ] Manual `deploy.yml` run with an older `tag` rolls back
- [ ] Ports 5432 and 3000 are not reachable from the internet; SSH password login is refused
- [ ] Other apps' databases on the shared Postgres are untouched; the `ride` role can't connect to them
- [ ] `backup.sh` produces an encrypted dump + checksum in `/var/backups/ride-hailing`; files are `0600`, folder `0700`, readable by no other user (checked as another user)
- [ ] The dump can't be read without a private key (`pg_restore --list` on the raw file fails); `grep` for a known email in the file finds nothing
- [ ] `backup-verify.sh` restores the newest dump into a scratch container and row counts match; a manual restore with the owner key also works (recorded in Notes)
- [ ] With free disk below the threshold, `backup.sh` refuses to run and logs why; rotation keeps exactly 7/4/3 files after a simulated month
- [ ] No private key for the owner exists on the VPS (`find / -name 'owner.key'` is empty)
- [ ] No secrets in the repo or the image (`docker history` shows none)
- [ ] `docs/INFRA.md` matches what was built

## Notes

