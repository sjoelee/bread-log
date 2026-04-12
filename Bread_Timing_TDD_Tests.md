# Bread Timing TDD Test Cases

## Overview
Comprehensive test cases for bread timing functionality using Test-Driven Development. Tests cover timing creation, retrieval with pagination, and updates while maintaining data integrity.

## Proposed Data Model

```python
@dataclass
class BreadTiming:
    id: UUID                          # Unique identifier
    recipe_name: str                  # Which bread recipe was used
    date: datetime.date               # Date when bread was made
    created_at: datetime              # When timing record was created
    updated_at: datetime              # When timing was last modified
    
    # Process timestamps (all optional)
    autolyse_ts: Optional[datetime] = None
    mix_ts: Optional[datetime] = None
    bulk_ts: Optional[datetime] = None
    preshape_ts: Optional[datetime] = None
    final_shape_ts: Optional[datetime] = None
    fridge_ts: Optional[datetime] = None
    
    # Temperature data
    room_temp: Optional[float] = None
    water_temp: Optional[float] = None
    flour_temp: Optional[float] = None
    preferment_temp: Optional[float] = None
    dough_temp: Optional[float] = None
    temperature_unit: str = "Fahrenheit"
    
    # Stretch & folds
    stretch_folds: List[StretchFold] = field(default_factory=list)
    
    # Notes
    notes: Optional[str] = None

@dataclass 
class StretchFold:
    fold_number: int
    timestamp: datetime
```

## 1. Bread Timing Creation Tests (POST /bread-timings)

### Test 1.1: Create Minimal Valid Timing
```python
def test_create_minimal_bread_timing():
    """Test creating bread timing with only required fields"""
    
    # GIVEN: Minimal valid timing data
    timing_data = {
        "recipe_name": "sourdough",
        "date": "2026-04-12"
    }
    
    # WHEN: Timing is created
    response = client.post("/bread-timings", json=timing_data)
    
    # THEN: Timing is created successfully
    assert response.status_code == 201
    data = response.json()
    
    # Verify required fields
    assert data["id"] is not None
    assert data["recipe_name"] == "sourdough"
    assert data["date"] == "2026-04-12"
    assert data["created_at"] is not None
    assert data["updated_at"] == data["created_at"]  # Same on creation
    
    # Verify optional fields are None/default
    assert data["autolyse_ts"] is None
    assert data["mix_ts"] is None
    assert data["room_temp"] is None
    assert data["temperature_unit"] == "Fahrenheit"  # Default
    assert data["stretch_folds"] == []
    assert data["notes"] is None
```

### Test 1.2: Create Complete Timing
```python
def test_create_complete_bread_timing():
    """Test creating timing with all fields populated"""
    
    # GIVEN: Complete timing data
    base_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    timing_data = {
        "recipe_name": "baguette",
        "date": "2026-04-12",
        "autolyse_ts": base_time.isoformat(),
        "mix_ts": (base_time + timedelta(hours=1)).isoformat(),
        "bulk_ts": (base_time + timedelta(hours=1, minutes=30)).isoformat(),
        "preshape_ts": (base_time + timedelta(hours=5)).isoformat(),
        "final_shape_ts": (base_time + timedelta(hours=5, minutes=30)).isoformat(),
        "fridge_ts": (base_time + timedelta(hours=6)).isostring(),
        "room_temp": 75.0,
        "water_temp": 80.0,
        "flour_temp": 70.0,
        "preferment_temp": 78.0,
        "dough_temp": 76.0,
        "temperature_unit": "Fahrenheit",
        "stretch_folds": [
            {"fold_number": 1, "timestamp": (base_time + timedelta(hours=2)).isoformat()},
            {"fold_number": 2, "timestamp": (base_time + timedelta(hours=2, minutes=30)).isoformat()},
            {"fold_number": 3, "timestamp": (base_time + timedelta(hours=3)).isoformat()}
        ],
        "notes": "Increased hydration to 80% for softer crumb"
    }
    
    # WHEN: Complete timing is created
    response = client.post("/bread-timings", json=timing_data)
    
    # THEN: All data is persisted correctly
    assert response.status_code == 201
    data = response.json()
    
    # Verify all timestamps
    assert data["autolyse_ts"] == timing_data["autolyse_ts"]
    assert data["mix_ts"] == timing_data["mix_ts"]
    assert data["bulk_ts"] == timing_data["bulk_ts"]
    
    # Verify temperatures
    assert data["room_temp"] == 75.0
    assert data["water_temp"] == 80.0
    assert data["dough_temp"] == 76.0
    
    # Verify stretch folds
    assert len(data["stretch_folds"]) == 3
    assert data["stretch_folds"][0]["fold_number"] == 1
    
    # Verify notes
    assert data["notes"] == "Increased hydration to 80% for softer crumb"
```

