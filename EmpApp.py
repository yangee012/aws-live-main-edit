from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'
table = 'payroll'

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('HomePage.html')

# @app.route("/about", methods=['POST'])
# def about():
#     return render_template('www.intellipaat.com')


@app.route("/toaddemp", methods=['GET', 'POST'])
def toAddEmp():
    return render_template('AddEmp.html')

@app.route("/tofetchemp", methods=['POST'])
def gofetchEmp():
    return render_template('GetEmp.html')

@app.route("/toattendance", methods=['GET', 'POST'])
def toAttend():
    return render_template('Attendance.html')

@app.route("/topayroll", methods=['GET', 'POST'])
def toPayroll():
    return render_template('Payroll.html')

@app.route("/todeleteEmp", methods=['GET', 'POST'])
def toDeleteEmp():
    return render_template('DeleteEmp.html')

@app.route("/tosearcheditEmp", methods=['GET', 'POST'])
def toEditEmp():
    return render_template('EditEmpSearch.html')

@app.route("/tomanageemp", methods=['GET', 'POST'])
def toManageEmp():
    return render_template('ManageEmployee.html')

@app.route("/tosearchbenefitemp", methods=['GET', 'POST'])
def toBenefitEmp():
    return render_template('BenefitEmpSearch.html')

@app.route("/addattendance", methods=['POST'])
def addAttend():
    duty_id = request.form['duty_id']
    emp_id = request.form['emp_id']
    date = request.form['date']
    duration = request.form['duration']

    if duty_id == "" or emp_id == "" or date == "" or duration == "":
        errorMsg = "Please fill in all the fields"
        buttonMsg = "BACK TO ATTENDANCE PAGE"
        action = "/toattendance"
        return render_template('ErrorPage.html', errorMsg=errorMsg, buttonMsg=buttonMsg, action=action)

    insert_attendance = "INSERT INTO duty VALUES (%s, %s, %s, %s)"
    cursor = db_conn.cursor()

    cursor.execute(insert_attendance, (duty_id, emp_id, date, duration))
    db_conn.commit()

    return render_template('AttendanceOutput.html', id=emp_id, date=date)  

@app.route("/viewattendance", methods=['POST'])
def getAllAttend():
    cur = db_conn.cursor()
    cur.execute("SELECT * FROM duty")
    data = cur.fetchall()
    return render_template('AttendanceAllOutput.html', data=data)



@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    if emp_id == "" or first_name == "" or last_name == "" or pri_skill == "" or location == "":
        errorMsg = "Please fill in all the fields"
        buttonMsg = "BACK TO ADD EMPLOYEE PAGE"
        action = "/toaddemp"
        return render_template('ErrorPage.html', errorMsg=errorMsg, buttonMsg=buttonMsg, action=action)

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    insert_payroll = "INSERT INTO payroll VALUES (%s, %s, %s, %s, %s, %s, %s)"
    insert_benefit = "INSERT INTO benefit VALUES (%s, %s)"
    cursor = db_conn.cursor()
    
    hourly_rate = 0
    hours_worked = 0
    leave_day = 0
    monthly_salary = 0
    
    emp_benefit = "No Benefit"

    if emp_image_file.filename == "":
        return "Please select a file"

    try:
        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location))
        cursor.execute(insert_payroll, (emp_id, first_name, last_name, hourly_rate, hours_worked, leave_day, monthly_salary))
        cursor.execute(insert_benefit, (emp_id, emp_benefit))

        #if statements to update hours_worked and hourly_rate in payroll table
        cursor.execute ("update payroll A, employee B set hourly_rate = 10, hours_worked = 8 where A.emp_id = B.emp_id and B.pri_skill = 'Cloud Computing'")
        cursor.execute ("update payroll A, employee B set hourly_rate = 15, hours_worked = 8 where A.emp_id = B.emp_id and B.pri_skill = 'R Programming'")
        cursor.execute ("update payroll A, employee B set hourly_rate = 20, hours_worked = 8 where A.emp_id = B.emp_id and B.pri_skill = 'C++ Programming'")
        cursor.execute ("update payroll A, employee B set hourly_rate = 25, hours_worked = 8 where A.emp_id = B.emp_id and B.pri_skill = 'Java Programming'")
        cursor.execute ("update payroll A, employee B set hourly_rate = 30, hours_worked = 8 where A.emp_id = B.emp_id and B.pri_skill = 'Python Programming'")
        cursor.execute ("update payroll A, employee B set hourly_rate = 35, hours_worked = 8 where A.emp_id = B.emp_id and B.pri_skill = 'SQL'")
        cursor.execute ("update payroll A, employee B set hourly_rate = 40, hours_worked = 8 where A.emp_id = B.emp_id and B.pri_skill = 'Machine Learning'")

        # #update monthly salary in payroll table
        # cursor.execute ("update payroll set monthly_salary = (hours_worked * hourly_rate)")
        
        #update monthly salary in payroll table
        cursor.execute ("update payroll set monthly_salary = (hours_worked * hourly_rate)")
        
        #insert month
        update_month_sql = "update payroll set month = MONTHNAME(CURDATE()) where emp_id = (%s)"
        cursor.execute(update_month_sql, (emp_id))


        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)



