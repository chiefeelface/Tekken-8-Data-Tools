# Tekken 8 Replay Analyzer

A comprehensive Python application for downloading, storing, and analyzing Tekken 8 replay data with a modern GUI interface.

## Features

### 🎮 **Core Functionality**
- **Download Replays**: Download Tekken 8 replay data from wank.wavu.wiki API
- **Data Storage**: Store data in SQLite databases with proper schema and relationships
- **Analysis**: Calculate character win rates, statistics, and generate charts
- **Modern GUI**: User-friendly interface with date pickers, progress bars, and real-time logging

### 📊 **Analysis Features**
- Character win rate calculations
- Wilson score intervals for statistical confidence
- Bayesian adjusted win rates
- Comprehensive charts and visualizations
- Export capabilities

### 🖥️ **User Interface**
- **Date Pickers**: Visual calendar selection for date ranges
- **Progress Tracking**: Real-time progress bars with ETA calculations
- **Live Logging**: Real-time status updates and error reporting
- **Responsive Design**: Clean, modern interface that works on different screen sizes

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Quick Setup
```bash
# Clone or download the project
cd tekken-replay-analyzer

# Install dependencies
pip install -r requirements.txt

# Run the GUI application
python main.py
```

### Manual Dependency Installation
```bash
# Core dependencies
pip install tkcalendar>=1.6.1
pip install pandas>=1.3.0
pip install numpy>=1.21.0
pip install tqdm>=4.62.0
pip install requests>=2.25.0
pip install scipy>=1.7.0
pip install matplotlib>=3.4.0
```

## Usage

### GUI Application (Recommended)
```bash
python main.py
```

The GUI provides:
- **Date Selection**: Choose start and end dates for downloads
- **Storage Options**: Select between SQLite database or CSV files
- **Download Control**: Start/stop downloads with progress tracking
- **Real-time Logs**: Monitor download progress and errors

### Command Line Interface
```bash
# Download replay data
python cli.py download --start-date 2025-09-01 --end-date 2025-09-02

# Analyze existing data
python cli.py analyze --file replay_data.csv --chart
```

### Programmatic Usage
```python
from src.core.downloader import ReplayDownloader
from src.core.analyzer import ReplayAnalyzer
from src.config.settings import AppConfig

# Download data
config = AppConfig()
downloader = ReplayDownloader()
replays = downloader.download_replay_data(
    start_date=datetime.datetime(2025, 9, 1),
    end_date=datetime.datetime(2025, 9, 2)
)

# Analyze data
analyzer = ReplayAnalyzer()
stats = analyzer.calculate_character_statistics(replay_data)
analyzer.create_win_rate_chart(stats, "win_rates.png")
```

## Project Structure

```
tekken-replay-analyzer/
├── src/                    # Source code
│   ├── core/              # Core functionality
│   │   ├── api_client.py  # API interaction
│   │   ├── database.py    # Database management
│   │   ├── downloader.py  # Download orchestration
│   │   └── analyzer.py    # Data analysis
│   ├── gui/               # GUI components
│   │   ├── main_window.py # Main application window
│   │   └── components.py  # Reusable GUI components
│   ├── models/            # Data models
│   │   ├── replay_data.py # Data structures
│   │   └── enums.py       # Game enums
│   ├── config/            # Configuration
│   │   └── settings.py    # Application settings
│   └── utils/             # Utilities
│       ├── logging_config.py
│       ├── file_utils.py
│       └── time_utils.py
├── tests/                 # Test suite
├── downloaded_replays/    # Data storage directory
├── main.py               # GUI entry point
├── cli.py                # Command-line interface
├── requirements.txt      # Dependencies
└── README.md            # This file
```

## Configuration

The application uses a configuration system that can be customized:

```python
from src.config.settings import AppConfig

config = AppConfig(
    start_date=datetime.datetime(2025, 9, 1),
    end_date=datetime.datetime(2025, 9, 2),
    max_replay_threshold=1_000_000,
    use_sqlite=True,
    data_directory="downloaded_replays"
)
```

## Data Models

### ReplayData
Raw replay data structure from the API containing all match information.

### SimplifiedReplayData
Processed data structure optimized for analysis with character names and rank information.

## API Reference

### Core Classes

#### ReplayDownloader
Main class for downloading replay data.

```python
downloader = ReplayDownloader(api_config, download_config)
replays = downloader.download_replay_data(start_date, end_date)
```

#### ReplayAnalyzer
Main class for analyzing replay data.

```python
analyzer = ReplayAnalyzer()
stats = analyzer.calculate_character_statistics(replay_data)
analyzer.create_win_rate_chart(stats, "output.png")
```

#### DatabaseManager
Manages database operations.

```python
db_manager = DatabaseManager("data_directory")
db_manager.create_tables(start_date, end_date)
db_manager.save_replay_data(replay_data, start_date, end_date)
```

## Testing

Run the test suite:

```bash
python -m pytest tests/
```

Or run individual tests:

```bash
python tests/test_analyzer.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on the project repository.

## Changelog

### Version 2.0.0
- Complete project restructure
- Modern GUI with date pickers
- Comprehensive error handling
- Configuration system
- Command-line interface
- Unit tests
- Documentation

### Version 1.0.0
- Basic download functionality
- Simple GUI interface
- CSV/JSON data storage
