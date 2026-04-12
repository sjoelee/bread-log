"""
Test cases for Bread Timing REST API endpoints
Following TDD approach with comprehensive coverage
"""

from fastapi.testclient import TestClient
from backend.service import app

client = TestClient(app)


class TestTimingEndpointCreation:
  """Test timing creation endpoint"""

  def test_create_basic_timing(self):
    """Test creating a basic timing entry with minimal required fields"""

    # GIVEN: Basic timing data with required fields
    timing_data = {"recipe_name": "Basic Sourdough", "date": "2024-01-15"}

    # WHEN: Timing creation is attempted
    response = client.post("/timings", json=timing_data)

    # THEN: Timing is created successfully
    assert response.status_code == 201
    timing = response.json()

    # Verify required fields
    assert timing["recipe_name"] == "Basic Sourdough"
    assert timing["date"] == "2024-01-15"
    assert "id" in timing  # UUID should be generated
    assert "created_at" in timing
    assert "updated_at" in timing
    assert timing["temperature_unit"] == "Fahrenheit"  # Default value

  def test_create_complete_timing(self):
    """Test creating a timing entry with all fields populated"""

    # GIVEN: Complete timing data
    timing_data = {
      "recipe_name": "Complex Sourdough",
      "date": "2024-01-16",
      "autolyse_ts": "2024-01-16T08:00:00",
      "mix_ts": "2024-01-16T08:30:00",
      "bulk_ts": "2024-01-16T09:00:00",
      "preshape_ts": "2024-01-16T13:00:00",
      "final_shape_ts": "2024-01-16T13:30:00",
      "fridge_ts": "2024-01-16T14:00:00",
      "room_temp": 75.0,
      "water_temp": 85.0,
      "flour_temp": 70.0,
      "preferment_temp": 78.0,
      "dough_temp": 80.0,
      "temperature_unit": "Fahrenheit",
      "stretch_folds": [
        {"fold_number": 1, "timestamp": "2024-01-16T09:30:00"},
        {"fold_number": 2, "timestamp": "2024-01-16T10:00:00"},
      ],
      "notes": "Perfect fermentation conditions today",
    }

    # WHEN: Timing creation is attempted
    response = client.post("/timings", json=timing_data)

    # THEN: Timing is created successfully with all fields
    assert response.status_code == 201
    timing = response.json()

    assert timing["recipe_name"] == "Complex Sourdough"
    assert timing["autolyse_ts"] == "2024-01-16T08:00:00"
    assert timing["dough_temp"] == 80.0
    assert timing["temperature_unit"] == "Fahrenheit"
    assert len(timing["stretch_folds"]) == 2
    assert timing["stretch_folds"][0]["fold_number"] == 1
    assert timing["notes"] == "Perfect fermentation conditions today"

  def test_create_timing_with_celsius(self):
    """Test creating a timing entry with Celsius temperature unit"""

    # GIVEN: Timing data with Celsius temperatures
    timing_data = {
      "recipe_name": "European Style",
      "date": "2024-01-17",
      "room_temp": 24.0,
      "dough_temp": 26.0,
      "temperature_unit": "Celsius",
    }

    # WHEN: Timing creation is attempted
    response = client.post("/timings", json=timing_data)

    # THEN: Timing is created with Celsius unit
    if response.status_code != 201:
      print("Response:", response.status_code, response.json())
    assert response.status_code == 201
    timing = response.json()

    assert timing["temperature_unit"] == "Celsius"
    assert timing["room_temp"] == 24.0
    assert timing["dough_temp"] == 26.0


