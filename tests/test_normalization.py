import pytest
from unittest.mock import patch, MagicMock

class TestNormalization:
    def test_compute_cycle_phase_accumulation(self):
        from src.normalization.normalize import Normalizer
        normalizer = Normalizer()
        result = normalizer._compute_cycle_phase(25.0, -10.0)
        assert result == "Accumulation"

    def test_compute_cycle_phase_run_up(self):
        from src.normalization.normalize import Normalizer
        normalizer = Normalizer()
        result = normalizer._compute_cycle_phase(40.0, 2.0)
        assert result == "Run-Up"

    def test_compute_cycle_phase_distribution(self):
        from src.normalization.normalize import Normalizer
        normalizer = Normalizer()
        result = normalizer._compute_cycle_phase(75.0, 10.0)
        assert result == "Distribution"

    def test_compute_cycle_phase_run_down(self):
        from src.normalization.normalize import Normalizer
        normalizer = Normalizer()
        result = normalizer._compute_cycle_phase(55.0, -5.0)
        assert result == "Run-Down"

    def test_compute_cycle_phase_60_rsi(self):
        from src.normalization.normalize import Normalizer
        normalizer = Normalizer()
        result = normalizer._compute_cycle_phase(60.0, 0.0)
        assert result == "Run-Down"


class TestDataIngestion:
    @patch('src.data_ingestion.validate_sync.db')
    def test_validate_airbyte_sync_all_ok(self, mock_db):
        mock_db.table_exists.return_value = True
        mock_db.execute_one.return_value = {"cnt": 100, "last_sync": "2024-01-01"}
        
        from src.data_ingestion.validate_sync import validate_airbyte_sync
        result = validate_airbyte_sync()
        
        assert "raw_coingecko" in result

    @patch('src.data_ingestion.validate_sync.db')
    def test_validate_airbyte_sync_table_missing(self, mock_db):
        mock_db.table_exists.return_value = False
        
        from src.data_ingestion.validate_sync import validate_airbyte_sync
        result = validate_airbyte_sync()
        
        for table in result.values():
            assert table["status"] == "missing"
