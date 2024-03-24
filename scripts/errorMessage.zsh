err() {
  echo "[$(date '+%Y-%m-%dT%H:%M:%S%z')]: $*" >&2
  exit 1
}