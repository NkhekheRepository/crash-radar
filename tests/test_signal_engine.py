import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

class TestSignalEngine:
    @patch('src.signal_engine.scorer.db')
    def test_score_price_layer_oversold(self, mock_db):
        from src.signal_engine.scorer import SignalEngine
        engine = SignalEngine()
        result = engine._score_price_layer(25.0)
        assert result == 1
    
    @patch('src.signal_engine.scorer.db')
    def test_score_price_layer_neutral(self, mock_db):
        from src.signal_engine.scorer import SignalEngine
        engine = SignalEngine()
        result = engine._score_price_layer(50.0)
        assert result == 0
    
    def test_score_price_layer_none(self):
        from src.signal_engine.scorer import SignalEngine
        engine = SignalEngine()
        result = engine._score_price_layer(None)
        assert result == 0
    
    @patch('src.signal_engine.scorer.db')
    def test_score_leverage_layer_oi_drop(self, mock_db):
        from src.signal_engine.scorer import SignalEngine
        engine = SignalEngine()
        result = engine._score_leverage_layer(-15.0, 0.001)
        assert result == 1
    
    @patch('src.signal_engine.scorer.db')
    def test_score_leverage_layer_negative_funding(self, mock_db):
        from src.signal_engine.scorer import SignalEngine
        engine = SignalEngine()
        result = engine._score_leverage_layer(5.0, -0.001)
        assert result == 1
    
    def test_score_sentiment_layer_fear(self):
        from src.signal_engine.scorer import SignalEngine
        engine = SignalEngine()
        result = engine._score_sentiment_layer(20)
        assert result == 1
    
    def test_score_sentiment_layer_greed(self):
        from src.signal_engine.scorer import SignalEngine
        engine = SignalEngine()
        result = engine._score_sentiment_layer(70)
        assert result == 0
    
    def test_score_cycle_layer_accumulation(self):
        from src.signal_engine.scorer import SignalEngine
        engine = SignalEngine()
        result = engine._score_cycle_layer("Accumulation")
        assert result == 1
    
    def test_score_cycle_layer_run_up(self):
        from src.signal_engine.scorer import SignalEngine
        engine = SignalEngine()
        result = engine._score_cycle_layer("Run-Up")
        assert result == 1
    
    def test_score_cycle_layer_distribution(self):
        from src.signal_engine.scorer import SignalEngine
        engine = SignalEngine()
        result = engine._score_cycle_layer("Distribution")
        assert result == 0
    
    def test_score_regulation_layer_none(self):
        from src.signal_engine.scorer import SignalEngine
        engine = SignalEngine()
        result = engine._score_regulation_layer("none")
        assert result == 1
    
    def test_score_regulation_layer_high(self):
        from src.signal_engine.scorer import SignalEngine
        engine = SignalEngine()
        result = engine._score_regulation_layer("high")
        assert result == 0
    
    def test_score_macro_layer_improving_cpi(self):
        from src.signal_engine.scorer import SignalEngine
        engine = SignalEngine()
        result = engine._score_macro_layer(3.0, 105.0, 4.0, 100.0)
        assert result == 1
    
    def test_score_macro_layer_declining(self):
        from src.signal_engine.scorer import SignalEngine
        engine = SignalEngine()
        result = engine._score_macro_layer(4.0, 110.0, 3.0, 100.0)
        assert result == 0
