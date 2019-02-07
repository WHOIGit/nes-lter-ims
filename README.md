# nes-lter-ims

NES-LTER information system components.

* Parsing backend, parses raw formats and generates clean tables
* EML generation utilities
* REST API

#### Deploying REST API with `docker-compose`

* Copy `config.py.example` to `config.py` to configure neslter, then run `docker-compose build`
* For SSL, put your certs in `certs`
* Copy `nginx/nlweb.conf.example` to `nginx/nlweb.conf` and edit important fields like hostname and location of certs (the `certs` directory is mapped to `/etc/certs` in the nginx container
* `docker-compose up`
* If `config.py` or any of the code changes you will need to run `docker-compose build` again.
