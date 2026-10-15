# MedInvo Backend

Pharma microservices backend providing Product and Order services. It implements two small FastAPI-based microservices:
- product-service — manages products (CRUD + stock update)
- order-service — creates orders and validates/updates product stock by calling product-service

## Stack
- Language(s): Python (primary), Dockerfile (for containerization)
- Framework / runtime: FastAPI + Uvicorn
- Notable libraries: SQLAlchemy (ORM), Pydantic / pydantic-settings (configuration), httpx (inter-service HTTP), Uvicorn (ASGI server)

## What this is
A minimal two-service backend for managing products and orders. The Order service validates and decrements product stock by calling the Product service over HTTP, then persists orders to a local database.

## How it's organized
Top-level layout (only the key entries shown)

```
.github/                 # CI/automation config (boilerplate)
.gitignore
order-service/
  .env.example
  Dockerfile
  requirements.txt
  app/
    __init__.py
    main.py             # FastAPI app, includes router + health
    routes.py           # endpoints: list/get/create/delete orders; calls product-service
    models.py           # SQLAlchemy Order model
    schemas.py          # pydantic request/response models
    database.py         # DB engine, session, settings (database_url, product_service_url)
  tests/                # tests for order-service
product-service/
  .env.example
  Dockerfile
  requirements.txt
  app/
    __init__.py
    main.py             # FastAPI app
    routes.py           # endpoints for managing products
    models.py
    schemas.py
    database.py         # DB engine and settings (database_url)
  tests/                # tests for product-service
```

How it fits together:
- Each folder is an independent FastAPI service with its own SQLAlchemy models and database connection (config via environment).
- The order-service calls product-service over HTTP (httpx) to validate product existence & price and to update product stock.
- Both services expose a `/health` endpoint for quick health checks.

## Architecture (diagram)

```mermaid
flowchart LR
    Client -->|create order| OrderSvc
    OrderSvc -->|GET /products/{id}| ProductSvc
    ProductSvc --> ProductDB[(Product DB)]
    OrderSvc --> OrderDB[(Order DB)]
    OrderSvc -->|PUT /products/{id}| ProductSvc

    OrderSvc["Order Service\nport 8000"]
    ProductSvc["Product Service\nport 8001"]
```

ASCII diagram (works everywhere):

```
[Client]
   |
   v
[Order Service] --GET/PUT--> [Product Service]
     |                          |
     v                          v
 [Order DB]                 [Product DB]
```

## Important behaviors (read the code)
- Order creation flow (order-service/app/routes.py):
  1. GET product from product-service: `${PRODUCT_SERVICE_URL}/products/{product_id}`
  2. Verify product exists and has enough quantity
  3. Compute total price = product.price * quantity
  4. PUT updated stock back to product-service
  5. Create Order row and persist to order DB
- Both services use pydantic-settings for environment configuration (see `database.py` in each service).

## How to run it (local quickstart)
This repository contains two separate services — run them in separate shells or containers.

Quick local (sqlite) approach for development:

1. Create a virtualenv and install dependencies for each service:

```bash
# from repo root
python -m venv .venv
source .venv/bin/activate

# product service
cd product-service
pip install -r requirements.txt
# set DATABASE_URL to a sqlite file or your DB
export DATABASE_URL="sqlite:///./product.db"
uvicorn app.main:app --reload --port 8001

# in a new shell for order service
cd ../order-service
pip install -r requirements.txt
export DATABASE_URL="sqlite:///./order.db"
# if you use the default settings, order-service expects product-service at http://localhost:8001
uvicorn app.main:app --reload --port 8000
```

Health check:
```bash
curl http://localhost:8001/health   # product service
curl http://localhost:8000/health   # order service
```

Create order example:
```bash
curl -X POST http://localhost:8000/orders -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2, "customer_name": "Alice"}'
```

## Environment variables
Each service uses pydantic-settings and reads environment variables from a `.env` file (see `.env.example` files in each service directory). Common vars:

- DATABASE_URL — SQLAlchemy connection string (e.g., sqlite:///./service.db or postgresql://user:pass@host:5432/dbname)
- (order-service) PRODUCT_SERVICE_URL — full base URL to the product service (default in code: http://localhost:8001)

Example `.env` (development / sqlite):
```
DATABASE_URL=sqlite:///./order.db
# order-service only:
PRODUCT_SERVICE_URL=http://localhost:8001
```

## Running with Docker Compose (recommended for multi-service local testing)
Below is a sample docker-compose you can add at repository root as `docker-compose.yml`. It runs a Postgres DB and both services.

```yaml
version: "3.8"
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: medinvo
    volumes:
      - db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]
      interval: 10s
      retries: 5

  product-service:
    build:
      context: ./product-service
    environment:
      DATABASE_URL: "postgresql://postgres:password@db:5432/medinvo"
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8001:8001"

  order-service:
    build:
      context: ./order-service
    environment:
      DATABASE_URL: "postgresql://postgres:password@db:5432/medinvo"
      PRODUCT_SERVICE_URL: "http://product-service:8001"
    depends_on:
      - product-service
      - db
    ports:
      - "8000:8000"

volumes:
  db-data:
```

If you add this file, run:
```bash
docker compose up --build
```
This starts Postgres, product-service on internal port 8001, and order-service on 8000. The order-service points to product-service via the Docker network.

## Tests
Each service has a `tests/` folder. Run tests per-service:

```bash
cd product-service
pytest

cd ../order-service
pytest
```

## Notes & suggestions
- The order-service currently performs synchronous HTTP calls to product-service while holding transactional changes to the order DB. Consider using distributed patterns for higher reliability (e.g., outbox pattern, retries, idempotency, or a message queue) if this will face high load or partial failures.
- Add API input validation and rate-limiting if public access is required.
- Consider centralizing configuration and secrets for production (do not keep DB passwords in plain `.env` files).
- Add CORS settings and authentication if the services will be called from browsers or external clients.

## Try asking
- "Can you add a docker-compose.yml to this repo that runs Postgres plus both services and migrations?"
- "Should the product-service expose a stock-reservation endpoint to avoid race conditions when multiple orders reserve the same product?"
- "Can we add simple integration tests that spin up both services and a test database to validate the order creation flow?"
