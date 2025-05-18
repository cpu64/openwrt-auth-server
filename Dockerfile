FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --break-system-packages --root-user-action ignore -r ./requirements.txt

COPY . .

EXPOSE 5000

ENV FLASK_APP=FlaskApp.py

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
