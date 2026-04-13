FROM python:3.9-slim

WORKDIR /workspace

COPY app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p app/logs /etc/eudiw/pid-issuer/cert

ENV FLASK_APP=app/app.py

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]