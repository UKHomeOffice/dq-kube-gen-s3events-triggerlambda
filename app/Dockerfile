FROM quay.io/ukhomeofficedigital/python-alpine:3.7.6-alpine3.11

ENV USERMAP_UID 1000
WORKDIR /APP

RUN mkdir -p /APP/scripts

COPY app/scripts/ /APP/scripts/

RUN apk add --no-cache --quiet --update

RUN adduser -D -H 1000 && \
    chown -R 1000 /APP
RUN chmod +x scripts/gen_events_trigger_lambda.py

RUN pip3 install boto3

RUN pip3 install pytz

USER ${USERMAP_UID}

CMD python scripts/gen_events_trigger_lambda.py
