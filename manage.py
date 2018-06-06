from flask_script import Manager

from webapp.app import app

manager = Manager(app, with_default_commands=False)

@manager.option('-c', '--config', dest='config', help='Configuration file name', default='scriptfan.cfg')
@manager.option('-H', '--host',   dest='host',   help='Host address', default='0.0.0.0')
@manager.option('-p', '--port',   dest='port',   help='Application port', default=5000)
def runserver(config, host, port):
    app.run(host=host, port=port,debug=True)


if __name__=="__main__":
    manager.run()

