import src.config as config, questionary as q, datetime, os
from src.get_replays import get_replay_data
from src.analyze_replays import analyze_replay_data
from src.utils.file_utils import write_results_to_excel

def ask_with_interrupt_check(q: q.Question):
    answer = q.ask()
    if answer != None:
        return answer
    raise KeyboardInterrupt

def has_replays():
    return os.path.exists(config.REPLAY_DIR) and os.listdir(config.REPLAY_DIR)

def prompt():
    choices = [
        config.DOWNLOAD,
        q.Choice(config.ANALYZE, disabled='No Replays Downloaded' if not has_replays() else None),
        config.HELP,
        config.QUIT
    ]

    match q.select(message='What would you like to do', choices=choices).ask():
        case config.DOWNLOAD:
            start_date = ask_with_interrupt_check(q.text(
                message='What is the start date to begin downloading replays from (YYYY-MM-DD)',
                default=datetime.date.today().replace(day=1).strftime('%Y-%#m-%#d')
            ))
            end_date = ask_with_interrupt_check(q.text(
                message='What is the end date to finish downloading replays from (YYYY-MM-DD)',
                default=datetime.date.today().strftime('%Y-%#m-%#d')
            ))
            file_type = ask_with_interrupt_check(q.select(
                message='What file type would you like the results to be saved to',
                choices=[
                    config.CSV,
                    config.SQLITE
                ]
            ))
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            
            get_replay_data(start_date, end_date, file_type == config.SQLITE)
        case config.ANALYZE:
            # Redundant but just in case
            if not has_replays():
                print('No replay files found.')
                return True
            replay_data_file_path = ask_with_interrupt_check(q.select(
                message='What file would you like to analyze',
                choices=[ 
                    file for file in os.listdir(config.REPLAY_DIR)
                ] + [config.BACK]
            ))
            if replay_data_file_path == config.BACK:
                return True
            stats, player_stats, rank_percentiles_and_distribution = analyze_replay_data(config.REPLAY_DIR + '/' + replay_data_file_path)
            if ask_with_interrupt_check(q.confirm('Would you like to save the results to an excel file')):
                write_results_to_excel(replay_data_file_path, [
                        (stats, 'Character Stats',),
                        (player_stats, 'Player Stats',),
                        (rank_percentiles_and_distribution, 'Rank Percentiles & Distribution',)
                ])
        case config.QUIT | None:
            return False
        case config.HELP:
            print('🐊 coming soon')
        case _:
            print('Unknown option selection, exiting.')
            return False
    return True