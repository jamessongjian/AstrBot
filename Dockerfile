# Use BuildKit for better caching
# DOCKER_BUILDKIT=1 docker build -t your-image-name .

FROM python:3.10-slim
WORKDIR /AstrBot

# Copy only requirements to leverage Docker cache
COPY requirements.txt /AstrBot/
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install -r requirements.txt --no-cache-dir \
    && python -m pip install socksio wechatpy cryptography --no-cache-dir

# Copy the rest of the application code
COPY . /AstrBot/

EXPOSE 6185 
EXPOSE 6186

CMD [ "python", "main.py" ]
