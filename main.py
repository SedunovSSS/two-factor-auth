from flask import Flask, render_template, request, redirect, make_response
from flask_sqlalchemy import SQLAlchemy
import hashlib, datetime
from random import randrange, shuffle
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


HOST = '0.0.0.0'
PORT = 5000

DB_NAME = "sqlite:///database.db"
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_NAME
UPLOAD_FOLDER = './static/uploads'
db = SQLAlchemy(app)

sender_email = ""
sender_password = ""


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    step2email = db.Column(db.String(150), nullable=False, default="")
    step2password = db.Column(db.String(150), nullable=False, default="")
    step2num = db.Column(db.Integer, default=0)
    dateR = db.Column(db.DateTime, default=datetime.datetime.utcnow())

    def __repr__(self):
        return '<Users %r>' % self.id


@app.route('/')
def main():
    clear("/")
    name = request.cookies.get('user')
    if name is None:
        name = "Guest"
    return render_template("index.html", name=name)


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        login = request.form['login']
        email = request.form['email']
        passw1 = request.form['passw1']
        passw2 = request.form['passw2']
        if passw1 == passw2:
            password = hashlib.md5(passw1.encode("utf-8")).hexdigest()
            exists = db.session.query(Users.id).filter_by(login=login).first() is not None or db.session.query(Users.id).filter_by(email=email).first() is not None
            if not exists:
                try:
                    user = Users(login=login, email=email, password=password)
                    db.session.add(user)
                    db.session.commit()
                    resp = make_response(redirect("/"))
                    resp.set_cookie('user', user.login)
                    return resp
                except Exception as ex:
                    print(ex)
                    return redirect("/register")
            else:
                return redirect("/register")
        else:
            name = request.cookies.get('user')
            return render_template("register.html", name=name)
    else:
        clear("/register")
        name = request.cookies.get('user')
        return render_template("register.html", name=name)


@app.route('/login', methods=['POST', "GET"])
def login():
    if request.method == "POST":
        email = request.form['email']
        passw1 = request.form['passw1']
        passw2 = request.form['passw2']
        if passw1 == passw2:
            password = hashlib.md5(passw1.encode("utf-8")).hexdigest()
            exists = db.session.query(Users.id).filter_by(email=email, password=password).first() is not None
            if exists:
                user = Users.query.filter_by(email=email, password=password).first()
                user.step2email = email
                user.step2password = password
                user.step2num = randrange(100000, 1000000, 1)
                db.session.commit()
                resp = make_response(redirect("/2steplog"))
                resp.set_cookie('step2user', user.step2email)
                return resp
            else:
                return redirect("/login")

        else:
            name = request.cookies.get('user')
            return render_template("login.html", name=name)
    else:
        clear("/login")
        name = request.cookies.get('user')
        return render_template("login.html", name=name)


@app.route('/logout')
def logout():
    resp = make_response(redirect("/login"))
    resp.set_cookie('user', '', expires=0)
    return resp


def clear(url):
    try:
        step2email = request.cookies.get('step2user')
        user = Users.query.filter_by(email=step2email).first()
        user.step2email = ""
        user.step2password = ""
        user.step2num = 0
        db.session.commit()
        resp = make_response(redirect(url))
        resp.set_cookie('step2user', '', expires=0)
        return resp
    except:
        return redirect("/login")


def sendmail():
    step2email = request.cookies.get('step2user')
    step2num = db.session.query(Users.step2num).filter_by(step2email=step2email).first()[0]
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = step2email
    msg['Subject'] = "Auth Code"
    body = str(step2num)
    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP('smtp.mail.ru', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    text = msg.as_string()
    server.sendmail(sender_email, step2email, text)
    server.quit()


def sendmail_password():
    step2email = request.cookies.get('step2user')
    step2num = db.session.query(Users.step2num).filter_by(step2email=step2email).first()[0]
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = step2email
    msg['Subject'] = "Reset Password"
    body = str(step2num)
    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP('smtp.mail.ru', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    text = msg.as_string()
    server.sendmail(sender_email, step2email, text)
    server.quit()


@app.route('/2steplog', methods=['GET', 'POST'])
def step2log():
    try:
        step2email = request.cookies.get('step2user')
        step2num = db.session.query(Users.step2num).filter_by(email=step2email).first()[0]
        step2password = db.session.query(Users.step2password).filter_by(email=step2email).first()[0]
    except:
        return redirect("/login")
    if request.method == "POST":
        number = int(request.form.get("num2step"))
        if number == step2num:
            try:
                user = Users.query.filter_by(email=step2email, password=step2password).first()
                resp = make_response(redirect("/"))
                resp.set_cookie('user', user.login)
                resp.set_cookie('step2user', '', expires=0)
                user.step2email = ""
                user.step2password = ""
                user.step2num = 0
                db.session.commit()
                return resp
            except Exception as ex:
                print(ex)
                return redirect("/login")
        else:
            return redirect("/login")
    else:
        if step2email is None or step2num == 0 or step2password == "":
            return redirect("/login")
        sendmail()
        return render_template("2step.html")


@app.route('/resetpassw', methods=['GET', 'POST'])
def reset_password():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        password = hashlib.md5(password.encode("utf-8")).hexdigest()
        exists = db.session.query(Users.id).filter_by(email=email). first() is not None
        if exists:
            user = Users.query.filter_by(email=email).first()
            user.step2email = email
            user.step2password = password
            user.step2num = randrange(100000, 1000000)
            db.session.commit()
            resp = make_response(redirect("/2stepreset"))
            resp.set_cookie('step2user', user.step2email)
            return resp
        return redirect("/login")
    else:
        name = request.cookies.get('user')
        clear("/resetpassw")
        return render_template("resetpassw.html", name=name)


@app.route('/2stepreset')
def step2_reset_password():
    try:
        step2email = request.cookies.get('step2user')
        step2num = db.session.query(Users.step2num).filter_by(email=step2email).first()[0]
        step2password = db.session.query(Users.step2password).filter_by(email=step2email).first()[0]
    except:
        return redirect("/resetpassw")
    if step2email != "" and step2num != 0 and step2password != "":
        sendmail_password()
        nums = [randrange(100000, 1000000) for i in range(5)]
        nums.append(step2num)
        shuffle(nums)
        name = request.cookies.get('user')
        return render_template("2steppassw.html", nums=nums, name=name)
    else:
        return redirect("/resetpassw")


@app.route('/endreset')
def end_reset_password():
    try:
        step2email = request.cookies.get('step2user')
        step2num = db.session.query(Users.step2num).filter_by(email=step2email).first()[0]
        step2password = db.session.query(Users.step2password).filter_by(email=step2email).first()[0]
    except:
        return redirect("/login")
    if step2email != "" and step2num != 0:
        try:
            code = int(request.args.get('code'))
            if code == step2num:
                user = Users.query.filter_by(email=step2email).first()
                user.password = step2password
                user.step2email = ""
                user.step2password = ""
                user.step2num = 0
                db.session.commit()
                resp = make_response(redirect("/"))
                resp.set_cookie('user', user.login)
                resp.set_cookie('step2user', '', expires=0)
                return resp
            else:
                return redirect("/resetpassw")
        except:
            return redirect("/resetpassw")
    else:
        return redirect("/resetpassw")


if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)