import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = 'app.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS router (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            router_name TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_router (
            user_id INTEGER,
            router_id INTEGER,
            PRIMARY KEY (user_id, router_id),
            FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
            FOREIGN KEY (router_id) REFERENCES router (id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

def add_user(username, password):
    if not username or not password:
        return "username and password are required"

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM user WHERE username = ?', (username,))
    if cursor.fetchone():
        return "User already exists"

    cursor.execute('INSERT INTO user (username, password) VALUES (?, ?)', (username, hashed_password))
    conn.commit()
    conn.close()

    return False

def get_all_users():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT username, password FROM user')
    rows = cursor.fetchall()
    conn.close()
    users = [{"username": row[0], "password": row[1]} for row in rows]

    return users

def delete_user(username):
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM user WHERE username = ?", (username,))
        conn.commit()
        conn.close()
    except Exception as e:
        return str(e)
    return False

def add_router(router_name):
    if not router_name:
        return "router_name is required"
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM router WHERE router_name = ?', (router_name,))
    if cursor.fetchone():
        return "Router name already used"

    cursor.execute('INSERT INTO router (router_name) VALUES (?)', (router_name,))
    conn.commit()
    conn.close()

    return False

def get_all_routers():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT id, router_name FROM router')
    rows = cursor.fetchall()
    conn.close()
    users = [{"id": row[0], "router_name": row[1]} for row in rows]
    return rows

def delete_router(router_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM router WHERE router_id = ?", (router_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        return str(e)
    return False

def assign_router(username, router_name):
    if not username or not router_name:
        return "username and router_name are required"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM user WHERE username = ?', (username,))
    user_result = cursor.fetchone()
    if not user_result:
        return "User not found"
    user_id = user_result[0]

    cursor.execute('SELECT id FROM router WHERE router_name = ?', (router_name,))
    router_result = cursor.fetchone()
    if not router_result:
        return "Router not found"
    router_id = router_result[0]

    cursor.execute('SELECT * FROM user_router WHERE user_id = ? AND router_id = ?', (user_id, router_id))
    if cursor.fetchone():
        return "This router is already assigned to the user"

    cursor.execute('INSERT INTO user_router (user_id, router_id) VALUES (?, ?)', (user_id, router_id))
    conn.commit()
    conn.close()

    return False

def search_user_routers(username):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT router_name
        FROM user_router AS ur
        JOIN router AS r ON r.id = ur.router_id
        JOIN user AS u ON u.id = ur.user_id
        WHERE username = ?;
    """, (username,))
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result

def search_router_users(router_name):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT username
        FROM user_router AS ur
        JOIN router AS r ON r.id = ur.router_id
        JOIN user AS u ON u.id = ur.user_id
        WHERE router_name = ?;
    """, (router_name,))
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result

def delete_user_router_assignment(username, router_name):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE
            FROM user_router AS ur
            JOIN router AS r ON r.id = ur.router_id
            JOIN user AS u ON u.id = ur.user_id
            WHERE username = ? AND router_name = ?""", (username, router_name))
        conn.commit()
        conn.close()
    except Exception as e:
        return str(e)
    return False

def delete_user_router_assignment(username, router_name):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, r.id
            FROM user u
            JOIN router r ON r.router_name = ?
            WHERE u.username = ?""", (router_name, username))
        result = cursor.fetchone()
        if result:
            user_id, router_id = result
            cursor.execute("""
                DELETE FROM user_router
                WHERE user_id = ? AND router_id = ?""", (user_id, router_id))
            conn.commit()
        else:
            conn.close()
            return "User or Router not found"
        conn.close()
    except Exception as e:
        return str(e)

    return False



def check_credentials(username, password, router_id):
    if not username or not password or not router_id:
        return "username and password and router_id are required"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.password, u.id
        FROM user u
        JOIN user_router ur ON ur.user_id = u.id
        JOIN router r ON r.id = ur.router_id
        WHERE u.username = ? AND r.id = ?;""", (username, router_id))

    user_data = cursor.fetchone()

    if user_data:
        hashed_password = user_data[0]
        if check_password_hash(hashed_password, password):
            return "success"

    cursor.execute("""
        SELECT u.password, u.id
        FROM user u
        WHERE u.username = ?;""", (username,))
    user_data = cursor.fetchone()

    if user_data:
        hashed_password = user_data[0]
        if check_password_hash(hashed_password, password):
            cursor.execute('SELECT router_name FROM router WHERE id = ?', (router_id,))
            router_name = cursor.fetchone()
            if router_name:
                return router_name[0]
            return "No such router"

    conn.close()

    return False

