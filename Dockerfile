FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --break-system-packages --root-user-action ignore -r ./requirements.txt

COPY . .

EXPOSE 5000

ENTRYPOINT ["gunicorn", "FlaskApp:app"]

CMD ["-b", "0.0.0.0:5000"]
