from PyInquirer import prompt
from src.get_replays import get_replay_data
import datetime, time

DOWNLOAD = 'Download Replays'
ANALYZE = 'Analyze Replays (Not Functional)'
QUIT = 'Quit'

def main():
    while True:
        answer = prompt({
            'type': 'list',
            'name': 'action',
            'message': 'What would you like to do',
            'choices': [DOWNLOAD, ANALYZE, QUIT],
            'default': 'Download Replays'
        })
        if answer['action'] == DOWNLOAD:
            answers = prompt(
                [
                    {
                        'type': 'input',
                        'name': 'start_date',
                        'message': 'What is the start date to begin downloading replays from (YYYY-MM-DD)',
                        'default': datetime.date.today().replace(day=1).strftime('%Y-%#m-%#d')
                    },
                    {
                        'type': 'input',
                        'name': 'end_date',
                        'message': 'What is the end date to finish downloading replays from (YYYY-MM-DD)',
                        'default': datetime.date.today().strftime('%Y-%#m-%#d')
                    },
                    {
                        'type': 'list',
                        'name': 'output_type',
                        'message': 'What file type would you like the results to be saved to',
                        'choices': ['SQLite Database', 'CSV'],
                        'default': 'SQLite Database'
                    }
                ]
            )
            start_date = datetime.datetime.strptime(answers['start_date'], '%Y-%m-%d').replace(tzinfo=datetime.timezone.utc)
            end_date = datetime.datetime.strptime(answers['end_date'], '%Y-%m-%d').replace(tzinfo=datetime.timezone.utc)
            
            start_time = time.perf_counter()
            downloaded_replays = get_replay_data(start_date, end_date, True if answers['output_type'] == 'SQLite Database' else False)
            print(f'[Download] | Finished gathering {downloaded_replays:,} replays in a total of {round(time.perf_counter() - start_time, 2):,} seconds')
        elif answer['action'] == ANALYZE:
            print('Analyzing replays is not currently implemented yet!')
        elif answer['action'] == QUIT:
            break

if __name__ == '__main__':
    main()