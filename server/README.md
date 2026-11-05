# INSTALAR DEPENDENCIAS
$ pip install uv;
$ pip install starlette;
$ pip install uvicorn;
$ pip install pydantic;

# CREAR SERVIDOR
$ uv init server
$ cd server

# AÑADIR FAST API
$ uv add "fastapi[standard]"

# CORRER SERVIDOR
$ uv run fastapi dev

# REFERENCIAS
$ https://pydevtools.com/handbook/tutorial/getting-started-with-uv
$ https://fastapi.tiangolo.com/#requirements
