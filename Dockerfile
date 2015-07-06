FROM debian:jessie
MAINTAINER Nadrieril "nadrieril@eleves.polytechnique.fr"

#ENV HTTP_PROXY http://kuzh.polytechnique.fr:8080
#ENV http_proxy http://kuzh.polytechnique.fr:8080
#ENV https_proxy http://kuzh.polytechnique.fr:8080

RUN apt-get update && \
    apt-get install -y cron python-pip gunicorn bpython python-dev libmysqlclient-dev python-dateutil

RUN mkdir /app
WORKDIR /app
ADD requirements.txt /app/
RUN pip install -r requirements.txt

ADD . /app/
RUN sed -i 's/bars_django\.settings\.dev_local/bars_django.settings.prod/' bars_django/wsgi.py && \
    sed -i 's/bars_django\.settings\.dev_local/bars_django.settings.prod/' manage.py && \
    echo yes | python manage.py collectstatic

# TODO: Temporary
ADD routes.html /app/static/

ADD agios.cron /etc/cron.d/agios
RUN chmod 0744 /etc/cron.d/agios


VOLUME /srv/api
CMD rm -r /srv/api/*; \
    cp -R /app/static /srv/api/static; \
    python manage.py migrate; \
    cron; \
    gunicorn bars_django.wsgi -w 4 -b unix:/srv/api/gunicorn.sock --log-level=warning --log-file=-
