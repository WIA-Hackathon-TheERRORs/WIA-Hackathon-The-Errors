# -*- coding: utf-8 -*-
"""
Created on Tue Jun 15 05:56:53 2021

@author: Administrator
"""

from flask import Flask, render_template, request, redirect, url_for
from cloudant.client import Cloudant
from twilio.rest import Client


def login(email_id, pwd, user_type):
    my_database = client[user_type]
    selector = {'email_id': {'$eq': email_id},'password' : {'$eq' : pwd}}
    docs = my_database.get_query_result(selector)
    docid = "";
    for doc in docs:
        print("User Found!")
        docid = doc['_id']
        return docid
    print("User Not Found!")
    return docid

def getUserName(docid, user_type):
    my_database = client[user_type]
    my_document = my_database[docid]
    return my_document['name']

def sendSMS(mobile):
    account_sid = "AC23e7189b21c4743e02d5ee4afa901bbc"
    auth_token = "7dd01fb94ed11d8ebe91fc0f0873542f"
    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
                              body='Hi there ! Someone requested for a scribe . Will you like to write their exam? If yes, go to your scribe account for more details',
                              from_='+16193892216',
                              to=mobile
                          )
    except Exception as e:
        print("An exception occured in sendSMS()"+str(e))
    return

def sendSMS2(mobile):
    account_sid = "AC23e7189b21c4743e02d5ee4afa901bbc"
    auth_token = "7dd01fb94ed11d8ebe91fc0f0873542f"
    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
                              body='Hi there ! Your request for a scribe has been accepted by a volunteer. Please go to ypur scribe account for more details',
                              from_='+16193892216',
                              to=mobile
                          )
    except Exception as e:
        print("An exception occured in sendSMS2()"+str(e))
    return
def raiseExamRequest(exam_name,venue,language,docid,exam_date,start_time,end_time,city,state,zip_code,email,contact):
    my_database = client['volunteer']
    selector = {'language': {'$eq': language}}
    docs = my_database.get_query_result(selector)
    applicable_vol = []
    contactnos = []
    for doc in docs:
        applicable_vol.append(doc['_id'])
        contactnos.append(doc['mobile'])
    print("hey mobile")
    data = {
    'exam_name': exam_name,
    'venue': venue,
    'language': language,
    'applicable_vol': applicable_vol,
    'creator' : docid,
    'exam_date' : exam_date,
    'start_time' : start_time,
    'end_time' : end_time,
    'city' : city,
    'state' : state,
    'zip_code' : zip_code,
    'email' : email,
    'contact' : contact,
    'scribe' : ""
    }
    my_database = client['exam_request']
    my_document = my_database.create_document(data)
    if my_document.exists():
       for mobile in contactnos:
           sendSMS(mobile)
       return True
    return False  
app = Flask(__name__,static_url_path='/home')

@app.route('/volunteer_home.html/<docid>', methods=['GET','POST'])
def getVolunteerDetails(docid):
    try:
        my_database = client['exam_request']
        selector = { "applicable_vol": {"$elemMatch": {"$eq": docid}}}
        docs = my_database.get_query_result(selector)
        name = getUserName(docid,'volunteer')
        if request.method == 'GET':
            print('-----------------------------------------------In GET')
            exam_request = []
            accepted_request = []
            for doc in docs:
                data = {}
                data['exam_name'] = doc['exam_name']
                data['venue'] = doc['venue']
                data['creator'] = getUserName(doc['creator'],'student')
                data['exam_date'] = doc['exam_date']
                data['start_time'] = doc['start_time']
                data['end_time'] = doc['end_time']
                data['city'] = doc['city']
                data['state'] = doc['state']
                data['zip_code'] = doc['zip_code']
                data['email'] = doc['email']
                data['contact'] = doc['contact']
                data['_id'] = doc['_id']
                if(doc['scribe'] == ""):
                    exam_request.append(data)
                elif(doc['scribe'] == docid):
                    accepted_request.append(data) 
            print(len(exam_request))
            print(len(accepted_request))
            return render_template('volunteer_home.html', length=len(exam_request),exam_request=exam_request,name = name,accepted_length = len(accepted_request),accepted_request=accepted_request)
        if request.method == 'POST':
            if request.form.get("accept"):
                print('-----------------------------------------------In accept')
                req_no = request.form['req_no']
                print(type(req_no))
                my_document = my_database[req_no]
                my_document['scribe'] = docid
                my_document.save()
                print("hey1")
                student_id = my_document['creator']
                print("hey2")
                student_db = client['student']
                print("hey3")
                student_mobile = student_db[student_id]['mobile']
                sendSMS2(student_mobile)
                print("msg send")
                return redirect(url_for('getVolunteerDetails' , docid = docid))
        else:
            return render_template('index.html')
       
    except Exception as e:
        print("An exception occured in samplefunction()"+str(e))
        

