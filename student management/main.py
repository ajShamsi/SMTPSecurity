from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_manager, LoginManager
from flask_login import login_required, current_user
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from flask_migrate import Migrate
import json


# MY db connection
local_server= True
app = Flask(__name__)
app.config['SECRET_KEY']='Define_The_Key'

#for email part
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = '' #these two fileds are kept blank for confidential issues, use your own mail n password
app.config['MAIL_PASSWORD'] = '' #we're using local host so keeping our info here won't work in your end anyway
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

s = URLSafeTimedSerializer('keepitcute!')

# this is for getting unique user access
login_manager=LoginManager(app)
login_manager.login_view='login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:@localhost/studentnet' 
#here studentnet is the name of our database so change it according to your database name
db=SQLAlchemy(app)

# here we will create db models that is tables
class Test(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100))
    email=db.Column(db.String(100))

class Department(db.Model):
    cid=db.Column(db.Integer,primary_key=True)
    branch=db.Column(db.String(100))

class Attendence(db.Model):
    aid=db.Column(db.Integer,primary_key=True)
    rollno=db.Column(db.String(100))
    attendance=db.Column(db.Integer())

class Trig(db.Model):
    tid=db.Column(db.Integer,primary_key=True)
    rollno=db.Column(db.String(100))
    action=db.Column(db.String(100))
    timestamp=db.Column(db.String(100))


class User(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(50))
    email=db.Column(db.String(50),unique=True)
    password=db.Column(db.String(1000))

class Student(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    rollno=db.Column(db.String(50))
    sname=db.Column(db.String(50))
    sem=db.Column(db.Integer)
    gender=db.Column(db.String(50))
    branch=db.Column(db.String(50))
    email=db.Column(db.String(50))
    number=db.Column(db.String(12))
    address=db.Column(db.String(100))
    

@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/about')
def about(): 
    return render_template('about.html')

@app.route('/studentdetails')
def studentdetails():
    with db.engine.begin() as conn:
        query = text("SELECT * FROM `student`")
        result = conn.execute(query) 
    return render_template('studentdetails.html',query=result)

@app.route('/triggers')
def triggers():
    with db.engine.begin() as conn:
        query = text("SELECT * FROM `trig`")
        result = conn.execute(query)
    return render_template('triggers.html',query=result)

@app.route('/department',methods=['POST','GET'])
def department():
    if request.method=="POST":
        dept=request.form.get('dept')
        query=Department.query.filter_by(branch=dept).first()
        if query:
            flash("Department Already Exist","warning")
            return redirect('/department')
        dep=Department(branch=dept)
        db.session.add(dep)
        db.session.commit()
        flash("Department Added","success")
    return render_template('department.html')

@app.route('/addattendance',methods=['POST','GET'])
def addattendance():
     
    if request.method=="POST":
        rollno=request.form.get('rollno')
        attend=request.form.get('attend')
        print(attend,rollno)
        with db.engine.begin() as conn:
            query = text("INSERT INTO `attendence` (`rollno`, `attendance`) VALUES (:rollno, :attendance)")
            conn.execute(query, {"rollno": rollno, "attendance": attend})
        
        flash("Attendance added","warning")

    with db.engine.begin() as conn:
        query = text("SELECT * FROM `student`")
        result = conn.execute(query)
        
    return render_template('attendance.html',query=result)

@app.route('/search',methods=['POST','GET'])
def search():
    if request.method=="POST":
        rollno=request.form.get('roll')
        bio=Student.query.filter_by(rollno=rollno).first()
        attend=Attendence.query.filter_by(rollno=rollno).first()
        return render_template('search.html',bio=bio,attend=attend)
        
    return render_template('search.html')

@app.route("/delete/<string:id>",methods=['POST','GET'])
@login_required
def delete(id):
    with db.engine.begin() as conn:
        query = text("DELETE FROM `student` WHERE `student`.`id` = :id")
        conn.execute(query, {"id": id})

    flash("Student Details Deleted Successfully","danger")
    return redirect('/studentdetails')

@app.route("/edit/<string:id>",methods=['POST','GET'])
@login_required
def edit(id):
      
    if request.method=="POST":
        rollno=request.form.get('rollno')
        sname=request.form.get('sname')
        sem=request.form.get('sem')
        gender=request.form.get('gender')
        branch=request.form.get('branch')
        email=request.form.get('email')
        num=request.form.get('num')
        address=request.form.get('address')
        
        post=Student.query.filter_by(id=id).first()
        post.rollno=rollno
        post.sname=sname
        post.sem=sem
        post.gender=gender
        post.branch=branch
        post.email=email
        post.number=num
        post.address=address
        db.session.commit()
        flash("Student information is Updated","success")
        return redirect('/studentdetails')
    dept=Department.query.all()
    posts=Student.query.filter_by(id=id).first()
    return render_template('edit.html',posts=posts,dept=dept)


@app.route('/signup',methods=['POST','GET'])
def signup():
    if request.method == "POST":
        username=request.form.get('username')
        email=request.form.get('email')
        password=request.form.get('password')
        user=User.query.filter_by(email=email).first()
        if user:
            flash("Email Already Exist","warning")
            return render_template('/signup.html')
        encpassword=generate_password_hash(password)

        with db.engine.begin() as conn:
            query = text("INSERT INTO `user` (`username`,`email`,`password`) VALUES (:username, :email, :password)")
            conn.execute(query, {"username": username, "email": email, "password": encpassword})

        token = s.dumps(email,salt='emailconfirmation')
        #send email with activation link
        send_activation_email(email, token, username, password)
        flash ("A confirmation link sent to your gmail account", "warning")
        
    return render_template('signup.html')

def send_activation_email(email, token, username, password):
    
    msg = Message('Account Activation', sender='your_email@example.com', recipients=[email])
    
    activation_link = url_for('activate_account', token=token, _external=True)
    
    msg.body = f"Click the following link to activate your account: {activation_link}"
    
    mail.send(msg)

@app.route('/activate/<token>')
def activate_account(token):
    try:
        # Verify the token
        email = s.loads(token, salt='emailconfirmation', max_age=3600)
        
        activate_user(email)
        flash("Account activated successfully", "success")
    except:
        flash("Invalid or expired token", "error")
    return redirect(url_for('login'))

def activate_user(email):
    user = User.query.filter_by(email=email).first()
    if user:
        db.session.commit()

@app.route('/login',methods=['POST','GET'])
def login():
    if request.method == "POST":
        email=request.form.get('email')
        password=request.form.get('password')
        user=User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password,password):
            login_user(user)
            
            return redirect(url_for('index'))
        else:
            flash("invalid credentials","danger")
            return render_template('login.html')    

    return render_template('login.html')