### Test 1.3: Validation Error Tests
```python
def test_create_timing_validation_errors():
    """Test validation failures for invalid timing data"""
    
    invalid_cases = [
        # Missing required fields
        ({}, "recipe_name is required"),
        ({"recipe_name": "sourdough"}, "date is required"),
        ({"date": "2026-04-12"}, "recipe_name is required"),
        
        # Invalid field types
        ({"recipe_name": "", "date": "2026-04-12"}, "recipe_name cannot be empty"),
        ({"recipe_name": "sourdough", "date": "invalid-date"}, "date must be valid ISO format"),
        ({"recipe_name": "sourdough", "date": "2026-04-12", "room_temp": "hot"}, "room_temp must be a number"),
        
        # Invalid temperature unit
        ({"recipe_name": "sourdough", "date": "2026-04-12", "temperature_unit": "Kelvin"}, "temperature_unit must be Fahrenheit or Celsius"),
        
        # Invalid timestamp format
        ({"recipe_name": "sourdough", "date": "2026-04-12", "autolyse_ts": "not-a-timestamp"}, "autolyse_ts must be valid ISO datetime"),
        
        # Logical timestamp order violations
        ({
            "recipe_name": "sourdough", 
            "date": "2026-04-12",
            "autolyse_ts": "2026-04-12T10:00:00Z",
            "mix_ts": "2026-04-12T09:00:00Z"  # Before autolyse
        }, "mix_ts cannot be before autolyse_ts"),
        
        # Temperature range violations
        ({"recipe_name": "sourdough", "date": "2026-04-12", "room_temp": -10}, "room_temp must be between 32 and 120 Fahrenheit"),
        ({"recipe_name": "sourdough", "date": "2026-04-12", "room_temp": 200}, "room_temp must be between 32 and 120 Fahrenheit"),
        
        # Invalid stretch folds
        ({
            "recipe_name": "sourdough", 
            "date": "2026-04-12",
            "stretch_folds": [{"fold_number": "one", "timestamp": "2026-04-12T10:00:00Z"}]
        }, "fold_number must be an integer"),
        
        # Stretch fold timestamp before process start
        ({
            "recipe_name": "sourdough",
            "date": "2026-04-12", 
            "autolyse_ts": "2026-04-12T10:00:00Z",
            "stretch_folds": [{"fold_number": 1, "timestamp": "2026-04-12T09:00:00Z"}]
        }, "stretch fold timestamp cannot be before autolyse_ts")
    ]
    
    for invalid_data, expected_error in invalid_cases:
        # WHEN: Invalid data is submitted
        response = client.post("/bread-timings", json=invalid_data)
        
        # THEN: Validation error is returned
        assert response.status_code == 422
        error_response = response.json()
        assert expected_error.lower() in error_response["detail"].lower()
```

### Test 1.4: Business Logic Validation
```python
def test_create_timing_business_logic_validation():
    """Test business logic constraints beyond basic validation"""
    
    # GIVEN: Various business logic violation scenarios
    test_cases = [
        # Future date restriction
        {
            "data": {"recipe_name": "sourdough", "date": (datetime.now() + timedelta(days=1)).date().isoformat()},
            "error": "cannot create timing for future dates"
        },
        
        # Excessive process duration
        {
            "data": {
                "recipe_name": "sourdough",
                "date": "2026-04-12",
                "autolyse_ts": "2026-04-12T08:00:00Z",
                "fridge_ts": "2026-04-15T08:00:00Z"  # 3 days later
            },
            "error": "process duration cannot exceed 48 hours"
        },
        
        # Too many stretch folds
        {
            "data": {
                "recipe_name": "sourdough",
                "date": "2026-04-12",
                "stretch_folds": [{"fold_number": i, "timestamp": f"2026-04-12T{10+i}:00:00Z"} for i in range(1, 11)]  # 10 folds
            },
            "error": "cannot have more than 8 stretch folds"
        }
    ]
    
    for case in test_cases:
        # WHEN: Business logic violating data is submitted
        response = client.post("/bread-timings", json=case["data"])
        
        # THEN: Business logic error is returned
        assert response.status_code == 422
        assert case["error"] in response.json()["detail"].lower()
```

