import os
import requests
import pandas as pd

BASE_URL = 'https://nes-lter-data.whoi.edu/api/'

NUT_DIR = './nut_data'

def fetch_endpoint(endpoint):
    url = f'{BASE_URL}{endpoint}'
    print('Fetching:', url)
    response = requests.get(url)
    return response


def main():
    response = fetch_endpoint('cruises')
    cruises = response.json()['cruises']
    for cruise in cruises:
        ep = f'nut/{cruise}.csv'
        response = fetch_endpoint(ep)
        if response.status_code == 200:
            with open(os.path.join(NUT_DIR, f'{cruise}.csv'), 'w') as f:
                f.write(response.text)

def cleanup():
    for file in os.listdir(NUT_DIR):
        path = os.path.join(NUT_DIR, file)
        with open(path, 'r') as f:
            lines = f.readlines()
            if len(lines) > 1 and lines[1].startswith('<!doctype html>'):
                print('Removing:', path)
                os.remove(path)


def concatenate():
    dfs = []
    with open('nut_data.csv', 'w') as out:
        for file in os.listdir(NUT_DIR):
            path = os.path.join(NUT_DIR, file)
            df = pd.read_csv(path)
            dfs.append(df)
        df = pd.concat(dfs)
        df = df.sort_values('date')
        df.to_csv(out, index=False)


if __name__ == '__main__':
    concatenate()
