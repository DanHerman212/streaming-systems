# use officient lightweight python image
# https://hub.docker.com/_/python
FROM python:3.9-slim-buster

# allow statements and log messages to immediately appear in the logs
ENV PYTHONUNBUFFERED True

# copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# install production dependencies
RUN pip install -r requirements.txt

# Run the web service on container startup
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app