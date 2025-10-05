# Tekken 8 Data Tools
Basic data gathering and analysis(soon™) tool for Tekken 8 replays.

## Getting Started

### Prerequisites
1. [Python 3.9](https://www.python.org/downloads/release/python-3913/)
    - If you have other versions of Python and dont want to manually handle different versions and paths, I strongly recommend [pyenv-win](https://github.com/pyenv-win/pyenv-win)

### Installation

1. Clone the repo

```
git clone https://github.com/chiefeelface/Tekken-8-Data-Tools.git
```

2. Create and activate a virtual environment

```
python -m venv .venv
.\.venv\Scripts\activate
```

3. Install requirements

```
pip install -r requirements.txt
```

4. Run small test suite to ensure functionality

```
python -m unittest test
```

## Running
Simply run the main file and follow the prompts

```
python main.py
```

If your terminal does not have a (.venv) in front of the prompt, you will need to activate the virtual environment before running the file

```
.\.venv\Scripts\activate
```

If downloading replays, it will download 700 seconds worth of replays every 1 second as per the Wavu Wank wiki [api](https://wank.wavu.wiki/api), so downloading a month of replays will take about an hour.

The replays will be saved intermittently once the total replays downloaded reaches 1,000,000 to the `downloaded_replays` folder, with numerous fail-safes to prevent any downloaded replays from being lost in the event of network failure or any other errors.

If you choose to use a SQLite database file and know how to write SQL, there are lookup tables you can join on to get the names of characters, stages, etc. to make the data readable.