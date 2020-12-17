from flask_sqlalchemy_booster import FlaskSQLAlchemyBooster
from sqlalchemy import func
from flask_sqlalchemy_booster import FlaskBooster
from flask_sqlalchemy_booster.crud_api_view import register_crud_routes_for_models
from flask_sqlalchemy_booster.crud_api_class import CrudAPI
from sqlalchemy.ext.associationproxy import association_proxy

from werkzeug.serving import run_simple


db = FlaskSQLAlchemyBooster()


class Project(db.Model):

    allow_updation_based_on_unique_keys = True

    id = db.Column(db.Integer, primary_key=True, unique=True)
    created_on = db.Column(db.DateTime(), default=func.now())
    name = db.Column(db.String(300), unique=True)
    owning_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    owning_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    description = db.Column(db.Text)

    owning_user = db.relationship("User", backref=db.backref("projects"))
    owning_team = db.relationship("Team", backref=db.backref("projects"))


class Team(db.Model):

    id = db.Column(db.Integer, primary_key=True, unique=True)
    created_on = db.Column(db.DateTime(), default=func.now())
    name = db.Column(db.String(300))


class Task(db.Model):
    _autogenerate_dict_struct_if_none_ = True

    id = db.Column(db.Integer, primary_key=True, unique=True)
    created_on = db.Column(db.DateTime(), default=func.now())
    title = db.Column(db.String(300))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    completed = db.Column(db.Boolean, default=False)
    completed_on = db.Column(db.DateTime())

    user = db.relationship("User", backref=db.backref("tasks"))
    user_email = association_proxy(
        "user", "email", creator=lambda email: User.first(email=email)
    )


class User(db.Model):
    _autogenerate_dict_struct_if_none_ = True

    id = db.Column(db.Integer, primary_key=True, unique=True)
    created_on = db.Column(db.DateTime(), default=func.now())
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    gender = db.Column(
        db.Enum('male', 'female', 'transgender'), nullable=False)
    marital_status = db.Column(db.Enum('married', 'single'))

    @property
    def first_name(self):
        return self.name.split(" ")[0]

    @classmethod
    def attrs_for_autogenerated_dict_struct(cls):
        return super(User, cls).attrs_for_autogenerated_dict_struct() + ['first_name']


