from flask import Flask, Blueprint, redirect, url_for, render_template, request, session, flash
# from admin.adminApp import adminApp
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import selectin_polymorphic

app = Flask(__name__)
# app.register_blueprint(adminApp, url_prefix="/admin")

app.secret_key = "hello"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(minutes=5)

db = SQLAlchemy(app)

class users(db.Model):
    _id = db.Column("id",db.Integer,primary_key=True)
    fullname = db.Column(db.String(100))
    email = db.Column(db.String(100))
    uname = db.Column(db.String(100))
    pswd = db.Column(db.String(100))

    def __init__(self,fullname,email,uname,pswd):
        self.fullname = fullname
        self.email = email
        self.uname = uname
        self.pswd = pswd

@app.route("/")
@app.route("/home")
def home():
	return render_template("index.html")

@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        uname = request.form["uname"]
        pswd = request.form["pswd"]

        found_user = users.query.filter_by(email=email).all()
        found_user2 = users.query.filter_by(uname=uname).all()

        if (found_user or found_user2):
           flash(f'User Already Exist. Pls, Login!','info') 
           return redirect(url_for("register"))
        else:
            user_info = users(fullname,email,uname,pswd)
            db.session.add(user_info)
            db.session.commit()
            flash(f'Registration Successful. You can now Login!','info')
            return redirect(url_for("register"))
    else:
        return render_template("register.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        uname = request.form["uname"]
        pswd = request.form["pswd"]

        found_user = users.query.filter_by(uname=uname).first()
        if found_user:
            orig_pswd = found_user.pswd
            # orig_uname = found_user.uname
            # Newuname = orig_uname[0:5]
            if orig_pswd == pswd:
                session.permanent = True
                session["user"] = found_user.uname

                if "Admin" in session["user"]:
                    flash(f'Admin Login Successfully!','info')
                    return redirect(url_for("admin"))
                else:
                    flash(f'Login Successfully!','info')
                    return redirect(url_for("user"))
            else:
                flash(f'Invalid Username/Password','info')
                return redirect(url_for("login"))
        else:
            flash(f'User Not Registered!','info')
            return redirect(url_for("login"))
    else:
        if "user" in session:
            if "Admin" in session["user"]:
                flash(f'Admin Already Logged In!','info')
                return redirect(url_for("admin"))
            else:
                flash(f'Already Logged In!','info')
                return redirect(url_for("user"))
            
        return render_template("login.html")

@app.route("/user")
def user():
    if "user" in session:
        user = session["user"]
        user_details = users.query.filter_by(uname=user).first()

        fname = user_details.fullname
        uemail = user_details.email
        funame = user_details.uname
        user_info = {'Full Name':fname, 'Email':uemail, 'Username':funame}

        return render_template("user.html",user=user, myinfo=user_info)
    else:
        flash(f'You are not logged in!','error')
        return redirect(url_for("login"))

@app.route("/forgetpswd", methods=['POST','GET'])
def forgetpswd():
    if request.method == "POST":
        uname = request.form["uname"]
        pswd = request.form["pswd"]
        cpswd = request.form["cpswd"]
        if (pswd != cpswd):
            flash(f'Password does not Match','error')
            return redirect(url_for("forgetpswd"))
        else:
            # Updating pswd
            rows_updated = users.query.filter_by(uname=uname).first()
            if (rows_updated):
                rows_updated.pswd = pswd
                db.session.commit()
                flash(f'Password Updated Successfully!','info')
                return redirect(url_for("forgetpswd"))
            else:
                flash(f'User does not Exist!','error')
                return redirect(url_for("forgetpswd"))     
    else:
        return render_template("forgetPassword.html")

@app.route("/about-us")
def aboutus():
    return render_template("about-us.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/admin")
def admin():
    if "user" in session:
        if "Admin" in session["user"]:
            user = session["user"]
            return render_template("admin_page.html",user=user, values=users.query.all())
        else:
            flash(f'Permission Denied!','error')
            return redirect(url_for("login"))
    else:
        flash(f'You are not logged in!','error')
        return redirect(url_for("login"))

@app.route("/admin/delete/<string:email>")
def adminDel(email):
    if "user" in session:
        if "Admin" in session["user"]:
            record_obj = db.session.query(users).filter(users.email==email).first()
            db.session.delete(record_obj)
            db.session.commit()
            flash(f'Record Deleted Successfully!','info')
            return redirect(url_for("admin"))
        else:
            flash(f'Permission Denied!','error')
            return redirect(url_for("login"))
    else:
        flash(f'You are not logged in!','error')
        return redirect(url_for("login"))

@app.route("/admin/update/<string:email>")
def adminUpdate(email):
    if "user" in session:
        if "Admin" in session["user"]:
            record_obj = db.session.query(users).filter(users.email==email).first()
            # print(record_obj)
            fullnameVal = record_obj.fullname
            emailVal = record_obj.email
            unameVal = record_obj.uname
            pswdVal = record_obj.pswd
            return render_template("updateinfo.html",fullname=fullnameVal,email=emailVal,uname=unameVal,pswd=pswdVal)
        else:
            flash(f'Permission Denied!','error')
            return redirect(url_for("login"))
    else:
        flash(f'You are not logged in!','error')
        return redirect(url_for("login"))

@app.route("/admin/updateInfo", methods=["POST", "GET"])
def adminUpdateInfo():
    if "user" in session:
        if "Admin" in session["user"]:
            if request.method == "POST":
                uname = request.form["uname"]
                fullname = request.form["fullname"]
                email = request.form["email"]
                pswd = request.form["pswd"]
                # Updating Data
                rows_updated = users.query.filter_by(uname=uname).first()
                rows_updated.uname = uname
                rows_updated.fullname = fullname
                rows_updated.email = email
                rows_updated.pswd = pswd
                db.session.commit()

                flash(f'Record Updated Successfully!','info')
                return redirect(url_for("admin"))
            else:
                return redirect(url_for("adminUpdateInfo"))
        else:
            flash(f'Permission Denied!','error')
            return redirect(url_for("login"))
    else:
        flash(f'You are not logged in!','error')
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    if "user" in session:
        user = session["user"]
        flash(f'You have been logged out, {user}','info')
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)