### Test 1.5: Duplicate Detection
```python
def test_create_timing_duplicate_prevention():
    """Test that duplicate timings are handled appropriately"""
    
    # GIVEN: Existing timing
    original_timing = {
        "recipe_name": "sourdough",
        "date": "2026-04-12",
        "autolyse_ts": "2026-04-12T08:00:00Z"
    }
    
    create_response = client.post("/bread-timings", json=original_timing)
    assert create_response.status_code == 201
    
    # WHEN: Attempt to create identical timing
    duplicate_response = client.post("/bread-timings", json=original_timing)
    
    # THEN: System behavior depends on business rules
    # Option A: Allow duplicates with unique IDs
    assert duplicate_response.status_code == 201
    assert duplicate_response.json()["id"] != create_response.json()["id"]
    
    # Option B: Reject duplicates (if this is preferred business rule)
    # assert duplicate_response.status_code == 409
    # assert "timing already exists" in duplicate_response.json()["detail"].lower()
```

### Test 1.6: Timezone Handling
```python
def test_create_timing_timezone_handling():
    """Test that timestamps are properly handled across timezones"""
    
    # GIVEN: Timing data with timezone-aware timestamps
    timing_data = {
        "recipe_name": "sourdough",
        "date": "2026-04-12",
        "autolyse_ts": "2026-04-12T08:00:00-07:00",  # PST
        "mix_ts": "2026-04-12T16:00:00Z"             # UTC (should be 9:00 PST)
    }
    
    # WHEN: Timing is created
    response = client.post("/bread-timings", json=timing_data)
    
    # THEN: Timestamps are normalized and validated
    assert response.status_code == 201
    data = response.json()
    
    # Verify timestamps are stored in UTC
    autolyse_utc = datetime.fromisoformat(data["autolyse_ts"].replace('Z', '+00:00'))
    mix_utc = datetime.fromisoformat(data["mix_ts"].replace('Z', '+00:00'))
    
    # PST (UTC-7) 8:00 AM should equal UTC 3:00 PM
    assert autolyse_utc.hour == 15
    assert mix_utc.hour == 16
    
    # Verify logical ordering is maintained
    assert autolyse_utc < mix_utc

## 2. Bread Timing Retrieval Tests (GET /bread-timings)

### Test 2.1: Get Empty List
```python
def test_get_empty_timing_list():
    """Test retrieval when no timings exist"""
    
    # GIVEN: No existing timings
    # (Clean database)
    
    # WHEN: Timings are requested
    response = client.get("/bread-timings")
    
    # THEN: Empty list with pagination metadata is returned
    assert response.status_code == 200
    data = response.json()
    
    assert data["timings"] == []
    assert data["total_count"] == 0
    assert data["page"] == 1
    assert data["limit"] == 20  # Default limit
    assert data["total_pages"] == 0
    assert data["has_next"] == False
    assert data["has_previous"] == False
```

### Test 2.2: Get Paginated List - First Page
```python
def test_get_timing_list_first_page():
    """Test retrieval of first page of timings"""
    
    # GIVEN: Multiple timings exist
    timings_created = []
    base_date = datetime(2026, 4, 10)
    
    # Create 25 timings across 3 days
    for i in range(25):
        timing_date = base_date + timedelta(days=i % 3)
        timing_data = {
            "recipe_name": f"recipe_{i}",
            "date": timing_date.date().isoformat(),
            "created_at": (base_date + timedelta(hours=i)).isoformat()
        }
        response = client.post("/bread-timings", json=timing_data)
        timings_created.append(response.json())
    
    # WHEN: First page is requested with default pagination
    response = client.get("/bread-timings")
    
    # THEN: First 20 timings are returned, ordered by created_at DESC (newest first)
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["timings"]) == 20
    assert data["total_count"] == 25
    assert data["page"] == 1
    assert data["limit"] == 20
    assert data["total_pages"] == 2
    assert data["has_next"] == True
    assert data["has_previous"] == False
    
    # Verify ordering (newest first)
    created_ats = [timing["created_at"] for timing in data["timings"]]
    assert created_ats == sorted(created_ats, reverse=True)
    
    # First timing should be the most recently created
    assert data["timings"][0]["recipe_name"] == "recipe_24"
