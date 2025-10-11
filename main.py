from src.get_replays import get_replay_data
from src.analyze_replays import analyze_replay_data
import datetime, time, src.config as config, questionary as q, os

def main():
    while True:
        action = q.select(
            message='What would you like to do',
            choices=[
                config.DOWNLOAD,
                config.ANALYZE,
                config.QUIT
            ]
        ).ask()
        if action == config.DOWNLOAD:
            start_date = q.text(
                message='What is the start date to begin downloading replays from (YYYY-MM-DD)',
                default=datetime.date.today().replace(day=1).strftime('%Y-%#m-%#d')
            ).ask()
            end_date = q.text(
                message='What is the end date to finish downloading replays from (YYYY-MM-DD)',
                default=datetime.date.today().strftime('%Y-%#m-%#d')
            ).ask()
            file_type = q.select(
                message='What file type would you like the results to be saved to',
                choices=[
                    config.CSV,
                    config.SQLITE
                ]
            ).ask()
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=datetime.timezone.utc)
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=datetime.timezone.utc)
            
            get_replay_data(start_date, end_date, file_type == config.SQLITE)
        elif action == config.ANALYZE:
            replay_data_file_path = q.select(
                message='What file would you like to analyze',
                choices=[
                    file for file in os.listdir(config.REPLAY_DIR)
                ]
            ).ask()
            analyze_replay_data(config.REPLAY_DIR + '/' + replay_data_file_path)
        elif action == config.QUIT:
            break

if __name__ == '__main__':
    main()