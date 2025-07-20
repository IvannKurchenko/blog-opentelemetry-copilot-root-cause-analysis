## Product service
This small application is a part of the system under observability and responsible for managing orders in 
hypothetical e-commerce store.


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
