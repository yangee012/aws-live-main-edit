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

@app.route("/toattendance", methods=['GET', 'POST'])
def toAttend():
    return render_template('Attendance.html')

@app.route("/topayroll", methods=['GET', 'POST'])
def toPayroll():
    return render_template('Payroll.html')

@app.route("/addattendance", methods=['POST'])
def addAttend():
    duty_id = request.form['duty_id']
    emp_id = request.form['emp_id']
    date = request.form['date']
    duration = request.form['duration']

    if duty_id == "" or emp_id == "" or date == "" or duration == "":
        errorMsg = "Please fill in all the fields"
        return render_template('ErrorPage.html', errorMsg=errorMsg)

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

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    insert_payroll = "INSERT INTO payroll VALUES (%s, %s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()
    
    hourly_rate = 0
    hours_worked = 0
    leave_day = 0
    monthly_salary = 0
    

    if emp_image_file.filename == "":
        return "Please select a file"

    try:
        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location))
        cursor.execute(insert_payroll, (emp_id, first_name, last_name, hourly_rate, hours_worked, leave_day, monthly_salary))
        
        #if statements to update hours_worked and hourly_rate in payroll table
        cursor.execute ("update payroll A, employee B set hourly_rate = 10, hours_worked = 8 where A.emp_id = B.emp_id and B.pri_skill = 'Cloud Computing'")
        cursor.execute ("update payroll A, employee B set hourly_rate = 15, hours_worked = 8 where A.emp_id = B.emp_id and B.pri_skill = 'R Programming'")
        cursor.execute ("update payroll A, employee B set hourly_rate = 20, hours_worked = 8 where A.emp_id = B.emp_id and B.pri_skill = 'C++ Programming'")
        cursor.execute ("update payroll A, employee B set hourly_rate = 25, hours_worked = 8 where A.emp_id = B.emp_id and B.pri_skill = 'Java Programming'")
        cursor.execute ("update payroll A, employee B set hourly_rate = 30, hours_worked = 8 where A.emp_id = B.emp_id and B.pri_skill = 'Python Programming'")
        cursor.execute ("update payroll A, employee B set hourly_rate = 35, hours_worked = 8 where A.emp_id = B.emp_id and B.pri_skill = 'SQL'")
        cursor.execute ("update payroll A, employee B set hourly_rate = 40, hours_worked = 8 where A.emp_id = B.emp_id and B.pri_skill = 'Machine Learning'")

        #update monthly salary in payroll table
        cursor.execute ("update payroll set monthly_salary = (hours_worked * hourly_rate)")
        
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

@app.route("/tofetchemp", methods=['POST'])
def gofetchEmp():
    return render_template('GetEmp.html')


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
    emp_id = request.form['emp_id']
    cur = db_conn.cursor()
    select_sql = "SELECT * FROM employee where emp_id = (%s)"
    cur.execute(select_sql, (emp_id))
    contents = show_image(custombucket)
    data = cur.fetchall()

    return render_template('GetOneEmp.html', data=data, contents=contents)



@app.route("/getemp", methods=['GET'])
def getEmp():
    cur = db_conn.cursor()
    cur.execute("SELECT * FROM employee")
    data = cur.fetchall()
    return render_template('GetEmpOutput.html', data=data)

# delete employee
@app.route("/deleteemp", methods=['GET', 'POST'])
def deleteEmp():
    emp_id = request.form['emp_id']
    cur = db_conn.cursor()
    delete_emp_sql = "DELETE from employee WHERE emp_id = %s"
    cur.execute(delete_emp_sql, (emp_id))
    db_conn.commit()

    emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
    s3_client = boto3.client('s3')
    
    try:
        s3_client.delete_object(Bucket=customBucket, Key=emp_image_file_name_in_s3)
        return render_template('DeleteEmpOutput.html', id = emp_id)
    except Exception as e:
        return render_template('ErrorPage.html', errorMsg="Delete Employee unsuccess")


# edit employee


@app.route("/getpayroll", methods=['POST', 'GET'])
def getPayroll():
    emp_id = request.form['emp_id']
    cur = db_conn.cursor()
    select_sql = "SELECT * FROM payroll where emp_id = (%s)"
    cur.execute(select_sql, (emp_id))
    data = cur.fetchall()

    return render_template('PayrollOutput.html', data=data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
