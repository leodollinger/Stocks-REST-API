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

# 
CMD ["fastapi", "run", "main.py", "--port", "80"]