def test_serialization_of_property_attr(todolist_with_users_tasks):
	with todolist_with_users_tasks.test_client() as client:
		resp = client.jget('/users?name~=Donald')
		assert resp['status'] == 'success'
		assert resp['result'][0]['name'] == "Donald Duck"
        print(resp['result'][0])
        assert resp['result'][0].get('first_name') == 'Donald'