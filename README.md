# Swisstination Backend

This is the backend part of Swisstination.

## How to Run

1. **Clone the repository**
    ```bash
    git clone https://github.com/ItSam77/Swisstination-BEs.git
    ```

2. **Navigate to the directory**
    ```bash
    cd Swisstination-BEs
    ```

3. **Set up environment variables**
    - Configure your `.env` file with your credentials
    - Use `.env.example` as a reference

4. **Set up database**
    - Import the provided SQL file(db.sql) into your Supabase database
    - This creates the necessary relation tables

5. **Ensure Docker is installed**
    - Make sure Docker is installed on your computer

6. **Build and run with Docker Compose**
    ```bash
    docker-compose up --build -d
    ```

## Services

After running docker-compose, you'll have 3 containers:

- **Backend Service**: `localhost:8001`
  - API documentation available at `localhost:8001/docs`
- **Prometheus**: `localhost:8002`
- **Grafana**: `localhost:8003`

## Optional: Monitoring

To access monitoring dashboard:
1. Go to `https://localhost:8003`
2. Login with:
    - Username: `admin`
    - Password: `admin`
3. Create custom monitoring using metrics from `metrics.py` in the `monitor-source` directory
