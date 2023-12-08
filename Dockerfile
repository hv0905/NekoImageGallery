FROM python:3.12
LABEL authors="epiphyllum"

ENTRYPOINT ["top", "-b"]