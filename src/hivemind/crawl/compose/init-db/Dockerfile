# Postgres with pg_cron and Firecrawl NuQ schema.
# Built locally for native arm64 support on Apple Silicon.
# Based on: github.com/firecrawl/firecrawl/apps/nuq-postgres

ARG PG_MAJOR=17
FROM postgres:${PG_MAJOR}

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        postgresql-${PG_MAJOR}-cron; \
    rm -rf /var/lib/apt/lists/*

# pg_cron must be in shared_preload_libraries before first server start.
# Init scripts run after the server is already up, so we patch the template.
RUN set -eux; \
    conf_sample="/usr/share/postgresql/${PG_MAJOR}/postgresql.conf.sample"; \
    sed -ri "s/^#?shared_preload_libraries\s*=.*/shared_preload_libraries = 'pg_cron'/" "$conf_sample"; \
    printf "\n# pg_cron\ncron.database_name = 'postgres'\n" >> "$conf_sample"

COPY nuq.sql /docker-entrypoint-initdb.d/010-nuq.sql
