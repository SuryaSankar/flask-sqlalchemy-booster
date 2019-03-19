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
				"name": "First task"
			}
		)
		print resp
		assert resp['status'] == 'success'
		assert 'id' in resp['result']
		print resp['result']['id']
		assert resp['result']['id'] == 1

