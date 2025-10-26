"""Analytics utilities for querying prediction and user activity data."""
from __future__ import annotations
import sqlite3
from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta
import json
from .db_utils import get_conn


def get_total_users() -> int:
	"""Get total number of registered users."""
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute("SELECT COUNT(*) FROM users")
		return cur.fetchone()[0]


def get_total_predictions() -> int:
	"""Get total number of predictions made."""
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute("SELECT COUNT(*) FROM predictions")
		return cur.fetchone()[0]


def get_predictions_by_class() -> Dict[str, int]:
	"""Get count of predictions per class."""
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
			SELECT predicted_label, COUNT(*) as count 
			FROM predictions 
			GROUP BY predicted_label
			ORDER BY count DESC
			"""
		)
		return {row[0]: row[1] for row in cur.fetchall()}


def get_daily_predictions(days: int = 30) -> List[Tuple[str, int]]:
	"""Get prediction counts per day for the last N days.
	
	Returns list of (date, count) tuples.
	"""
	cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
			SELECT DATE(created_at) as date, COUNT(*) as count
			FROM predictions
			WHERE created_at >= ?
			GROUP BY DATE(created_at)
			ORDER BY date ASC
			""",
			(cutoff,),
		)
		return cur.fetchall()


def get_average_confidence() -> float:
	"""Get average confidence score across all predictions."""
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute("SELECT AVG(confidence) FROM predictions")
		result = cur.fetchone()[0]
		return result if result is not None else 0.0


def get_confidence_by_class() -> Dict[str, float]:
	"""Get average confidence score per class."""
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
			SELECT predicted_label, AVG(confidence) as avg_conf
			FROM predictions
			GROUP BY predicted_label
			"""
		)
		return {row[0]: row[1] for row in cur.fetchall()}


def get_low_confidence_predictions(threshold: float = 0.7, limit: int = 20) -> List[Dict[str, Any]]:
	"""Get predictions with confidence below threshold (potential review cases).
	
	Returns list of prediction dicts with relevant fields.
	"""
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
			SELECT id, filename, predicted_label, confidence, user, created_at
			FROM predictions
			WHERE confidence < ?
			ORDER BY confidence ASC, created_at DESC
			LIMIT ?
			""",
			(threshold, limit),
		)
		rows = cur.fetchall()
		return [
			{
				"id": r[0],
				"filename": r[1],
				"predicted_label": r[2],
				"confidence": r[3],
				"user": r[4],
				"created_at": r[5],
			}
			for r in rows
		]


def get_active_users(days: int = 7) -> List[Tuple[str, int]]:
	"""Get most active users in the last N days.
	
	Returns list of (username, prediction_count) tuples.
	"""
	cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
			SELECT user, COUNT(*) as count
			FROM predictions
			WHERE created_at >= ? AND user IS NOT NULL
			GROUP BY user
			ORDER BY count DESC
			LIMIT 10
			""",
			(cutoff,),
		)
		return cur.fetchall()


def get_predictions_per_hour() -> Dict[int, int]:
	"""Get prediction count distribution by hour of day (0-23).
	
	Useful for identifying peak usage times.
	"""
	with get_conn() as conn:
		cur = conn.cursor()
		# SQLite strftime '%H' returns hour as string, cast to int
		cur.execute(
			"""
			SELECT CAST(strftime('%H', created_at) AS INTEGER) as hour, COUNT(*) as count
			FROM predictions
			GROUP BY hour
			ORDER BY hour
			"""
		)
		return {row[0]: row[1] for row in cur.fetchall()}


def get_recent_predictions_full(limit: int = 10) -> List[Dict[str, Any]]:
	"""Get recent predictions with full details including probabilities.
	
	Returns list of dicts with all prediction fields.
	"""
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
			SELECT id, filename, predicted_label, confidence, user, created_at, 
			       model_version, probabilities, patient_id, processing_time_ms
			FROM predictions
			ORDER BY created_at DESC
			LIMIT ?
			""",
			(limit,),
		)
		rows = cur.fetchall()
		results = []
		for r in rows:
			prob_dict = None
			if r[7]:  # probabilities column
				try:
					prob_dict = json.loads(r[7])
				except:
					pass
			results.append({
				"id": r[0],
				"filename": r[1],
				"predicted_label": r[2],
				"confidence": r[3],
				"user": r[4],
				"created_at": r[5],
				"model_version": r[6],
				"probabilities": prob_dict,
				"patient_id": r[8],
				"processing_time_ms": r[9],
			})
		return results


