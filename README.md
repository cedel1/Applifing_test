# How to Install and Run This Excersise

## Steps to run this locally:

1. Make sure you have Docker installed on your computer.
2. Go to the repository (you are most likely there, if you are reading this) and either download the project to a directory or clone the project using git.
3. Open file `.env` located at the root of the project. This file contains basic settings for the project. You may change these as you see fit. Actually, it is **recommended** to do just that, as the file contains secrets and was placed in a repo, which would not be a smart move to do, if this wasn't an excersise. Note that on some operating systems (Linux, MacOS etc.), the files whose names start with `.` (dot) are considered hidden. If you don't see the file, make sure you have hidden files displayed.
3. Open a terminal and change to the directory where you cloned or downloaded the exercise project.
5. Run `docker compose up --build` command. That should download the required images and run the project in terminal (display runtime messages etc.). If you want to run it in the background, use `docker compose up -d --build` command. The `--build` flag will rebuild the images, so once you are satisfied (or in production), you can safely omit it (but without it the Celery images/container will not be updated on the next run, since it does not have autoreload set on code change).
6. Once the project builds, you can access the API and tools. These are described in the next section.
7. To run the test (which are rather basic and incomplete at the moment), keep the containers running and in a separate terminal (or the same one, if you chose to use the `-d` daemon mode flag) enter the following command: `docker exec fastapi-app bash test.sh`. If you want faster running test (and can do without a test coverage report), you can also run `docker exec fastapi-app pytest [optional_test_path]`.

## Available API and Tools

If you run the stack locally on your computer, you should have the following tools available at the following URLs. If the project is not run locally, the URLs might change.

- The **API** proper: `http://localhost:4000`
- The API **OpenAPI** description (you can also use this to test the API): `http://localhost:4000/docs`
- **PgAdmin** (PostgreSQL administration tool, see the `.env` file for login details): `http://localhost:5050/browser/`
- **Flower** (Celery monitoring tool): `http://localhost:5555`

## Description of the Stack and Notes

The whole exercise is based in FastAPI, PostgreSQL, Celery, Celery Beat, Redis and the above monitoring and documentation tools.

It is based on fastapi-postgresql-starterkit project, but modified in a few ways:

- Tests use separate PostgreSQL database, so running tests does not mess with production database (this took quite some time to figure out, sorry for the delay).
- Celery and Flower were added (in a similar way to `https://github.com/tiangolo/full-stack-fastapi-postgresql` project.
- Celery backend and results store was changed to Redis. Redis (and its automatic key expiration) was also used for storing Offer API this is connected to. Unfortunately, it seems there is no free SQLAlchemy redis dialect, so it has to be used on rather low level.
- Celery Beat is used for planning the periodical Offer download from (provided) external API. The Periodicity can be set via environment variable (or via the `.env` file) using `DOWNLOAD_NEW_OFFERS_TASK_INTERVAL` setting (in seconds)
- Dependencies in the original template project are managed by `requirements.txt` file, which seems to be a bit bloated with unnecessary dependencies. So I have provided a new file `requirements_minimal.txt` which is not very well tested, so it's not used by default.


## Notes on Usage of the provided API:

- The product endpoints can be found under `/api/v1/products/` route.
- Note that calling `POST /api/v1/products/` will register the product in 'remote' service then create it in 'local' database and immediately download the offers related to the product just registered.
- If the product registration in 'remote' service fails, an error is returned and product is not registered in 'local' database (so a user/admin can take appropriate action to remedy the situation).
- Product DELETE also deletes related downloaded offers. This is a deliberate decision. There are many other possible solutions - for example the product (and offers) could be kept in the 'local' database and just marked as inactive.
- Offers can be found under the `/api/v1/offers/` route and are read only - they are downloaded from the remote service by periodic Celery task (triggered by Celery Beat).
