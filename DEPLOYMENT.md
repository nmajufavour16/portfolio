# Running and deploying the portfolio

Use Python 3.12 or newer. Install `requirements.txt` into a virtual environment,
copy `.env.example` to `.env`, and set a private `SECRET_KEY`.

For a local SQLite database, set `LOCAL=1` and `DEBUG=True` in `.env`.
Run:

```powershell
rtk proxy venv/Scripts/python.exe -m pip install -r requirements.txt
rtk proxy venv/Scripts/python.exe manage.py migrate
rtk proxy venv/Scripts/python.exe manage.py collectstatic --noinput
rtk proxy venv/Scripts/python.exe manage.py runserver
```

## Upgrading this version

Back up your production database before running `migrate`. Migration 0009 keeps
the first project at each existing slug, assigns distinct slugs to later duplicates,
and adds a database uniqueness constraint. It preserves all project records and
relationships. Review any renamed project URLs after migration. Migration 0010
creates the shared database cache. After migrating, set `USE_DATABASE_CACHE=1`
on production deployments with multiple workers. The default in-memory cache
needs no cache table, so optional integration data can render during local setup.

GitHub statistics and Spotify listening data are included in the initial page
HTML on every load and refresh. Cached values reduce API calls; Spotify also
refreshes every 30 seconds when JavaScript is available. Provider failures use
previously cached data or a visible unavailable message.

Database files and dumps are no longer tracked by Git. The local copies remain
on disk; existing Git history is unchanged.

## Production security

Set `DEBUG=False`, a strong random `SECRET_KEY`, and explicit production
`ALLOWED_HOSTS`. HTTPS redirects and secure session/CSRF cookies are enabled
when debugging is off. Set a private `ADMIN_GATE_KEY` before logging into
`/admin/login/?key=YOUR_KEY`; an empty key leaves the login gate closed.
The gate supplements the owner's normal Django password authentication.

Terminate HTTPS at your hosting proxy. Set `TRUST_PROXY_HTTPS=1` only when
the trusted proxy strips client-supplied `X-Forwarded-Proto` and replaces it
with the correct scheme. This prevents redirect loops behind TLS termination.

## Durable media uploads

On Vercel or another host with an ephemeral filesystem, configure a dedicated
S3-compatible bucket using:

- `AWS_STORAGE_BUCKET_NAME`
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` (or an AWS workload role)
- `AWS_S3_REGION_NAME`
- `AWS_S3_ENDPOINT_URL` for non-AWS providers

The application uses private objects with signed read URLs and distinct names
for uploads. Grant the application read, write, delete, and list access only to
its media bucket. Static CSS, JavaScript, and logos continue to use WhiteNoise.
See the [django-storages S3 documentation](https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html).

Copy existing files from `media/` into the bucket while preserving their relative
paths, such as `projects/example.png` and `resume/example.pdf`. Setting a bucket
does not copy existing media. Verify a project image and resume download before
switching production traffic. Vercel startup rejects missing bucket configuration.

For a persistent server instead, set `MEDIA_ROOT` to a mounted durable directory
and `MEDIA_URL=/media/`. Configure the web server to serve that directory; Django
serves filesystem media itself only in development. Example Nginx location,
when `MEDIA_ROOT=/var/lib/portfolio/media`:

```nginx
location /media/ {
    alias /var/lib/portfolio/media/;
    add_header X-Content-Type-Options nosniff;
}
```

## Checks

```powershell
rtk proxy venv/Scripts/python.exe manage.py test portfolio --settings=config.test_settings
rtk proxy node --test tests/main.test.cjs
rtk proxy venv/Scripts/python.exe manage.py check --deploy
```

Tests use an in-memory SQLite database, a local email backend, and fake credentials.
They do not send mail or call GitHub, Spotify, or a real bucket. The storage test
generates a signed URL locally. Set GitHub, Spotify, and SMTP credentials separately
in production; test their real delivery after configuring the hosting environment.
