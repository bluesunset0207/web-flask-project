FROM python:3.12

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]
