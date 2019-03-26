import requests
import json


def test_api_endpoint_existence(todolist_app):
	with todolist_app.test_client() as client:
		resp = client.get('/tasks')
		assert resp.status_code == 200

def test_task_creation(todolist_app):
	with todolist_app.test_client() as client:
		resp = client.jpost(
			'/tasks', {
				"title": "First task"
			}
		)
		assert resp['status'] == 'success'
		assert 'id' in resp['result']
		assert resp['result']['id'] == 1

def test_task_updation(todolist_app):
	with todolist_app.test_client() as client:
		modified_title = "First task - modified"
		resp = client.jput(
			'/tasks/1', {
				"title": "First task - modified"
			}
		)
		assert resp['status'] == 'success'
		assert 'id' in resp['result']
		assert resp['result']['title'] == modified_title