def get_class_distribution_over_time(days: int = 30) -> Dict[str, List[Tuple[str, int]]]:
	"""Get daily counts per class for the last N days.
	
	Returns dict of {class_name: [(date, count), ...]}
	"""
	cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
			SELECT predicted_label, DATE(created_at) as date, COUNT(*) as count
			FROM predictions
			WHERE created_at >= ?
			GROUP BY predicted_label, DATE(created_at)
			ORDER BY date ASC
			""",
			(cutoff,),
		)
		rows = cur.fetchall()
		
		# Organize by class
		result = {}
		for row in rows:
			class_name = row[0]
			if class_name not in result:
				result[class_name] = []
			result[class_name].append((row[1], row[2]))
		return result


def get_model_performance_summary() -> Dict[str, Any]:
	"""Get comprehensive model performance metrics.
	
	Returns dict with various aggregate metrics.
	"""
	with get_conn() as conn:
		cur = conn.cursor()
		
		# Get overall stats
		cur.execute("SELECT COUNT(*), AVG(confidence), MIN(confidence), MAX(confidence) FROM predictions")
		total, avg_conf, min_conf, max_conf = cur.fetchone()
		
		# Get class counts
		cur.execute(
			"""
			SELECT predicted_label, COUNT(*) as count
			FROM predictions
			GROUP BY predicted_label
			"""
		)
		class_counts = {row[0]: row[1] for row in cur.fetchall()}
		
		# Get average processing time
		cur.execute("SELECT AVG(processing_time_ms) FROM predictions WHERE processing_time_ms IS NOT NULL")
		avg_time = cur.fetchone()[0]
		
		return {
			"total_predictions": total if total else 0,
			"average_confidence": avg_conf if avg_conf else 0.0,
			"min_confidence": min_conf if min_conf else 0.0,
			"max_confidence": max_conf if max_conf else 0.0,
			"class_distribution": class_counts,
			"average_processing_time_ms": avg_time if avg_time else 0,
		}


# ============================================
# USER-SPECIFIC ANALYTICS FUNCTIONS
# ============================================

def get_user_total_predictions(username: str) -> int:
	"""Get total number of predictions made by a specific user."""
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute("SELECT COUNT(*) FROM predictions WHERE user = ?", (username,))
		return cur.fetchone()[0]


def get_user_predictions_by_class(username: str) -> Dict[str, int]:
	"""Get count of predictions per class for a specific user."""
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
			SELECT predicted_label, COUNT(*) as count 
			FROM predictions 
			WHERE user = ?
			GROUP BY predicted_label
			ORDER BY count DESC
			""",
			(username,)
		)
		return {row[0]: row[1] for row in cur.fetchall()}


def get_user_daily_predictions(username: str, days: int = 30) -> List[Tuple[str, int]]:
	"""Get prediction counts per day for a specific user over the last N days.
	
	Returns list of (date, count) tuples.
	"""
	cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
			SELECT DATE(created_at) as date, COUNT(*) as count
			FROM predictions
			WHERE user = ? AND created_at >= ?
			GROUP BY DATE(created_at)
			ORDER BY date ASC
			""",
			(username, cutoff),
		)
		return cur.fetchall()


def get_user_average_confidence(username: str) -> float:
	"""Get average confidence score for a specific user's predictions."""
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute("SELECT AVG(confidence) FROM predictions WHERE user = ?", (username,))
		result = cur.fetchone()[0]
		return result if result is not None else 0.0


def get_user_recent_predictions(username: str, limit: int = 10) -> List[Dict[str, Any]]:
	"""Get recent predictions for a specific user with full details.
	
	Returns list of dicts with all prediction fields.
	"""
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
			SELECT id, filename, predicted_label, confidence, created_at, 
			       model_version, probabilities, patient_id, processing_time_ms
			FROM predictions
			WHERE user = ?
			ORDER BY created_at DESC
			LIMIT ?
			""",
			(username, limit),
		)
		rows = cur.fetchall()
		results = []
		for r in rows:
			prob_dict = None
			if r[6]:  # probabilities column
				try:
					prob_dict = json.loads(r[6])
				except:
					pass
			results.append({
				"id": r[0],
				"filename": r[1],
				"predicted_label": r[2],
				"confidence": r[3],
				"created_at": r[4],
				"model_version": r[5],
				"probabilities": prob_dict,
				"patient_id": r[7],
				"processing_time_ms": r[8],
			})
		return results


def get_user_activity_stats(username: str) -> Dict[str, Any]:
	"""Get activity statistics for a specific user.
	
	Returns dict with login count, prediction count, PDF downloads, etc.
	"""
	with get_conn() as conn:
		cur = conn.cursor()
		
		# Get activity counts by type
		cur.execute(
			"""
			SELECT activity_type, COUNT(*) as count
			FROM user_activity
			WHERE username = ?
			GROUP BY activity_type
			""",
			(username,)
		)
		activity_counts = {row[0]: row[1] for row in cur.fetchall()}
		
		# Get first and last activity dates
		cur.execute(
			"""
			SELECT MIN(timestamp), MAX(timestamp)
			FROM user_activity
			WHERE username = ?
			""",
			(username,)
		)
		first_activity, last_activity = cur.fetchone()
		
		# Get user registration date
		cur.execute(
			"SELECT created_at FROM users WHERE username = ?",
			(username,)
		)
		registered_at = cur.fetchone()
		
		return {
			"activity_counts": activity_counts,
			"first_activity": first_activity,
			"last_activity": last_activity,
			"registered_at": registered_at[0] if registered_at else None,
			"total_logins": activity_counts.get("login", 0),
			"total_predictions": activity_counts.get("prediction", 0),
			"total_pdf_downloads": activity_counts.get("pdf_download", 0),
		}


def get_user_confidence_trend(username: str, days: int = 30) -> List[Tuple[str, float]]:
	"""Get average confidence score per day for a specific user.
	
	Returns list of (date, avg_confidence) tuples.
	"""
	cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
			SELECT DATE(created_at) as date, AVG(confidence) as avg_conf
			FROM predictions
			WHERE user = ? AND created_at >= ?
			GROUP BY DATE(created_at)
			ORDER BY date ASC
			""",
			(username, cutoff),
		)
		return cur.fetchall()

