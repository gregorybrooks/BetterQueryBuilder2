set -v
docker rmi gregorybrooks/better-query-builder-2:2.0.0
docker build -t gregorybrooks/better-query-builder-2:2.0.0 .
