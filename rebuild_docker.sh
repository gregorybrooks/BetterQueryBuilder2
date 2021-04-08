set -v
docker rmi better-query-builder-2:1.0.0
docker build -t better-query-builder-2:1.0.0 .
