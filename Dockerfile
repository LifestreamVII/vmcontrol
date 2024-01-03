FROM alpine:latest
LABEL maintainer="LifestreamVII"

ENV PYTHONUNBUFFERED=1 
RUN apk add nano 
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools
RUN apk add build-base
ADD server/requirements.txt /usr/src/app/requirements.txt
RUN python3 -m pip install -r /usr/src/app/requirements.txt
RUN python3 -m pip install redis
RUN apk add supervisor
COPY server/init.sh /usr/src/app/init.sh
WORKDIR /usr/src/app
EXPOSE 5000
ENTRYPOINT ["/usr/src/app/init.sh"]
