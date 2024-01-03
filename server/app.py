from flask import Flask, request, jsonify, url_for
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import json
from celery import Celery
from celery.exceptions import Ignore
from celery.result import AsyncResult
import bcrypt
from flask_cors import CORS
import requests
from wakeonlan import send_magic_packet
from ping3 import ping, verbose_ping
import paramiko
import time
import traceback
import sys

app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'redis://redis:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://redis:6379/0'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)
global_server_ip = "192.168.1.42"
global_mac = "D8:5E:D3:AB:7B:0E"

app.config['JWT_SECRET_KEY'] = 'youripodsmells'
CORS(app, resources={r"*": {"origins": "*"}})
jwt = JWTManager(app)

with open('users.json', 'r') as file:
    users_data = json.load(file)

@app.route('/api/login', methods=['POST'])
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

@app.route('/api/user', methods=['GET'])
@jwt_required()
def protected():
    return jsonify(message="Access granted"), 200

@app.route('/api/servertest', methods=['GET'])
def servertest():
    try:
        response_time = ping(global_server_ip, timeout=2500)
        if response_time:
            print(response_time)
            print("Ping successful -" + " response time: " + str(response_time) + " ms")
            return jsonify(message="Server reached successfully at " + str(response_time)), 200
        else:
            return jsonify(message='Server did not return a response'), 400
    except requests.exceptions.RequestException as e:
        return jsonify(message='Unhandled Error ' + str(e)), 400

@app.route('/api/checkqemu', methods=['GET'])
def checkqemu():
    try:
      check_task = check_qemu_status.apply_async(args=[global_server_ip, 'amogus', '/tmp/key'])
      return jsonify(message=f"Operation started", statusUrl=url_for('taskstatus', task_id=check_task.id)), 202

    except requests.exceptions.RequestException as e:
        return jsonify(message='Unhandled Error ' + str(e)), 400

@celery.task(bind=True)
def check_qemu_status(self, server_ip, username, private_key_path):
    try:
        ssh_client = paramiko.SSHClient()
        self.update_state(state='PROGRESS', meta={'current': 10, 'status': 'Opening SSH session', 'total': 100})

        # Establish an SSH connection
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Load your private key
        private_key = paramiko.RSAKey.from_private_key_file(private_key_path)

        # Connect to the remote server
        ssh_client.connect(server_ip, username=username, port=35218, pkey=private_key)
        self.update_state(state='PROGRESS', meta={'current': 30, 'status': 'SSH connected', 'total': 100})

        # Execute the QEMU status check script
        stdin, stdout, stderr = ssh_client.exec_command('/home/amogus/scripts/99.sh')
        self.update_state(state='PROGRESS', meta={'current': 50, 'status': 'Executing command', 'total': 100})

        # Capture and print the command's output
        output = stdout.read().decode('utf-8')
        print(output)

        ssh_client.close()

        # Interpret the result
        if "QEMUROOT" in output:
            self.update_state(state='SUCCESS',
                    meta={'current': 100, 'status': 'isONROOT'})
            return True
        elif "QEMUNOTROOT" in output:
            self.update_state(state='SUCCESS',
                    meta={'current': 100, 'status': 'isON'})
            return True
        elif "QEMUOFF" in output:
            self.update_state(state='SUCCESS',
                    meta={'current': 100, 'status': 'isOFF'})
            return True
        else:
            raise ValueError()

    except Exception as e:
      self.update_state(state='FAILURE', meta={'status': 'Unhandled Error ' + str(e),
                                             'exc_type': type(e).__name__,
                                             'exc_message': 'The value returned by the startup script is wrong',
                                             'custom': '...'
                                              })
      raise Ignore()


@app.route('/api/powerqemu', methods=['POST'])
#@jwt_required()
def powerqemuatt():
    try:
#        user = get_jwt_identity()

        vmid = request.json.get('vmid')
        action = request.json.get('action')
        server_ip = global_server_ip
        username = 'amogus'
        private_key_path = '/tmp/key'
        mac = global_mac
        target = server_ip
        print(vmid, action, server_ip, username, private_key_path)
        response_time = ping(server_ip, timeout=2500)

        if response_time:
            print(response_time)
            print("Ping successful -" + " response time: " + str(response_time) + " ms")
            time.sleep(4)
            power_task = powerqemu.apply_async(args=[vmid, action, server_ip, username, private_key_path])
            return jsonify(message=f"Operation started by ..", statusUrl=url_for('taskstatus', task_id=power_task.id)), 202

        else:
            wake = wol(mac, target)
            return jsonify(message="Ping failed, WoL and Ping tasks started", status="PINGFAIL", statusUrlWOL=wake['statusUrlWOL'], statusUrlPing=wake['statusUrlPing']), 202

    except requests.exceptions.RequestException as e:
        return jsonify(message="Request failed: " + str(e))

