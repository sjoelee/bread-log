from contextlib import contextmanager
from datetime import date
from exceptions import DatabaseError
from models import DoughMake
from psycopg_pool import ConnectionPool
from typing import Optional

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

class DBConnector():
  USER = 'sammylee'
  def __init__(self, dbname):
    self.user = DBConnector.USER
    self.dbname = dbname
    self.db_pool = DatabasePool.get_instance(self.dbname, self.user)


  def insert_dough_make(self, dough_make: DoughMake) -> None:
    table = 'dough_makes'
    insert_data = {
      'dough_name': dough_make.name,
      'make_date': dough_make.date,
      'room_temp': dough_make.room_temp,
      'water_temp': dough_make.water_temp,
      'flour_temp': dough_make.flour_temp,
      'preferment_temp': dough_make.preferment_temp,
      'start_ts': dough_make.start,
      'pull_ts': dough_make.pull,
      'preshape_ts': dough_make.preshape,
      'final_shape_ts': dough_make.final_shape,
      'fridge_ts': dough_make.fridge,
      'autolyse_ts': dough_make.autolyse,
    }
    # maybe add first fermentation and second fermentation
    insert_data = {k: v for k, v in insert_data.items() if v is not None}
    columns = ', '.join(insert_data.keys())
    placeholders = ', '.join(['%s'] * len(insert_data))
    values = list(insert_data.values())
    sql = f"""
      INSERT INTO {table} ({columns})
      VALUES ({placeholders})
      RETURNING make_num;
    """
    logger.debug(f'SQL Command\n {sql}')
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, values)
          conn.commit()
    except Exception as e:
      logger.error(f"Error inserting dough make: {str(e)}")
      raise  # Re-raise the exception after printing it


  def get_dough_make(self, make_date: date, make_name: str, make_num: int) -> Optional[DoughMake]:
    sql = """
        SELECT dough_name, make_date, room_temp, water_temp,
               flour_temp, preferment_temp, start_ts, autolyse_ts,
               pull_ts, preshape_ts, final_shape_ts, fridge_ts
        FROM dough_makes
        WHERE make_date = %s AND dough_name = %s AND make_num = %s;
    """
    values = (make_date, make_name, make_num)
    try: 
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, values)
          res = cur.fetchone()
    except Exception as e:
      logger.error(f"Error getting entry: {str(e)}")
    
    if not res:
      raise DatabaseError(f"Dough make {make_name} #{make_num} on {make_date} doesn't exist")
    (dough_name, make_date, room_temp, water_temp, flour_temp, preferment_temp, start_ts, autolyse_ts, pull_ts, preshape_ts, final_shape_ts, fridge_ts) = res
    logger.info(f"Retrieved make {make_name} for {make_date}")

    return DoughMake(
      name=dough_name,
      date=make_date,
      autolyse_ts=autolyse_ts,
      start_ts=start_ts,
      pull_ts=pull_ts,
      preshape_ts=preshape_ts,
      final_shape_ts=final_shape_ts,
      fridge_ts=fridge_ts,
      room_temp=int(room_temp) if room_temp else None,
      preferment_temp=int(preferment_temp) if preferment_temp else None,
      water_temp=int(water_temp) if water_temp else None,
      flour_temp=int(flour_temp) if flour_temp else None
    )

  # if there are any updates needed to be made
  def update_dough_make(self, make_date: date, make_name: str, make_num: int, updates: dict):
    """
    Updates only the specified fields for a dough make.
    
    Args:
        make_name: Name of the dough make
        make_date: Date of the make
        make_num: Number of the make for that date
        updates: Dictionary of field names and their new values
    """
    # Construct the SET clause dynamically based on what fields are being updated
    set_clause = ", ".join(f"{key} = %s" for key in updates.keys())
    
    # Build the query with only the fields being updated
    query = f"""
        UPDATE dough_makes 
        SET {set_clause}, updated_at = CURRENT_TIMESTAMP
        WHERE dough_name = %s 
        AND make_date = %s 
        AND make_num = %s
    """
    
    # Create parameter list with update values followed by WHERE clause values
    params = list(updates.values()) + [make_name, make_date, make_num]
    logger.debug(f'SQL Command\n {query}')
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, params)
          conn.commit()
    except Exception as e:
      logger.error(f"Error updating dough make: {str(e)}")
      raise DatabaseError(f"Error updating dough make: {e}")
  

  def delete_dough_make(self, make_date: date, make_name: str, make_num: int):
    """
    Deletes a specific dough make by name, date, and num
    """
    query = f"""
        DELETE FROM dough_makes
        WHERE dough_name = %s
        AND make_date = %s
        AND make_num = %s
    """
    params = [make_name, make_date, make_num]
    logger.debug(f'SQL Command\n {query}')
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, params)
          if cur.rowcount == 0:
            raise DatabaseError(f"No dough make found with name {make_name} #{make_num} on {make_date}")
          conn.commit()
    except Exception as e:
      raise DatabaseError(f"{e}")


# testing
if __name__ == '__main__':
  from datetime import datetime, date

  dt = datetime(2024, 12, 1)
  dt_strfmt = "%Y-%m-%d %H:%M:%S"
  dbname = 'bread_makes'
  db_conn = DBConnector(dbname=dbname)
  # autolyse_ts = datetime.strptime("2024-12-01 04:45:00", dt_strfmt)
  # start_ts = datetime.strptime("2024-12-01 05:45:00", dt_strfmt)
  # pull_ts = datetime.strptime("2024-12-01 06:05:00", dt_strfmt)
  # preshape_ts = datetime.strptime("2024-12-01 08:45:00", dt_strfmt)
  # final_shape_ts = datetime.strptime("2024-12-01 09:30:00", dt_strfmt)
  # fridge_ts = datetime.strptime("2024-12-01 11:45:00", dt_strfmt)

  # dough = DoughMake(
  #   # company="Rize Up Bakery",
  #   name="Hoagie A",
  #   date=dt,
  #   autolyse=autolyse_ts,
  #   start=start_ts,
  #   pull=pull_ts,
  #   preshape=preshape_ts,
  #   final_shape=final_shape_ts,
  #   fridge=fridge_ts,
  #   room_temp=72,
  #   preferment_temp=75,
  #   water_temp=80,
  #   flour_temp=70,
  #   notes="Perfect spring day for baking"
  # )


  # make_id = db_conn.insert_dough_make(dough)
  # print(f"Inserted dough make with ID: {make_id}")

  # connector1 = DBConnector(dbname)
  # connector2 = DBConnector(dbname)
  # print(connector1.db_pool == connector2.db_pool)

  dt = datetime(2024, 12, 1)
  dough_make = db_conn.get_dough_make(dt, make_name="hoagie_a")
  print(dough_make)