class TestTimingEndpointValidation:
  """Test timing endpoint validation rules"""

  def test_missing_recipe_name(self):
    """Test validation when recipe_name is missing"""

    # GIVEN: Timing data without recipe name
    timing_data = {"date": "2024-01-15"}

    # WHEN: Timing creation is attempted
    response = client.post("/timings", json=timing_data)

    # THEN: Validation error is returned
    assert response.status_code == 422
    error_data = response.json()
    assert "recipe_name" in str(error_data["detail"])

  def test_missing_date(self):
    """Test validation when date is missing"""

    # GIVEN: Timing data without date
    timing_data = {"recipe_name": "Test Bread"}

    # WHEN: Timing creation is attempted
    response = client.post("/timings", json=timing_data)

    # THEN: Validation error is returned
    assert response.status_code == 422
    error_data = response.json()
    assert "date" in str(error_data["detail"])

  def test_invalid_temperature_unit(self):
    """Test validation of temperature unit"""

    # GIVEN: Timing data with invalid temperature unit
    timing_data = {
      "recipe_name": "Test Bread",
      "date": "2024-01-15",
      "temperature_unit": "Kelvin",
    }

    # WHEN: Timing creation is attempted
    response = client.post("/timings", json=timing_data)

    # THEN: Validation error is returned
    assert response.status_code == 422
    error_data = response.json()
    assert "temperature_unit" in str(error_data["detail"])

  def test_temperature_range_validation(self):
    """Test temperature range validation"""

    # GIVEN: Timing data with out-of-range temperatures
    timing_data = {
      "recipe_name": "Test Bread",
      "date": "2024-01-15",
      "room_temp": -50.0,  # Too cold
      "water_temp": 300.0,  # Too hot
    }

    # WHEN: Timing creation is attempted
    response = client.post("/timings", json=timing_data)

    # THEN: Validation error is returned
    assert response.status_code == 422

  def test_excessive_stretch_folds(self):
    """Test validation of stretch folds limit"""

    # GIVEN: Timing data with too many stretch folds
    stretch_folds = [
      {"fold_number": i, "timestamp": f"2024-01-15T09:{i:02d}:00"}
      for i in range(1, 11)  # 10 stretch folds (max is 8)
    ]

    timing_data = {
      "recipe_name": "Over-folded Bread",
      "date": "2024-01-15",
      "stretch_folds": stretch_folds,
    }

    # WHEN: Timing creation is attempted
    response = client.post("/timings", json=timing_data)

    # THEN: Validation error is returned
    assert response.status_code == 422
    error_data = response.json()
    assert "stretch_folds" in str(error_data["detail"])

  def test_invalid_stretch_fold_number(self):
    """Test validation of stretch fold numbers"""

    # GIVEN: Timing data with invalid fold number
    timing_data = {
      "recipe_name": "Bad Fold Bread",
      "date": "2024-01-15",
      "stretch_folds": [
        {"fold_number": 0, "timestamp": "2024-01-15T09:00:00"}  # Invalid: must be > 0
      ],
    }

    # WHEN: Timing creation is attempted
    response = client.post("/timings", json=timing_data)

    # THEN: Validation error is returned
    assert response.status_code == 422


class TestTimingEndpointRetrieval:
  """Test timing retrieval operations"""

  def test_get_timing_by_id(self):
    """Test retrieving a specific timing by UUID"""

    # GIVEN: A timing entry exists
    timing_data = {
      "recipe_name": "Retrievable Bread",
      "date": "2024-01-18",
      "dough_temp": 78.0,
    }

    create_response = client.post("/timings", json=timing_data)
    assert create_response.status_code == 201
    timing_id = create_response.json()["id"]

    # WHEN: Timing is retrieved by ID
    response = client.get(f"/timings/{timing_id}")

    # THEN: Timing data is returned correctly
    assert response.status_code == 200
    timing = response.json()
    assert timing["id"] == timing_id
    assert timing["recipe_name"] == "Retrievable Bread"
    assert timing["dough_temp"] == 78.0

  def test_get_nonexistent_timing(self):
    """Test retrieving a timing that doesn't exist"""

    # GIVEN: A UUID that doesn't exist
    fake_uuid = "12345678-1234-1234-1234-123456789abc"

    # WHEN: Timing retrieval is attempted
    response = client.get(f"/timings/{fake_uuid}")

    # THEN: 404 error is returned
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

  def test_get_invalid_uuid_format(self):
    """Test retrieving timing with invalid UUID format"""

    # GIVEN: An invalid UUID format
    invalid_uuid = "not-a-uuid"

    # WHEN: Timing retrieval is attempted
    response = client.get(f"/timings/{invalid_uuid}")

    # THEN: 422 validation error is returned
    assert response.status_code == 422


