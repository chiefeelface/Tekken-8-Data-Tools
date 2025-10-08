# Tekken 8 Data Tools
Basic data gathering and analysis(soon™) tool for Tekken 8 replays.

---

## Getting Started

### Requirements
1. Any modern version of Python
    - Exact minimum version TBD - Python 3.14 will ***NOT*** work

2. CPU that supports AVX
    - Most CPUs released after 2011 will support AVX

### Installation

1. **Clone the repo**

```
git clone https://github.com/chiefeelface/Tekken-8-Data-Tools.git
cd Tekken-8-Data-Tools
```

2. **Create and activate a virtual environment**

```
python -m venv .venv
.\.venv\Scripts\activate
```

3. **Install dependencies**

```
pip install -r requirements.txt
```

4. **Run small test suite to ensure functionality**

```
python -m unittest test
```

## Usage
Simply run the main file and follow the prompts

```
python main.py
```

If your terminal does not have a (.venv) in front of the prompt, you will need to activate the virtual environment before running the file

```
.\.venv\Scripts\activate
```

If downloading replays, it will download 700 seconds worth of replays every 1 second as per the Wavu Wank wiki [api](https://wank.wavu.wiki/api), so downloading a month of replays will take about an hour.

Saving replays to an SQLite database is only recommended if you are going to write your own queries, as the analysis is much slower (10-15x) then when using a CSV file. If you choose to save the replays to a SQLite database file there are lookup tables you can join on to get the names of characters, stages, etc. to make the data readable.

The replays will be saved intermittently once the total replays downloaded reaches 1,000,000 to the `downloaded_replays` folder, with numerous fail-safes to prevent any downloaded replays from being lost in the event of network failure or any other errors.