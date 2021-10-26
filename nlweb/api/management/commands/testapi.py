import requests

from django.core.management.base import BaseCommand, CommandError


class HttpError(Exception):
    def __init__(self, code, url, message='HTTP error returned'):
        self.code = code
        self.url = url
        self.message = message
        super().__init__(self, message)


class Command(BaseCommand):
    help = 'test all API endpoints'

    def add_arguments(self, parser):
        parser.add_argument('url', type=str, help='base URL e.g., https://host')
        parser.add_argument('-c', '--cruise', type=str, help='cruise (optional)')

    def handle(self, *args, **options):
        self.base_url = f"{options['url']}/api"
        cruise = options.get('cruise')

        cruises = self.get_cruises()

        if cruise is not None:
            self.test_cruise(cruise.lower())
        else:
            for cruise in cruises:
                self.test_cruise(cruise)

    def endpoint(self, suffix):
        return f'{self.base_url}/{suffix}'

    def hit_endpoint(self, suffix):
        url = self.endpoint(suffix)
        r = requests.get(url)
        print(f'{r.status_code} {url}')
        return r

    def fetch_endpoint(self, suffix):
        url = self.endpoint(suffix)
        r = requests.get(url)
        print(f'{r.status_code} {url}')
        if r.ok:
            return r
        raise HttpError(r.status_code, url)

    def get_cruises(self):
        try:
            json = self.fetch_endpoint('cruises').json()
            return json['cruises']
        except HttpError:
            return []

    def get_casts(self, cruise):
        try:
            json = self.fetch_endpoint(f'ctd/{cruise}/casts').json()
            return json['casts']
        except HttpError:
            return []

    def test_ctd(self, cruise):
        self.hit_endpoint(f'ctd/{cruise}/metadata.csv')
        self.hit_endpoint(f'ctd/{cruise}/bottles.csv')
        self.hit_endpoint(f'ctd/{cruise}/bottle_summary.csv')
        self.hit_endpoint(f'ctd/{cruise}/metadata.csv')

        casts = self.get_casts(cruise)

        for cast in casts:
            try:
                self.fetch_endpoint(f'ctd/{cruise}/cast_{cast}.csv')
            except HttpError:
                pass

    def test_cruise(self, cruise):
        for datatype in ['underway', 'events', 'stations', 'nut', 'chl', 'hplc']:
            self.hit_endpoint(f'{datatype}/{cruise}.csv')
        self.test_ctd(cruise)