class TeamMembership(db.Model):
    __table_args__ = (
        db.UniqueConstraint(
            'user_id', 'team_id',
            name='user_id_team_id_uc'),
    )
    id = db.Column(db.Integer, primary_key=True, unique=True)
    created_on = db.Column(db.DateTime(), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    role = db.Column(db.Enum("Manager", "Lead", "Developer", "Tester"))

    user = db.relationship("User", backref=db.backref("team_memberships"))
    team = db.relationship("Team", backref=db.backref("memberships"))


def create_todolist_app(testing=False):
    app = FlaskBooster(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    app.config['DEBUG'] = True
    app.testing = testing

    db.init_app(app)

    with app.app_context():
        db.create_all()

    print("about to call register_crud_routes_for_models")

    register_crud_routes_for_models(app, {
        Task: {
            'url_slug': 'tasks'
        },
        User: {
            'url_slug': 'users',
            'remove_property_keys_before_validation': True,
            'dict_struct': {
                'rels': {
                    'tasks': {},
                    'projects': {}
                }
            },
            'views': {
                'get': {
                    'id_attr': 'email'
                }
            }
        },
        Project: {
            'url_slug': 'projects'
        },
        Team: {
            'url_slug': 'teams'
        }
    }, register_views_map=True, register_schema_definition=True)
    return app

def create_ecomm_app():
    app = FlaskBooster(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    app.config['DEBUG'] = True
    app.testing = testing

    db.init_app(app)

    with app.app_context():
        db.create_all()

    entities = EntityGroup(
        entities=[
            Entity('uploaded-files', UploadedFile,
                    enable_caching=True, cache_timeout=3600,
                    access_checker=uploaded_file_access_checker,
                    forbidden_operations=[Index, BatchSave]),
            Entity('uploaded-files-folders', UploadedFilesFolder),
            Entity('customizable-products', CustomizableProduct,
                    enable_caching=True, cache_timeout=3600,
                    query_constructor=lambda q: q.filter(CustomizableProduct.can_be_viewed_in_marketplace == True),
                    permitted_operations=[Index, Get],
                    response_dict_struct={
                        "attrs": difference(
                            CustomizableProduct.attrs_for_autogenerated_dict_struct(),
                            ["matching_attribute_prop_ids"]),
                        "rels": {
                            "displayed_prices": {}
                        }
                    },
                    index=Index(
                        query_constructor=lambda q: q.filter(
                            CustomizableProduct.can_be_viewed_in_marketplace == True
                            ) if g.args.get('url_slug') else q.filter(
                            CustomizableProduct.is_listed_in_marketplace == True,
                            CustomizableProduct.can_be_viewed_in_marketplace == True))),
            Entity('jobs', Job,
                    forbidden_operations=[BatchSave],
                    non_settable_fields=[
                        'production_charges', 'shipping_charges', 'production_charges_rush_component',
                        'total_amount', 'commission_percent', 'commission', 'seller_take_home', 'status',
                        'no_of_working_days_for_production',
                        'scheduled_dispatch_datetime', 'scheduled_delivery_datetime', 'has_been_placed_by_customer',
                        'moved_to_seller_queue', 'received_by_seller_on', 'is_accepted_for_production',
                        'production_completed', 'dispatched', 'delivered', 'reason_for_declining',
                        'reason_for_declining_explanation', 'is_archived',
                        'design_verified_by_platform', 'assigned_moderator_id'],
                    response_dict_modifiers=[remove_moderator_note_ids_from_message_ids],
                    response_dict_struct={
                        "rels": {
                            "production_specification": {},
                            "output_items": {},
                            "customized_layout": {
                                "rels": {
                                    "customized_locations_map": {},
                                    "design_associations": {}
                                }
                            },
                            "review_rating": {},
                            "consignments": {
                                "rels": {
                                    "items_map": {}
                                }
                            }
                        }
                    },
                    query_constructor=query_owned_jobs_only,
                    post=Post(
                        before_save=[
                            user_id_marker,
                            pincode_marker,
                            cart_id_marker,
                            seller_order_marker_for_new_job],
                        after_save=[
                            update_sales_tax_fields,
                            update_total_amount_for_order_and_cart,
                            update_seller_order_id_in_job_output_items,
                            update_full_id_for_job_order_and_cart,
                            create_customized_product,
                            set_design_submitted_flag_on_job,
                            cart_id_marker_on_job_customized_layout_and_designs                            
                        ]),
                    put=Put(
                        before_save=[
                            ensure_ownership_for_existing_job,
                            abort_if_job_category_is_changed,
                            cart_id_marker,
                            seller_order_marker_for_existing_job
                        ],
                        after_save=[
                            update_sales_tax_fields,
                            update_total_amount_for_order_and_cart,
                            set_design_submitted_flag_on_job,
                            cart_id_marker_on_job_customized_layout_and_designs,
                            update_full_id_for_job_order_and_cart
                        ]),
                    delete=Delete(
                        before_save=[
                            abort_if_job_has_been_placed,
                            ensure_ownership_for_existing_job_on_delete
                        ],
                        after_save=[
                            update_seller_order_and_cart_after_job_deletion
                        ]),
                    patch=Patch(
                        access_checker=job_access_checker,
                        command_handlers=[
                            convert_job_to_template,
                            save_job_for_later]
                    ))
        ]
    )

def create_todolist_app_using_constants(testing=False):
    app = FlaskBooster(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    app.config['DEBUG'] = True
    app.testing = testing

    db.init_app(app)

    with app.app_context():
        db.create_all()

    print("about to call register_crud_routes_for_models")

    model_views_dict = {
        Task: {
            URL_SLUG: 'tasks'
        },
        User: {
            URL_SLUG: 'users',
            REMOVE_PROPERTY_KEYS_BEFORE_VALIDATION: True,
            DICT_STRUCT: {
                RELS: {
                    'tasks': {},
                    'projects': {}
                }
            },
            VIEWS: {
                GET: {
                    ID_ATTR: 'email'
                }
            }
        },
        Project: {
            URL_SLUG: 'projects'
        },
        Team: {
            URL_SLUG: 'teams'
        }
    }

    register_crud_routes_for_models(app, model_views_dict, register_views_map=True, register_schema_definition=True)
    return app


def create_app_with_function_based_crud(testing=False):
    app = FlaskBooster(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    app.config['DEBUG'] = True
    app.testing = testing

    db.init_app(app)

    with app.app_context():
        db.create_all()

    todolist_entities = EntitySet()
    todolist_entities.define_entity(model_class=Task, url_slug='tasks')
    todolist_user = todolist_entities.define_entity(
        model_class=User, url_slug='users',
        remove_property_keys_before_validation=True,
        dict_struct= {
            'rels': {
                'tasks': {},
                'projects': {}
            }
        }
    )
    todolist_user.define_get(id_attr='email')

    todolist_entities.define_entity(Project, url_slug='projects')
    todolist_entities.define_entity(Team, url_slug='teams')
    todolist_entities.register(app, register_views_map=True, register_schema_definition=True)

    return app

def run_application(app):
    run_simple('0.0.0.0', 5000, app)


if __name__ == '__main__':
    app = create_todolist_app()

    run_application(app)
