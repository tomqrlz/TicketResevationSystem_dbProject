from flask import Flask, render_template, request, redirect, url_for, session, json
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import hashlib, binascii
import uuid
import datetime

app = Flask(__name__)

app.secret_key = 'O\x94\x18\xdb}\xef\x05\x1d\x88RG\xc0\x8f\xdaT\xe3x\xe19\xd8;\nQ\xc4'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'g03'

try:
    mysql = MySQL(app)
except MySQLdb.Error:
    render_template('err.html')
seatId= None;

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''

    try:
        if request.method == 'POST' and 'login' in request.form and 'password' in request.form:
            login = request.form['login']
            password = request.form['password']
            password = hashPassword(password)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM users WHERE userLogin = %s AND userPassword = %s', (login, password,))
            account = cursor.fetchone()
            if account:
                session['loggedin'] = True
                session['id'] = account['userId']
                session['login'] = account['userLogin']
                return redirect(url_for('home'))
            else:
                msg = 'Incorrect login/password!'
        return render_template('index.html', msg=msg)
    except MySQLdb.Error:
        return render_template('err.html')


@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('login', None)
   return redirect(url_for('login'))


@app.route('/register', methods=['POST', 'GET'])
def register():
    msg = ''
    try:
        if (request.method == 'POST'
        and 'username' in request.form
        and 'lastname' in request.form
        and 'DoB' in request.form
        and 'login' in request.form
        and 'password' in request.form
        and 'email' in request.form
        and 'pesel' in request.form):
            username = request.form['username']
            lastname = request.form['lastname']
            DoB = request.form['DoB']
            login = request.form['login']
            password = request.form['password']
            email = request.form['email']
            creationdate = datetime.datetime.utcnow()
            modifydate = creationdate
            pesel = request.form['pesel']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM users WHERE userLogin = %s', (login,))
            account = cursor.fetchone()
            if account:
                msg = 'Account already exists!'
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                msg = 'Invalid email address!'
            elif not re.match(r'^\d{11}$', pesel):
                msg = 'Invalid PESEL!'
            elif not re.match(r'[A-Za-z0-9]+', username):
                msg = 'Username must contain only characters and numbers!'
            elif not re.match(r'[A-Za-z0-9]+', login):
                msg = 'Login must contain only characters and numbers!'
            elif not username or not lastname or not DoB or not login or not password or not email or not pesel:
                msg = 'Please fill out the form!'
            else:
                password = hashPassword(password)
                cursor.execute('INSERT INTO users VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                               (username, lastname, DoB, login, password, email, creationdate, modifydate, pesel))
                mysql.connection.commit()
                msg = 'You have successfully registered!'
        elif request.method == 'POST':
            msg = 'Please fill out the form!'
        return render_template('register.html', msg=msg)
    except MySQLdb.Error:
        return render_template('err.html')

@app.route('/home')
@app.route('/')
def home():

    try:
        if 'loggedin' in session:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT ms.matchId as matchId, ms.homeTeam as home, ms.awayTeam as away, st.stadiumName, ms.date, st.address '
                           'FROM matchSchedule ms JOIN stadium st ON st.stadiumId=ms.stadium WHERE ms.date > NOW() ORDER BY ms.matchId ASC')
            fixture = cursor.fetchmany(5)
            return render_template('home.html', login=session['login'], fixture=fixture)
        return redirect(url_for('login'))
    except MySQLdb.Error:
        return render_template('err.html')


@app.route('/profile', methods=["POST", "GET"])
def profile():
    try:
        if 'loggedin' in session:

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT userId as ID, userName as Name, userLastName as "Last name", userLogin as Login, '
                           'userDoB as "Date of birth", userCreationDate as "Creation date", userModifyDate as "Modify date", '
                           'userPESEL as PESEL FROM users WHERE userId = %s', (session['id'],))
            account = cursor.fetchone()

            cursor.execute('SELECT ms.matchId as matchId, ms.homeTeam as home, ms.awayTeam as away, st.stadiumName, ms.date, st.address, s.sector as sect, s.column as col, s.row as row FROM matchSchedule ms '
                           'JOIN stadium st ON st.stadiumId=ms.stadium JOIN reservation r ON (r.match=ms.matchId and r.user=%s) JOIN seats s ON (r.seat=s.seatId) ORDER BY ms.matchId ASC', (session['id'],))
            reservations = cursor.fetchall()

            if request.method == "POST" and request.form["loginChange"] == "loginChange":
                try:
                    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    userLogin = request.form["userLogin"]
                    cursor.execute('UPDATE users SET userLogin = %s WHERE userId=%s', (userLogin, session['id']))
                    mysql.connection.commit()
                    message = "Success"

                    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cursor.execute(
                        'SELECT userId as ID, userName as Name, userLastName as "Last name", userLogin as Login, '
                        'userDoB as "Date of birth", userCreationDate as "Creation date", userModifyDate as "Modify date", '
                        'userPESEL as PESEL FROM users WHERE userId = %s', (session['id'],))
                    account = cursor.fetchone()

                    return render_template('profile.html', account=account, reservations=reservations, message=message)
                except MySQLdb._exceptions.OperationalError as err:
                    message=err
                    return render_template('profile.html', account=account, reservations=reservations, message=message)

            return render_template('profile.html', account=account, reservations=reservations)
        return redirect(url_for('login'))
    except MySQLdb.Error:
        return render_template('err.html')


