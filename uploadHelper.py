import cs304dbi as dbi 

def insertFilename(conn,fileName,classID,week,topic,kind,uploader_id):
    ''' inserts a file into the Materials table.
    Also locks table before inserting for thread safety'''
    curs = dbi.cursor(conn)
    curs.execute('''insert into Materials(fileName,classID,week,topic,kind,uploader_id)
                    values (%s,%s,%s,%s,%s,%s) '''
                    ,[fileName,classID,week,topic, kind, uploader_id])
    conn.commit()
    return True

def get_uploaded_files(conn, uploader_id):
    '''gets all uploaded files by the uploader, given the uploader ID'''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select mID, fileName, week, topic, department,classNumber,kind 
                    from Materials 
                    inner join Classes using (classID) 
                    where uploader_id = %s
                    order by week DESC''',[uploader_id])
    return curs.fetchall()

def delete_file(conn, mID):
    '''deletes the material from the database, given mID'''
    curs = dbi.cursor(conn)
    try:
        curs.execute('''delete from Materials 
                    where mID = %s''',[mID])
        conn.commit()
        return True
    except pymysql.IntegrityError as err:
        print('unable to delete due to {}'.format(repr(err)))
        return False

def get_fileName(conn, mID):
    '''returns the file name given the ID of the material'''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select fileName from Materials
                    where mID = %s''',[mID])
    conn.commit()
    return curs.fetchone()

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg','doc','docx'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


if __name__ == '__main__':
    dbi.cache_cnf()  
    dbi.use('tutorrep_db')
    conn = dbi.connect()
