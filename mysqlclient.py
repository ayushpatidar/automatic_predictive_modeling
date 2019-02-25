"""DATABASE CONNECTIVITYY FILE..."""
import MySQLdb
import os
import warnings
import sys

warnings.filterwarnings('ignore')


def connection():
    

    db = MySQLdb.connect("localhost", "root", "ayushpatidar@04", "TIME_SERIES")
    print("DB conencted")



    cur = db.cursor()

    try:
        f = 0
        sql = """SHOW TABLES"""
        cur.execute(sql)
        rs = cur.fetchall()
        rs = [item[0] for item in rs]
        if "RESULTS" in rs:
            f = 1
    except Exception as e:
        print("error while fetching table,{}".format(e))
        exit()

    try:
        if f==0:
            sql = """CREATE TABLE RESULTS(TRAINING_ID INT NOT NULL AUTO_INCREMENT,
                                          MODEL_NAME VARCHAR(100) NULL,
                                          MODEL_ACCURACY FLOAT NULL,
                                          TRAINING_ERROR VARCHAR(550) NULL,
                                          PRIMARY KEY(TRAINING_ID)
                                          )"""

            cur.execute(sql)
            print("table created")
            #db.close()
            return (db)
        else:
            print("TABLE IS ALREADY THERE")
            return (db)




    except Exception as e:
        db.close()
        print("error while creating table,{}".format(e))





def commit_results_db():

    db = MySQLdb.connect("localhost", "root", "ayushpatidar@04", "AUTO_ML")
    print("DB CONNETCED")

    cur = db.cursor()

    try:
        f = 0
        sql = "SHOW TABLES LIKE 'RESULTS'"
        cur.execute(sql)
        rs = cur.fetchone()
        print("rs is ", rs)


        if rs:
            print("table is already there")

        else:
            print("create a table with name RESULTS")

            sql = """CREATE TABLE RESULTS(DATASET_ID VARCHAR(100) NOT NULL, TRAINING_ID VARCHAR(100) NOT NULL, MODEL_NAME VARCHAR(100) NULL,
            ACCURACY FLOAT NULL, FEATURE_SELECTOR VARCHAR(100) NULL, PRIMARY KEY(TRAINING_ID), ERROR_MODEL_TRAINING VARCHAR(100) NULL)"""

            cur.execute(sql)
            db.commit()
            print("table created")


    except Exception as e:
        print("error while creating table ", e)


    db.close()



def set_results_db(data):
     print("here")
     return "here"
     db = MySQLdb.connect("localhost", "root", "ayushpatidar@04", "AUTO_ML")
     print("db connected")

     cur = db.cursor()

     try:
         print("trying to insert in db")
         sql = "INSERT INTO RESULTS(DATASET_ID, TRAINING_ID, MODEL_NAME, ACCURACY, FEATURE_SELECTOR, ERROR_MODEL_TRAINING)" \
               "VALUES(%s, %s, %s, %s, %s, %s)"

         cur.execute(sql, data)
         print("results added successfully in database AUTO_ML")
         db.commit()


     except Exception as e:
         print("error while inserting content in database AUTO_ML", e)


     db.close()
