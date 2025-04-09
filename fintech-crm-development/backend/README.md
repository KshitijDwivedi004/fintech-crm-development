# Introduction

This is a project which contaning Admin/CA/Auditor/User API's collection for Saral.

# Getting Started

### Installation process

1.  Through Docker

    - Prerequisite - [Docker](https://docs.docker.com/get-docker/)
      After forking the repository

    to build:

    ```bash
    docker-compose build
    ```

    to run:

    ```bash
    docker-compose up
    ```

    - Visit `http://127.0.0.1/` with the endpoints or /docs for documentation

2.  Through virtual env

    - Prerequisite
      - [Python](https://www.python.org/downloads/)
      - use a [git bash](https://gitforwindows.org/#bash) console to run the commands below
    - After forking the repository
    - Create [virtual env](https://docs.python.org/3/library/venv.html)
    - Activate you virtual environment `. path/to/virtualenv/bin/activate`
    - Install requirements.txt

    ```
    pip install -r requirements.txt
    ```

    - Load the environment variables: `. load_env.sh`
    - Now you ready to runserver.

    ```
    uvicorn app.main:app --reload
    ```

    - Checkout your local host `http://127.0.0.1:8000/` with the endpoints or /docs for documentation

### Software dependencies

- Please refer to requirements.txt

### Latest releases

### API references

- Currently it is deployed here https://zerokaradminapi.techdomeaks.com/docs

# Build and Test

TODO: Describe and show how to build your code and run the tests.

# Contribute

TODO: Explain how other users and developers can contribute to make your code better.

If you want to learn more about creating good readme files then refer the following [guidelines](https://docs.microsoft.com/en-us/azure/devops/repos/git/create-a-readme?view=azure-devops). You can also seek inspiration from the below readme files:

- [ASP.NET Core](https://github.com/aspnet/Home)
- [Visual Studio Code](https://github.com/Microsoft/vscode)
- [Chakra Core](https://github.com/Microsoft/ChakraCore)



# Database Migration with Alembic  

To migrate the database with updated tables, we use **Alembic**. Follow these steps:  

## 1. Add Model Imports in `alembic/env.py`  

Before running migrations, ensure the models are imported in `alembic/env.py`:  

```python
from app.models import (
    auditor,
    ca,
    credit_report,
    leads,
    notes,
    user,
    telecallers,
    password_reset,
    otp,
    failed_login_attempts,
    tokens,
)
 

## 2. Generate a New Migration by deleting the old one

delete the existing alembic/versions file then, hit this command |

--> alembic revision --autogenerate -m "Initial migration Test"


## 3. Apply the Migration

--> alembic upgrade head


# Python path for no app found