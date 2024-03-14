from flask import Flask, render_template ,request, send_from_directory,Response,redirect,url_for,flash
import cv2
import os
import datetime
from flask import jsonify
import time
import requests
import fitz
import re
import scipy.misc
import warnings
from werkzeug.utils import secure_filename
from deepface import DeepFace
import matplotlib.pyplot as plt

import db
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy  import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config["IMAGE_UPLOADS"] = r"D:\PROJECT_AND_CODES\KYC_VERIFICATION\\"

app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///D:\PROJECT_AND_CODES\KYC_VERIFICATION\\database.db'
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
#db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    try:
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(15), unique=True)
        email = db.Column(db.String(50), unique=True)
        password = db.Column(db.String(80))
        fname = db.Column(db.String(1000))
        lname = db.Column(db.String(1000))
	status = db.Column(db.String(50), default="Not Verified")
        print("User created")
    except:
        print("User not created")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=6, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=6, max=80)])
    fname = StringField('first name', validators=[InputRequired(), Length(min=4)])
    lname = StringField('last name', validators=[InputRequired(), Length(min=4)])

#=======================ROUTES=================================================================

#-------------Home Page---------------------
@app.route('/')
def index():
    return render_template('home.html')

#--------------LOGIN PAGE-------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                print("Succefully Logged in user\n")
                return redirect(url_for('dashboard'))
        print("Invalid Username or Password\n")
        flash("Invalid username or password")  
        return redirect(url_for('login'))
        #return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'

    return render_template('login.html', form=form)

#---------------SIGNUP PAGE----------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password,fname=form.fname.data,lname=form.lname.data)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("New user has been created!")  
            print('New user has been created!\n') 
            return redirect(url_for('login'))
            #return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'
        except:
            print("There was an issue while adding new user") 

    return render_template('signup.html', form=form)
#------------------------DASHBOARD----------------------
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', fname=current_user.fname,lname=current_user.lname,uname=current_user.username,email=current_user.email)

#------------------------CREATED BY----------------------
@app.route('/created')
@login_required
def created():
    return render_template('created.html')

#------------------------PROFILE----------------------
@app.route('/profile')
@login_required
def profile():
    #f=open(app.config["IMAGE_UPLOADS"]+'comparison_result.txt','r')
    #st=f.read()
    #stat='Not Verified'
    #if st=='1':
    #    stat='Verified'
    #print('status : ',stat)
    return render_template('profile.html',status=current_user.status,password='******',fname=current_user.fname,lname=current_user.lname,uname=current_user.username,email=current_user.email)

#-----------Steps Routes-------------------
@app.route('/stp1')
def stp1():
    return render_template('stp1.html')

@app.route('/stp2')
def stp2():
    return render_template('stp2.html')

@app.route('/stp3')
def stp3():
    f=open(app.config["IMAGE_UPLOADS"]+'comparison_result.txt','r')
    res=f.read()
    print(res)
    print(type(res))
    if res=='0':
        return render_template('stp3.html',result=False,fname=current_user.fname,lname=current_user.lname)
    else:
        return render_template('stp3.html',result=True,fname=current_user.fname,lname=current_user.lname)

#--------------------------End Page------------------------------
@app.route('/end')
def endpage():
    return render_template('end.html')

#------------------LOGOUT--------------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('home2.html')

#------------Make New Dir DatTime.Now ----------------------------------   
@app.route("/upload-image", methods=["GET", "POST"])
def upload_image():
    dirname=''
    if request.method == "POST":
        if request.files:
            print("REQUEST FILES")
            image = request.files["image"]
            print("IMAGE")
            image.save(os.path.join(app.config["IMAGE_UPLOADS"]+'Uploads\\', image.filename))
            dirname=str(datetime.datetime.now())
            dirname=dirname.replace(':','')
            dirname=dirname.replace('-','')
            dirname=dirname.replace(' ','')
            newpath = r'D:\PROJECT_AND_CODES\KYC_VERIFICATION\\imgdatabase'+str(dirname) +'\\Dataset'
            print(image.filename)
            if not os.path.exists(newpath):
                os.makedirs(newpath)
            if allowed_pdf(image.filename):
                formImg(image.filename,dirname)     
            else:
                print(image.filename) 
                formDirectImg(image.filename,dirname)  
    return render_template('stp2.html',dirname=dirname)

