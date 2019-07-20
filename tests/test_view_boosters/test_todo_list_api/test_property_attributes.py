def test_serialization_of_property_attr(todolist_with_users_tasks):
    with todolist_with_users_tasks.test_client() as client:
        resp = client.jget('/users?name~=Donald')
        assert resp['status'] == 'success'
        assert resp['result'][0]['name'] == "Donald Duck"
        assert resp['result'][0].get('first_name') == 'Donald'

def test_if_put_ignores_property_attr(todolist_with_users_tasks):
    with todolist_with_users_tasks.test_client() as client:
        resp = client.jget('/users/1')
        first_name = resp['result']['first_name']
        modified_first_name = "Mr.{}".format(first_name)
        resp = client.jput(
            '/users/1', {
                "first_name": modified_first_name
            })
        print(resp)
        assert resp['status'] == 'success'
        assert resp['result']['first_name'] == modified_first_name
