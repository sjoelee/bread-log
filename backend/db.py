from contextlib import contextmanager
from datetime import date, datetime
from exceptions import DatabaseError
from models import DoughMake, SimpleMake, StretchFoldCreate
from psycopg_pool import ConnectionPool
from psycopg import sql
from typing import List, Optional
from uuid import UUID

import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('psycopg')
logger.setLevel(logging.DEBUG)

class DatabasePool:
  _instance: Optional['DatabasePool'] = None

  def __init__(self, dbname: str, user: str, min_size: int=2, max_size: int=10):
    self.pool = ConnectionPool(
      f"dbname={dbname} user={user}",
      min_size=min_size,
      max_size=max_size
    )
    self.pool.open()

  @classmethod
  def get_instance(cls, dbname: str, user: str) -> 'DatabasePool':
    if cls._instance is None:
      cls._instance = DatabasePool(dbname, user)
    return cls._instance

  @contextmanager
  def get_connection(self):
    conn = self.pool.getconn()
    logger.debug(f"Got connection from pool: {conn}")
    try:
        yield conn
    except Exception as e:
        logger.error(f"Error during database operation: {str(e)}")
        raise
    finally:
        logger.debug(f"Returning connection to pool: {conn}")
        self.pool.putconn(conn)

  def close(self):
    self.pool.close()

