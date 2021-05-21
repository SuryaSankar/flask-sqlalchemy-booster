from flask_sqlalchemy_booster import run_interactive_shell
from todo_list_api.app import create_todolist_app, db

app = create_todolist_app()

if __name__ == '__main__':
    run_interactive_shell(app, db)