```

### Test 2.3: Get Paginated List - Subsequent Pages
```python
def test_get_timing_list_pagination():
    """Test retrieval of different pages with custom limits"""
    
    # GIVEN: 25 existing timings (from previous test setup)
    
    # WHEN: Second page is requested
    response = client.get("/bread-timings?page=2")
    
    # THEN: Remaining 5 timings are returned
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["timings"]) == 5
    assert data["page"] == 2
    assert data["has_next"] == False
    assert data["has_previous"] == True
    
    # WHEN: Custom limit is used
    custom_response = client.get("/bread-timings?limit=10")
    custom_data = custom_response.json()
    
    # THEN: Only 10 items returned
    assert len(custom_data["timings"]) == 10
    assert custom_data["limit"] == 10
    assert custom_data["total_pages"] == 3  # 25 items / 10 per page = 3 pages
    
    # WHEN: Specific page with custom limit
    page_response = client.get("/bread-timings?page=3&limit=10")
    page_data = page_response.json()
    
    assert len(page_data["timings"]) == 5  # Remaining items
    assert page_data["page"] == 3
```

### Test 2.4: Filtering and Search
```python
def test_get_timing_list_filtering():
    """Test filtering timings by various criteria"""
    
    # GIVEN: Timings with different recipes and dates
    test_data = [
        {"recipe_name": "sourdough", "date": "2026-04-10"},
        {"recipe_name": "sourdough", "date": "2026-04-11"},
        {"recipe_name": "baguette", "date": "2026-04-10"},
        {"recipe_name": "ciabatta", "date": "2026-04-12"},
    ]
    
    for timing_data in test_data:
        client.post("/bread-timings", json=timing_data)
    
    test_cases = [
        # Filter by recipe name
        {
            "query": "recipe_name=sourdough",
            "expected_count": 2,
            "description": "filter by recipe name"
        },
        
        # Filter by date
        {
            "query": "date=2026-04-10", 
            "expected_count": 2,
            "description": "filter by specific date"
        },
        
        # Filter by date range
        {
            "query": "date_from=2026-04-10&date_to=2026-04-11",
            "expected_count": 3,
            "description": "filter by date range"
        },
        
        # Combined filters
        {
            "query": "recipe_name=sourdough&date=2026-04-11",
            "expected_count": 1,
            "description": "combine recipe and date filters"
        },
        
        # Search in notes (if notes exist)
        {
            "query": "search=hydration",
            "expected_count": 0,  # None have notes with 'hydration'
            "description": "search in notes field"
        }
    ]
    
    for case in test_cases:
        # WHEN: Filtered request is made
        response = client.get(f"/bread-timings?{case['query']}")
        
        # THEN: Correct filtered results are returned
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == case["expected_count"], f"Failed: {case['description']}"
```

### Test 2.5: Ordering Options
```python
def test_get_timing_list_ordering():
    """Test different ordering options for timing list"""
    
    # GIVEN: Timings with different creation times and dates
    base_time = datetime(2026, 4, 10, 8, 0, 0)
    test_timings = [
        {"recipe_name": "a_first", "date": "2026-04-12", "created_at": (base_time + timedelta(hours=3))},
        {"recipe_name": "b_second", "date": "2026-04-10", "created_at": (base_time + timedelta(hours=1))},
        {"recipe_name": "c_third", "date": "2026-04-11", "created_at": (base_time + timedelta(hours=2))},
    ]
    
    created_ids = []
    for timing_data in test_timings:
        timing_data["created_at"] = timing_data["created_at"].isoformat()
        response = client.post("/bread-timings", json=timing_data)
        created_ids.append(response.json()["id"])
    
    ordering_tests = [
        # Default: created_at descending (newest first)
        {
            "query": "",
            "expected_order": ["a_first", "c_third", "b_second"],
            "field": "recipe_name"
        },
        
        # Created at ascending (oldest first)  
        {
            "query": "order_by=created_at&order_direction=asc",
            "expected_order": ["b_second", "c_third", "a_first"],
            "field": "recipe_name"
        },
        
        # Date descending
        {
            "query": "order_by=date&order_direction=desc", 
            "expected_order": ["a_first", "c_third", "b_second"],
            "field": "recipe_name"
        },
        
        # Date ascending
        {
            "query": "order_by=date&order_direction=asc",
            "expected_order": ["b_second", "c_third", "a_first"], 
            "field": "recipe_name"
        },
        
        # Recipe name alphabetical
        {
            "query": "order_by=recipe_name&order_direction=asc",
            "expected_order": ["a_first", "b_second", "c_third"],
            "field": "recipe_name"
        }
    ]
    
    for test_case in ordering_tests:
        # WHEN: Specific ordering is requested
        url = f"/bread-timings?{test_case['query']}" if test_case['query'] else "/bread-timings"
        response = client.get(url)
        
        # THEN: Results are ordered correctly
        assert response.status_code == 200
        data = response.json()
        
        actual_order = [timing[test_case['field']] for timing in data["timings"]]
        assert actual_order == test_case['expected_order']
