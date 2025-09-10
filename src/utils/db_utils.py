from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from typing import Iterator, Any, Tuple, List, Optional, Dict
import json
import bcrypt

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
	}
	for col, coltype in wanted.items():
		if col not in cols:
			cur.execute(f"ALTER TABLE predictions ADD COLUMN {col} {coltype}")


def _hash_password(password: str) -> bytes:
	return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


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
) -> int:
	"""Insert a prediction row and return its id.

	probabilities will be JSON-serialized if provided.
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
