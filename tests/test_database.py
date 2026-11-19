"""The Database wrapper: transactions, idempotent init and the shared instance."""

import pytest

from syncfit_database import Database, User
from syncfit_database.database import get_database


def make_db(tmp_path):
    db = Database(f"sqlite:///{tmp_path}/helpers.db")
    db.init_db()
    return db


def test_session_scope_commits_on_success_and_rolls_back_on_error(tmp_path):
    db = make_db(tmp_path)
    with db.session_scope() as session:
        session.add(User(email="kept@example.com", password_hash="x", display_name="Kept"))

    with pytest.raises(RuntimeError):
        with db.session_scope() as session:
            session.add(User(email="lost@example.com", password_hash="x", display_name="Lost"))
            session.flush()
            raise RuntimeError("boom")

    with db.session_scope() as session:
        emails = {user.email for user in session.query(User).all()}
    assert emails == {"kept@example.com"}


def test_init_db_twice_adds_nothing_the_second_time(tmp_path):
    db = make_db(tmp_path)
    assert db.init_db() == []


def test_get_database_reuses_the_instance_until_the_url_changes(tmp_path):
    first = get_database(f"sqlite:///{tmp_path}/a.db")
    assert get_database() is first
    assert get_database(first.url) is first
    second = get_database(f"sqlite:///{tmp_path}/b.db")
    assert second is not first and second.url.endswith("b.db")
