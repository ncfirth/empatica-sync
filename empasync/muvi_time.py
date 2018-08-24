from typing import List
from datetime import timedelta


#TODO: array checks, handle cases where sync event 

class MuviTimes(object):
	"""docstring for MuviTimes"""
	def __init__(self,
				 sync_timestamp: int,
				 sync_muvi_time: str,
				 muvi_lengths: List[str],
				 event_muvi_times: List[str],
				 event_muvi_file_n: List[int],
				 sync_muvi_file: int = 1,
				 event_names: List[str] = []):
		super(MuviTimes, self).__init__()
		self.sync_timestamp = sync_timestamp
		self.sync_muvi_time = str_to_datetime(sync_muvi_time)
		self.muvi_lengths = [str_to_datetime(x) for x in muvi_lengths]
		self.n_muvi = len(muvi_lengths)
		self.event_muvi_file_n = [x-1 for x in event_muvi_file_n]
		self.event_muvi_times = [str_to_datetime(x) for x in event_muvi_times]
		if not event_names:
			event_names = [f'event_{x}' for x in range(len(event_muvi_times))]
		self.event_names = event_names
		self.sync_muvi_file = sync_muvi_file - 1

	def check_events(self):
		for idx in self.event_muvi:
			if idx > self.n_muvi:
				raise ValueError((f'Muvi event {idx} out of'
								  f' max index {self.n_muvi}'))

	def get_event_unixtime(self, event_name):
		if isinstance(event_name, str):
			event_idx = self.event_names.index(event_name)
		elif isinstance(event_name, int):
			event_idx = event_names

		muvi_lengths  = self.muvi_lengths
		event_muvi_file_n = self.event_muvi_file_n
		previous_muvi_t = sum(muvi_lengths[:event_muvi_file_n[event_idx]],
			  				  timedelta())
		event_time = self.event_muvi_times[event_idx]
		sync_time = self.sync_muvi_time
		time_diff = previous_muvi_t + event_time - sync_time
		time_diff = time_diff.total_seconds()
		print(self.sync_timestamp + time_diff)


def str_to_datetime(time_str: str):
	time_splits = [int(x) for x in time_str.split(':')]
	time_datetime = timedelta(hours=time_splits[0],
							  minutes=time_splits[1],
							  seconds=time_splits[2])
	return time_datetime


def main():
	mt = MuviTimes(
		sync_timestamp=1529571778, sync_muvi_time='00:00:24',
		muvi_lengths=['00:50:27', '00:45:32', '01:25:27'],
		event_muvi_times=['00:41:45', '00:48:14'],
		event_muvi_file_n=[2, 3],
		event_names=['Choir session started', 'Choir session ended']
				)

	mt.get_event_unixtime('Choir session started')

if __name__ == '__main__':
	main()



		