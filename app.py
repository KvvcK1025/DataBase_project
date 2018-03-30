from flask import Flask, render_template, flash ,redirect, request, url_for, session , logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, RadioField, DateField
from passlib.hash import sha256_crypt
from functools import wraps
from wtforms.fields.html5 import DateField


app = Flask(__name__)

# config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'iiita123'
app.config['MYSQL_DB'] = 'MobileVoting'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#init MYSQL
mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')


class Registerform(Form):
    name = StringField('Name*',[validators.Length(min=1,max=30)])
    gender = RadioField(
        'Gender?',
        [validators.Required()],
        choices=[('M', 'Male'), ('F', 'Female'),('F', 'Other')], default='M'
    )
    # dob = StringField('Date of Birth(YYYY-MM-DD)*',[validators.Length(min=10,max=10)])
    dob = DateField('DatePicker', format='%Y-%m-%d')
    aadhaar_no = StringField('Aadhaar Number*',[validators.Length(min=12,max=16)])
    father_name = StringField('Father Name*',[validators.Length(min=1,max=30)])
    address = StringField('Address*',[validators.Length(min=1,max=30)])
    city = StringField('City*',[validators.Length(min=1,max=30)])
    pincode = StringField('Pincode*',[validators.Length(min=6,max=6)])
    state = StringField('State*',[validators.Length(min=1,max=30)])
    phone = StringField('Phone Number*',[validators.Length(min=10,max=11)])
    email_id = StringField('Email-ID')
    password = PasswordField('Password*',[
        validators.DataRequired(),
        validators.EqualTo('confirm', message='passwords do not match')
    ])
    confirm = PasswordField('Confirm Password*')

@app.route('/register',methods=['GET','POST'])
def register():
    form =Registerform(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        gender = form.gender.data
        # dob = form.dob.data
        dob = form.date.data.strftime('%Y-%m-%d')
        aadhaar_no = form.aadhaar_no.data
        father_name = form.father_name.data
        address = form.address.data
        city = form.city.data
        pincode = form.pincode.data
        state = form.state.data
        phone = form.phone.data
        email_id =form.email_id.data
        password = sha256_crypt.encrypt(str(form.password.data))
	
	cur =mysql.connection.cursor()

        #get user by username
        result = cur.execute("SELECT * FROM Voter WHERE AadhaarNumber=%s",[aadhaar_no])
        if result>0 :
            
            error = 'Already a user! Try logging in'
            return render_template('login.html', error = error)
            # cur close
            cur.close()

        #Create cursor
        cur = mysql.connection.cursor()

        #execute query
        cur.execute("INSERT INTO Voter(Name, Gender, DateOfBirth, AadhaarNumber, FatherName, Address, PinCode, MobileNumber, EmailId, Password) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",(name, gender, dob, aadhaar_no, father_name, address, pincode, phone, email_id, password))
	
        #Commit to DB
        mysql.connection.commit()

        #close connection
        cur.close()
	
	cur = mysql.connection.cursor()
	cur.execute("INSERT INTO City(PinCode,ConstituencyId) VALUES(%s,%s)",(pincode,result))
	#Commit to DB
        mysql.connection.commit()

        #close connection
        cur.close()

        

        flash('you are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html',form=form)

#user login
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method =='POST':
        #get form feilds
        username = request.form['aadhaar']
        password_candidate = request.form['password']

        #craete cursor

        cur =mysql.connection.cursor()

        #get user by username
        result = cur.execute("SELECT * FROM Voter WHERE AadhaarNumber=%s",[username])
        if result>0 :
            #get hash
            data = cur.fetchone()
            password = data['Password']

            #campare passwords
            if sha256_crypt.verify(password_candidate, password):
                #passed
                session['logged_in'] = True
                session['username'] = username

                flash('you are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error = error)
            # cur close
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error = error)

    return render_template('login.html')

# check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please login', 'danger')
            return redirect(url_for('login'))
    return wrap


#logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('you are now logged out','success')
    return redirect(url_for('login'))


@app.route('/dashboard')
@is_logged_in
def dashboard():
    #create cursor
    cur = mysql.connection.cursor()

    #get articles
    result=cur.execute("SELECT * FROM Voter")

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg= 'No Articles Found'
        return render_template('dashboard.html',msg=msg)
    
    #close connection
    cur.close()

#Article form class
class ArticleForm(Form):
    title = StringField('Title',[validators.Length(min=1,max=200)])
    body = TextAreaField('Body',[validators.Length(min=30)])


if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)

