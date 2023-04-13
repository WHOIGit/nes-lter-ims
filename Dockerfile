FROM condaforge/mambaforge

WORKDIR /neslter

# save space by using OpenBLAS instead of mkl, install gunicorn
RUN conda install nomkl gunicorn

COPY environment.yml .
RUN conda env update -n root -f environment.yml

COPY requirements.txt .

# copy the neslter library code
COPY ./neslter ./neslter

# copy what's needed for setup.py
COPY README.md .
COPY VERSION .
COPY setup.py .

# install neslter library in the conda environment
RUN python setup.py install

# now copy the django app
COPY ./nlweb ./nlweb

EXPOSE 8000

CMD gunicorn --chdir nlweb --bind :8000 nlweb.wsgi:application --reload
