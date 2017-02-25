FROM python:3.5  
ENV PYTHONUNBUFFERED 1  
RUN mkdir /config && mkdir /src && mkdir -p /www/media && mkdir -p /www/static
ADD /config/requirements_docker.txt /config/  
RUN pip install -r /config/requirements_docker.txt
WORKDIR /src

