rm -f ../data/lan_control_plane.db
docker compose -f ../server/docker-compose.yml --profile tools run --rm migrate
docker compose -f ../server/docker-compose.yml up -d --build