# ===================================
# ADDITIONAL ADMIN ANALYTICS FUNCTIONS
# ===================================

def get_active_users_count(days: int = 7) -> int:
    """Get count of active users in the last N days"""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(DISTINCT user) 
            FROM predictions 
            WHERE created_at >= ?
            """,
            (cutoff,),
        )
        result = cur.fetchone()
        return result[0] if result else 0


def get_new_users_count(days: int = 30) -> int:
    """Get count of new users registered in the last N days"""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) 
            FROM users 
            WHERE created_at >= ?
            """,
            (cutoff,),
        )
        result = cur.fetchone()
        return result[0] if result else 0


def get_predictions_today() -> int:
    """Get count of predictions made today"""
    today = datetime.now().date().isoformat()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) 
            FROM predictions 
            WHERE DATE(created_at) = ?
            """,
            (today,),
        )
        result = cur.fetchone()
        return result[0] if result else 0


def get_predictions_this_week() -> int:
    """Get count of predictions made this week"""
    preds = get_daily_predictions(days=7)
    return sum(count for _, count in preds)


def get_predictions_this_month() -> int:
    """Get count of predictions made this month"""
    preds = get_daily_predictions(days=30)
    return sum(count for _, count in preds)


def get_class_distribution() -> List[Dict[str, Any]]:
    """Get distribution of predictions by class"""
    predictions_by_class = get_predictions_by_class()
    return [
        {"label": label, "count": count}
        for label, count in predictions_by_class.items()
    ]


def get_most_active_users(limit: int = 10) -> List[Tuple[str, int]]:
    """Get the most active users by prediction count"""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT user, COUNT(*) as count
            FROM predictions
            GROUP BY user
            ORDER BY count DESC
            LIMIT ?
            """,
            (limit,),
        )
        return cur.fetchall()


def get_confidence_distribution() -> List[Dict[str, Any]]:
    """Get distribution of predictions by confidence ranges"""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 
                CASE 
                    WHEN confidence < 0.5 THEN '0-50%'
                    WHEN confidence < 0.7 THEN '50-70%'
                    WHEN confidence < 0.8 THEN '70-80%'
                    WHEN confidence < 0.9 THEN '80-90%'
                    ELSE '90-100%'
                END as range,
                COUNT(*) as count
            FROM predictions
            WHERE confidence IS NOT NULL
            GROUP BY range
            ORDER BY range
            """
        )
        results = cur.fetchall()
        return [{"range": r[0], "count": r[1]} for r in results]


def get_recent_predictions(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent predictions (system-wide)"""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 
                filename,
                predicted_label,
                confidence,
                user,
                created_at
            FROM predictions
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
        return [dict(row) for row in rows]


# ===================================
# FEEDBACK & GROUND TRUTH ANALYTICS
# ===================================

def get_feedback_stats() -> Dict[str, int]:
    """Get overall feedback statistics."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 
                feedback_type,
                COUNT(*) as count
            FROM prediction_feedback
            GROUP BY feedback_type
            """
        )
        results = cur.fetchall()
        stats = {row[0]: row[1] for row in results}
        
        # Get total feedback count
        cur.execute("SELECT COUNT(*) FROM prediction_feedback")
        stats['total'] = cur.fetchone()[0]
        
        return stats


