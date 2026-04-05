# Test Scripts

This directory contains test scripts for validating EA Tutorial Hub functionality.

## Test Scripts

### test_veto_system.py
**Purpose**: Test the simplified VETO system functionality

**What it tests**:
- System initialization
- Balance queries
- VETO usage and deduction
- VETO restoration
- Transaction logging
- Top holders ranking
- System status reporting

**Usage**:
```bash
python -m pytest tests/test_veto_system.py
# Or directly:
python tests/test_veto_system.py
```

**Expected Output**:
- ✓ System initialization test
- ✓ Balance query test
- ✓ VETO usage test
- ✓ Transaction history test
- ✓ Top holders test

---

### test_attendance_sync.py
**Purpose**: Test attendance synchronization between systems

**What it tests**:
- Attendance data loading
- Sync operations
- Data consistency
- Error handling

**Usage**:
```bash
python tests/test_attendance_sync.py
```

---

### test_calculation.py
**Purpose**: Test scoring and calculation logic

**What it tests**:
- Point calculations
- Star calculations
- VETO deductions
- Net score calculations
- Ranking algorithms

**Usage**:
```bash
python tests/test_calculation.py
```

---

### test_voting.py
**Purpose**: Test voting and election logic

**What it tests**:
- Vote counting
- Election results
- Post allocation
- VETO quota assignment
- Role transitions

**Usage**:
```bash
python tests/test_voting.py
```

---

## Running Tests

### Run All Tests
```bash
# Using pytest
pytest tests/

# Or run individually
python tests/test_veto_system.py
python tests/test_attendance_sync.py
python tests/test_calculation.py
python tests/test_voting.py
```

### Run Specific Test
```bash
pytest tests/test_veto_system.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

## Test Dependencies

- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
- Flask test client
- Standard Python libraries

## Test Data

Tests use mock data from:
- `instance/offline_scoreboard_data.json` (if available)
- Generated test fixtures
- Mock objects

## Best Practices

1. **Run before deployment**: Always run tests before pushing changes
2. **Test in isolation**: Each test should be independent
3. **Use fixtures**: Create reusable test data
4. **Mock external calls**: Don't depend on external systems
5. **Clear assertions**: Make test failures obvious

## Adding New Tests

### Test Template
```python
#!/usr/bin/env python3
"""
Test: <Feature being tested>
"""
import unittest
from pathlib import Path

class TestFeature(unittest.TestCase):
    """Tests for <feature>"""
    
    def setUp(self):
        """Set up test fixtures"""
        pass
    
    def tearDown(self):
        """Clean up after tests"""
        pass
    
    def test_feature_basic(self):
        """Test basic functionality"""
        # Arrange
        # Act
        # Assert
        pass
    
    def test_feature_edge_case(self):
        """Test edge cases"""
        pass

if __name__ == '__main__':
    unittest.main()
```

### Naming Conventions
- Test files: `test_<feature>.py`
- Test classes: `Test<Feature>`
- Test methods: `test_<specific_behavior>`

## Continuous Integration

Tests should be run:
- On every commit (pre-commit hook)
- Before pull requests
- On deployment
- Nightly for comprehensive testing

## Troubleshooting

### Test Fails: "No module named 'app'"
- Ensure you're running from project root
- Check Python path includes project directory

### Test Fails: "No such file or directory"
- Verify test data files exist
- Check file paths are relative to project root

### Test Hangs
- Check for infinite loops
- Verify mock objects are set up correctly
- Add timeouts to long-running tests

## Test Coverage Goals

Target coverage by module:
- `app/models/` - 90%+
- `app/routes/` - 85%+
- `app/utils/` - 95%+
- `scripts/` - 80%+

## Running Tests in CI/CD

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov=app
```

## Test Results

Keep track of test results:
- ✅ All tests passing
- ⚠️ Some tests failing
- ❌ Critical tests failing

Document any known failures and their status.
