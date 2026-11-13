import os

from library import create_app

app = create_app()

if __name__ == '__main__':
    # For everyday development use:  flask --app app run --debug
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')
