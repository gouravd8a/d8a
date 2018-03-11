from flask import Flask

import smtplib
import base64
from textwrap import dedent

app = Flask(__name__)

app.config['SECRET_KEY'] = 'hard to guess string'
app.config['TEMPLATES_AUTO_RELOAD'] = True




sender = 'rocking.boys11@gmail.com'
reciever = 'gourav.jjw2810@gmail.com'

message = 'hello'

try:
   smtpObj = smtplib.SMTP('localhost')
   smtpObj.sendmail(sender, reciever, message)
   print ("Successfully sent email")
except Exception as e:
   print (e)