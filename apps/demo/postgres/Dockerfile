FROM postgres:16
COPY demo.sql.gz /docker-entrypoint-initdb.d/10-demo.sql.gz
COPY --chmod=755 demo-reset.sh /usr/local/bin/demo-reset
