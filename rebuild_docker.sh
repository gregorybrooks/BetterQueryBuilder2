set -v
docker rmi task-query-builder1:1.0.0
docker build -t task-query-builder1:1.0.0 .
