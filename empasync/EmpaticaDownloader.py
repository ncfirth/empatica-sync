import requests
import re
from datetime import datetime, timedelta
import pandas as pd
import os


class EmpaticaDownloader(object):
    """docstring for EmpaticaDownloader"""
    def __init__(self, username, password):
        super(EmpaticaDownloader, self).__init__()
        self.username = username
        self.password = password
        self.base_url = 'https://www.empatica.com/connect'
        session, user_id = self.create_session_(username, password)
        self.session = session
        self.user_id = user_id

    def create_session_(self, username, password):
        data = dict(username=username, password=password)
        session = requests.session()

        session.post(f'{self.base_url}/authenticate.php',
                     data=data)
        res = session.get(f'{self.base_url}/sessions.php')
        user_id = re.findall('userId = \d+',
                             res.text)[0].replace('userId = ', '')
        return session, user_id

    def get_empatica_sessions(self, date):
        session = self.session
        date = datetime.strptime(date, '%d/%m/%y')
        start_date = date.timestamp()
        end_date = date + timedelta(days=1)
        end_date = end_date.timestamp()
        sessions_url = (f'{self.base_url}/connect.php'
                        f'/users/{self.user_id}/sessions?from='
                        f'{start_date:.0f}&to={end_date-1:.0f}')
        res = session.get(sessions_url)
        df = pd.read_json(res.text)
        self.empatica_sessions = df
        return df

    def download_sessions(self, save_loc):
        session = self.session
        df = self.empatica_sessions
        for dev_id, session_id in zip(df.device_id, df.id):
            save_name = f'{save_loc}/{dev_id}_{session_id}.zip'
            if os.path.exists(save_name):
                continue
            download_url = f'{self.base_url}/download.php?id={session_id}'
            res = session.get(download_url, stream=True)
            with open(f'{save_name}', 'wb') as f:
                    for chunk in res.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