class TestTimingEndpointList:
  """Test timing list endpoint with pagination and filtering"""

  def setup_method(self):
    """Setup test data for list operations"""

    # Create multiple timing entries for testing
    self.test_timings = []

    for i in range(15):
      timing_data = {
        "recipe_name": f"Test Bread {i + 1}",
        "date": f"2024-01-{i + 1:02d}",
        "dough_temp": 75.0 + i,
      }
      response = client.post("/timings", json=timing_data)
      if response.status_code == 201:
        self.test_timings.append(response.json())

  def test_list_timings_default_pagination(self):
    """Test listing timings with default pagination"""

    # WHEN: Timings are listed without parameters
    response = client.get("/timings")

    # THEN: Paginated results are returned
    assert response.status_code == 200
    data = response.json()

    assert "timings" in data
    assert "total_count" in data
    assert "page" in data
    assert "limit" in data
    assert "total_pages" in data
    assert "has_next" in data
    assert "has_previous" in data

    # Check pagination defaults
    assert data["page"] == 1
    assert data["limit"] == 20
    assert len(data["timings"]) <= 20

  def test_list_timings_custom_pagination(self):
    """Test listing timings with custom pagination parameters"""

    # WHEN: Timings are listed with custom pagination
    response = client.get("/timings?page=2&limit=5")

    # THEN: Custom pagination is applied
    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 2
    assert data["limit"] == 5
    assert len(data["timings"]) <= 5

  def test_list_timings_filter_by_recipe_name(self):
    """Test filtering timings by recipe name"""

    # GIVEN: A specific recipe name exists
    recipe_name = "Test Bread 5"

    # WHEN: Timings are filtered by recipe name
    response = client.get(f"/timings?recipe_name={recipe_name}")

    # THEN: Only matching timings are returned
    assert response.status_code == 200
    data = response.json()

    for timing in data["timings"]:
      assert timing["recipe_name"] == recipe_name

  def test_list_timings_filter_by_date(self):
    """Test filtering timings by specific date"""

    # WHEN: Timings are filtered by date
    response = client.get("/timings?date=2024-01-05")

    # THEN: Only timings from that date are returned
    assert response.status_code == 200
    data = response.json()

    for timing in data["timings"]:
      assert timing["date"] == "2024-01-05"

  def test_list_timings_date_range_filter(self):
    """Test filtering timings by date range"""

    # WHEN: Timings are filtered by date range
    response = client.get("/timings?date_from=2024-01-05&date_to=2024-01-10")

    # THEN: Only timings within date range are returned
    assert response.status_code == 200
    data = response.json()

    for timing in data["timings"]:
      timing_date = timing["date"]
      assert "2024-01-05" <= timing_date <= "2024-01-10"

  def test_list_timings_search(self):
    """Test search functionality across timing data"""

    # WHEN: Timings are searched
    response = client.get("/timings?search=Bread")

    # THEN: Matching timings are returned
    assert response.status_code == 200
    data = response.json()

    # All results should contain "Bread" somewhere
    for timing in data["timings"]:
      timing_text = f"{timing['recipe_name']} {timing.get('notes', '')}"
      assert "Bread" in timing_text

  def test_list_timings_ordering(self):
    """Test ordering of timing results"""

    # WHEN: Timings are ordered by created_at descending
    response = client.get("/timings?order_by=created_at&order_direction=desc")

    # THEN: Results are properly ordered
    assert response.status_code == 200
    data = response.json()

    # Check that timestamps are in descending order
    timestamps = [timing["created_at"] for timing in data["timings"]]
    assert timestamps == sorted(timestamps, reverse=True)


class TestTimingEndpointUpdate:
  """Test timing update operations"""

  def test_update_timing_partial(self):
    """Test partial update of timing entry"""

    # GIVEN: An existing timing entry
    timing_data = {
      "recipe_name": "Original Bread",
      "date": "2024-01-20",
      "dough_temp": 75.0,
    }

    create_response = client.post("/timings", json=timing_data)
    assert create_response.status_code == 201
    timing_id = create_response.json()["id"]

    # WHEN: Timing is partially updated
    update_data = {"recipe_name": "Updated Bread", "dough_temp": 80.0}

    response = client.patch(f"/timings/{timing_id}", json=update_data)

    # THEN: Only specified fields are updated
    assert response.status_code == 200
    updated_timing = response.json()

    assert updated_timing["recipe_name"] == "Updated Bread"
    assert updated_timing["dough_temp"] == 80.0
    assert updated_timing["date"] == "2024-01-20"  # Unchanged
    assert updated_timing["updated_at"] != updated_timing["created_at"]

  def test_update_timing_process_timestamps(self):
    """Test updating process timestamps"""

    # GIVEN: An existing timing entry
    timing_data = {"recipe_name": "Process Bread", "date": "2024-01-21"}

    create_response = client.post("/timings", json=timing_data)
    timing_id = create_response.json()["id"]

    # WHEN: Process timestamps are added
    update_data = {
      "autolyse_ts": "2024-01-21T08:00:00",
      "mix_ts": "2024-01-21T08:30:00",
      "bulk_ts": "2024-01-21T09:00:00",
    }

    response = client.patch(f"/timings/{timing_id}", json=update_data)

    # THEN: Timestamps are updated correctly
    assert response.status_code == 200
    updated_timing = response.json()

    assert updated_timing["autolyse_ts"] == "2024-01-21T08:00:00"
    assert updated_timing["mix_ts"] == "2024-01-21T08:30:00"
    assert updated_timing["bulk_ts"] == "2024-01-21T09:00:00"

  def test_update_stretch_folds(self):
    """Test updating stretch folds data"""

    # GIVEN: An existing timing entry
    timing_data = {"recipe_name": "Folded Bread", "date": "2024-01-22"}

    create_response = client.post("/timings", json=timing_data)
    timing_id = create_response.json()["id"]

    # WHEN: Stretch folds are added
    update_data = {
      "stretch_folds": [
        {"fold_number": 1, "timestamp": "2024-01-22T09:30:00"},
        {"fold_number": 2, "timestamp": "2024-01-22T10:00:00"},
        {"fold_number": 3, "timestamp": "2024-01-22T10:30:00"},
      ]
    }

    response = client.patch(f"/timings/{timing_id}", json=update_data)

    # THEN: Stretch folds are updated correctly
    assert response.status_code == 200
    updated_timing = response.json()

    assert len(updated_timing["stretch_folds"]) == 3
    assert updated_timing["stretch_folds"][0]["fold_number"] == 1
    assert updated_timing["stretch_folds"][2]["fold_number"] == 3

  def test_update_nonexistent_timing(self):
    """Test updating a timing that doesn't exist"""

    # GIVEN: A UUID that doesn't exist
    fake_uuid = "12345678-1234-1234-1234-123456789abc"

    # WHEN: Update is attempted
    update_data = {"recipe_name": "Ghost Bread"}
    response = client.patch(f"/timings/{fake_uuid}", json=update_data)

    # THEN: 404 error is returned
    assert response.status_code == 404

  def test_update_with_validation_errors(self):
    """Test update with validation errors"""

    # GIVEN: An existing timing entry
    timing_data = {"recipe_name": "Valid Bread", "date": "2024-01-23"}

    create_response = client.post("/timings", json=timing_data)
    timing_id = create_response.json()["id"]

    # WHEN: Invalid update data is submitted
    update_data = {
      "temperature_unit": "Kelvin",  # Invalid
      "room_temp": -100.0,  # Out of range
    }

    response = client.patch(f"/timings/{timing_id}", json=update_data)

    # THEN: Validation error is returned
    assert response.status_code == 422


