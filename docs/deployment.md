# Deployment

```
cp .env.example .env     # set AUTH_SECRET (>=16 chars), provider settings
docker compose up --build
cd frontend && npm install && npm run dev
```

**Unverified:** the Dockerfile, `docker-compose.yml`, CI workflow and the FastAPI app were never executed in the build environment.
The API stores data in SQLite at `DB_PATH`; the compose file also provisions qdrant, postgres, redis and neo4j, but the code does not yet use postgres, redis or neo4j,
and the vector store is in-memory unless `QDRANT_URL` is set (Qdrant adapter unexecuted; the in-memory index is rebuilt from SQLite at startup).
Health check: `GET /health`.