```

### Test 2.6: Performance and Edge Cases
```python
def test_get_timing_list_performance():
    """Test performance considerations and edge cases"""
    
    # Test large limit values
    response = client.get("/bread-timings?limit=1000")
    assert response.status_code == 400  # Should reject excessive limits
    assert "limit cannot exceed 100" in response.json()["detail"]
    
    # Test invalid page numbers
    response = client.get("/bread-timings?page=0")
    assert response.status_code == 400
    assert "page must be greater than 0" in response.json()["detail"]
    
    response = client.get("/bread-timings?page=999999")
    assert response.status_code == 200  # Should return empty results gracefully
    data = response.json()
    assert data["timings"] == []
    assert data["page"] == 999999
    
    # Test invalid ordering fields
    response = client.get("/bread-timings?order_by=invalid_field")
    assert response.status_code == 400
    assert "invalid order_by field" in response.json()["detail"]
    
    # Test malformed query parameters
    response = client.get("/bread-timings?limit=not_a_number")
    assert response.status_code == 400
    assert "limit must be an integer" in response.json()["detail"]
```

### Test 2.7: Get Single Timing by ID
```python
def test_get_single_timing_by_id():
    """Test retrieval of specific timing by ID"""
    
    # GIVEN: Existing timing
    timing_data = {
        "recipe_name": "test_recipe", 
        "date": "2026-04-12",
        "autolyse_ts": "2026-04-12T08:00:00Z",
        "notes": "Test timing for retrieval"
    }
    
    create_response = client.post("/bread-timings", json=timing_data)
    timing_id = create_response.json()["id"]
    
    # WHEN: Timing is retrieved by ID
    response = client.get(f"/bread-timings/{timing_id}")
    
    # THEN: Complete timing data is returned
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == timing_id
    assert data["recipe_name"] == "test_recipe"
    assert data["autolyse_ts"] == "2026-04-12T08:00:00Z"
    assert data["notes"] == "Test timing for retrieval"
    
    # Verify timestamps are present
    assert data["created_at"] is not None
    assert data["updated_at"] is not None

def test_get_timing_by_invalid_id():
    """Test 404 response for non-existent timing ID"""
    
    # GIVEN: Non-existent timing ID
    fake_id = "00000000-0000-0000-0000-000000000000"
    
    # WHEN: Timing retrieval is attempted
    response = client.get(f"/bread-timings/{fake_id}")
    
    # THEN: 404 error is returned
    assert response.status_code == 404
    assert "timing not found" in response.json()["detail"].lower()
    assert response.json()["timing_id"] == fake_id

def test_get_timing_invalid_uuid():
    """Test 422 response for invalid UUID format"""
    
    # GIVEN: Invalid UUID format
    invalid_id = "not-a-valid-uuid"
    
    # WHEN: Timing retrieval is attempted
    response = client.get(f"/bread-timings/{invalid_id}")
    
    # THEN: 422 validation error is returned
    assert response.status_code == 422
    assert "invalid uuid format" in response.json()["detail"].lower()
```

## 3. Bread Timing Update Tests (PATCH /bread-timings/{timing_id})

### Test 3.1: Update Basic Fields
```python
def test_update_timing_basic_fields():
    """Test updating basic timing fields while preserving core data"""
    
    # GIVEN: Existing timing
    original_data = {
        "recipe_name": "sourdough",
        "date": "2026-04-12",
        "notes": "Original notes"
    }
    
    create_response = client.post("/bread-timings", json=original_data)
    timing_id = create_response.json()["id"]
    original_created_at = create_response.json()["created_at"]
    original_date = create_response.json()["date"]
    
    # WHEN: Basic fields are updated
    update_data = {
        "recipe_name": "updated_sourdough",
        "notes": "Updated notes with more detail"
    }
    
    response = client.patch(f"/bread-timings/{timing_id}", json=update_data)
    
    # THEN: Fields are updated correctly
    assert response.status_code == 200
    data = response.json()
    
    # Updated fields
    assert data["recipe_name"] == "updated_sourdough"
    assert data["notes"] == "Updated notes with more detail"
    
    # Preserved fields
    assert data["date"] == original_date  # CRITICAL: Date must not change
    assert data["created_at"] == original_created_at  # Creation time preserved
    
    # Updated timestamp
    assert data["updated_at"] != data["created_at"]  # Should be different now
    assert data["updated_at"] > data["created_at"]   # Should be newer
