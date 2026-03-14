-- signal_history
SELECT 
                DATE(created_at) as date,
                signal_type,
                score,
                btc_price,
                fear_index
            FROM signals
            ORDER BY created_at DESC
            LIMIT 1000

-- signal_distribution
SELECT 
                signal_type,
                COUNT(*) as count,
                AVG(score) as avg_score
            FROM signals
            GROUP BY signal_type

-- metrics_over_time
SELECT 
                np.timestamp,
                np.rsi_24h,
                nl.oi_change_pct,
                ns.fear_greed_index
            FROM normalized_prices np
            LEFT JOIN normalized_leverage nl ON np.symbol = nl.symbol
            LEFT JOIN normalized_sentiment ns ON np.timestamp = ns.timestamp
            ORDER BY np.timestamp DESC
            LIMIT 500

-- daily_alerts
SELECT 
                DATE(created_at) as date,
                COUNT(*) as alert_count,
                SUM(CASE WHEN signal_type = 'RISK OFF' THEN 1 ELSE 0 END) as risk_off_count
            FROM signals
            GROUP BY DATE(created_at)
            ORDER BY date DESC

