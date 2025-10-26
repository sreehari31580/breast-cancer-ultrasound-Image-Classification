from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from typing import Iterator, Any, Tuple, List, Optional, Dict
import json
import bcrypt
import re

DB_PATH = "cancer_app.db"


@contextmanager
def get_conn(db_path: str = DB_PATH) -> Iterator[sqlite3.Connection]:
	conn = sqlite3.connect(db_path)
	try:
		yield conn
	finally:
		conn.commit()
		conn.close()


def init_db():
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS predictions (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				filename TEXT,
				predicted_label TEXT,
				confidence REAL,
				user TEXT,
				created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
			)
			"""
		)
		# Create user_activity table for analytics
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS user_activity (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				username TEXT,
				activity_type TEXT,
				timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
			)
			"""
		)
		# Create prediction_feedback table for ground truth collection
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS prediction_feedback (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				prediction_id INTEGER NOT NULL,
				user TEXT NOT NULL,
				feedback_type TEXT NOT NULL,
				actual_label TEXT,
				notes TEXT,
				created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				FOREIGN KEY (prediction_id) REFERENCES predictions(id)
			)
			"""
		)
		# Ensure new columns exist for extended metadata while connection is open
		_ensure_prediction_columns(cur)


def ensure_user_table():
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS users (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				username TEXT UNIQUE,
				password_hash BLOB,
				created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
			)
			"""
		)

def _ensure_prediction_columns(cur: sqlite3.Cursor) -> None:
	cur.execute("PRAGMA table_info(predictions)")
	cols = {row[1] for row in cur.fetchall()}
	# Optional metadata columns
	wanted: Dict[str, str] = {
		"model_version": "TEXT",
		"report_path": "TEXT",
		"probabilities": "TEXT",  # JSON-serialized dict of class->prob
		"patient_id": "TEXT",
		"confidence_score": "REAL",  # Max probability (redundant with confidence but explicit)
		"processing_time_ms": "INTEGER",  # Time taken for inference
	}
	for col, coltype in wanted.items():
		if col not in cols:
			cur.execute(f"ALTER TABLE predictions ADD COLUMN {col} {coltype}")


def _hash_password(password: str) -> bytes:
	return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def validate_password(password: str) -> Tuple[bool, str]:
	"""Validate password strength and return (is_valid, message).
	
	Requirements:
	- Minimum 8 characters
	- At least 1 uppercase letter
	- At least 1 lowercase letter
	- At least 1 number
	- At least 1 special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
	
	Returns:
		Tuple[bool, str]: (is_valid, error_message or success_message)
	"""
	if len(password) < 8:
		return False, "❌ Password must be at least 8 characters long"
	
	if len(password) > 128:
		return False, "❌ Password must be less than 128 characters"
	
	if not re.search(r"[A-Z]", password):
		return False, "❌ Password must contain at least 1 uppercase letter"
	
	if not re.search(r"[a-z]", password):
		return False, "❌ Password must contain at least 1 lowercase letter"
	
	if not re.search(r"\d", password):
		return False, "❌ Password must contain at least 1 number"
	
	if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password):
		return False, "❌ Password must contain at least 1 special character (!@#$%^&*...)"
	
	# Check for common weak passwords
	common_passwords = [
		"password", "12345678", "qwerty", "abc123", "password1",
		"admin123", "welcome1", "letmein", "monkey", "1234567890"
	]
	if password.lower() in common_passwords:
		return False, "❌ This password is too common. Please choose a stronger password"
	
	return True, "✅ Strong password!"


def get_password_strength(password: str) -> str:
	"""Return password strength level: 'Weak', 'Medium', or 'Strong'.
	
	Used for visual feedback in UI.
	"""
	if len(password) < 8:
		return "Weak"
	
	strength_score = 0
	
	# Length bonus
	if len(password) >= 12:
		strength_score += 2
	elif len(password) >= 10:
		strength_score += 1
	
	# Character diversity
	if re.search(r"[A-Z]", password):
		strength_score += 1
	if re.search(r"[a-z]", password):
		strength_score += 1
	if re.search(r"\d", password):
		strength_score += 1
	if re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password):
		strength_score += 1
	
	# Multiple character types
	char_types = sum([
		bool(re.search(r"[A-Z]", password)),
		bool(re.search(r"[a-z]", password)),
		bool(re.search(r"\d", password)),
		bool(re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password))
	])
	
	if char_types >= 4:
		strength_score += 2
	elif char_types >= 3:
		strength_score += 1
	
	# Determine strength level
	if strength_score >= 7:
		return "Strong"
	elif strength_score >= 4:
		return "Medium"
	else:
		return "Weak"


