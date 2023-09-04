from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import json
from celery import Celery, task
from celery.result import AsyncResult
import bcrypt
from flask_cors import CORS
import requests
from wakeonlan import send_magic_packet
from ping3 import ping, verbose_ping
import time


app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'redis://redis:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://redis:6379/0'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

app.config['JWT_SECRET_KEY'] = 'youripodsmells'
CORS(app, resources={r"*": {"origins": "*"}})
jwt = JWTManager(app)

with open('users.json', 'r') as file:
    users_data = json.load(file)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username in users_data and 'hashed_password' in users_data[username]:
        hashed_password = users_data[username]['hashed_password']
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            access_token = create_access_token(identity=username)
            return jsonify(access_token=access_token), 200
    return jsonify(message="Invalid credentials"), 401

@app.route('/user', methods=['GET'])
@jwt_required()
def protected():
    return jsonify(message="Access granted"), 200

@app.route('/servertest', methods=['GET'])
def test():
    try:
        url = 'http://na-no.pro:9100/api/test'
        response = requests.get(url)
        if response.status_code == 200:
            return jsonify(message="Server reached successfully"), 200
        else:
            return jsonify(message='Server returned status code ' + str(response.status_code)), 400
    except requests.exceptions.RequestException as e:
        return jsonify(message='Unhandled Error ' + str(e)), 400

@app.route('/checkqemu', methods=['GET'])
@jwt_required()
def checkqemu():
    try:
        url = 'https://na-no.pro/checkqemu'
        if True:
            return jsonify(message="QEMU is ON", status="isON"), 200
    except requests.exceptions.RequestException as e:
        return jsonify(message='Unhandled Error ' + str(e)), 400

@app.route('/powerqemu', methods=['POST'])
@jwt_required()
def powerqemuatt():
    try:
        url = 'https://na-no.pro/powerqemu'
        headers = {'Authorization': 'Bearer ' + request.headers['Authorization']}
        payload = {
            'vmid': request.json.get('vmid'),
            'action': request.json.get('action')
        }

        user = get_jwt_identity()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(powerqemu(url, headers, payload))

        if result:
            return jsonify(status_url=result), 200
        else:
            return wol()

    except requests.exceptions.RequestException as e:
        return jsonify(message="Request failed: " + str(e))

        
async def powerqemu(url, headers, payload):
    response = requests.post(url, json=payload, headers=headers)
    if not response.ok:
        return False

    try:
        response_data = await asyncio.wait_for(response.json(), timeout=5)  # Wait for response with a timeout
        if response_data.get('status') == 'OK':
            return response_data.get('status_url')
        elif response_data.get('status') == 'FAIL':
            return "Fail"
        else:
            return response.status_code

    except asyncio.TimeoutError:
        pass

    return False

@app.route('/killqemu', methods=['POST'])
@jwt_required()
def killqemu():
    try:
        url = 'https://na-no.pro/killqemu'
        headers = {'Authorization': 'Bearer ' + request.headers['Authorization']}
        payload = {
            'user': request.json.get('user')
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.ok:
            response_data = response.json()
            if response_data.get('status') == 'OK':
                status_url = response_data.get('status_url')
                return jsonify({'message': 'OK', 'status_url': status_url}), 200
            elif response_data.get('status') == 'FAIL':
                return jsonify({'message': 'FAIL'}), 400
            else:
                return jsonify({'message': 'Unexpected response'}), 500
        else:
            return jsonify({'message': 'Server returned status code ' + str(response.status_code)}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'message': 'Request failed: ' + str(e)}), 500

def wol():
    # Trigger the Celery tasks
    wol_task = wake_on_lan_task.apply_async(args=[mac])
    time.sleep(8)
    ping_task = ping_task.apply_async(args=[target])
    return jsonify(message="WoL and Ping tasks started", statusUrlWOL=url_for('taskstatus', intask=wake_on_lan_task, task_id=wol_task.id), statusUrlPing=url_for('taskstatus', intask=ping_task, task_id=ping_task.id)), 202

@celery.task(bind=True)
def wake_on_lan_task(self, mac):
    # Your Wake-on-LAN logic here
    try:
        send_magic_packet(mac)
        print("Waking up: " + mac)
        time.sleep(2)  # Simulate WoL operation
        return True
    except:
        return False

@celery.task(bind=True)
def ping_task(self, target):
    target_host = target  # Replace with your target host's IP or hostname
    max_retries = 5
    retry_interval = 3  # seconds
    timeout = 1  # seconds
    i = 1

    for attempt in range(1, max_retries + 1):
        self.update_state(state='PROGRESS', meta={'current': i, 'total': max_retries})
        response_time = ping(target_host, timeout=timeout)
        if response_time is not None:
            print("Ping successful after attempt" + attempt + " response time: " + response_time + " ms")
            self.update_state(state='FINISHED')
            return True
        time.sleep(retry_interval)
        i = i+1

    print("Failed to ping")
    self.update_state(state='FAILURE', meta={'status': "Ping failed"})
    return False

@app.route('/status/<task_id>')
def taskstatus(intask, task_id):
    task = intask.AsyncResult(task_id)
    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state == 'PROGRESS':
        # job in progress
        response = {
            'state': task.state,
            'current': task.info.get('current', ''),
            'total': 1,
            'status': task.info.get('status', '')
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info)  #this is the exception raised
	}
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)