class DBConnector:
  USER = 'sammylee'
  def __init__(self, dbname):
    self.user = DBConnector.USER
    self.dbname = dbname
    self.db_pool = DatabasePool.get_instance(self.dbname, self.user)


  def insert_dough_make(self, dough_make: DoughMake) -> None:
    table = 'dough_makes'
    
    # Convert stretch_folds to JSON
    stretch_folds_json = None
    if dough_make.stretch_folds:
      stretch_folds_data = [
        {
          "fold_number": sf.fold_number,
          "timestamp": sf.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
        for sf in dough_make.stretch_folds
      ]
      stretch_folds_json = json.dumps(stretch_folds_data)
    
    insert_data = {
      'name': dough_make.name,
      'date': dough_make.date,
      'room_temp': dough_make.room_temp,
      'water_temp': dough_make.water_temp,
      'flour_temp': dough_make.flour_temp,
      'preferment_temp': dough_make.preferment_temp,
      'dough_temp': dough_make.dough_temp,
      'temperature_unit': dough_make.temperature_unit,
      'autolyse_ts': dough_make.autolyse_ts,
      'mix_ts': dough_make.mix_ts,
      'bulk_ts': dough_make.bulk_ts,
      'preshape_ts': dough_make.preshape_ts,
      'final_shape_ts': dough_make.final_shape_ts,
      'fridge_ts': dough_make.fridge_ts,
      'stretch_folds': stretch_folds_json,
      'notes': dough_make.notes,
    }
    
    # Filter out None values
    insert_data = {k: v for k, v in insert_data.items() if v is not None}
    
    # Build query using psycopg.sql for safety
    columns = sql.SQL(', ').join([sql.Identifier(k) for k in insert_data.keys()])
    placeholders = sql.SQL(', ').join([sql.Placeholder() for _ in insert_data])
    values = list(insert_data.values())
    
    query = sql.SQL("""
      INSERT INTO {} ({})
      VALUES ({});
    """).format(sql.Identifier(table), columns, placeholders)
    logger.debug(f'SQL Command\n {query}')
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, values)
          conn.commit()
    except Exception as e:
      logger.error(f"Error inserting dough make: {str(e)}")
      raise

  def get_dough_makes(self, date: date) -> Optional[List[DoughMake]]:
    sql = """
        SELECT name, date, room_temp, water_temp,
               flour_temp, preferment_temp, dough_temp, temperature_unit, mix_ts, autolyse_ts,
               bulk_ts, preshape_ts, final_shape_ts, fridge_ts, stretch_folds, notes, created_at
        FROM dough_makes
        WHERE date = %s
        ORDER BY created_at ASC;
    """
    values = (date,)
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, values)
          res = cur.fetchall()
    except Exception as e:
      logger.error(f"Error getting entry: {str(e)}")
      raise DatabaseError(f"Database error: {str(e)}")
    
    if not res:
      return None
    
    dough_makes = []
    for row in res:
      (name, date, room_temp, water_temp, flour_temp, preferment_temp, dough_temp,
       temperature_unit, mix_ts, autolyse_ts, bulk_ts, preshape_ts, final_shape_ts, 
       fridge_ts, stretch_folds_json, notes, created_at) = row
      
      # Parse stretch_folds JSON
      stretch_folds = []
      if stretch_folds_json:
        try:
            stretch_folds_data = stretch_folds_json if isinstance(stretch_folds_json, list) else json.loads(stretch_folds_json)
            for sf_data in stretch_folds_data:
              stretch_folds.append(StretchFoldCreate(
                fold_number=sf_data["fold_number"],
                timestamp=datetime.strptime(sf_data["timestamp"], "%Y-%m-%d %H:%M:%S")
              ))
        except (json.JSONDecodeError, KeyError) as e:
          logger.warning(f"Error parsing stretch_folds JSON: {e}")
          stretch_folds = []
      
      dough_make = DoughMake(
        name=name,
        date=date,
        created_at=created_at,
        autolyse_ts=autolyse_ts,
        mix_ts=mix_ts,
        bulk_ts=bulk_ts,
        preshape_ts=preshape_ts,
        final_shape_ts=final_shape_ts,
        fridge_ts=fridge_ts,
        room_temp=room_temp,
        preferment_temp=preferment_temp,
        water_temp=water_temp,
        flour_temp=flour_temp,
        dough_temp=dough_temp,
        temperature_unit=temperature_unit or 'Fahrenheit',
        stretch_folds=stretch_folds,
        notes=notes
      )
      dough_makes.append(dough_make)
    
    return dough_makes
  
  def get_dough_make(self, date: date, name: str, created_at: datetime) -> Optional[DoughMake]:
    sql = """
        SELECT name, date, 
               room_temp, water_temp, flour_temp, preferment_temp, dough_temp,
               temperature_unit, mix_ts, autolyse_ts, bulk_ts, preshape_ts, final_shape_ts, fridge_ts,
               stretch_folds, notes, created_at
        FROM dough_makes
        WHERE date = %s AND name = %s AND created_at = %s;
    """
    values = (date, name, created_at)
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          logger.info(f"Executing SQL: {sql} with {values}")
          cur.execute(sql, values)
          res = cur.fetchone()
    except Exception as e:
      logger.error(f"Error getting entry: {str(e)}")
      raise DatabaseError(f"Database error: {str(e)}") 
  
    if not res:
      raise DatabaseError(f"Make {name} created at {created_at} on {date} doesn't exist")
    
    (name, date, 
     room_temp, water_temp, flour_temp, preferment_temp, dough_temp,
     temperature_unit, mix_ts, autolyse_ts, bulk_ts, preshape_ts, final_shape_ts, fridge_ts, 
     stretch_folds_json, notes, created_at) = res
    
    logger.info(f"Retrieved make {name} for {date}")
  
    # Parse stretch_folds JSON
    stretch_folds = []
    if stretch_folds_json:
      try:
          stretch_folds_data = stretch_folds_json if isinstance(stretch_folds_json, list) else json.loads(stretch_folds_json)
          for sf_data in stretch_folds_data:
            stretch_folds.append(StretchFoldCreate(
              fold_number=sf_data["fold_number"],
              timestamp=datetime.strptime(sf_data["timestamp"], "%Y-%m-%d %H:%M:%S")
            ))
          # stretch_folds.append(StretchFoldCreate(
            # fold_number=sf_data["fold_number"],
            # timestamp=datetime.strptime(sf_data["timestamp"], "%Y-%m-%d %H:%M:%S")
          # ))
      except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Error parsing stretch_folds JSON: {e}")
        stretch_folds = []
  
    return DoughMake(
      name=name,
      date=date,
      created_at=created_at,
      autolyse_ts=autolyse_ts,
      mix_ts=mix_ts,
      bulk_ts=bulk_ts,
      preshape_ts=preshape_ts,
      final_shape_ts=final_shape_ts,
      fridge_ts=fridge_ts,
      room_temp=room_temp,
      preferment_temp=preferment_temp,
      water_temp=water_temp,
      flour_temp=flour_temp,
      dough_temp=dough_temp,
      temperature_unit=temperature_unit,
      stretch_folds=stretch_folds,
      notes=notes
    )
  

  def update_dough_make(self, date: date, name: str, created_at: datetime, updates: dict):
    """
    Updates only the specified fields for a dough make.
    """
    # Handle stretch_folds conversion to JSON if present
    if 'stretch_folds' in updates and updates['stretch_folds'] is not None:
      stretch_folds_data = []
      for sf in updates['stretch_folds']:
        # Handle both dict (from frontend) and object formats
        if isinstance(sf, dict):
          fold_number = sf['fold_number']
          timestamp = sf['timestamp']
          # Parse ISO timestamp string to datetime, then format
          if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
          timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
          # Handle object format (existing code)
          fold_number = sf.fold_number
          timestamp_str = sf.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        stretch_folds_data.append({
          "fold_number": fold_number,
          "timestamp": timestamp_str
        })
      updates['stretch_folds'] = json.dumps(stretch_folds_data)
    
    # Construct the SET clause dynamically based on what fields are being updated
    set_assignments = [sql.SQL("{} = %s").format(sql.Identifier(key)) for key in updates.keys()]
    set_clause = sql.SQL(", ").join(set_assignments)
  
    # Build the query with only the fields being updated
    query = sql.SQL("""
        UPDATE dough_makes
        SET {}, updated_at = CURRENT_TIMESTAMP
        WHERE name = %s
        AND date = %s
        AND created_at = %s
    """).format(set_clause)
  
    # Create parameter list with update values followed by WHERE clause values
    params = list(updates.values()) + [name, date, created_at]
    logger.debug(f'SQL Command\n {query}')
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, params)
          conn.commit()
    except Exception as e:
      logger.error(f"Error updating dough make: {str(e)}")
      raise DatabaseError(f"Error updating dough make: {e}")

  def delete_dough_make(self, date: date, name: str, created_at: datetime):
    """
    Deletes a specific dough make by name, date, and created_at
    """
    query = f"""
        DELETE FROM dough_makes
        WHERE name = %s
        AND date = %s
        AND created_at = %s
    """
    params = [name, date, created_at]
    logger.debug(f'SQL Command\n {query}')
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, params)
          if cur.rowcount == 0:
            raise DatabaseError(f"No dough make found with name {name} created at {created_at} on {date}")
          conn.commit()
    except Exception as e:
      raise DatabaseError(f"{e}")

  def get_account_makes(self, account_id: UUID) -> list:
    """
    Retrieves all makes for a specific account ID
    """
    sql = """
        SELECT display_name, key
        FROM account_makes
        WHERE account_id = %s
        ORDER BY display_name;
    """

    try:
        with self.db_pool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, [account_id])
                results = cur.fetchall()

                # Convert results to list of dictionaries
                account_makes = []
                for row in results:
                    account_makes.append({
                        "display_name": row[0],
                        "key": row[1]
                    })

                return account_makes
    except Exception as e:
        logger.error(f"Error retrieving account makes: {str(e)}")
        raise DatabaseError(f"Error retrieving account makes: {e}")

  def add_account_make(self, account_id: str, account_name: str, display_name: str, key: str):
    # Execute SQL to insert new make
    sql = """
        INSERT INTO account_makes (account_id, account_name, display_name, key, created_at)
        VALUES (%s, %s, %s, %s, NOW())
        RETURNING account_id, account_name, display_name, key, created_at
    """
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (account_id, account_name, display_name, key))

          result = cur.fetchone()
          conn.commit()
    except Exception as e:
        logger.error(f"Error adding makes: {str(key)}")
        raise DatabaseError(f"Error adding make: {e}")

    if not result:
        raise DatabaseError("Failed to insert account make - no result returned")

    # Return as a SimpleMake object
    return SimpleMake(display_name=result[2], key=result[3])
