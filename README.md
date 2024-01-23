# BidOut Auction V2

![alt text](https://github.com/kayprogrammer/bidout-auction-v2/blob/main/display/sanic.png?raw=true)


#### Sanic Docs: [Documentation](https://sanic.dev)

#### PG ADMIN: [Documentation](https://pgadmin.org) 

#### Swagger: [Documentation](https://swagger.io/docs/)

## How to run locally

* Download this repo or run: 
```bash
    $ git clone git@github.com:kayprogrammer/bidout-auction-v2.git
```

#### In the root directory:
- Install all dependencies
```bash
    $ pip install -r requirements.txt
```
- Create an `.env` file and copy the contents from the `.env.example` to the file and set the respective values. A postgres database can be created with PG ADMIN or psql

- Run Locally
```bash
    $ alembic upgrade heads 
```
```bash
    $ sanic app.main:app --debug --reload
```

- Run With Docker
```bash
    $ docker-compose up --build -d --remove-orphans
```
OR
```bash
    $ make build
```

- Test Coverage
```bash
    $ pytest --disable-warnings -vv
```
OR
```bash
    $ make test
```

## Docs
#### SWAGGER API Url: [BidOut Docs](https://bidout-fastapi.vercel.app/)
#### POSTMAN API Url: [BidOut Docs](https://bit.ly/bidout-api)

![alt text](https://github.com/kayprogrammer/bidout-auction-v2/blob/main/display/display1.png?raw=true)

![alt text](https://github.com/kayprogrammer/bidout-auction-v2/blob/main/display/display2.png?raw=true)

![alt text](https://github.com/kayprogrammer/bidout-auction-v2/blob/main/display/display3.png?raw=true)

![alt text](https://github.com/kayprogrammer/bidout-auction-v2/blob/main/display/display4.png?raw=true)

![alt text](https://github.com/kayprogrammer/bidout-auction-v2/blob/main/display/display5.png?raw=true)
