from PyInquirer import prompt
from src.get_replays import get_replay_data
import datetime, time

def main():
    answer = prompt({
        'type': 'list',
        'name': 'action',
        'message': 'What would you like to do',
        'choices': ['Download Replays', 'Analyze Replays (Not Functional)'],
        'default': 'Download Replays'
    })
    if answer['action'] == 'Download Replays':
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
            ]
        )
        start_date = datetime.datetime.strptime(answers['start_date'], '%Y-%m-%d')
        end_date = datetime.datetime.strptime(answers['end_date'], '%Y-%m-%d')
        
        start_time = time.perf_counter()
        downloaded_replays = get_replay_data(start_date, end_date)
        print(f'[Download] | Finished gathering {downloaded_replays:,} replays in a total of {round(time.perf_counter() - start_time, 2):,} seconds')
    else:
        raise(NotImplementedError('Analyzing replays is not currently implemented yet'))

if __name__ == '__main__':
    main()