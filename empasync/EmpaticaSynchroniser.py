import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
import os
from zipfile import ZipFile


class EmpaticaSynchroniser(object):
    """docstring for EmpaticaSyncroniser"""
    def __init__(self, empatica_sessions):
        super(EmpaticaSynchroniser, self).__init__()
        self.empatica_sessions = empatica_sessions

    def unzip_downloads(self, save_loc=''):
        df = self.empatica_sessions
        if save_loc:
            save_loc = save_loc + '/'
        for dev_id, session_id in zip(df.device_id, df.id):
            if not os.path.exists(f'{save_loc}{dev_id}_{session_id}.zip'):
                raise ValueError((f'{dev_id}_{session_id}.zip '
                                  f'does not exist'))
            if os.path.exists(f'{save_loc}{dev_id}_{session_id}'):
                continue
            os.mkdir(f'{save_loc}{dev_id}_{session_id}')
            zf = ZipFile(f'{save_loc}{dev_id}_{session_id}.zip')
            zf.extractall(f'{save_loc}{dev_id}_{session_id}')
            zf.close()

    def create_session_df(self, event_time, window=5, save_loc=''):
        df = self.empatica_sessions
        self.event_time = event_time
        session_list = []
        if save_loc:
            save_loc = save_loc + '/'
        for dev_id, session_id in zip(df.device_id, df.id):
            fname = f'{save_loc}{dev_id}_{session_id}/ACC.csv'
            session_df = self.read_empatica(fname)
            session_df = self.get_time_of_interest(session_df, fname,
                                                   event_time, window)
            session_list.append(session_df)
        session_list = session_list[0].join(session_list[1:],
                                            how='outer')
        self.session_df = session_list
        return session_list

    @staticmethod
    def read_empatica(fname):
        f = open(fname)
        start_times = [float(x) for x in f.readline().split(',')]
        freqs = [float(x) for x in f.readline().split(',')]
        df = pd.read_csv(f, header=None)
        df.index = start_times[0] + np.arange(df.shape[0]) / freqs[0]
        return df

    @staticmethod
    def get_time_of_interest(df, fname, event_time, window=5):
        df = df.copy()
        df = df[(df.index > event_time - window) &
                (df.index < event_time + window)]
        df.loc[:, fname] = df.abs().sum(axis=1)
        df = df.drop([0, 1, 2], axis=1)
        return df

    @staticmethod
    def calculate_shift(template, query, max_shift=75):
        distances = np.zeros(max_shift*2)
        for i in range(max_shift):
            neg_shift_temp = template[:template.shape[0]-i]
            neg_shift_quer = query[i:]
            pos_shift_temp = template[i:]
            pos_shift_quer = query[:query.shape[0]-i]
            distances[max_shift - i - 1] = np.mean(np.abs(neg_shift_temp - neg_shift_quer))
            distances[max_shift + i] = np.mean(np.abs(pos_shift_temp - pos_shift_quer))
        return distances

    def get_time_shifts(self, max_shift=75):
        session_df = self.session_df
        fig, ax = plt.subplots()
        for i in range(session_df.shape[1]):
            ax.plot(session_df.iloc[:, i], alpha=0.5)
        raw_values = session_df.values.copy()
        raw_values = np.abs(np.diff(raw_values, axis=0))
        distances = raw_values - np.median(raw_values, axis=1).reshape(-1, 1)
        template = np.argmin(np.sqrt(np.square(distances).sum(axis=0)))
        shifts = np.zeros(session_df.shape[1], dtype=int)
        for i in range(session_df.shape[1]):
            distances = self.calculate_shift(raw_values[:, template],
                                             raw_values[:, i], max_shift)

            shift = distances.argmin() - max_shift
            shifts[i] = shift
        self.shifts = shifts
        return shifts

    def synchronise(self):
        shifts = self.shifts
        session_df = self.session_df
        min_shift, max_shift = shifts.min(), shifts.max()
        if min_shift > 0:
            min_shift = 0
        if max_shift < 0:
            max_shift = 0
        X = np.zeros((shifts.shape[0],
                      session_df.values.shape[0] + np.abs(min_shift) + max_shift))
        X[:, :] = np.nan
        for i, shift in enumerate(shifts):
            offset = shift-min_shift
            X[i, offset:session_df.shape[0]+offset] = np.abs(session_df.values[:, i])
        fig, ax = plt.subplots()
        for i in range(X.shape[0]):
            ax.plot(X[i, :], alpha=0.5)
        X_diff = np.nanmean(np.abs(np.diff(X, axis=1)), axis=0)
        mean, std = X_diff.mean(), X_diff.std()
        X_diff_filter = X_diff.copy()
        X_diff_filter[X_diff_filter < mean + 2.5*std] = np.nan
        sync_index = np.where(~np.isnan(X_diff_filter))[0]
        sync_index = np.split(sync_index,
                              np.where(np.diff(sync_index) != 1)[0] + 1)
        for sync in sync_index:
            ax.axvspan(sync.min(), sync.max(), color='r')
        fig, ax = plt.subplots()
        sync_point = np.median(sync_index[0]).astype(int)
        for i in range(X.shape[0]):
            ax.plot(session_df.values[sync_point-shifts[i]:, i], alpha=0.5)
        plt.show()

        self.align_times = self.session_df.index[sync_point - shifts].values
        return sync_index

    def write_combined_files(self, save_loc='', suffix='_synced'):
        df = self.empatica_sessions

        if save_loc:
            save_loc = save_loc + '/'
        for modality in ['HR', 'EDA', 'TEMP']:
            session_list = []
            for i, (dev_id, session_id) in enumerate(zip(df.device_id, df.id)):
                session_df = self.read_empatica((f'{save_loc}{dev_id}'
                                                 f'_{session_id}/{modality}.csv'))
                session_df.rename(mapper={0: f'{dev_id}_{session_id}'},
                                  inplace=True, axis=1)
                session_df = session_df[session_df.index >= self.align_times[i]]
                session_df.index = session_df.index - session_df.index[0] + self.event_time
                session_list.append(session_df)
            session_list = session_list[0].join(session_list[1:],
                                                how='outer')
            session_list.to_csv(f'{save_loc}{modality}{suffix}.csv')
        session_list = []
        for i, (dev_id, session_id) in enumerate(zip(df.device_id, df.id)):
            session_df = self.read_empatica((f'{save_loc}{dev_id}'
                                             f'_{session_id}/ACC.csv'))
            session_df.loc[:, f'{dev_id}_{session_id}'] = session_df.abs().sum(axis=1)
            session_df = session_df.drop([0, 1, 2], axis=1)
            session_df = session_df[session_df.index >= self.align_times[i]]
            session_df.index = session_df.index - session_df.index[0] + self.event_time
            session_list.append(session_df)
        session_list = session_list[0].join(session_list[1:],
                                            how='outer')
        session_list.to_csv(f'{save_loc}ACC{suffix}.csv')

