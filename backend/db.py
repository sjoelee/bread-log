import psycopg
from models import DoughMake

# establish connection to DB
# return connection if it's already made

class DBConnector():
  USER = 'sammylee'
  def __init__(self, dbname):
    self.user = DBConnector.USER
    self.dbname = dbname
    pass

  def insert_dough_make(self, dough_make: DoughMake):
    table = 'dough_makes'
    insert_data = {
      'dough_name': dough_make.name,
      'make_date': dough_make.date.date(),  # Extract just the date part
      'room_temp': dough_make.room_temp,
      'water_temp': dough_make.water_temp,
      'flour_temp': dough_make.flour_temp,
      'preferment_temp': dough_make.preferment_temp,
      'start_time': dough_make.start,
      'pull_time': dough_make.pull,
      'pre_shape_time': dough_make.preshape,
      'final_shape_time': dough_make.final_shape,
      'fridge_time': dough_make.fridge,
      'autolyse_time': int((dough_make.start - dough_make.autolyse).total_seconds() / 60)  # Convert to minutes
    }
    # maybe add first fermentation and second fermentation
    insert_data = {k: v for k, v in insert_data.items() if v is not None}
    columns = ', '.join(insert_data.keys())
    placeholders = ', '.join(['%s'] * len(insert_data))
    values = list(insert_data.values())
    sql = f"""
        INSERT INTO dough_makes ({columns})
        VALUES ({placeholders})
        RETURNING make_id;
    """
    with psycopg.connect(f"dbname={self.dbname} user={self.user}") as conn:
      with conn.cursor() as cur:
        cur.execute(sql, values)
        make_id = cur.fetchone()[0]
        print(f"Inserted dough make with ID: {make_id}")

# testing
if __name__ == '__main__':
  from datetime import datetime, timedelta

  dough = DoughMake(
    # company="Rize Up Bakery",
    name="Hoagie A",
    date=datetime.now(),
    autolyse=datetime.now() - timedelta(hours=2),
    start=datetime.now(),
    pull=datetime.now() + timedelta(hours=3),
    preshape=datetime.now() + timedelta(hours=3, minutes=30),
    final_shape=datetime.now() + timedelta(hours=4),
    fridge=datetime.now() + timedelta(hours=4, minutes=30),
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