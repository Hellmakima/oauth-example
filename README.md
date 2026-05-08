# Trying OAuth

Trying out external auth with Authentik and integration with a simple app.

## Setup

1. Install [Authentik](https://docs.goauthentik.io/install-config/install/docker-compose/)
2. Make an application in Authentik with the following settings:
    *These are minimal settings, leaving the defaults as is*
    - Name: `Tweets` (or whatever you want)
    - Provider: `OAuth2/OpenID Provider`
    - Authorization flow: pick any (explicit: shows login screen every time)
    - Redirect URI: `http://localhost:8000/callback` (also configurable)
    - Click `Next` and `Submit`
3. Run the app
    3.1. Setup DB
    ```bash
    docker pull postgres:16

    docker run -d \
        --name pg \
        -e POSTGRES_USER=app \
        -e POSTGRES_PASSWORD=secret \
        -e POSTGRES_DB=tweets \
        -p 5432:5432 \
        postgres:16

    docker ps

    docker exec -it auth-postgresql-1 psql -U authentik

    docker exec -it pg bash # to get into the postgres container
    psql -U app -d tweets
    ```

    ```
    3.2. Uvicorn
    ```bash
    uv run uvicorn main:app --reload
    ```

4. Try it out
localhost:8000/
localhost:8000/login
localhost:8000/me
localhost:8000/logout
localhost:8000/health

