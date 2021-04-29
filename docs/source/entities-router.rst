################
Entities Router
################

Entities router is an api definition framework which lets the developer define rest apis
in a declarative manner. 

Example:
"""""""""

.. code-block:: python


    catalogue_management_api_entities = EntitiesRouter(
        routes={
            "products": Entity(
                model_class=Product,
                get=Get(), index=Index(), post=Post(),
                put=Put(), delete=Delete()),

            "product-price-slabs": Entity(
                model_class=ProductPriceSlab,
                get=Get(), index=Index(), post=Post(),
                put=Put(), delete=Delete()),

            "users": Entity(
                model_class=User, get=Get(), index=Index(),
                post=Post(), put=Put(), delete=Delete()),
        }
    )

    main_api_entities = EntitiesRouter(
        router={
            "products": Entity(
                model_class=Product,
                query_modifier=lambda q: q.filter(Product.published == True),
                enable_caching=True, cache_timeout=3600,
                get=Get(), index=Index()),

            "product-price-slabs": Entity(
                model_class=ProductPriceSlab,
                get=Get(), index=Index()),

            "users": Entity(
                model_class=User,
                get=Get()),

            "orders": Entity(
                model_class=Order,
                query_modifier=lambda q: q.filter(
                    Order.user_id == current_user.id),
                get=Get(), index=Index(),
                post=Post(before_save=[set_current_user_id]),
                put=Put()
            )
        }
    )

    catalogue_management_api_entities.mount_on(catalogue_management_api_bp)

    main_api_entities.mount_on(main_api_bp)


In the above example two routers have been mounted on two different blueprints. The model class
named Product has been mounted on both routers. In the catalogue management api, it has been
allowed to support all CRUD operations. In the main api however, we have declared only get
and index operations. We have also restricted what products can be fetched by using a query_modifier

Thus the framework provides a neat way for declaring REST api endpoints for various model classes
with as minimal code as possible. 

***********************
How to define a router
***********************

The above example shows one way to define a router - by declaring the urls to routes map in the routers
argument of the constructor. Another way it to use the `route` method on the router. The above
router can also be defined as follows

.. code-block:: python

    main_api_entities = EntitiesRouter()

    main_api_entities.route("products", Entity(
        model_class=Product,
        query_modifier=lambda q: q.filter(Product.published == True),
        enable_caching=True, cache_timeout=3600,
        get=Get(), index=Index()))
    
    main_api_entities.route("product-price-slabs", Entity(
        model_class=ProductPriceSlab,
        get=Get(), index=Index()))

Both styles of declaration can be used together as well, ie some routes can be defined as a part of the
constructor and the remaining can be defined separately. Irrespective of how they are defined
all these routes get attached to the blueprint only when the `mount_on` method is called.

***************************************
The actual urls of the REST endpoints
***************************************

In the above code, we are mapping an entity to a string which is going to act as an url slug.

Let's say the catalog_api_bp is registered at the url '/catalog-api/v1' in the app. Now when a router is mounted
on it, the various entities in the router will be under this blueprint. If the base_url argument
is specified when declaring the router, the base_url is prepended before all the entity urls.
For example if we mount the entities with base url as "entities", then the common url
base for all the entities in the router becomes '/catalog-api/v1/entities'. If the base_url is left
empty, then the common base will be the root of the blueprint ie '/catalog-api/v1/'

Now the url slug to which each entity is routed will act as the base for all the operations defined
on the entity.

The framework allows 7 different operations. Let's consider the entity for the model Product which
is routed via the url slug products and attached to a router with base_url `entities` which
in turn is mounted on the catalog_api_bp registered at `/catalog-api/v1/`

The following 7 api endpoints can be registered on the entity

1. Index
""""""""""
The operation used to index all permitted records of the entity. Registered at `/catalog-api/v1/entities/products`

2. Get
""""""""""
The operation used to get a record with a particular id. A flask route is registered automatically at
`/catalog-api/v1/entities/products/<_id>'. The automatically created view function gets passed this
_id parameter with the value obtained from the request. For example, if the user accesses `/catalog-api/v1/entities/products/1234`
then _id will be passed as 1234 to the view function. You will not need to work with this variable
and can instead implement the functionality by passing various callables to the Get constructor.

3. Post
""""""""""
A Post operation will be registered at `/catalog-api/v1/entities/products`.

4. Put 
"""""""
A Put operation will be registered at `/catalog-api/v1/entities/products/<_id>`.

5. Patch
""""""""""
A patch endpoint gets registered at `/catalog-api/v1/entities/products/<_id>`. The request data
expects a key called `cmd` to be set. And based on the value of the cmd, the appropriate
handler will be invoked. Use Patch if the functionality needed cannot be trivially modelled via a PUT request.

6. Delete
""""""""""
A delete endpoint registered at `/catalog-api/v1/entities/products//<_id>`

7. Batch Save
"""""""""""""""
An endpoint which can allow a batch save operation, registered at `/catalog-api/v1/entities/products`
It can accept a collection of records which can be a mix of new records and existing records
differentiated by the presence of primary key






