FROM python:3.11-slim

WORKDIR /code

# install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 9000
COPY . .

CMD ["./startup_script.sh"]