def show_image(bucket):
    s3_client = boto3.client('s3')
    public_urls = []

    emp_id = request.form['emp_id']

    try:
        for item in s3_client.list_objects(Bucket=bucket)['Contents']:
            presigned_url = s3_client.generate_presigned_url('get_object', Params = {'Bucket': bucket, 'Key': item['Key']}, ExpiresIn = 100)
            
            if emp_id in presigned_url:
                public_urls.append(presigned_url)

    except Exception as e:
        pass
    # print("[INFO] : The contents inside show_image = ", public_urls)
    return public_urls

@app.route("/fetchemp", methods=['GET','POST'])
def fetchEmp():
    emp_id = ""
    emp_id = request.form['emp_id']

    if emp_id == "":
        errorMsg = "Please fill in all the fields"
        buttonMsg = "BACK TO SEARCH EMPLOYEE PAGE"
        action = "/tofetchemp"
        return render_template('ErrorPage.html', errorMsg=errorMsg, buttonMsg=buttonMsg, action=action)

    cur = db_conn.cursor()
    select_sql = "SELECT * FROM employee where emp_id = (%s)"
    cur.execute(select_sql, (emp_id))

    if cur.rowcount == 0:
        errorMsg = "The employee ID is not exist"
        buttonMsg = "BACK TO SEARCH EMPLOYEE PAGE"
        action = "/tofetchemp"
        return render_template('ErrorPage.html', errorMsg=errorMsg, buttonMsg=buttonMsg, action=action)


    contents = show_image(custombucket)
    data = cur.fetchall()

    return render_template('GetOneEmp.html', emp_id=emp_id, data=data, contents=contents)



@app.route("/getemp", methods=['GET','POST'])
def getEmp():
    cur = db_conn.cursor()
    cur.execute("SELECT * FROM employee")
    data = cur.fetchall()
    return render_template('GetEmpOutput.html', data=data)



#delete employee
@app.route("/deleteemp", methods=['POST'])
def deleteEmp():
    emp_id = request.form['emp_id']

    if emp_id == "":
        errorMsg = "Please fill in all the fields"
        buttonMsg = "BACK TO DELETE EMPLOYEE PAGE"
        action = "/todeleteEmp"
        return render_template('ErrorPage.html', errorMsg=errorMsg, buttonMsg=buttonMsg, action=action)

    cur = db_conn.cursor()
    delete_emp_sql = "DELETE from employee WHERE emp_id = %s"
    cur.execute(delete_emp_sql, (emp_id))

    if cur.rowcount == 0:
        errorMsg = "The employee ID is not exist"
        buttonMsg = "BACK TO DELETE EMPLOYEE PAGE"
        action = "/todeleteEmp"
        return render_template('ErrorPage.html', errorMsg=errorMsg, buttonMsg=buttonMsg, action=action)


    db_conn.commit()
    # data = cur.fetchall()

    emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
    s3_client = boto3.client('s3')
    
    try:
        s3_client.delete_object(Bucket=custombucket, Key=emp_image_file_name_in_s3)
        return render_template('DeleteEmpOutput.html', id = emp_id)
    except Exception as e:
        return render_template('ErrorPage.html', errorMsg="Delete Employee unsuccess")

# edit employee
@app.route("/searcheditEmp", methods=['POST', 'GET'])
def searcheditEmp():
    emp_id = request.form['emp_id']

    if emp_id == "":
        errorMsg = "Please fill in all the fields"
        buttonMsg = "BACK TO EDIT EMPLOYEE PAGE"
        action = "/tosearcheditEmp"
        return render_template('ErrorPage.html', errorMsg=errorMsg, buttonMsg=buttonMsg, action=action)
    
    cur = db_conn.cursor()
    select_sql = "SELECT * FROM employee where emp_id = (%s)"
    cur.execute(select_sql, (emp_id))

    if cur.rowcount == 0:
        errorMsg = "The employee ID is not exist"
        buttonMsg = "BACK TO EDIT EMPLOYEE PAGE"
        action = "/tosearcheditEmp"
        return render_template('ErrorPage.html', errorMsg=errorMsg, buttonMsg=buttonMsg, action=action)
    

    data = cur.fetchall()
    return render_template('EditEmp.html', emp_id=emp_id, data=data)


