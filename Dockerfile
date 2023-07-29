FROM python:3.11

WORKDIR /app

COPY requirements.txt ./
RUN python3.11 -m pip install --no-cache-dir -r requirements.txt

COPY . .


CMD [ "python", "main.py"]