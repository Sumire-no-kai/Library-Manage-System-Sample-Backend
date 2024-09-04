import mysql.connector
from mysql.connector import Error

def check_login(connection, username, password):
    query = "SELECT id FROM users WHERE username = %s AND password = %s"
    cursor = connection.cursor()
    cursor.execute(query, (username, password))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return {"success": True, "user_id": result[0]}
    else:
        return {"success": False, "user_id": None}

def register_user(connection, username, password):
    query = "INSERT INTO users (username, password) VALUES (%s, %s)"
    cursor = connection.cursor()
    try:
        cursor.execute(query, (username, password))
        connection.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False
    finally:
        cursor.close()


def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="220607.LxnUT",
            database="library_manage"
        )
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

def get_books(connection):
    query = """
    SELECT books.bookID, books.title, books.author, books.publication_year, books.publisher, books.entry_date, book_status.status
    FROM books
    LEFT JOIN book_status ON books.bookID = book_status.bookID
    """
    cursor = connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()

    books = []
    for row in rows:
        book = {
            "bookID": row[0],
            "title": row[1],
            "author": row[2],
            "publication_year": row[3],
            "publisher": row[4],
            "entry_date": row[5].strftime('%Y-%m-%d') if row[5] else None,  # 转换日期格式
            "status": row[6] if row[6] else 'available'  # 如果状态为空，默认设置为 'available'
        }
        books.append(book)

    return books

def insert_book(connection, title, author, publication_year, publisher, entry_date):
    cursor = connection.cursor()
    query = """
    INSERT INTO books (title, author, publication_year, publisher, entry_date)
    VALUES (%s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(query, (title, author, publication_year, publisher, entry_date))
        connection.commit()
        book_id = cursor.lastrowid
        status_query = "INSERT INTO book_status (bookID, status) VALUES (%s, 'available')"
        cursor.execute(status_query, (book_id,))
        connection.commit()
        return True
    except Error as e:
        print(f"The error '{e}' occurred")
        return False


def delete_book(connection, book_id):
    delete_status_query = "DELETE FROM book_status WHERE bookID = %s"
    delete_book_query = "DELETE FROM books WHERE bookID = %s"
    cursor = connection.cursor()
    try:
        # 先删除 book_status 表中的相关记录
        cursor.execute(delete_status_query, (book_id,))
        connection.commit()

        # 再删除 books 表中的记录
        cursor.execute(delete_book_query, (book_id,))
        connection.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False
    finally:
        cursor.close()

def borrow_book(connection, book_id, user_id):
    cursor = connection.cursor()
    query = """
    UPDATE book_status
    SET status = 'borrowed', borrowed_by = %s, borrowed_date = NOW()
    WHERE bookID = %s AND status = 'available'
    """
    try:
        cursor.execute(query, (user_id, book_id))
        if cursor.rowcount == 0:
            return False
        connection.commit()
        return True
    except Error as e:
        print(f"The error '{e}' occurred")
        return False

def return_book(connection, book_id):
    cursor = connection.cursor()
    query = """
    UPDATE book_status
    SET status = 'available', borrowed_by = NULL, borrowed_date = NULL
    WHERE bookID = %s AND status = 'borrowed'
    """
    try:
        cursor.execute(query, (book_id,))
        if cursor.rowcount == 0:
            return False
        connection.commit()
        return True
    except Error as e:
        print(f"The error '{e}' occurred")
        return False