@app.route('/student_home.html/<docid>', methods=['GET','POST'])
def getStudentDetails(docid):
    print("hey")
    try:
        if request.method == 'GET':
            print('-----------------------------------------------In GET')
            my_database = client['exam_request']
            selector = { "creator": {"$eq": docid}}
            docs = my_database.get_query_result(selector)
            name = getUserName(docid,'student')
            exam_request = []
            for doc in docs:
                data = {}
                data['exam_name'] = doc['exam_name']
                if(doc['scribe'] != ""):
                    data['scribe'] = getUserName(doc['scribe'],'volunteer')
                    volunteer_db = client['volunteer']
                    data['email'] = volunteer_db[doc['scribe']]['email_id']
                    data['contact'] = volunteer_db[doc['scribe']]['mobile']
                else:
                    data['scribe'] = ""
                exam_request.append(data)
            print(docid)
            return render_template('student_home.html',length=len(exam_request),exam_request=exam_request,name=name)
        if request.method == 'POST':
            if request.form.get("exam_request"):
                
                print('-----------------------------------------------In exam request')
                exam_name = request.form['exam_name']
                venue = request.form['venue']
                language = request.form['language']
                exam_date = request.form['exam_date']
                start_time = request.form['start_time']
                end_time = request.form['end_time']
                city = request.form['city']
                state = request.form['state']
                zip_code = request.form['zip']
                email = request.form['eaddress']
                contact = request.form['phone']
                if(raiseExamRequest(exam_name,venue,language,docid,exam_date,start_time,end_time,city,state,zip_code,email,contact)):
                    print("Request created")
                return redirect(url_for('getStudentDetails', docid = docid))
        else:
            return render_template('index.html')
        
    except Exception as e:
        print("An exception occured in samplefunction()"+str(e))
        
     
@app.route('/', methods=['GET','POST'])
def samplefunction():
  
  try:
    if request.method == 'GET':
        print('-----------------------------------------------In GET')
        
        return render_template('index.html')
    
    if request.method == 'POST':
        print('-----------------------------------------------In POST')
        email_id = request.form['email_id']
        pwd = request.form['pwd']
        print(email_id)
        print(pwd)
        if request.form.get("form1"):
            docid = login(email_id, pwd, 'student');
            if(len(docid) != 0):
                return redirect(url_for('getStudentDetails', docid = docid))
        elif request.form.get("form2"):
            docid = login(email_id, pwd, 'volunteer');
            if(len(docid) != 0):
                return redirect(url_for('getVolunteerDetails' , docid = docid))
        else:
            return render_template('index.html')
        
    
  except Exception as e:
        print("An exception occured in samplefunction()"+str(e))

        
if __name__ == "__main__":
    
    client = Cloudant.iam("3ec6f5ba-c5cf-4b25-8f37-b259bbed85ca-bluemix", 'N92W5RIX-VLaog-5zUXomrDpTcC4ofKiEV-FIlWn5So8', connect=True)
    session = client.session()
    print("db connection started")
    app.run(host='0.0.0.0', port=8080, debug=False)
    client.disconnect()
    print("db connection ended")