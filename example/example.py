from empasync import EmpaticaDownloader
from empasync import EmpaticaSynchroniser
import joblib


def main():
    # credentials
    username = ''
    password = ''

    # date of the recordings to download
    date = '28/06/18'
    # the time of the sync event
    event_time = 1530173665
    # where to save the data downloaded
    save_loc = 'data'

    dl = EmpaticaDownloader(username, password)
    # get the information about the sessions
    df = dl.get_empatica_sessions(date)
    #*******************************************
    # download the zip file of each session
    # need to filter out any crap sessions here
    # TODO: add some filtering function
    #*******************************************
    dl.download_sessions(save_loc)

    es = EmpaticaSynchroniser(df)
    # unzip all of the data
    es.unzip_downloads(save_loc)
    # load the ACC files into one big datafram
    es.create_session_df(event_time, save_loc=save_loc)
    # work out how much we need to shift each device by
    es.get_time_shifts()
    # actually do the time shifts 
    es.synchronise()
    # write our files for each modality
    es.write_combined_files(save_loc=save_loc,
                            suffix='_session_3_synced')


if __name__ == '__main__':
    main()
