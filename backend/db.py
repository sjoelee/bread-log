from contextlib import contextmanager
from datetime import date
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

  def insert_dough_make(self, dough_make: DoughMake) -> int:
    table = 'dough_makes'
    insert_data = {
      'dough_name': dough_make.name,
      'make_date': dough_make.date,  # Extract just the date part
      'room_temp': dough_make.room_temp,
      'water_temp': dough_make.water_temp,
      'flour_temp': dough_make.flour_temp,
      'preferment_temp': dough_make.preferment_temp,
      'start_time': dough_make.start,
      'pull_time': dough_make.pull,
      'pre_shape_time': dough_make.preshape,
      'final_shape_time': dough_make.final_shape,
      'fridge_time': dough_make.fridge,
      'autolyse_time': dough_make.autolyse,
    }
    # maybe add first fermentation and second fermentation
    insert_data = {k: v for k, v in insert_data.items() if v is not None}
    columns = ', '.join(insert_data.keys())
    placeholders = ', '.join(['%s'] * len(insert_data))
    values = list(insert_data.values())
    sql = f"""
      INSERT INTO {table} ({columns})
      VALUES ({placeholders})
      RETURNING make_id;
    """
    logger.debug(f'SQL Command\n {sql}')
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, values)
          make_id = cur.fetchone()[0]
          conn.commit()
          logger.info(f"Inserted dough make with ID: {make_id}")
          return make_id
    except Exception as e:
      logger.error(f"Error inserting dough make: {str(e)}")
      raise  # Re-raise the exception after printing it

  def get_dough_make(self, date: date, make_name: str) -> Optional[DoughMake]:
    sql = """
        SELECT dough_name, make_date, room_temp, water_temp,
               flour_temp, preferment_temp, start_time, autolyse_time,
               pull_time, pre_shape_time, final_shape_time, fridge_time
        FROM dough_makes
        WHERE make_date = %s AND dough_name = %s;
    """
    values = (date, make_name)
    with self.db_pool.get_connection() as conn:
      with conn.cursor() as cur:
        cur.execute(sql, values)
        res = cur.fetchone()
        if res is None:
          return None
 
        (dough_name, make_date, room_temp, water_temp, flour_temp, preferment_temp, start_time, autolyse_time, pull_time, pre_shape_time, final_shape_time, fridge_time) = res

        room_temp = int(room_temp) if room_temp else None
        water_temp = int(water_temp) if water_temp else None
        flour_temp = int(flour_temp) if flour_temp else None
        preferment_temp = int(preferment_temp) if preferment_temp else None

        return DoughMake(
          name=dough_name,
          date=make_date,
          autolyse=autolyse_time,
          start=start_time,
          pull=pull_time,
          preshape=pre_shape_time,
          final_shape=final_shape_time,
          fridge=fridge_time,
          room_temp=room_temp,
          preferment_temp=preferment_temp,
          water_temp=water_temp,
          flour_temp=flour_temp,
          notes=None  # This field isn't in the database
        )

  # if there are any updates needed to be made
  def update_dough_make(self, dough_make: DoughMake) -> None:
    pass

# testing
if __name__ == '__main__':
  from datetime import datetime, date

  dt = datetime(2024, 12, 1)
  dt_strfmt = "%Y-%m-%d %H:%M:%S"
  autolyse_time = datetime.strptime("2024-12-01 04:45:00", dt_strfmt)
  start_time = datetime.strptime("2024-12-01 05:45:00", dt_strfmt)
  pull_time = datetime.strptime("2024-12-01 06:05:00", dt_strfmt)
  preshape_time = datetime.strptime("2024-12-01 08:45:00", dt_strfmt)
  final_shape_time = datetime.strptime("2024-12-01 09:30:00", dt_strfmt)
  fridge_time = datetime.strptime("2024-12-01 11:45:00", dt_strfmt)

  dough = DoughMake(
    # company="Rize Up Bakery",
    name="Hoagie A",
    date=dt,
    autolyse=autolyse_time,
    start=start_time,
    pull=pull_time,
    preshape=preshape_time,
    final_shape=final_shape_time,
    fridge=fridge_time,
    room_temp=72,
    preferment_temp=75,
    water_temp=80,
    flour_temp=70,
    notes="Perfect spring day for baking"
  )

  dbname = 'bread_makes'
  db_conn = DBConnector(dbname=dbname)
  make_id = db_conn.insert_dough_make(dough)
  print(f"Inserted dough make with ID: {make_id}")

  connector1 = DBConnector(dbname)
  connector2 = DBConnector(dbname)
  print(connector1.db_pool == connector2.db_pool)
