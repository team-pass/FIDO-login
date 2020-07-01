# :file_cabinet: FIDO Login Backend

This folder contains the backend for our web app---that is, request processing and frontend-database interaction.

## :file_folder: Project Structure

This section of the project is broken up as follows:

- `project/`: A Python package that groups together backend functionality for (hopefully) clean scalability in the future
- `run.py`: The driving code for a server; simply run it with `python3 run.py`

## :package: Python Packages Required

***Note:*** *It's recommended to install Python packages on a per-project basis within virtual environments. Flask provides a quick explanation of the motivation and process [here](https://flask.palletsprojects.com/en/1.1.x/installation/#virtual-environments).*

| Package Name | Purpose | Installation with `pip` |
| :----------: | :-----: | :---------------------: |
| Flask | Everything the backend is built on | `pip install Flask` |
| Flask-Bcrypt | Hashing and password checking | `pip install Flask-Bcrypt` |
| MySQL Connector (Python) | Connecting to MariaDB databases | `pip install mysql-connector-python` |