```

### Test 3.2: Update Process Timestamps
```python
def test_update_timing_process_timestamps():
    """Test updating process timing data"""
    
    # GIVEN: Timing with some initial process times
    base_time = datetime(2026, 4, 12, 8, 0, 0)
    original_data = {
        "recipe_name": "baguette",
        "date": "2026-04-12", 
        "autolyse_ts": base_time.isoformat(),
        "mix_ts": (base_time + timedelta(hours=1)).isoformat()
    }
    
    create_response = client.post("/bread-timings", json=original_data)
    timing_id = create_response.json()["id"]
    
    # WHEN: Process times are updated and new ones added
    update_data = {
        "mix_ts": (base_time + timedelta(hours=1, minutes=15)).isoformat(),  # Modified
        "bulk_ts": (base_time + timedelta(hours=2)).isoformat(),             # Added
        "preshape_ts": (base_time + timedelta(hours=6)).isoformat()          # Added
    }
    
    response = client.patch(f"/bread-timings/{timing_id}", json=update_data)
    
    # THEN: Process times are updated correctly
    assert response.status_code == 200
    data = response.json()
    
    # Original autolyse unchanged
    assert data["autolyse_ts"] == base_time.isoformat()
    
    # Updated and new times
    assert data["mix_ts"] == (base_time + timedelta(hours=1, minutes=15)).isoformat()
    assert data["bulk_ts"] == (base_time + timedelta(hours=2)).isoformat()
    assert data["preshape_ts"] == (base_time + timedelta(hours=6)).isoformat()
    
    # Final shape still None
    assert data["final_shape_ts"] is None
```

### Test 3.3: Update Temperature Data
```python
def test_update_timing_temperature_data():
    """Test updating temperature information"""
    
    # GIVEN: Timing with some temperature data
    original_data = {
        "recipe_name": "ciabatta",
        "date": "2026-04-12",
        "room_temp": 72.0,
        "water_temp": 75.0,
        "temperature_unit": "Fahrenheit"
    }
    
    create_response = client.post("/bread-timings", json=original_data)
    timing_id = create_response.json()["id"]
    
    # WHEN: Temperatures are updated with unit conversion
    update_data = {
        "room_temp": 22.0,    # Celsius equivalent of 72F
        "flour_temp": 21.0,   # New temperature
        "dough_temp": 24.0,   # New temperature
        "temperature_unit": "Celsius"  # Unit changed
    }
    
    response = client.patch(f"/bread-timings/{timing_id}", json=update_data)
    
    # THEN: Temperature data is updated
    assert response.status_code == 200
    data = response.json()
    
    assert data["room_temp"] == 22.0
    assert data["flour_temp"] == 21.0
    assert data["dough_temp"] == 24.0
    assert data["temperature_unit"] == "Celsius"
    
    # Water temp preserved from original (not updated)
    assert data["water_temp"] == 75.0  # Original value kept
```

### Test 3.4: Update Stretch Folds
```python
def test_update_timing_stretch_folds():
    """Test updating stretch and fold data"""
    
    # GIVEN: Timing with existing stretch folds
    base_time = datetime(2026, 4, 12, 10, 0, 0)
    original_data = {
        "recipe_name": "sourdough",
        "date": "2026-04-12",
        "stretch_folds": [
            {"fold_number": 1, "timestamp": (base_time + timedelta(hours=1)).isoformat()},
            {"fold_number": 2, "timestamp": (base_time + timedelta(hours=1, minutes=30)).isoformat()}
        ]
    }
    
    create_response = client.post("/bread-timings", json=original_data)
    timing_id = create_response.json()["id"]
    
    # WHEN: Stretch folds are updated (modify existing, add new, implicitly remove one)
    update_data = {
        "stretch_folds": [
            {"fold_number": 1, "timestamp": (base_time + timedelta(hours=1, minutes=5)).isoformat()},  # Modified time
            {"fold_number": 3, "timestamp": (base_time + timedelta(hours=2)).isoformat()},             # New fold
            {"fold_number": 4, "timestamp": (base_time + timedelta(hours=2, minutes=30)).isoformat()}  # New fold
        ]
    }
    
    response = client.patch(f"/bread-timings/{timing_id}", json=update_data)
    
    # THEN: Stretch folds are completely replaced
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["stretch_folds"]) == 3
    
    # Verify updated fold data
    folds_by_number = {fold["fold_number"]: fold for fold in data["stretch_folds"]}
    
    assert 1 in folds_by_number
    assert folds_by_number[1]["timestamp"] == (base_time + timedelta(hours=1, minutes=5)).isoformat()
    
    assert 2 not in folds_by_number  # Removed
    assert 3 in folds_by_number     # Added
    assert 4 in folds_by_number     # Added