# edit employee
@app.route("/editemp", methods=['POST', 'GET'])
def editEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']

    if emp_id == "" or first_name == "" or last_name == "" or pri_skill == "" or location == "":
        errorMsg = "Please fill in all the fields"
        buttonMsg = "BACK TO EDIT EMPLOYEE PAGE"
        action = "/tosearcheditEmp"
        return render_template('ErrorPage.html', errorMsg=errorMsg, buttonMsg=buttonMsg, action=action)

    cur = db_conn.cursor()
    update_emp_sql = "UPDATE employee SET first_name=%s, last_name=%s, pri_skill=%s, location=%s where emp_id = %s"

   
    cur.execute(update_emp_sql, (first_name, last_name, pri_skill, location, emp_id))

    cur.execute ("update payroll A, employee B set hourly_rate = 10, hours_worked = 8 where A.emp_id = B.emp_id and B.pri_skill = 'Cloud Computing'")
    cur.execute ("update payroll A, employee B set hourly_rate = 15, hours_worked = 8 where A.emp_id = B.emp_id and B.pri_skill = 'R Programming'")
    cur.execute ("update payroll A, employee B set hourly_rate = 20, hours_worked = 8 where A.emp_id = B.emp_id and B.pri_skill = 'C++ Programming'")
    cur.execute ("update payroll A, employee B set hourly_rate = 25, hours_worked = 8 where A.emp_id = B.emp_id and B.pri_skill = 'Java Programming'")
    cur.execute ("update payroll A, employee B set hourly_rate = 30, hours_worked = 8 where A.emp_id = B.emp_id and B.pri_skill = 'Python Programming'")
    cur.execute ("update payroll A, employee B set hourly_rate = 35, hours_worked = 8 where A.emp_id = B.emp_id and B.pri_skill = 'SQL'")
    cur.execute ("update payroll A, employee B set hourly_rate = 40, hours_worked = 8 where A.emp_id = B.emp_id and B.pri_skill = 'Machine Learning'")
    
    #update monthly salary in payroll table
    cur.execute ("update payroll set monthly_salary = (hours_worked * hourly_rate)")
        
    #insert month
    update_month_sql = "update payroll set month = MONTHNAME(CURDATE()) where emp_id = (%s)"
    cur.execute(update_month_sql, (emp_id))

    db_conn.commit()
    cur.close()

    return render_template('EditEmpOutput.html', emp_id=emp_id, first_name=first_name, last_name=last_name, pri_skill=pri_skill, location=location)


# employee benefit
@app.route("/searchbenefitemp", methods=['POST', 'GET'])
def searchBenefitEmp():
    emp_id = request.form['emp_id']

    if emp_id == "":
        errorMsg = "Please fill in all the fields"
        buttonMsg = "BACK TO EMPLOYEE BENEFIT PAGE"
        action = "/tosearchbenefitemp"
        return render_template('ErrorPage.html', errorMsg=errorMsg, buttonMsg=buttonMsg, action=action)
    
    cur = db_conn.cursor()
    select_sql = "SELECT * FROM benefit where emp_id = (%s)"
    cur.execute(select_sql, (emp_id))

    if cur.rowcount == 0:
        errorMsg = "The employee ID is not exist"
        buttonMsg = "BACK TO EMPLOYEE BENEFIT PAGE"
        action = "/tosearcheditEmp"
        return render_template('ErrorPage.html', errorMsg=errorMsg, buttonMsg=buttonMsg, action=action)
    

    data = cur.fetchall()
    return render_template('BenefitEmp.html', emp_id=emp_id, data=data)

@app.route("/benefitemp", methods=['POST', 'GET'])
def benefitEmp():
    emp_id = request.form['emp_id']
    emp_benefit = request.form['emp_benefit']

    if emp_id == "" or emp_benefit == "":
        errorMsg = "Please fill in all the fields"
        buttonMsg = "BACK TO EDIT EMPLOYEE PAGE"
        action = "/tosearchbenefitemp"
        return render_template('ErrorPage.html', errorMsg=errorMsg, buttonMsg=buttonMsg, action=action)

    cur = db_conn.cursor()
    benefit_emp_sql = "UPDATE benefit SET emp_benefit=%s where emp_id = %s"

   
    cur.execute(benefit_emp_sql, (emp_benefit, emp_id))
    db_conn.commit()
    cur.close()

    return render_template('EditEmpOutput.html', emp_id=emp_id, emp_benefit=emp_benefit)


@app.route("/getpayroll", methods=['POST'])
def getPayroll():
    emp_id = request.form['emp_id']

    if emp_id == "":
        errorMsg = "Please fill in all the fields"
        buttonMsg = "BACK TO PAYROLL PAGE"
        action = "/topayroll"
        return render_template('ErrorPage.html', errorMsg=errorMsg, buttonMsg=buttonMsg, action=action)

    cur = db_conn.cursor()
    select_sql = "SELECT * FROM payroll where emp_id = (%s)"

    cur.execute(select_sql, (emp_id))

    if cur.rowcount == 0:
        errorMsg = "The employee ID is not exist"
        buttonMsg = "BACK TO PAYROLL PAGE"
        action = "/topayroll"
        return render_template('ErrorPage.html', errorMsg=errorMsg, buttonMsg=buttonMsg, action=action)


    data = cur.fetchall()

    return render_template('PayrollOutput.html', data=data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
