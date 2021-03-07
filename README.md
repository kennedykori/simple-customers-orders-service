
# Beverage Shop Service

[![Beverage Shop CI](https://github.com/kennedykori/simple-customers-orders-service/actions/workflows/django.yml/badge.svg?branch=master)](https://github.com/kennedykori/simple-customers-orders-service/actions/workflows/django.yml)
[![codecov](https://codecov.io/gh/kennedykori/simple-customers-orders-service/branch/master/graph/badge.svg?token=06QTFWF6LY)](https://codecov.io/gh/kennedykori/simple-customers-orders-service)


This is a simple REST service that allows customers of a beverage shop to make
orders. Employees of the shop can then review those orders and either approve
or reject them. The project is authored in 
[Django](https://www.djangoproject.com/) and 
[Django REST framework](https://www.django-rest-framework.org/) and a working 
version is hosted [here](https://beverage-shop.herokuapp.com/api/).

## Project Summary

The main components of the service are:

* __Customers__ - Customers can register, create new orders, add, update or 
  remove items from existing orders and cancel orders they have made. A 
  customer cannot access or modify other customer orders, and a customer can
  neither approve nor reject any orders including their own. A customer can
  cancel any of their existing orders as long as they haven't been reviewed by
  an employee(i.e. approved or rejected). Customers can view items in the
  beverage shop's inventory and their statuses(i.e. _available_, 
  _few remaining_, _out of stock_) but, they can not add new inventory items
  nor modify existing ones.
  
* __Employees__ - The main role of the employees is to review customer orders. 
  But in addition to reviewing orders, employees can also make new orders for
  customers and, add, remove or update items on an order belonging to any
  customer. Employees can also add new inventory items and modify existing
  ones.
  
* __Inventories__ - These are the beverage items that make up the shop's 
  stock. Customers can neither add new items nor modify existing ones, but 
  they can view the existing items. Employees however can add, remove and 
  update inventory items including making stock adjustments. Each inventory
  item has an `on-hand` property which indicates the current quantity of the
  item available in the shop. Only employees can view or modify this property.
  Each inventory item also has a ready oly property,`state` that indicates the
  item's availability. The property can only contain one of the following
  values: _AVAILABLE_, _FEW REMAINING_ or _OUT OF STOCK_. The _FEW REMAINING_
  state is determined by another property, `warn_limit` which is a threshold
  used to indicate low stock. only employees can view or modify this property.
  
* __Orders__ - An order is a request by a customer for purchase of an 
  item or multiple items in the shop's inventory. While a new order has zero
  items associated with it, for an order to be valid and approvable, it should
  contain at least one inventory item. Each order has one of the following 
  states:
  1. **_CREATED: N_** - This is the default state of a newly created order. An
    order with this state can transition to any other state.
     
  2. **_PENDING: P_** - This state indicates that an order is ready for
     review. An order can only transition to this state from the _created_ 
     state and can only transition to one of the following states from this
     state: _approved_, _canceled_ or _rejected_. Both employees and customers
     can mark an order as ready for review transitioning it to this state. An
     order can only be marked as ready for review if it has at least one item.
     
  3. **_APPROVED: A_** - This state represents an order that has already been
     reviewed by an employee and okayed for delivery. An order can only
     transition to this state from the _pending_ state and cannot transition
     into any further states after this. An order can only be approved if it
     contains at least one inventory item. Once an order is approved, all it's
     items are subtracted from the available inventory. Only employees can 
     approve an order.
     
  4. **_REJECTED: R_** - This state represents an order that has already been
     reviewed by an employee but not okayed for delivery. An order can only
     transition to this state from the _pending_ state and cannot transition
     into any further states after this. Only employees can reject an order.
     
  5. **_CANCELED: C_** - This state represents an order that has been canceled 
     and thus should not be considered for further review. An order can only
     transition into this state from either the _created_ or _pending_ states
     but cannot transition into any other further states after this. Both
     employees and customers can cancel an order.
  
  An order's item list can only be modified while the order is either in the 
  _created_ state or _pending_ state. Also, whenever a new order is created 
  or, an existing order changes from one state to the other, the customer is 
  sent a sms notification informing them of the change.
    
* __Order Items__ - These are the inventory items added to an order. Each 
  valid order has one or more items in it. Each order item describes the
  item ordered, quantity of the item ordered and, the price that the item was
  ordered at.

## API

An OpenAPI 3.0 schema of the service can be downloaded from the 
[api/schema](https://beverage-shop.herokuapp.com/api/schema/) endpoint. HTML 
documentation of the service in Swagger UI can be accessed at the 
[api/schema/swagger-ui/](https://beverage-shop.herokuapp.com/api/schema/swagger-ui/)
endpoint and, HTML documentation in Redoc can be accessed at the 
[api/schema/redoc/](https://beverage-shop.herokuapp.com/api/schema/redoc/).

The service both supports OpenID connect and Token authentication. To obtain
a token, send a *POST* request to the 
[api/auth-token/](https://beverage-shop.herokuapp.com/api/auth-token/) 
endpoint with the username and password of a user in the request body.
OpenID Connect standard endpoints are available at the 
[accounts/](https://beverage-shop.herokuapp.com/accounts/) endpoint.

## Getting Started

Before you can run the app locally, make sure you have 
[Python 3.8.0](https://www.python.org/downloads/release/python-380/) or above
and, [PostgreSQL 12.0](https://www.postgresql.org/download/) installed. Create
an empty PostgreSQL database and then make sure the following environment
variables are set:

| Variable                  	| Example Value                       	| Description                                                                                                                                         	|
|---------------------------	|-------------------------------------	|-----------------------------------------------------------------------------------------------------------------------------------------------------	|
| AFRICASTALKING_API_KEY    	| a86b363138331383079680af385a8a9e080 	| The API key of the [Africastalking](https://africastalking.com/) app to use.                                                                        	|
| AFRICASTALKING_SENDER_ID  	| Beverage Shop                       	| The SMS sender id to use when sending sms notifications.                                                                                            	|
| AFRICASTALKING_SHORT_CODE 	| 4747                                	| The SMS short code to use when sending sms notifications.                                                                                           	|
| AFRICASTALKING_USERNAME   	| beverage_shop                     	| The username of the [Africastalking](https://africastalking.com/) app to use.
| DATABASE_HOST             	| localhost                           	| The address of the server where the database is hosted.                                                                                             	|
| DATABASE_NAME             	| beverage_shop_db                    	| The name of the database you created earlier.                                                                                                       	|
| DATABASE_PASSWORD         	| s3cure_Pa$5WoRd!                    	| The password of the database user to use.                                                                                                           	|
| DATABASE_PORT             	| 5432                                	| The port that the database server is listening to for new connections.                                                                              	|
| DATABASE_USER             	| beverage_shop_admin                 	| The database user to use. This user should have read & write permissions of the database in use and should have permission to create new databases. 	|
| DJANGO_SETTINGS_MODULE    	| config.settings.local               	| The settings module to use.                                                                                                                         	|
| SECRET_KEY                	| vd%t#wvijbu +ypag78w4vd%t#w3sq=     	| The django application secret key.                                                                                                                  	|
| TEST_DATABASE_NAME        	| beverage_shop_test_db               	| The name of the database to use as a test database.                                                                                                 	|

The easiest way to set the environment variables is to use the 
virtualenvwrapper's `postactivate script`(_hopefully you're using a virtual 
environment_). For details on how to use the `postactivate script`, check out
the [virtualenvwrapper docs](https://virtualenvwrapper.readthedocs.io/en/latest/scripts.html#postactivate).
Next, perform the following steps in order:

1. Clone this repository (if you haven't already) and CD into the root
   directory, that is, the directory containing `manage.py`. Unless otherwise
   specified, this is the directory we are going to run all the rest of the 
   commands from.
   
2. Install the project's dependencies by running:-
   ```bash
    pip install -r requirements.txt
   ```
   
3. Run the following commands to create the database tables, generate an RSA 
   key for the server and to collect static assets:-.
   ```bash
    python manage.py migrate
    python manage.py creatersakey
    python manage.py collectstatic --no-input
   ```
   
4. Create the superuser by running and following command and filling the 
   resulting prompts.
    ```bash
    python manage.py createsuperuser
    ```

You're good to go. :thumbsup: You can now run the development server using 
the following command:-
```bash
  python manage.py runserver
```

## Tests

To run tests with coverage, CD in to the project root and run:
```bash
 coverage run manage.py test --settings=config.settings.test
```

To view the coverage report, run:
```bash
 coverage report -m
```