#------------If the file is PDF----------------------------------------------------
def allowed_pdf(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() =='pdf'

count1=0
#-------------- Get Images from PDF & extracting Faces---------------------------------------
def formImg(fileName,dirname):
    doc = fitz.open(app.config["IMAGE_UPLOADS"]+'Uploads\\' + fileName)
    if len(doc)!=0:
        print(len(doc))
    counter = 0
    for i in range(len(doc)):
        for img in doc.getPageImageList(i):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            if pix.n < 5:       # this is GRAY or RGB
                pix.writePNG(app.config["IMAGE_UPLOADS"]+"pdf%s.png" % (i))
                counter += 1
            else:               # CMYK: convert to RGB first
                pix1 = fitz.Pixmap(fitz.csRGB, pix)
                pix1.writePNG(app.config["IMAGE_UPLOADS"]+"pdf%s.png" % (i))
                pix1 = None
                counter += 1
            pix = None
    global count1
    count1=0
    for i in range(0, counter):
        imagePath = r"D:\PROJECT_AND_CODES\KYC_VERIFICATION\pdf" +str(i)+".png"
        print(imagePath)
        image = cv2.imread(imagePath)
        print(image)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        print(gray)
        #create the haar cascade
        faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        #Detect faces in image
        faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=3,
            minSize=(30, 30)
        )
        
        print("[INFO] Found {0} Faces.".format(len(faces)))
        padding = 30
        #drawing the rectangles in the image
        for (x, y, w, h) in faces:
            image = cv2.rectangle(image, (x-padding, y-padding),(x + w+padding, y + h+padding), (0, 255, 0), 2)
            roi_color = image[y-30:y + h+30, x-30:x + w+30]
            print("[INFO] Object found. Saving locally.")
            #if(count==0):
            cv2.imwrite(f'D:\PROJECT_AND_CODES\KYC_VERIFICATION\\imgdatabase{dirname}\\Dataset\\face'+str(count1)+'.jpg', roi_color)
            count1=count1+1
        status = cv2.imwrite('D:\PROJECT_AND_CODES\KYC_VERIFICATION\\faces_detected.jpg', image)
        print('count: ',count1)
        print("[INFO] Image faces_detected.jpg written to filesystem: ", status)
    return ''

#-------------------Getting faces from Image directly---------------------------------
def formDirectImg(filename,dirname):
    print("OK NO PDF ONLY IMAGE")
    global count1
    count1=0
    image = cv2.imread(app.config["IMAGE_UPLOADS"] +'Uploads\\'+ filename)
    print(filename,dirname)
    print("Image : ")
    #print(image)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    print(gray)
    #create the haar cascade
    faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    #Detect faces in image
    faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.3,
            minNeighbors=3,
            minSize=(30, 30)
    )
    print("[INFO] Found {0} Faces.".format(len(faces)))
    padding = 30
    #drawing the rectangles in the image
    for (x, y, w, h) in faces:
        image = cv2.rectangle(image, (x-padding, y-padding),(x + w+padding, y + h+padding), (0, 255, 0), 2)
        roi_color = image[y-30:y + h+30, x-30:x + w+30]
        print("[INFO] Object found. Saving locally.")
        #if(count1==0):
        cv2.imwrite(f'D:\PROJECT_AND_CODES\KYC_VERIFICATION\\imgdatabase{dirname}\\Dataset\\face'+str(count1)+'.jpg', roi_color)
        count1=count1+1
    status = cv2.imwrite('D:\PROJECT_AND_CODES\KYC_VERIFICATION\\faces_detected.jpg', image)
    print("[INFO] Image faces_detected.jpg written to filesystem: ", status)
    return ''



#-------------------------------CAM SCREENSHOT CODE------------------------------------
@app.route('/opencamera',methods=['GET','POST'])    
def camera():
    dirname=request.form['dirname']
    t=int(1500)
    cam = cv2.VideoCapture(0)
    cv2.namedWindow("Test")
    count = 0
    while True and t:
        ret,img=cam.read()
        cv2.imshow("Test", img)
        cv2.waitKey(1)
        
        #cv2.imshow("Test",img)
        mins,secs=divmod(t,60)
		#timer='{:02d}:{02d}'.format(mins,secs)
        if(t==500 or t==1000):
            print("Image "+str(count)+"saved")
            cv2.imwrite(f'D:\PROJECT_AND_CODES\KYC_VERIFICATION\\imgdatabase{dirname}\\Dataset\\cam{str(count)}.jpeg', img)
            count +=1
            #time.sleep(1)
            
        time.sleep(0.01)
            
        t-=1
        #cv2.imshow("Test",img)
        if(t==0 and cv2.waitKey(1)):
            print("Close")
            break
    cam.release()
    cv2.destroyAllWindows() 
    compare(dirname)
    return redirect(url_for('stp3'))

#------------- Compare Images ------------------------

def compare(dirname):
    #surl="http://localhost:8000/api/v1/compare_faces"
    print('Compare')
    global count1
    print('Count1 : ',count1)
    for j in range(2):
        print('Path1 '+str(j))
        path1=f'D:\PROJECT_AND_CODES\KYC_VERIFICATION\\imgdatabase{dirname}\\Dataset\\cam'+str(j)+'.jpeg'
        for i in range(0,count1):
            print('Path2 '+str(i))
            try:
                path2=f'D:\PROJECT_AND_CODES\KYC_VERIFICATION\\imgdatabase{dirname}\\Dataset\\face'+str(i)+'.jpg'
                print('Comparing image cam'+str(j)+' & face'+str(i))
                result = DeepFace.verify(img1_path =path1,img2_path =path2, model_name = "VGG-Face", distance_metric = "cosine")
                threshold = 0.30 #threshold for VGG-Face and Cosine Similarity
                print("Is verified: ", result["verified"])
                f=open('D:\PROJECT_AND_CODES\KYC_VERIFICATION\\comparison_result.txt','w+')
                if result["verified"] == True:
                    f.write('1')
		    current_user.status="Verified"
                    return ''
                else:
                    f.write('0')
            except:
                print("There was an issue")
    return ''

#================RUN===============================================================================    

if __name__ == "__main__":
    app.run(debug=True)
    if not os.path.exists('D:\PROJECT_AND_CODES\KYC_VERIFICATION\database.db'):
        db.create_all()
        print("DATABASE CREATED\n")
    if not os.path.exists('D:\PROJECT_AND_CODES\KYC_VERIFICATION\database.db'):
        print("NO") 
