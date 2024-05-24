FROM python:3.12-slim

WORKDIR /neslter

COPY requirements.txt .

# copy the neslter library code
COPY ./neslter ./neslter

# copy what's needed for setup.py
COPY README.md .
COPY VERSION .
COPY setup.py .

# install neslter library
RUN python setup.py install

# now copy the django app
COPY ./nlweb ./nlweb

EXPOSE 8000

CMD gunicorn --chdir nlweb --bind :8000 nlweb.wsgi:application --reload