@app.route('/fixtures')
def fixtures():

    try:
        if 'loggedin' in session:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT ms.matchId as matchId, ms.matchweekNo as matchweek, ms.homeTeam as home, ms.awayTeam as away, st.stadiumName, CAST(ms.date AS char) AS date, st.address '
                           'FROM matchSchedule ms JOIN stadium st ON st.stadiumId=ms.stadium ORDER BY ms.matchId ASC')
            fixture = cursor.fetchall()
            fixturejs = json.dumps(fixture)

            cursor2 = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor2.execute('SELECT ms.matchId, ms.matchweekNo as matchweek FROM matchSchedule ms WHERE ms.date > NOW() ORDER BY ms.matchId ASC')
            currentMatchweek = cursor2.fetchone()
            currentMatchweekjs = json.dumps(currentMatchweek)
            cursor3 = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor3.execute('SELECT DISTINCT ms.matchweekNo as matchweek FROM matchSchedule ms ORDER BY ms.matchId ASC')
            allMatchweeks = cursor3.fetchall()
            allMatchweeks = json.dumps(allMatchweeks)
            reservationCtr = {}
            for j in range(1, 39):
                cursor4 = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor4.execute(f'SELECT countReservation({j})')
                val = cursor4.fetchone()
                val = val[f'countReservation({j})']

                reservationCtr[f"{j}"] = val

            currentReservationCtr = reservationCtr[f"{currentMatchweek['matchweek']}"]
            reservationCtr = json.dumps(reservationCtr)


            return render_template('fixtures.html', fixture=fixture, fixturejs=fixturejs, currentMatchweek=currentMatchweek, currentMatchweekjs=currentMatchweekjs, allMatchweeks=allMatchweeks, reservationCtr=reservationCtr, currentReservationCtr=currentReservationCtr)

        return redirect(url_for('login'))
    except MySQLdb.Error:
        return render_template('err.html')


@app.route('/reservation', methods=["POST", "GET"])
def reservation():
    try:
        if 'loggedin' in session:
            if request.method != "POST":
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT teamName FROM stadium')
                teams = cursor.fetchall()
                return render_template('reservation.html', teams=teams, fixtures=None)
            elif request.method == "POST" and request.form["submit1"]=="submit":
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                team = request.form["teamSelection"]
                cursor.execute('SELECT ms.matchId as matchId, ms.homeTeam as home, ms.awayTeam as away, st.stadiumName, ms.date, st.address '
                               'FROM matchSchedule ms JOIN stadium st ON st.stadiumId=ms.stadium WHERE ms.date > NOW() AND (ms.homeTeam = %s OR ms.awayTeam = %s) ORDER BY ms.matchId ASC', (team, team))
                fixtures = cursor.fetchall()
                return render_template('reservation.html', teams=None, fixtures=fixtures, team=team)

        return redirect(url_for('login'))
    except MySQLdb.Error:
        return render_template('err.html')


@app.route('/reservation/<matchId>', methods=["POST", "GET"])
def seat_reservation(matchId):
    try:
        if 'loggedin' in session:
            if request.method != "POST":
                return render_template('reservation.html', teams=None, fixtures=None, matchId=matchId)
            elif request.method == "POST" and request.form["Book"]=="Book":
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                sector = request.form["sector"]
                column = request.form["column"]
                row = request.form["row"]
                matchId = request.form["matchId"]

                cursor.execute('INSERT INTO seats VALUES (NULL, %s, %s, %s, %s)', (column, sector, row, 15))
                mysql.connection.commit()

                cursor.execute('SELECT seatId FROM seats ORDER BY seatId DESC LIMIT 1')
                seatId = cursor.fetchone()

                cursor.execute('INSERT INTO reservation VALUES (NULL, %s, %s, %s)', (matchId, session['id'], seatId["seatId"]))
                mysql.connection.commit()

                return redirect(url_for('home'))

        return redirect(url_for('login'))
    except MySQLdb.Error:
        return render_template('err.html')


def hashPassword(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(b'skad wracali litwini? z nocnej wracali wycieczki').hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                                  salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return pwdhash.decode('ascii')

app.run(host='localhost', port=5000)