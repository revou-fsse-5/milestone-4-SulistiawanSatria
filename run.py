from app import create_app, db

app = create_app()

if __name__ == '__main__':

    app.config['WTF_CSRF_ENABLED'] = False

    app.run(debug=True)