@app.route('/resetPassword', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            # Generate password reset token
            token = generate_password_reset_token(user)
            # Send the password reset email
            send_password_reset_email(user, token)
            flash('A password reset link has been sent to your email.', 'info')
        else:
            flash('Invalid email. Please try again.', 'danger')
    return render_template('resetPassword.html')

def generate_password_reset_token(user):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(user.id, salt='password_reset')

def send_password_reset_email(user, token):
    reset_link = url_for('reset_password_confirm', token=token, _external=True)
    msg = Message('Password Reset', sender='your_email@example.com', recipients=[user.email])
    msg.body = f"Click the following link to reset your password: {reset_link}"
    mail.send(msg)

@app.route('/resetPasswordConfirm/<token>', methods=['GET', 'POST'])
def reset_password_confirm(token):
    try:
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        user_id = serializer.loads(token, salt='password_reset', max_age=3600)
        user = User.query.get(user_id)
        if user:
            if request.method == 'POST':
                password = request.form.get('password')
                user.password = generate_password_hash(password)
                db.session.commit()
                flash('Your password has been reset successfully.', 'success')
                return redirect(url_for('login'))
        else:
            flash('Invalid or expired token. Please try again.', 'danger')
    except:
        flash('Invalid or expired token. Please try again.', 'danger')
    return render_template('resetPasswordConfirm.html', token=token)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout SuccessFul","warning")
    return redirect(url_for('login'))

@app.route('/addstudent', methods=['POST', 'GET'])
@login_required
def addstudent():
    with db.engine.begin() as conn:
        query = text("SELECT * FROM department")
        result = conn.execute(query)

    if request.method == "POST":
        rollno = request.form.get('rollno')
        sname = request.form.get('sname')
        sem = request.form.get('sem')
        gender = request.form.get('gender')
        branch = request.form.get('branch')
        email = request.form.get('email')
        num = request.form.get('num')
        address = request.form.get('address')

        with db.engine.begin() as conn:
            query = text("INSERT INTO `student` (`rollno`, `sname`, `sem`, `gender`, `branch`, `email`, `number`, `address`) VALUES (:rollno, :sname, :sem, :gender, :branch, :email, :number, :address)")
            conn.execute(query, {"rollno": rollno, "sname": sname, "sem": sem, "gender": gender, "branch": branch, "email": email, "number": num, "address": address})

        flash("Information added", "info")

    return render_template('student.html', dept=result)


@app.route('/test')
def test():
    try:
        Test.query.all()
        return 'My database is Connected'
    except:
        return 'My db is not Connected'

app.run(debug=True)    
