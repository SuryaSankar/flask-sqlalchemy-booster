import pytest
from .todo_list_api.app import db, create_todolist_app, User, Task


@pytest.fixture(scope="session")
def todolist_app():
	return create_todolist_app()

@pytest.fixture(scope="session")
def todolist_with_users_tasks(todolist_app):
    with  todolist_app.test_request_context():
		User.create_all([{
			"name": "Donald Duck",
			"email": "duck@disney.com",
			"gender": "male"
		}, {
			"name": "Tin Tin",
			"email": "tintin@cn.com",
			"gender": "male"
		}])
		Task.create_all([{
			"title": "Swim",
			"user_email": "duck@disney.com"
		}, {
			"title": "Solve Mysteries",
			"user_email": "tintin@cn.com"
		}])
		return todolist_app