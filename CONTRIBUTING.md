# 👨‍💻 Contribution Guide

If you want to help us improve this project, feel free to create issues or submit pull requests.

## 📦 Download and Setup

1. Download a text editor such as [VSCode](https://code.visualstudio.com/) or [Atom](https://atom.io/).
2. Download [git](https://git-scm.com/downloads).
3. Run the following command to download this repository to your computer (in `terminal` on OS X or Linux, in `cmd` for Windows)

```bash
git clone https://github.com/team-pass/FIDO-login.git
```

If you haven't already, take a brief look at [how git works](https://guides.github.com/introduction/git-handbook/)

1. If you're on Team PASS, request access for the `.env` file, which contains server environment variables such as the database username/password. You should place it in `./.env`. If you're not on the team, you can create your own `.env` file and host the database yourself (we use [MariaDB](https://mariadb.org/) for our production environment and [SQLite](https://www.sqlite.org/index.html) for development). You can see what our `.env` looks like in the [`.env.example`](.env.example) file.

2. Setup and activate a Python virtual environment (see the [official Python docs on venv](https://docs.python.org/3/tutorial/venv.html)).
3. Install the necessary Python packages using

```bash
pip install -r requirements.txt
```

7. Create the database with the correct tables

```bash
python setup-db.py
```

8. Run the server using 

```bash
python run.py
```

## 🧪 Running Tests
We use `pytest` to verify the behavior of our application. You can invoke our test suite by running:

```bash
pytest web/tests/
```

As you add new features to the application, please add unit tests to ensure that your changes work as intended!

## 📦 Running a Production Version

To run a production version of the web app, you can simply run

```bash
docker-compose up
```

in the root of the repository. The [`docker-compose.yml`](./docker-compose.yml) file defines how to setup the Flask and MariaDB instance. 

### ✈ DB Migrations

To setup the DB on the Dockerized stack, you can run the following commands after starting the services w/ `docker-compose up`:


```bash
docker-compose exec web bash # Opens up a shell in the active `web` service
python app/setup-db.py       # Sets up the DB
```

## 📝 Adding a New Feature


Let's say you want to add a new feature to the code. Here are the steps you would follow (assuming you use `git` from the command line):

1. Make a [GitHub issue](https://github.com/team-pass/FIDO-login/issues) describing the feature. Write enough info so that someone else could complete the task just by reading through your description.
2. In terminal, navigate to your local `FIDO-login` folder and run

```bash
git checkout master # Switch branches to `master` (if you're not already there)
git pull            # Pull down changes from the remote FIDO-login repository (on github.com)
```

3. Now, make a new branch off of `master` for your feature. For example, if you were writing the HTML for the login page, you might run the following:

```bash
git branch login-page   # Create a new branch called `login-page`
git checkout login-page # Change branches (from `master` to `login-page`)
```

or (equivalently)

```bash
git checkout -b login-page # Create a new branch called `login-page` and check it out
```

4. Make the feature!!!
5. Once the feature is ready, it's time to make your code official. First you have to **stage** your code using `git add` (which tells git which file changes you want to include in your code snapshot), then you `git commit` your changes (to save/take the snapshot of the files you just staged):

```bash
git add FILE_YOU_EDITED ANOTHER_FILE_YOU_EDITED
git commit -m "Write a descriptive commit message that describes all of the changes you made"
```

6. After you've commited all your changes, it's time to send the code up to GitHub so everyone on Team PASS has access. To do that, run

```bash
git push # Sends all of your committed changes to the remote (github.com)
```

This command might throw an error because the branch isn't currently tracked by github. In that case, it will show you a command to run, which looks something like this:

```bash
git push --set-upstream origin login-page
```

7. Now, you should see a new branch on github with your new changes.
8. If you think your code is ready to go into the app, it's time to submit a pull request (from your feature branch into master). To do so, click on the `Pull Requests` tab at the top of the FIDO-login repository and submit a new `Pull Request`.
8. DON'T merge in your own pull request, even if you think it is ready. Someone else will review the changes you made and provide you with feedback. If you need to make new changes to address the feedback, make them on your local version of the branch and continue pushing changes to github. Your pull request will update with the new changes automatically.
9.  Eventually... your pull request will be accepted! After that, you can start working on the next set of features :)
