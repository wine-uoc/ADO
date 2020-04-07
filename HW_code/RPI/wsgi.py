from flaskapp import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0')     # host='0.0.0.0' to run on machines IP address

# TODO: - script sh, download app from git and run (use supervisord linux tool)
#       - coexistence of several nodes in the same LAN, which node is myrpi.local?
#         https://www.raspberrypi.org/documentation/remote-access/ip-address.md
#         https://www.raspberrypi.org/documentation/configuration/nfs.md
#         https://flask.palletsprojects.com/en/1.1.x/deploying/
#         https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xvii-deployment-on-linux

