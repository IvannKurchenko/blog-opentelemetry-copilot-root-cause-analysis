## Orders Service
This small application is a part of the system under observability and responsible for managing orders in
hypothetical e-commerce store.

📦 **Orders Service API**
| Method | Endpoint       | Description           |
|--------|----------------|-----------------------|
| GET    | `/orders`      | Get all orders        |
| GET    | `/orders/{id}` | Get order by id       |
| POST   | `/orders`      | Create new order      |
| PUT    | `/orders/{id}` | Update order status   |
| DELETE | `/orders/{id}` | Delete order          |

📌 **JSON Examples for APIs:**

**Create new order (POST /orders):**
```json
{
  "user_id": 789,
  "items": [
    {"product_id": 101, "quantity": 1},
    {"product_id": 202, "quantity": 3}
  ]
}
```

**Update order status (PUT /orders/{id}):**
```json
{
  "status": "shipped"
}
```

### Setup
To set up a project to start work on the run:
```shell
make setup
```
This command will create a virtual environment and install necessary dependencies

### Lint 
Run basic code quality checks with:
```shell
make lint
```

### Run
To run the application along with the environment 
```shell
make run
```
To ensure the application is up and running execute requests from [orders.http](orders.http)

### Build
To build the application, the docker file runs:
```shell
make build
```
