import requests
import json


def test_list_relationship_new_item(todolist_with_users_tasks):
    with todolist_with_users_tasks.test_client() as client:
        first_task_resp_before_update = client.jget("/tasks/1")
        resp = client.jpost(
            '/users?_ds={"rels":{"tasks":{}}}', {
                "name": "Sheldon",
                "email": "sheldon@bbt.com",
                "gender": "male",
                "tasks": [
                    {
                        "title": "Build a minature rocket"
                    }
                ]
            })
        print(resp)
        assert resp['status'] == 'success'
        first_task_resp = client.jget("/tasks/1")
        print(first_task_resp)
        assert first_task_resp['result']['title'] == first_task_resp_before_update['result']['title']


def test_list_relationship_updation_of_existing_item(todolist_with_users_tasks):
    """
    Regression test case for https://github.com/SuryaSankar/flask-sqlalchemy-booster/issues/17

    """
    with todolist_with_users_tasks.test_client() as client:
        first_task = client.jget("/tasks/1")["result"]
        second_task = client.jget('/tasks/2')['result']
        print("second_task ", second_task)
        new_title = "Modified second task title"
        resp = client.jput(
            '/users/' + str(second_task['user_id'])+'?_ds={"rels":{"tasks":{}}}', {
                "tasks": [
                    {
                        "id": second_task["id"],
                        "title": new_title
                    }
                ]
            })
        assert resp['status'] == 'success'
        first_task_after_update = client.jget("/tasks/1")["result"]
        assert first_task['title'] == first_task_after_update['title']
        second_task_after_update = client.jget("/tasks/2")["result"]
        print("second_task_after_update ", second_task_after_update)
        assert second_task_after_update['title'] == new_title
