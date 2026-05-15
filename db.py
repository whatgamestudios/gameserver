import os

import sqlalchemy as sa
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = sa.create_engine(DATABASE_URL, connect_args=_connect_args)

metadata = sa.MetaData()
wordlist = sa.Table(
    "wordlist",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("word", sa.String, unique=True, nullable=False),
)
seedwords = sa.Table(
    "seedwords",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("day", sa.Integer, unique=True, nullable=False),
    sa.Column("word", sa.String, nullable=False),
)
submissions = sa.Table(
    "submissions",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("game_day", sa.Integer, nullable=False),
    sa.Column("score", sa.Integer, nullable=False),
    sa.Column("player", sa.String, nullable=False),
    sa.Column("board", sa.String, nullable=False),
)
player_stats = sa.Table(
    "player_stats",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("player", sa.String, unique=True, nullable=False),
    sa.Column("most_recent_game_day", sa.Integer, nullable=False),
    sa.Column("days_played", sa.Integer, nullable=False),
)
daily_stats = sa.Table(
    "daily_stats",
    metadata,
    sa.Column("game_day", sa.Integer, primary_key=True),
    sa.Column("num_players", sa.Integer, nullable=False, default=0),
    sa.Column("num_sessions", sa.Integer, nullable=False, default=0),
)
_14_player_stats = sa.Table(
    "14_player_stats",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("player", sa.String, unique=True, nullable=False),
    sa.Column("most_recent_game_day", sa.Integer, nullable=False),
    sa.Column("days_played", sa.Integer, nullable=False),
)
_14_daily_stats = sa.Table(
    "14_daily_stats",
    metadata,
    sa.Column("game_day", sa.Integer, primary_key=True),
    sa.Column("num_players", sa.Integer, nullable=False, default=0),
    sa.Column("num_sessions", sa.Integer, nullable=False, default=0),
)
metadata.create_all(engine)