```

### Test 3.5: Partial Updates and Null Values
```python
def test_update_timing_partial_and_nulls():
    """Test partial updates and setting fields to null"""
    
    # GIVEN: Timing with full data
    original_data = {
        "recipe_name": "enriched",
        "date": "2026-04-12",
        "autolyse_ts": "2026-04-12T08:00:00Z",
        "mix_ts": "2026-04-12T09:00:00Z",
        "room_temp": 75.0,
        "notes": "Original detailed notes"
    }
    
    create_response = client.post("/bread-timings", json=original_data)
    timing_id = create_response.json()["id"]
    
    test_cases = [
        # Clear specific timestamp
        {
            "update_data": {"mix_ts": None},
            "verify_func": lambda data: data["mix_ts"] is None and data["autolyse_ts"] is not None
        },
        
        # Clear temperature
        {
            "update_data": {"room_temp": None},
            "verify_func": lambda data: data["room_temp"] is None
        },
        
        # Clear notes
        {
            "update_data": {"notes": None},
            "verify_func": lambda data: data["notes"] is None
        },
        
        # Update only one field, leaving others unchanged
        {
            "update_data": {"recipe_name": "updated_enriched"},
            "verify_func": lambda data: data["recipe_name"] == "updated_enriched" and data["autolyse_ts"] is not None
        }
    ]
    
    for i, case in enumerate(test_cases):
        # WHEN: Partial update is applied
        response = client.patch(f"/bread-timings/{timing_id}", json=case["update_data"])
        
        # THEN: Only specified fields are updated
        assert response.status_code == 200
        data = response.json()
        
        # Verify the specific change
        assert case["verify_func"](data), f"Test case {i} failed"
        
        # Date should never change
        assert data["date"] == "2026-04-12"
```

### Test 3.6: Update Validation Tests
```python
def test_update_timing_validation():
    """Test validation during timing updates"""
    
    # GIVEN: Existing timing
    original_data = {"recipe_name": "sourdough", "date": "2026-04-12"}
    create_response = client.post("/bread-timings", json=original_data)
    timing_id = create_response.json()["id"]
    
    invalid_updates = [
        # Cannot change date
        ({"date": "2026-04-13"}, "date cannot be modified"),
        
        # Cannot change created_at
        ({"created_at": "2026-04-12T10:00:00Z"}, "created_at cannot be modified"),
        
        # Cannot change ID
        ({"id": "new-id"}, "id cannot be modified"),
        
        # Invalid recipe name
        ({"recipe_name": ""}, "recipe_name cannot be empty"),
        ({"recipe_name": None}, "recipe_name cannot be null"),
        
        # Invalid temperature values
        ({"room_temp": -50}, "temperature out of valid range"),
        ({"room_temp": 300}, "temperature out of valid range"),
        
        # Invalid timestamp format
        ({"autolyse_ts": "not-a-timestamp"}, "invalid timestamp format"),
        
        # Invalid timestamp ordering
        ({
            "autolyse_ts": "2026-04-12T10:00:00Z",
            "mix_ts": "2026-04-12T09:00:00Z"
        }, "mix_ts cannot be before autolyse_ts"),
        
        # Invalid temperature unit
        ({"temperature_unit": "Kelvin"}, "invalid temperature unit"),
        
        # Invalid stretch fold data
        ({"stretch_folds": [{"fold_number": "one"}]}, "fold_number must be integer")
    ]
    
    for invalid_data, expected_error in invalid_updates:
        # WHEN: Invalid update is attempted
        response = client.patch(f"/bread-timings/{timing_id}", json=invalid_data)
        
        # THEN: Validation error is returned
        assert response.status_code == 422
        assert expected_error.lower() in response.json()["detail"].lower()
