import cs304dbi as dbi 
import pymysql
from flask import (Flask,flash)
    
def checkPerson(conn, username):
    ''' checks if given username already exists in Person table'''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select username from Person where username = %s''',
                    [username])
    return curs.fetchone()

def checkAndInsertPerson(conn, username, name, role):
    '''inserts a new person into the Person table.
     Also locks table before inserting for thread safety'''
    curs = dbi.dict_cursor(conn)
    try:
        curs.execute('''lock tables Person write''')
        checker = curs.execute('''select username from Person where username = %s''',
                    [username])
        if checker == 0:
            curs.execute('''insert into Person (username, name, role)
                        values (%s, %s, %s)''',
                        [username, name, role])
            conn.commit()
        curs.execute('''unlock tables''')
        return True
    except pymysql.IntegrityError as err:
        print('unable to insert {} due to {}'.format(name,repr(err)))
        return False

def getAllNames(conn):
    ''' gets the names and usernames of all students in the
        Person table in the database'''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select name, username from Person where role = 'student' ''')
    return curs.fetchall()

def checkAndInsertSILeader(conn, username, classID):
    '''inserts a new SI Leader into the SI_Leaders table.
    Also locks table before inserting for thread safety'''
    curs = dbi.dict_cursor(conn)
    try:
        curs.execute('''lock tables SI_Leaders write''')
        checker = curs.execute('''select username from SI_Leaders 
                            where username = %s and classID = %s''',
                            [username, classID])
        if checker == 0:
            curs.execute('''insert into SI_Leaders (username, classID)
                        values (%s, %s)''',
                        [username, classID])
            conn.commit()
            flash('SI Leader ' + username + ' successfully added')
        else:
            flash('SI Leader ' + username + ' already added for that class')
        curs.execute('''unlock tables''')       
        return True
    except pymysql.IntegrityError as err:
        print('unable to insert {} due to {}'.format(username,repr(err)))
        return False

def checkSIExists(conn, username, classID):
    ''' gets the usernames of SI leader given username and classID
        in the SI_Leaders table in the database'''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select username from SI_Leaders where username = %s and classID = %s''',
                    [username, classID])
    return curs.fetchone()

def checkIfSI(conn, username):
    ''' checks if SI leaders is in the SI_Leaders table in the database'''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select username from SI_Leaders where username = %s''',
                    [username])
    return curs.fetchone()

    

if __name__ == '__main__':
    dbi.cache_cnf()  
    dbi.use('tutorrep_db')
    conn = dbi.connect()
