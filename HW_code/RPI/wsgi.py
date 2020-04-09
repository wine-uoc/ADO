"""Web server application."""
from flaskapp import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0')     # host='0.0.0.0' to run on machines IP address


# TODO:
#  - firmware update page
#  - enable database migration using Flask-Migrate (to allow app upgrade to modify db schema)?

