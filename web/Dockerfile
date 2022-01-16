FROM python

EXPOSE 8080

WORKDIR /app/

# Only copy over the requirments.txt for now (helps with Docker layer caching)
COPY ./requirements.txt /app/requirements.txt

RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . /app/

CMD [ "gunicorn" ]