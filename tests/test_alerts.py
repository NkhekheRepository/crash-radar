import pytest
from unittest.mock import patch, MagicMock

class TestAlertManager:
    @patch('src.alerts.alerter.config')
    def test_format_message_risk_off(self, mock_config):
        mock_config.alert_score = 5
        from src.alerts.alerter import AlertManager
        manager = AlertManager()
        
        signal = {
            "score": 5,
            "signal_type": "RISK OFF",
            "btc_price": 50000.00,
            "rsi": 25.5,
            "oi_pct": -12.5,
            "fear_index": 20,
            "cycle_phase": "Accumulation",
            "macro_indicator": "improving",
            "regulation_status": "none"
        }
        
        msg = manager._format_message(signal)
        assert "🚨" in msg
        assert "RISK OFF" in msg
        assert "$50,000.00" in msg

    @patch('src.alerts.alerter.config')
    def test_format_message_watch(self, mock_config):
        mock_config.alert_score = 5
        from src.alerts.alerter import AlertManager
        manager = AlertManager()
        
        signal = {
            "score": 3,
            "signal_type": "WATCH",
            "btc_price": 45000.00,
            "rsi": 40.0,
            "oi_pct": 5.0,
            "fear_index": 45,
            "cycle_phase": "Neutral",
            "macro_indicator": "neutral",
            "regulation_status": "low"
        }
        
        msg = manager._format_message(signal)
        assert "⚠️" in msg
        assert "WATCH" in msg

    @patch('src.alerts.alerter.requests.post')
    @patch('src.alerts.alerter.config')
    def test_send_message_success(self, mock_config, mock_post):
        mock_config.telegram_bot_token = "test_token"
        mock_config.telegram_chat_id = "test_chat"
        mock_post.return_value.status_code = 200
        
        from src.alerts.alerter import AlertManager
        manager = AlertManager()
        result = manager.send_message("Test message")
        
        assert result is True
        mock_post.assert_called_once()

    @patch('src.alerts.alerter.requests.post')
    @patch('src.alerts.alerter.config')
    def test_send_message_api_error(self, mock_config, mock_post):
        mock_config.telegram_bot_token = "test_token"
        mock_config.telegram_chat_id = "test_chat"
        mock_post.return_value.status_code = 400
        
        from src.alerts.alerter import AlertManager
        manager = AlertManager()
        result = manager.send_message("Test message")
        
        assert result is False

    @patch('src.alerts.alerter.config')
    def test_check_and_alert_threshold_met(self, mock_config):
        mock_config.alert_score = 5
        from src.alerts.alerter import AlertManager
        manager = AlertManager()
        
        signal = {"score": 5, "signal_type": "RISK OFF"}
        
        with patch.object(manager, 'send_message', return_value=True) as mock_send:
            result = manager.check_and_alert(signal)
            assert result is True
            mock_send.assert_called_once()

    @patch('src.alerts.alerter.config')
    def test_check_and_alert_threshold_not_met(self, mock_config):
        mock_config.alert_score = 5
        from src.alerts.alerter import AlertManager
        manager = AlertManager()
        
        signal = {"score": 3, "signal_type": "WATCH"}
        
        with patch.object(manager, 'send_message', return_value=True) as mock_send:
            result = manager.check_and_alert(signal)
            assert result is False
            mock_send.assert_not_called()
