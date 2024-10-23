import mysql.connector
from datetime import date
import os
from dotenv import load_dotenv

load_dotenv()

def connect():
    mydb = mysql.connector.connect(
    host=os.getenv('sql_host'),
    port="3306",
    user=os.getenv('sql_username'),
    database=os.getenv('sql_db'),
    password=os.getenv('sql_password')
    )

    return mydb

def execute(sql,type:str=None):
    mydb = connect()
    mycursor = mydb.cursor()
    
    # sql = f"SELECT * FROM RedeemCode WHERE `Type` = '{_type}' AND `Used` = '0'"
    mycursor.execute(sql)

    if type == None: fetch = mycursor.fetchall()
    else:
        mydb.commit()
        fetch = ['Nothing To Return!']

    return fetch