@celery.task(bind=True)
def powerqemu(self, vmid, action, server_ip, username, private_key_path):
    ssh_client = paramiko.SSHClient()
    self.update_state(state='PROGRESS', meta={'current': 10, 'status': 'Opening SSH session', 'total': 100})
    exit_code = "Unknown"
    try:
        # Establish an SSH connection
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Load your private key
        private_key = paramiko.RSAKey.from_private_key_file(private_key_path)

        # Connect to the remote server
        ssh_client.connect(server_ip, username=username, port=35218, pkey=private_key)
        self.update_state(state='PROGRESS', meta={'current': 30, 'status': 'SSH connected', 'total': 100})

        # Execute the QEMU status check script
        stdin, stdout, stderr = ssh_client.exec_command('/home/amogus/vmcontrol.sh '+ vmid + ' ' + action)
        self.update_state(state='PROGRESS', meta={'current': 50, 'status': 'Executing command', 'total': 100})

        # Wait for the command to finish and get the exit code
        exit_code = stdout.channel.recv_exit_status()

        # Read the output and error streams if needed
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')

        print(output)
        print(error)
        print(exit_code)
        ssh_client.close()

        # Interpret the result
        if exit_code == 0:
            self.update_state(state='SUCCESS',
                meta={'current': 100, 'status': 'Command executed successfully.'})
            print("Command executed successfully.")
            return True
        else:
            raise ValueError()

    except Exception as e:
      print(e)
      self.update_state(state='FAILURE', meta={'status': str(e),
                                             'current':100,
                                             'total':100,
                                             'exc_type': type(e).__name__,
                                             'exc_message': str(e)
                                              })
      raise Ignore()

# Define the on_failure handler
@celery.task
def on_failure_handler(task_id, exception, args, kwargs, traceback):
    # Log the failure or perform other actions
    print(f'Task {task_id} failed with exception: {exception}')


def wol(mac, target):
    # Trigger the Celery tasks
    broad = "192.168.1.255"
    try:
      wol_task = wake_on_lan_task.apply_async(args=[mac, broad])
      time.sleep(8)
      pingtask = ping_task.apply_async(args=[target])
      return {
            'message': 'WoL and Ping tasks started',
            'statusUrlWOL': url_for('taskstatus', task_id=wol_task.id),
            'statusUrlPing': url_for('taskstatus', task_id=pingtask.id)
      }
    except:
     print("Error Ping/WOL")
     pass

@celery.task(bind=True)
def wake_on_lan_task(self, mac, broad):
    # Your Wake-on-LAN logic here
    try:
        self.update_state(state='PROGRESS', meta={'current': 50, 'total': 100, 'status': 'Waking....'})
        send_magic_packet(mac, ip_address=broad)
        print("Waking up: " + mac)
        time.sleep(2)  # Simulate WoL operation
        self.update_state(state='SUCCESS',
           meta={'current': 100, 'status': 'Magic packet sent.'})
        return True
    except:
        pass

@celery.task(bind=True)
def ping_task(self, target):
    target_host = target
    max_retries = 24
    retry_interval = 4  # seconds
    timeout = 3  # seconds
    i = 1
    try:
      for attempt in range(1, max_retries + 1):
        if i >= max_retries:
          raise ValueError()
        self.update_state(state='PROGRESS', meta={'current': i, 'total': max_retries, 'status': 'Trying ping....'+str(i)})
        response_time = ping(target_host, timeout=timeout)
        if response_time:
            print("Ping successful after attempt" + str(attempt))
            self.update_state(state='SUCCESS',
                meta={'current': 100, 'status': 'Ping reached server.'})
            return True
        time.sleep(retry_interval)
        i = i+1
    except Exception as e:
      self.update_state(state='FAILURE', meta={'status': 'Ping failed ! ' + str(e), 'exc_type': type(e).__name__, 'exc_message': 'Ping failed ! ' + str(e), 'current':100, 'total':100})
      raise Ignore()

@app.route('/api/status/<task_id>')
def taskstatus(task_id):
    task = celery.AsyncResult(task_id)
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
        print(task)
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
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
    app.run(host="0.0.0.0",debug=True)