def create_user(username: str, password: str) -> bool:
	try:
		with get_conn() as conn:
			cur = conn.cursor()
			cur.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, _hash_password(password)))
		return True
	except sqlite3.IntegrityError:
		return False


def authenticate_user(username: str, password: str) -> bool:
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
		row = cur.fetchone()
		if not row:
			return False
		stored = row[0]
		try:
			return bcrypt.checkpw(password.encode("utf-8"), stored)
		except Exception:
			return False


def log_prediction(
	filename: str,
	predicted_label: str,
	confidence: float,
	user: Optional[str] = None,
	*,
	model_version: Optional[str] = None,
	probabilities: Optional[Dict[str, float]] = None,
	patient_id: Optional[str] = None,
	processing_time_ms: Optional[int] = None,
) -> int:
	"""Insert a prediction row and return its id.

	probabilities will be JSON-serialized if provided.
	processing_time_ms: Time taken for inference in milliseconds.
	"""
	with get_conn() as conn:
		cur = conn.cursor()
		# Make sure columns exist
		_ensure_prediction_columns(cur)
		cols = ["filename", "predicted_label", "confidence", "user"]
		vals = [filename, predicted_label, confidence, user]
		if model_version is not None:
			cols.append("model_version"); vals.append(model_version)
		if probabilities is not None:
			cols.append("probabilities"); vals.append(json.dumps(probabilities))
		if patient_id is not None:
			cols.append("patient_id"); vals.append(patient_id)
		if processing_time_ms is not None:
			cols.append("processing_time_ms"); vals.append(processing_time_ms)
		# Store confidence_score explicitly
		cols.append("confidence_score"); vals.append(confidence)
		placeholders = ", ".join(["?"] * len(vals))
		sql = f"INSERT INTO predictions ({', '.join(cols)}) VALUES ({placeholders})"
		cur.execute(sql, tuple(vals))
		return cur.lastrowid


def fetch_predictions(limit: int = 50) -> List[Tuple[Any, ...]]:
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute(
			"SELECT id, filename, predicted_label, confidence, user, created_at, model_version, report_path FROM predictions ORDER BY id DESC LIMIT ?",
			(limit,),
		)
		rows = cur.fetchall()
	return rows


def update_prediction_report_path(prediction_id: int, report_path: str) -> None:
	with get_conn() as conn:
		cur = conn.cursor()
		_ensure_prediction_columns(cur)
		cur.execute(
			"UPDATE predictions SET report_path = ? WHERE id = ?",
			(report_path, prediction_id),
		)


def log_user_activity(username: str, activity_type: str) -> None:
	"""Log user activity for analytics tracking.
	
	activity_type examples: 'login', 'logout', 'prediction', 'pdf_download'
	"""
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute(
			"INSERT INTO user_activity (username, activity_type) VALUES (?, ?)",
			(username, activity_type),
		)


def submit_prediction_feedback(
	prediction_id: int,
	user: str,
	feedback_type: str,
	actual_label: Optional[str] = None,
	notes: Optional[str] = None,
) -> int:
	"""Submit feedback for a prediction.
	
	Args:
		prediction_id: ID of the prediction being reviewed
		user: Username submitting feedback
		feedback_type: One of 'correct', 'incorrect', 'uncertain'
		actual_label: The actual/correct label (if known)
		notes: Optional notes about the feedback
		
	Returns:
		ID of the inserted feedback record
	"""
	with get_conn() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
			INSERT INTO prediction_feedback 
			(prediction_id, user, feedback_type, actual_label, notes) 
			VALUES (?, ?, ?, ?, ?)
			""",
			(prediction_id, user, feedback_type, actual_label, notes),
		)
		return cur.lastrowid


def get_prediction_feedback(prediction_id: int) -> Optional[Dict[str, Any]]:
	"""Get feedback for a specific prediction (if exists)."""
	with get_conn() as conn:
		conn.row_factory = sqlite3.Row
		cur = conn.cursor()
		cur.execute(
			"""
			SELECT id, prediction_id, user, feedback_type, actual_label, notes, created_at
			FROM prediction_feedback
			WHERE prediction_id = ?
			ORDER BY created_at DESC
			LIMIT 1
			""",
			(prediction_id,),
		)
		row = cur.fetchone()
		return dict(row) if row else None
