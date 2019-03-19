import pytest
from todo_list_api.app import create_todolist_app


@pytest.fixture(scope="session")
def todolist_app():
	return create_todolist_app()