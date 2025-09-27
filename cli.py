"""
Command-line interface for the Tekken Replay Analyzer.
"""

import argparse
import sys
from pathlib import Path
import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from core.downloader import ReplayDownloader
    from core.api_client import APIConfig
    from core.analyzer import ReplayAnalyzer
    from config.settings import load_config
    from utils.logging_config import setup_logging
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


def download_command(args):
    """Handle download command."""
    # Set up logging
    setup_logging(level=20)
    
    # Load configuration
    config = load_config()
    
    # Parse dates
    start_date = datetime.datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.datetime.strptime(args.end_date, "%Y-%m-%d")
    
    # Create downloader
    api_config = APIConfig(
        max_retries=args.max_retries,
        request_delay=args.delay
    )
    
    downloader = ReplayDownloader(api_config)
    
    try:
        print(f"Downloading replays from {start_date.date()} to {end_date.date()}")
        total_replays = downloader.download_replay_data(start_date, end_date)
        print(f"Successfully downloaded {total_replays:,} replays")
        
    except KeyboardInterrupt:
        print("\nDownload interrupted by user")
    except Exception as e:
        print(f"Download failed: {e}")
        sys.exit(1)
    finally:
        downloader.close()


def analyze_command(args):
    """Handle analyze command."""
    # Set up logging
    setup_logging(level=20)
    
    # Create analyzer
    analyzer = ReplayAnalyzer()
    
    try:
        # Load data
        if args.file.endswith('.csv'):
            replay_data = analyzer.load_replay_data_from_csv(args.file)
        else:
            print("Only CSV files are supported for analysis")
            sys.exit(1)
        
        # Calculate statistics
        stats = analyzer.calculate_character_statistics(replay_data)
        
        # Display results
        print(f"\nCharacter Statistics (from {len(replay_data)} replays):")
        print("-" * 60)
        print(f"{'Character':<15} {'Wins':<8} {'Losses':<8} {'Win Rate':<10}")
        print("-" * 60)
        
        for character, data in sorted(stats.items(), key=lambda x: x[1]['wins'] + x[1]['losses'], reverse=True):
            total_games = data['wins'] + data['losses']
            if total_games > 0:
                win_rate = (data['wins'] / total_games) * 100
                print(f"{character:<15} {data['wins']:<8} {data['losses']:<8} {win_rate:<10.1f}%")
        
        # Create chart if requested
        if args.chart:
            output_path = f"character_win_rates_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            analyzer.create_win_rate_chart(stats, output_path)
            print(f"\nChart saved to: {output_path}")
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        sys.exit(1)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Tekken 8 Replay Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py download --start-date 2025-09-01 --end-date 2025-09-02
  python cli.py analyze --file replay_data.csv --chart
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download replay data')
    download_parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    download_parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    download_parser.add_argument('--max-retries', type=int, default=3, help='Maximum retry attempts')
    download_parser.add_argument('--delay', type=float, default=1.005, help='Request delay in seconds')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze replay data')
    analyze_parser.add_argument('--file', required=True, help='CSV file to analyze')
    analyze_parser.add_argument('--chart', action='store_true', help='Generate win rate chart')
    
    args = parser.parse_args()
    
    if args.command == 'download':
        download_command(args)
    elif args.command == 'analyze':
        analyze_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
