# 
FROM python:3.11

# 
WORKDIR /code

# 
COPY ./requirements.txt /code/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt \
    && playwright install --with-deps \
    && apt-get update -y \
    && apt-get -y install xvfb
# 
COPY . /code

ENV SQLALCHEMY_DATABASE_URL="postgresql://postgres:cial_dnbstock0@stocks.c1agyi0ym4tm.us-east-1.rds.amazonaws.com:5432/postgres"

# 
CMD ["fastapi", "run", "main.py", "--port", "80"]