class TestTimingEndpointDeletion:
  """Test timing deletion operations"""

  def test_delete_timing(self):
    """Test deleting a timing entry"""

    # GIVEN: An existing timing entry
    timing_data = {"recipe_name": "Doomed Bread", "date": "2024-01-24"}

    create_response = client.post("/timings", json=timing_data)
    timing_id = create_response.json()["id"]

    # WHEN: Timing is deleted
    response = client.delete(f"/timings/{timing_id}")

    # THEN: Timing is successfully deleted
    assert response.status_code == 204

    # AND: Timing can no longer be retrieved
    get_response = client.get(f"/timings/{timing_id}")
    assert get_response.status_code == 404

  def test_delete_nonexistent_timing(self):
    """Test deleting a timing that doesn't exist"""

    # GIVEN: A UUID that doesn't exist
    fake_uuid = "12345678-1234-1234-1234-123456789abc"

    # WHEN: Deletion is attempted
    response = client.delete(f"/timings/{fake_uuid}")

    # THEN: 404 error is returned
    assert response.status_code == 404


class TestTimingEndpointEdgeCases:
  """Test edge cases and error scenarios"""

  def test_malformed_json(self):
    """Test handling of malformed JSON"""

    # WHEN: Malformed JSON is sent
    response = client.post(
      "/timings",
      data="{'invalid': json}",  # Malformed JSON
      headers={"Content-Type": "application/json"},
    )

    # THEN: 422 validation error is returned
    assert response.status_code == 422

  def test_empty_request_body(self):
    """Test handling of empty request body"""

    # WHEN: Empty JSON is sent
    response = client.post("/timings", json={})

    # THEN: Validation error for missing required fields
    assert response.status_code == 422

  def test_very_long_recipe_name(self):
    """Test validation of recipe name length"""

    # GIVEN: Extremely long recipe name
    long_name = "A" * 300  # Exceeds 255 char limit

    timing_data = {"recipe_name": long_name, "date": "2024-01-25"}

    # WHEN: Timing creation is attempted
    response = client.post("/timings", json=timing_data)

    # THEN: Validation error is returned
    assert response.status_code == 422

  def test_invalid_date_format(self):
    """Test validation of date format"""

    # GIVEN: Invalid date format
    timing_data = {
      "recipe_name": "Bad Date Bread",
      "date": "January 1st, 2024",  # Wrong format
    }

    # WHEN: Timing creation is attempted
    response = client.post("/timings", json=timing_data)

    # THEN: Validation error is returned
    assert response.status_code == 422

  def test_future_date_allowed(self):
    """Test that future dates are allowed for planning purposes"""

    # GIVEN: A future date
    timing_data = {"recipe_name": "Future Bread", "date": "2025-12-31"}

    # WHEN: Timing creation is attempted
    response = client.post("/timings", json=timing_data)

    # THEN: Future dates are accepted
    assert response.status_code == 201
