# Agent

1. Create PostgreSQL persistence data storage in Docker
docker run --name claims_db -e POSTGRES_PASSWORD=claims -p 5432:5432 -v claims_data:/var/lib/postgresql/data -d postgres:16

docker ps

docker exec -it claims_db psql -U postgres

2. Open backend, create main.py and .env files. 
3. Create Virtual environment where packages you install for this project won't interfere with other Python projects on your computer, and vice versa. It keeps your project's dependencies clean and manageable.
python -m venv .venv
source .venv/Scripts/activate
pip install fastapi python-multipart 

4. Open frontend folder
 npx create-next-app@latest .
  
5. Once everything is done, handle container creation of postgresql and grafana on compose.yml file
docker stop claims_db
docker rm claims_db
docker compose down -v
find . -name "__pycache__" -exec rm -rf {} +

6. pip install aio-pika (for RabbitMQ). Also login to Grafana