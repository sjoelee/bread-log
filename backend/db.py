from contextlib import contextmanager
from datetime import date, datetime
from exceptions import DatabaseError
from models import DoughMake, Recipe, RecipeStep, Ingredient, SimpleMake, StretchFoldCreate, RecipeVersion, RecipeListItem, BakersPercentages
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

  def get_recent_dough_makes(self, account_id: UUID, limit: int = 10, offset: int = 0) -> List[DoughMake]:
    """
    Get recent dough makes for an account, sorted by creation date
    """
    sql = """
        SELECT dm.name, dm.date, dm.room_temp, dm.water_temp,
               dm.flour_temp, dm.preferment_temp, dm.dough_temp, dm.temperature_unit, 
               dm.mix_ts, dm.autolyse_ts, dm.bulk_ts, dm.preshape_ts, dm.final_shape_ts, 
               dm.fridge_ts, dm.stretch_folds, dm.notes, dm.created_at
        FROM dough_makes dm
        JOIN account_makes am ON dm.name = am.key
        WHERE am.account_id = %s
        ORDER BY dm.created_at DESC
        LIMIT %s OFFSET %s;
    """
    
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (account_id, limit, offset))
          res = cur.fetchall()
    except Exception as e:
      logger.error(f"Error getting recent dough makes: {str(e)}")
      raise DatabaseError(f"Database error: {str(e)}")
    
    dough_makes = []
    for row in res:
      (name, date, room_temp, water_temp, flour_temp, preferment_temp, dough_temp,
       temperature_unit, mix_ts, autolyse_ts, bulk_ts, preshape_ts, final_shape_ts, 
       fridge_ts, stretch_folds_json, notes, created_at) = row
      
      # Parse stretch_folds JSON
      stretch_folds = []
      if stretch_folds_json:
        try:
          # Handle case where psycopg already parsed JSON as a list
          if isinstance(stretch_folds_json, list):
            stretch_folds_data = stretch_folds_json
          else:
            # Parse JSON string
            stretch_folds_data = json.loads(stretch_folds_json)
          
          if isinstance(stretch_folds_data, list):
            for fold in stretch_folds_data:
              if isinstance(fold, dict):
                stretch_folds.append(StretchFoldCreate(**fold))
        except (json.JSONDecodeError, TypeError) as e:
          logger.warning(f"Invalid JSON in stretch_folds for make {name}: {stretch_folds_json}, error: {e}")
      
      dough_make = DoughMake(
        name=name,
        date=date,
        room_temp=room_temp,
        water_temp=water_temp,
        flour_temp=flour_temp,
        preferment_temp=preferment_temp,
        dough_temp=dough_temp,
        temperature_unit=temperature_unit or 'fahrenheit',
        mix_ts=mix_ts,
        autolyse_ts=autolyse_ts,
        bulk_ts=bulk_ts,
        preshape_ts=preshape_ts,
        final_shape_ts=final_shape_ts,
        fridge_ts=fridge_ts,
        stretch_folds=stretch_folds,
        notes=notes,
        created_at=created_at
      )
      
      dough_makes.append(dough_make)
    
    return dough_makes

  def get_distinct_bread_names(self, account_id: UUID) -> List[dict]:
    """
    Get distinct bread names from dough_makes ordered by most recent created_at
    Note: For now we ignore account_id since we're moving away from account_makes table
    """
    sql = """
        SELECT name, MAX(created_at) as latest_created_at
        FROM dough_makes
        WHERE name IS NOT NULL AND name != ''
        GROUP BY name
        ORDER BY latest_created_at DESC;
    """
    
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql)
          res = cur.fetchall()
    except Exception as e:
      logger.error(f"Error getting distinct bread names: {str(e)}")
      raise DatabaseError(f"Database error: {str(e)}")
    
    distinct_names = []
    for row in res:
      (name, latest_created_at) = row
      distinct_names.append({
        "name": name,
        "latest_created_at": latest_created_at
      })
    
    return distinct_names

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

  def create_recipe(self, recipe_data: dict):
    """
    Create a new recipe in the database
    """
    insert_data = {
      'id': recipe_data['id'],
      'name': recipe_data['name'],
      'description': recipe_data['description'],
      'instructions': json.dumps(recipe_data['instructions']),
      'flour_ingredients': json.dumps(recipe_data['flour_ingredients']),
      'other_ingredients': json.dumps(recipe_data['other_ingredients'])
    }
    
    # Filter out None values
    insert_data = {k: v for k, v in insert_data.items() if v is not None}
    
    # Build query using psycopg.sql for safety
    columns = sql.SQL(', ').join([sql.Identifier(k) for k in insert_data.keys()])
    placeholders = sql.SQL(', ').join([sql.Placeholder() for _ in insert_data])
    values = list(insert_data.values())
    
    query = sql.SQL("""
      INSERT INTO recipes ({})
      VALUES ({});
    """).format(columns, placeholders)
    
    logger.debug(f'SQL Command\n {query}')
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, values)
          conn.commit()
    except Exception as e:
      logger.error(f"Error creating recipe: {str(e)}")
      raise DatabaseError(f"Error creating recipe: {e}")

  def get_recipe(self, recipe_id: UUID) -> Optional[Recipe]:
    """
    Get a recipe by ID
    """
    query = """
      SELECT id, name, description, instructions, flour_ingredients, other_ingredients, created_at, updated_at
      FROM recipes
      WHERE id = %s
    """
    
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, [recipe_id])
          result = cur.fetchone()
    except Exception as e:
      logger.error(f"Error getting recipe: {str(e)}")
      raise DatabaseError(f"Error getting recipe: {e}")
    
    if not result:
      return None
    
    (id, name, description, instructions_json, flour_ingredients_json, other_ingredients_json, created_at, updated_at) = result
    
    # Parse JSON data
    instructions = [RecipeStep(**step) for step in instructions_json]
    flour_ingredients = [Ingredient(**ingredient) for ingredient in flour_ingredients_json]
    other_ingredients = [Ingredient(**ingredient) for ingredient in other_ingredients_json]
    
    return Recipe(
      id=id,
      name=name,
      description=description,
      instructions=instructions,
      flour_ingredients=flour_ingredients,
      other_ingredients=other_ingredients,
      created_at=created_at,
      updated_at=updated_at
    )

  # New versioned recipe methods
  def create_versioned_recipe(self, recipe_data: dict) -> dict:
    """
    Create a new versioned recipe with initial version 1.0
    """
    recipe_id = recipe_data['id']
    version_id = recipe_data.get('version_id')
    
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          # Insert into recipes table
          cur.execute("""
            INSERT INTO recipes (id, name, description, category, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
          """, [
            recipe_id,
            recipe_data['name'],
            recipe_data.get('description'),
            recipe_data.get('category'),
            datetime.now(),
            datetime.now()
          ])
          
          # Insert initial version (v1)
          cur.execute("""
            INSERT INTO recipe_versions (id, recipe_id, version_number, 
                                       description, ingredients, instructions, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
          """, [
            version_id,
            recipe_id,
            1,
            recipe_data.get('version_description', 'Initial version'),
            json.dumps({"ingredients": recipe_data['ingredients']}),
            json.dumps({"instructions": recipe_data['instructions']}),
            datetime.now()
          ])
          
          # Update current_version_id
          cur.execute("""
            UPDATE recipes SET current_version_id = %s WHERE id = %s
          """, [version_id, recipe_id])
          
          # Insert baker's percentages if provided
          if recipe_data.get('bakers_percentages'):
            bp = recipe_data['bakers_percentages']
            cur.execute("""
              INSERT INTO bakers_percentages (id, recipe_id, recipe_version_id, 
                                            total_flour_weight, flour_ingredients, other_ingredients)
              VALUES (%s, %s, %s, %s, %s, %s)
            """, [
              recipe_data.get('bp_id'),
              recipe_id,
              version_id,
              bp['total_flour_weight'],
              json.dumps(bp['flour_ingredients']),
              json.dumps(bp['other_ingredients'])
            ])
          
          conn.commit()
          return {"recipe_id": recipe_id, "version_id": version_id}
          
    except Exception as e:
      logger.error(f"Error creating versioned recipe: {str(e)}")
      raise DatabaseError(f"Error creating versioned recipe: {e}")

  def create_recipe_version(self, version_data: dict) -> dict:
    """
    Create a new version of an existing recipe
    """
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          # Insert new version
          cur.execute("""
            INSERT INTO recipe_versions (id, recipe_id, version_number,
                                       description, ingredients, instructions, created_at, change_summary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
          """, [
            version_data['id'],
            version_data['recipe_id'],
            version_data['version_number'],
            version_data.get('description'),
            json.dumps({"ingredients": version_data['ingredients']}),
            json.dumps({"instructions": version_data['instructions']}),
            datetime.now(),
            json.dumps(version_data.get('change_summary', {}))
          ])
          
          # Update current_version_id
          cur.execute("""
            UPDATE recipes SET current_version_id = %s, updated_at = %s WHERE id = %s
          """, [version_data['id'], datetime.now(), version_data['recipe_id']])
          
          # Insert baker's percentages if provided
          if version_data.get('bakers_percentages'):
            bp = version_data['bakers_percentages']
            cur.execute("""
              INSERT INTO bakers_percentages (id, recipe_id, recipe_version_id,
                                            total_flour_weight, flour_ingredients, other_ingredients)
              VALUES (%s, %s, %s, %s, %s, %s)
            """, [
              version_data.get('bp_id'),
              version_data['recipe_id'],
              version_data['id'],
              bp['total_flour_weight'],
              json.dumps(bp['flour_ingredients']),
              json.dumps(bp['other_ingredients'])
            ])
          
          conn.commit()
          return {"version_id": version_data['id']}
          
    except Exception as e:
      logger.error(f"Error creating recipe version: {str(e)}")
      raise DatabaseError(f"Error creating recipe version: {e}")

  def get_versioned_recipe(self, recipe_id: UUID) -> Optional[Recipe]:
    """
    Get a versioned recipe with current version and baker's percentages
    """
    query = """
      SELECT r.id, r.name, r.description, r.category, r.current_version_id, r.created_at, r.updated_at,
             rv.id, rv.version_number, rv.description, rv.ingredients, rv.instructions, rv.created_at,
             bp.total_flour_weight, bp.flour_ingredients, bp.other_ingredients
      FROM recipes r
      LEFT JOIN recipe_versions rv ON r.current_version_id = rv.id
      LEFT JOIN bakers_percentages bp ON rv.id = bp.recipe_version_id
      WHERE r.id = %s
    """
    
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, [recipe_id])
          result = cur.fetchone()
    except Exception as e:
      logger.error(f"Error getting versioned recipe: {str(e)}")
      raise DatabaseError(f"Error getting versioned recipe: {e}")
    
    if not result:
      return None
    
    (r_id, r_name, r_description, r_category, r_current_version_id, r_created_at, r_updated_at,
     rv_id, rv_version_number, rv_description, rv_ingredients, rv_instructions, rv_created_at,
     bp_total_flour, bp_flour_ingredients, bp_other_ingredients) = result
    
    # Parse ingredients and instructions
    ingredients_data = rv_ingredients.get('ingredients', []) if rv_ingredients else []
    instructions_data = rv_instructions.get('instructions', []) if rv_instructions else []
    
    ingredients = [Ingredient(**ing) for ing in ingredients_data]
    instructions = [RecipeStep(**step) for step in instructions_data]
    
    # Create current version
    current_version = RecipeVersion(
      id=rv_id,
      recipe_id=r_id,
      version_number=rv_version_number,
      description=rv_description,
      ingredients=ingredients,
      instructions=instructions,
      created_at=rv_created_at
    )
    
    # Create baker's percentages if available
    bakers_percentages = None
    if bp_total_flour is not None:
      bakers_percentages = BakersPercentages(
        total_flour_weight=bp_total_flour,
        flour_ingredients=bp_flour_ingredients,
        other_ingredients=bp_other_ingredients
      )
    
    return Recipe(
      id=r_id,
      name=r_name,
      description=r_description,
      category=r_category,
      current_version_id=r_current_version_id,
      current_version=current_version,
      bakers_percentages=bakers_percentages,
      created_at=r_created_at,
      updated_at=r_updated_at
    )

  def list_recipes(self, category: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[RecipeListItem]:
    """
    List recipes with basic info and current version
    """
    base_query = """
      SELECT r.id, r.name, r.category, r.created_at, r.updated_at,
             rv.version_number,
             jsonb_array_length(rv.ingredients->'ingredients') as ingredient_count,
             jsonb_array_length(rv.instructions->'instructions') as step_count
      FROM recipes r
      LEFT JOIN recipe_versions rv ON r.current_version_id = rv.id
    """
    
    conditions = []
    params = []
    
    if category:
      conditions.append("r.category = %s")
      params.append(category)
    
    if conditions:
      query = base_query + " WHERE " + " AND ".join(conditions)
    else:
      query = base_query
    
    query += " ORDER BY r.updated_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, params)
          results = cur.fetchall()
    except Exception as e:
      logger.error(f"Error listing recipes: {str(e)}")
      raise DatabaseError(f"Error listing recipes: {e}")
    
    recipes = []
    for result in results:
      (r_id, r_name, r_category, r_created_at, r_updated_at,
       rv_version_number, ingredient_count, step_count) = result
      
      version_str = str(rv_version_number) if rv_version_number is not None else "1"
      
      recipes.append(RecipeListItem(
        id=r_id,
        name=r_name,
        category=r_category,
        version=version_str,
        ingredient_count=ingredient_count or 0,
        step_count=step_count or 0,
        created_at=r_created_at,
        updated_at=r_updated_at
      ))
    
    return recipes

  def get_recipe_versions(self, recipe_id: UUID) -> List[RecipeVersion]:
    """
    Get all versions of a recipe ordered by version number
    """
    query = """
      SELECT id, recipe_id, version_number, description, 
             ingredients, instructions, created_at, change_summary
      FROM recipe_versions
      WHERE recipe_id = %s
      ORDER BY version_number DESC
    """
    
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, [recipe_id])
          results = cur.fetchall()
    except Exception as e:
      logger.error(f"Error getting recipe versions: {str(e)}")
      raise DatabaseError(f"Error getting recipe versions: {e}")
    
    versions = []
    for result in results:
      (rv_id, rv_recipe_id, rv_version_number, rv_description,
       rv_ingredients, rv_instructions, rv_created_at, rv_change_summary) = result
      
      ingredients_data = rv_ingredients.get('ingredients', []) if rv_ingredients else []
      instructions_data = rv_instructions.get('instructions', []) if rv_instructions else []
      
      ingredients = [Ingredient(**ing) for ing in ingredients_data]
      instructions = [RecipeStep(**step) for step in instructions_data]
      
      versions.append(RecipeVersion(
        id=rv_id,
        recipe_id=rv_recipe_id,
        version_number=rv_version_number,
        description=rv_description,
        ingredients=ingredients,
        instructions=instructions,
        created_at=rv_created_at,
        change_summary=rv_change_summary
      ))
    
    return versions

  def get_recipe_version(self, version_id: UUID) -> Optional[RecipeVersion]:
    """
    Get a specific recipe version by ID
    """
    query = """
      SELECT id, recipe_id, version_number, description,
             ingredients, instructions, created_at, change_summary
      FROM recipe_versions
      WHERE id = %s
    """
    
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, [version_id])
          result = cur.fetchone()
    except Exception as e:
      logger.error(f"Error getting recipe version: {str(e)}")
      raise DatabaseError(f"Error getting recipe version: {e}")
    
    if not result:
      return None
    
    (rv_id, rv_recipe_id, rv_version_number, rv_description,
     rv_ingredients, rv_instructions, rv_created_at, rv_change_summary) = result
    
    ingredients_data = rv_ingredients.get('ingredients', []) if rv_ingredients else []
    instructions_data = rv_instructions.get('instructions', []) if rv_instructions else []
    
    ingredients = [Ingredient(**ing) for ing in ingredients_data]
    instructions = [RecipeStep(**step) for step in instructions_data]
    
    return RecipeVersion(
      id=rv_id,
      recipe_id=rv_recipe_id,
      version_number=rv_version_number,
      description=rv_description,
      ingredients=ingredients,
      instructions=instructions,
      created_at=rv_created_at,
      change_summary=rv_change_summary
    )
  
  def update_recipe_basic_fields(self, recipe_id: UUID, updates: dict):
    """
    Update basic recipe fields (name, description, category, current_version_id, updated_at)
    Used by the PATCH endpoint to update recipe metadata after creating a new version.
    """
    try:
      # Build dynamic update query based on provided fields
      update_fields = []
      params = []
      param_num = 1
      
      for field, value in updates.items():
        if field in ['name', 'description', 'category', 'current_version_id', 'updated_at']:
          update_fields.append(f"{field} = %s")
          params.append(value)
        else:
          logger.warning(f"Skipping unknown field in update: {field}")
      
      if not update_fields:
        return  # Nothing to update
      
      # Add recipe_id parameter for WHERE clause
      params.append(recipe_id)
      
      query = f"UPDATE recipes SET {', '.join(update_fields)} WHERE id = %s"
      
      
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, params)
          if cur.rowcount == 0:
            raise ValueError(f"Recipe with ID {recipe_id} not found")
      
    except Exception as e:
      logger.error(f"Error updating recipe basic fields: {str(e)}")
      raise DatabaseError(f"Failed to update recipe basic fields: {str(e)}")
  
  def delete_recipe(self, recipe_id: UUID) -> bool:
    """
    Delete a recipe and all its associated data.
    The CASCADE constraints will automatically delete recipe_versions and bakers_percentages.
    """
    try:
      query = "DELETE FROM recipes WHERE id = $1"
      
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, [recipe_id])
          rows_deleted = cur.rowcount
          
      # Return True if a row was deleted, False if recipe didn't exist
      return rows_deleted > 0
      
    except Exception as e:
      logger.error(f"Error deleting recipe: {str(e)}")
      raise DatabaseError(f"Failed to delete recipe: {str(e)}")
