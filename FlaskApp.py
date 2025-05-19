from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, send_from_directory, abort, make_response
import sqlite3
from db import *
from crypto import generate_keys
from io import BytesIO
import json
import os
import jwt
import time
from urllib.parse import urlparse, urlencode
import uuid

app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY", "fallback-secret-key")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

create_tables()

private_key = generate_keys()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash("You need to log in to access this page", "error")
            return redirect(url_for('admin_login_page'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin', methods=['GET', 'POST'])
def admin_login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            # flash("Login successful!", "success")
            return redirect(url_for('add_user_page'))
        else:
            flash("Invalid username or password", "error")

    return render_template('admin_login.html')

@app.route('/adminLogout')
def admin_logout_page():
    session.pop('logged_in', None)
    flash("You have logged out", "success")
    return redirect(url_for('admin_login_page'))

@app.route('/')
def home_page():
    return redirect(url_for('admin_login_page'))

@app.route('/addUser', methods=['GET', 'POST'])
@login_required
def add_user_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        error_message = add_user(username, password)

        if error_message:
            flash(error_message, 'error')
        else:
            flash('User successfully added!', 'success')
            return redirect(url_for('add_user_page'))

    return render_template('add_user.html', users=get_all_users())

@app.route('/delete_user/<username>', methods=['POST'])
@login_required
def delete_user_page(username):
    err = delete_user(username)
    if err:
        flash(f'Error deleting user: {username} => {err}', 'danger')
    else:
        flash(f'User {username} deleted successfully.', 'success')
    return redirect(url_for('add_user_page'))

@app.route('/addRouter', methods=['GET', 'POST'])
@login_required
def add_router_page():
    if request.method == 'POST':
        router_name = request.form.get('router_name')

        error_message = add_router(router_name)

        if error_message:
            flash(error_message, 'error')
        else:
            flash('Router successfully added!', 'success')
            return redirect(url_for('add_router_page'))

    routers = get_all_routers()

    return render_template('add_router.html', routers=routers)

@app.route('/delete_router/<uuid:router_id>', methods=['POST'])
@login_required
def delete_router_page(router_id):
    err = delete_router(router_id)
    if err:
        flash(f'Error deleting router: {router_id} => {err}', 'danger')
    else:
        flash(f'Router {router_id} deleted successfully.', 'success')
    return redirect(url_for('add_router_page'))

@app.route('/assignRouter', methods=['GET', 'POST'])
@login_required
def assign_router_page():
    user_routers = []
    router_users = []
    username_query = request.args.get('username_query')
    router_query = request.args.get('router_query')

    if request.method == 'POST':
        username = request.form.get('username')
        router_name = request.form.get('router_name')

        error_message = assign_router(username, router_name)

        if error_message:
            flash(error_message, 'error')
        else:
            flash('Router successfully assigned to user!', 'success')

    if username_query:
        user_routers = search_user_routers(username_query)

    if router_query:
        router_users = search_router_users(router_query)

    users = [user["username"] for user in get_all_users()]
    routers = [router["router_name"] for router in get_all_routers()]

    return render_template('assign_router.html', users=users, routers=routers, user_routers=user_routers, username_query=username_query, router_users=router_users, router_query=router_query)

@app.route('/delete_user_router_assignment', methods=['POST'])
@login_required
def delete_user_router_assignment_page():
    username = request.form['username']
    router_name = request.form['router_name']

    err = delete_user_router_assignment(username, router_name)
    if err:
        flash(f'Error deleting assignment: {username} <=> {router_name} => {err}', 'danger')
    else:
        flash(f'Removed assignment: {username} <=> {router_name}', 'success')
    return redirect(url_for('assign_router_page', ))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    redirectURL = request.args.get('return', None)
    routerId = request.args.get('routerId', None)

    if not redirectURL:
        flash('No return URL provided.', 'danger')
    if not routerId:
        flash('No router ID provided.', 'danger')
    if not (redirectURL and routerId):
        return render_template('login.html')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        ret = check_credentials(username, password, routerId)
        if ret == "success":
            encoded_jwt = jwt.encode({ "routerId": routerId, "username": username, "iat": int(time.time()) }, private_key, algorithm="RS256")
            # print(encoded_jwt)
            stripped_url = urlparse(redirectURL)._replace(query="").geturl()
            response = make_response(redirect(stripped_url + f"?jwt={encoded_jwt}"))
            # response = make_response(redirect(redirectURL))
            # response.headers['Authorization'] = f'Bearer {encoded_jwt}'
            return response
        elif ret != False:
            flash(f'User "{username}" does not have access to router: {ret}.', 'danger')
        elif ret == False:
            flash('Invalid username or password, please try again!', 'danger')
        else:
            flash('Error!', 'danger')

    return render_template('login.html')

@app.route('/download_router_file/<uuid:router_id>', methods=['GET'])
def download_router_file_page(router_id):

    server_url = os.environ.get("SERVER_DOMAIN_NAME", request.url_root)
    # if not server_url.endswith('/'):
    #     server_url += '/'

    data = { "url": server_url, "routerId": str(router_id) }
    file_content = json.dumps(data)

    memory_file = BytesIO()
    memory_file.write(file_content.encode('utf-8'))
    memory_file.seek(0)
    filename = "config.json"

    return Response(
        memory_file,
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@app.route('/certificates/public_key.pem')
def serve_certificate_page():
    certificates_directory = os.path.join(os.getcwd(), 'certificates')
    try:
        return send_from_directory(certificates_directory, "public_key.pem", as_attachment=True)
    except FileNotFoundError:
        abort(404)

if __name__ == '__main__':
    app.run(debug=True)
