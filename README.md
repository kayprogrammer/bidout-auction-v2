# BidOut Auction V2 (WORK IN PROGRESS)

![alt text](https://github.com/kayprogrammer/bidout-auction-v2/blob/main/display/sanic.png?raw=true)


#### Sanic Docs: [Documentation](https://docs.djangoproject.com/en/4.2/)

#### PG ADMIN: [pgadmin.org](https://sanic.dev) 


## How to run locally

* Download this repo or run: 
```bash
    $ git clone git@github.com:kayprogrammer/bidout-auction-v1.git
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

## DOCS
![alt text](https://github.com/kayprogrammer/bidout-auction-v2/blob/main/display/display1.png?raw=true)

![alt text](https://github.com/kayprogrammer/bidout-auction-v2/blob/main/display/display2.png?raw=true)

![alt text](https://github.com/kayprogrammer/bidout-auction-v2/blob/main/display/display3.png?raw=true)

![alt text](https://github.com/kayprogrammer/bidout-auction-v2/blob/main/display/display4.png?raw=true)
