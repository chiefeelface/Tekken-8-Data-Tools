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

2. Create a virtual environment

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
Simply run the main file

```
python main.py
```