def get_model_accuracy_with_feedback() -> Dict[str, Any]:
    """Calculate model accuracy based on user feedback."""
    with get_conn() as conn:
        cur = conn.cursor()
        
        # Get predictions with feedback
        cur.execute(
            """
            SELECT 
                p.predicted_label,
                f.feedback_type,
                f.actual_label
            FROM predictions p
            INNER JOIN prediction_feedback f ON p.id = f.prediction_id
            WHERE f.feedback_type IN ('correct', 'incorrect')
            """
        )
        results = cur.fetchall()
        
        if not results:
            return {
                'total_reviewed': 0,
                'correct_count': 0,
                'incorrect_count': 0,
                'accuracy': 0.0,
                'sample_size': 0
            }
        
        correct = sum(1 for r in results if r[1] == 'correct')
        incorrect = sum(1 for r in results if r[1] == 'incorrect')
        total = len(results)
        
        return {
            'total_reviewed': total,
            'correct_count': correct,
            'incorrect_count': incorrect,
            'accuracy': (correct / total * 100) if total > 0 else 0.0,
            'sample_size': total
        }


def get_feedback_by_class() -> List[Dict[str, Any]]:
    """Get accuracy breakdown by predicted class."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 
                p.predicted_label,
                SUM(CASE WHEN f.feedback_type = 'correct' THEN 1 ELSE 0 END) as correct,
                SUM(CASE WHEN f.feedback_type = 'incorrect' THEN 1 ELSE 0 END) as incorrect,
                COUNT(*) as total
            FROM predictions p
            INNER JOIN prediction_feedback f ON p.id = f.prediction_id
            WHERE f.feedback_type IN ('correct', 'incorrect')
            GROUP BY p.predicted_label
            """
        )
        results = cur.fetchall()
        
        return [
            {
                'class': row[0],
                'correct': row[1],
                'incorrect': row[2],
                'total': row[3],
                'accuracy': (row[1] / row[3] * 100) if row[3] > 0 else 0.0
            }
            for row in results
        ]


def get_flagged_predictions(limit: int = 20) -> List[Dict[str, Any]]:
    """Get predictions flagged as incorrect or uncertain."""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 
                p.id,
                p.filename,
                p.predicted_label,
                p.confidence,
                p.user,
                p.created_at,
                f.feedback_type,
                f.actual_label,
                f.notes,
                f.created_at as feedback_date
            FROM predictions p
            INNER JOIN prediction_feedback f ON p.id = f.prediction_id
            WHERE f.feedback_type IN ('incorrect', 'uncertain')
            ORDER BY f.created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
        return [dict(row) for row in rows]


def get_user_feedback_history(username: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get feedback submitted by a specific user."""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 
                f.id,
                f.prediction_id,
                f.feedback_type,
                f.actual_label,
                f.notes,
                f.created_at,
                p.filename,
                p.predicted_label,
                p.confidence
            FROM prediction_feedback f
            INNER JOIN predictions p ON f.prediction_id = p.id
            WHERE f.user = ?
            ORDER BY f.created_at DESC
            LIMIT ?
            """,
            (username, limit),
        )
        rows = cur.fetchall()
        return [dict(row) for row in rows]


def get_user_feedback_stats(username: str) -> Dict[str, Any]:
    """Get feedback statistics for a specific user."""
    with get_conn() as conn:
        cur = conn.cursor()
        
        # Total feedback submitted
        cur.execute(
            "SELECT COUNT(*) FROM prediction_feedback WHERE user = ?",
            (username,)
        )
        total = cur.fetchone()[0]
        
        # Breakdown by type
        cur.execute(
            """
            SELECT feedback_type, COUNT(*) 
            FROM prediction_feedback 
            WHERE user = ? 
            GROUP BY feedback_type
            """,
            (username,)
        )
        breakdown = {row[0]: row[1] for row in cur.fetchall()}
        
        # Agreement rate (correct feedback)
        correct = breakdown.get('correct', 0)
        agreement_rate = (correct / total * 100) if total > 0 else 0.0
        
        return {
            'total_feedback': total,
            'correct': breakdown.get('correct', 0),
            'incorrect': breakdown.get('incorrect', 0),
            'uncertain': breakdown.get('uncertain', 0),
            'agreement_rate': agreement_rate
        }


def get_feedback_trend(days: int = 30) -> List[Tuple[str, int]]:
    """Get daily feedback submission trend."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM prediction_feedback
            WHERE created_at >= ?
            GROUP BY DATE(created_at)
            ORDER BY date ASC
            """,
            (cutoff,),
        )
        return cur.fetchall()


def get_low_confidence_predictions(threshold: float = 0.7, limit: int = 50) -> List[Dict[str, Any]]:
    """Get predictions below confidence threshold (for quality review)."""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 
                p.id,
                p.filename,
                p.predicted_label,
                p.confidence,
                p.user,
                p.created_at,
                f.feedback_type
            FROM predictions p
            LEFT JOIN prediction_feedback f ON p.id = f.prediction_id
            WHERE p.confidence < ?
            ORDER BY p.confidence ASC, p.created_at DESC
            LIMIT ?
            """,
            (threshold, limit),
        )
        rows = cur.fetchall()
        return [dict(row) for row in rows]
