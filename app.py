from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://u_test:testpwd@92.242.58.173:1984/db_test'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


tag_problem = db.Table('tag_problem',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
    db.Column('problem_id', db.Integer, db.ForeignKey('problem.id'))
)
# так посоветовали сделать тут  https://flask-sqlalchemy-russian.readthedocs.io/ru/latest/models.html
# https://flask-sqlalchemy.palletsprojects.com/en/2.x/models/


class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    deadline = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.String(100), nullable=False)

    post_client_id = db.Column(db.Integer, db.ForeignKey('user_info.id'), nullable=False)  # TODO foreign key
    user_post = db.relationship('User_info', foreign_keys=[post_client_id], backref=db.backref('posted_problems', lazy=True))

    post_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    solve_client_id = db.Column(db.Integer, db.ForeignKey('user_info.id'), nullable=True)  # TODO foreign key
    user_solve = db.relationship('User_info', foreign_keys=[solve_client_id], backref=db.backref('solved_problems', lazy=True))

    solve_date = db.Column(db.DateTime, nullable=True)
    file = db.Column(db.LargeBinary, nullable=False)

    status_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=False, default=0)  # TODO foreign key
    status = db.relationship('Status', backref=db.backref('problems_with_statuses', lazy=True))

    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)  # TODO foreign key
    subject = db.relationship('Subject', backref=db.backref('problems_with_subject', lazy=True))

    tags = db.relationship('Tag', secondary=tag_problem, lazy='subquery',
                           backref=db.backref('problems_with_tag', lazy=True))


class User_info(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    password = db.Column(db.String(100), nullable=False)
    full_name = db.Column(db.String(100), nullable=False, default='ULIA')
    email = db.Column(db.String(200), unique=True, nullable=False)  #TODO не забывать чекать уникальность логина потом и
    telephone = db.Column(db.String(40), nullable=False, default='89637637403')
    rating = db.Column(db.Float, nullable=False, default=0.0)  # TODO В базе данных там double precision одно и то же?
    country_code = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)  # TODO foreign key
    country = db.relationship('Countries', backref=db.backref('users', lazy=True))
    info = db.Column(db.String(2000), nullable=False, default='')


class Countries(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(100), nullable=False)


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    parent_id = db.Column(db.Integer, nullable=True)  # TODO foreign key


class Status(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False, unique=True)


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False, unique=True)



@app.route('/')
def index():
    return render_template("index.html")


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/user/<string:name>/<string:id>')
def user(name, id):
    return 'Страница пользователя: ' + name + ' - ' + id


@app.route('/offer_order')
def offer_order():
    return render_template("offer_order.html")


@app.route('/select_order')
def select_order():

    return render_template("select_order.html")


@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/get_registration', methods=['POST'])
def get_registration():
    a = User_info.query.filter_by(email='user0@yandex.ru').first()
    print(a.password)
    return redirect(url_for('index'))


@app.route('/registration')
def registration():
    return render_template("registration.html")


if __name__ == "__main__":
    app.run(debug=True)

db.create_all()
