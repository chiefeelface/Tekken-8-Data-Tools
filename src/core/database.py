"""
Database management for storing and retrieving Tekken replay data.
"""

import sqlite3
import pandas as pd
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.replay_data import ReplayData
from models.enums import Characters, Ranks, BattleTypes, Regions, Stages

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database operations for replay data."""
    
    def __init__(self, data_dir: str = "downloaded_replays"):
        """Initialize the database manager.
        
        Args:
            data_dir: Directory to store database files.
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    def get_database_path(self, start_date: datetime.datetime, end_date: datetime.datetime) -> Path:
        """Get the database file path for a date range.
        
        Args:
            start_date: Start date for the data.
            end_date: End date for the data.
            
        Returns:
            Path to the database file.
        """
        filename = f"replay_data_{start_date.date()}_{end_date.date()}.db"
        return self.data_dir / filename
    
    def create_tables(self, start_date: datetime.datetime, end_date: datetime.datetime) -> None:
        """Create database tables with proper schema.
        
        Args:
            start_date: Start date for the data.
            end_date: End date for the data.
        """
        db_path = self.get_database_path(start_date, end_date)
        
        # Ensure file exists
        db_path.touch()
        
        logger.info(f"Creating database tables in {db_path}")
        
        try:
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                
                # Enable foreign keys
                cursor.execute('PRAGMA foreign_keys = ON;')
                
                # Create main replay data table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS ReplayData (
                    battle_at INTEGER NOT NULL,
                    battle_id TEXT PRIMARY KEY,
                    battle_type INTEGER NOT NULL,
                    game_version INTEGER NOT NULL,
                    
                    p1_area_id INTEGER,
                    p1_chara_id INTEGER NOT NULL,
                    p1_lang TEXT,
                    p1_name TEXT NOT NULL,
                    p1_polaris_id TEXT NOT NULL,
                    p1_power INTEGER NOT NULL,
                    p1_rank INTEGER NOT NULL,
                    p1_rating_before INTEGER,
                    p1_rating_change INTEGER,
                    p1_region_id INTEGER,
                    p1_rounds INTEGER NOT NULL,
                    p1_user_id INTEGER NOT NULL,
                    
                    p2_area_id INTEGER,
                    p2_chara_id INTEGER NOT NULL,
                    p2_lang TEXT,
                    p2_name TEXT NOT NULL,
                    p2_polaris_id TEXT NOT NULL,
                    p2_power INTEGER NOT NULL,
                    p2_rank INTEGER NOT NULL,
                    p2_rating_before INTEGER,
                    p2_rating_change INTEGER,
                    p2_region_id INTEGER,
                    p2_rounds INTEGER NOT NULL,
                    p2_user_id INTEGER NOT NULL,
                    
                    stage_id INTEGER NOT NULL,
                    winner INTEGER NOT NULL,
                    
                    FOREIGN KEY (battle_type) REFERENCES BattleTypes(Id),
                    FOREIGN KEY (p1_chara_id) REFERENCES Characters(Id),
                    FOREIGN KEY (p2_chara_id) REFERENCES Characters(Id),
                    FOREIGN KEY (p1_region_id) REFERENCES Regions(Id),
                    FOREIGN KEY (p2_region_id) REFERENCES Regions(Id),
                    FOREIGN KEY (p1_rank) REFERENCES Ranks(Id),
                    FOREIGN KEY (p2_rank) REFERENCES Ranks(Id),
                    FOREIGN KEY (stage_id) REFERENCES Stages(Id)
                );
                ''')
                
                # Create lookup tables
                lookup_tables = ['BattleTypes', 'Characters', 'Regions', 'Ranks', 'Stages']
                for table in lookup_tables:
                    cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {table} (
                        Id INTEGER PRIMARY KEY,
                        Name TEXT NOT NULL
                    );
                    ''')
                
                connection.commit()
                logger.info("Database tables created successfully")
                
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def populate_lookup_tables(self, start_date: datetime.datetime, end_date: datetime.datetime) -> None:
        """Populate lookup tables with enum data.
        
        Args:
            start_date: Start date for the data.
            end_date: End date for the data.
        """
        db_path = self.get_database_path(start_date, end_date)
        
        logger.info("Populating lookup tables")
        
        try:
            with sqlite3.connect(db_path) as connection:
                # Define enum tables and their corresponding enum classes
                enum_tables = [
                    (Characters, 'Characters'),
                    (Ranks, 'Ranks'),
                    (BattleTypes, 'BattleTypes'),
                    (Regions, 'Regions'),
                    (Stages, 'Stages')
                ]
                
                for enum_class, table_name in enum_tables:
                    # Convert enum to DataFrame
                    enum_data = [
                        {'Id': member.value, 'Name': member.name} 
                        for member in enum_class
                    ]
                    df = pd.DataFrame(enum_data)
                    
                    # Insert data
                    df.to_sql(table_name, connection, if_exists='append', index=False)
                
                connection.commit()
                logger.info("Lookup tables populated successfully")
                
        except Exception as e:
            logger.error(f"Failed to populate lookup tables: {e}")
            raise
    
    def save_replay_data(
        self, 
        replay_data: List[ReplayData], 
        start_date: datetime.datetime, 
        end_date: datetime.datetime,
        use_sqlite: bool = True
    ) -> None:
        """Save replay data to database or CSV file.
        
        Args:
            replay_data: List of replay data to save.
            start_date: Start date for the data.
            end_date: End date for the data.
            use_sqlite: Whether to save to SQLite database or CSV file.
        """
        if not replay_data:
            return
        
        logger.info(f"Saving {len(replay_data)} replays to {'database' if use_sqlite else 'CSV'}")
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(replay_data)
            
            if use_sqlite:
                db_path = self.get_database_path(start_date, end_date)
                with sqlite3.connect(db_path) as connection:
                    df.to_sql('ReplayData', connection, if_exists='append', index=False)
                    connection.commit()
            else:
                csv_path = self.get_csv_path(start_date, end_date)
                # Check if file exists to determine header
                header = not csv_path.exists()
                df.to_csv(csv_path, mode='a', header=header, index=False)
            
            logger.info(f"Successfully saved {len(replay_data)} replays to {'database' if use_sqlite else 'CSV'}")
            
        except Exception as e:
            logger.error(f"Failed to save replay data: {e}")
            raise
    
    def get_csv_path(self, start_date: datetime.datetime, end_date: datetime.datetime) -> Path:
        """Get the CSV file path for a date range.
        
        Args:
            start_date: Start date for the data.
            end_date: End date for the data.
            
        Returns:
            Path to the CSV file.
        """
        filename = f"replay_data_{start_date.date()}_{end_date.date()}.csv"
        return self.data_dir / filename
    
    def get_replay_data(
        self, 
        start_date: datetime.datetime, 
        end_date: datetime.datetime,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Retrieve replay data from the database.
        
        Args:
            start_date: Start date for the data.
            end_date: End date for the data.
            limit: Maximum number of records to return.
            
        Returns:
            DataFrame containing replay data.
        """
        db_path = self.get_database_path(start_date, end_date)
        
        if not db_path.exists():
            logger.warning(f"Database file not found: {db_path}")
            return pd.DataFrame()
        
        try:
            query = "SELECT * FROM ReplayData"
            if limit:
                query += f" LIMIT {limit}"
            
            with sqlite3.connect(db_path) as connection:
                df = pd.read_sql_query(query, connection)
            
            logger.info(f"Retrieved {len(df)} replay records from database")
            return df
            
        except Exception as e:
            logger.error(f"Failed to retrieve replay data: {e}")
            raise
