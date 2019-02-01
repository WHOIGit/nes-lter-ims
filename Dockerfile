FROM continuumio/miniconda3

WORKDIR /neslter

RUN apt-get update

# save space by using OpenBLAS instead of mkl
RUN conda install nomkl

COPY requirements.txt .
RUN conda install --file requirements.txt
RUN conda install gunicorn

# copy the neslter library code
COPY ./neslter ./neslter

# copy what's needed for setup.py
COPY README.md .
COPY VERSION .
COPY setup.py .

# install neslter library in the conda environment
RUN python setup.py develop

# configure the neslter library
COPY config.py.example config.py

# now copy the django app
COPY ./nlweb ./nlweb

EXPOSE 8000

CMD gunicorn --chdir nlweb --bind :8000 nlweb.wsgi:application --reload