```

### Test 3.7: No-Change Detection
```python
def test_update_timing_no_change_detection():
    """Test that submitting identical data doesn't update timestamps"""
    
    # GIVEN: Timing with specific data
    original_data = {
        "recipe_name": "sourdough",
        "date": "2026-04-12", 
        "autolyse_ts": "2026-04-12T08:00:00Z",
        "room_temp": 75.0,
        "notes": "Test notes"
    }
    
    create_response = client.post("/bread-timings", json=original_data)
    timing_id = create_response.json()["id"]
    original_updated_at = create_response.json()["updated_at"]
    
    # WHEN: Identical data is submitted
    identical_update = {
        "recipe_name": "sourdough",  # Same
        "autolyse_ts": "2026-04-12T08:00:00Z",  # Same  
        "room_temp": 75.0,  # Same
        "notes": "Test notes"  # Same
    }
    
    # Wait a moment to ensure timestamp would be different if updated
    import time
    time.sleep(0.1)
    
    response = client.patch(f"/bread-timings/{timing_id}", json=identical_update)
    
    # THEN: No actual update occurs
    assert response.status_code == 200
    data = response.json()
    
    # updated_at should NOT change if no real changes detected
    assert data["updated_at"] == original_updated_at
    
    # All data should remain the same
    assert data["recipe_name"] == "sourdough"
    assert data["autolyse_ts"] == "2026-04-12T08:00:00Z"
    assert data["room_temp"] == 75.0
```

### Test 3.8: Concurrency and Race Conditions
```python
def test_update_timing_concurrency():
    """Test concurrent updates to same timing"""
    
    # GIVEN: Timing that will be updated concurrently
    original_data = {
        "recipe_name": "concurrent_test",
        "date": "2026-04-12",
        "notes": "original"
    }
    
    create_response = client.post("/bread-timings", json=original_data)
    timing_id = create_response.json()["id"]
    
    # WHEN: Multiple concurrent updates are attempted
    import threading
    import time
    
    results = []
    errors = []
    
    def update_timing(update_suffix):
        try:
            update_data = {"notes": f"updated_{update_suffix}"}
            response = client.patch(f"/bread-timings/{timing_id}", json=update_data)
            results.append((update_suffix, response.status_code, response.json()))
        except Exception as e:
            errors.append((update_suffix, str(e)))
    
    # Start 5 concurrent update threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=update_timing, args=(i,))
        threads.append(thread)
        thread.start()
        time.sleep(0.01)  # Small delay to increase chance of conflict
    
    # Wait for all to complete
    for thread in threads:
        thread.join()
    
    # THEN: All updates should succeed (last writer wins)
    assert len(errors) == 0
    assert len(results) == 5
    
    # All should return 200
    for suffix, status_code, data in results:
        assert status_code == 200
    
    # Final state should be consistent
    final_response = client.get(f"/bread-timings/{timing_id}")
    final_data = final_response.json()
    
    # Should have one of the updated notes values
    assert "updated_" in final_data["notes"]
    assert final_data["date"] == "2026-04-12"  # Date preserved
```

### Test 3.9: Update Non-Existent Timing
```python
def test_update_nonexistent_timing():
    """Test updating timing that doesn't exist"""
    
    # GIVEN: Non-existent timing ID
    fake_id = "00000000-0000-0000-0000-000000000000"
    
    # WHEN: Update is attempted
    update_data = {"recipe_name": "updated"}
    response = client.patch(f"/bread-timings/{fake_id}", json=update_data)
    
    # THEN: 404 error is returned
    assert response.status_code == 404
    assert "timing not found" in response.json()["detail"].lower()
    assert response.json()["timing_id"] == fake_id

def test_update_timing_invalid_uuid():
    """Test updating with invalid UUID format"""
    
    # GIVEN: Invalid UUID format
    invalid_id = "not-a-valid-uuid"
    
    # WHEN: Update is attempted
    update_data = {"recipe_name": "updated"}
    response = client.patch(f"/bread-timings/{invalid_id}", json=update_data)
    
    # THEN: 422 validation error is returned
    assert response.status_code == 422
    assert "invalid uuid format" in response.json()["detail"].lower()
```

## Key Design Insights from TDD

### Critical Issues Exposed:
1. **Current API lacks unique IDs** - using date/name/timestamp is brittle
2. **No pagination support** - can't efficiently list large numbers of timings  
3. **Update mechanism is broken** - requiring exact timestamp matching fails
4. **No proper filtering/search** - only date-based retrieval exists
5. **Concurrency not handled** - race conditions will corrupt data

### Recommended Architecture:
1. **UUID-based timing IDs** for reliable CRUD operations
2. **Proper pagination** with offset/limit and total counts
3. **Filtering and search** by recipe, date ranges, notes content
4. **Immutable dates** with separate updated_at timestamps
5. **Optimistic concurrency control** or proper transaction handling
6. **Business logic validation** beyond basic type checking