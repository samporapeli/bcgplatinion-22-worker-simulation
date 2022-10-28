#!/usr/bin/env python3

import requests
import subprocess
from time import sleep

from led_indicator import LedIndicator

li = LedIndicator()

config = {
    'endpoint': 'http://ec2-3-68-221-30.eu-central-1.compute.amazonaws.com:3333/api/v1',
    'datacenter_id': 'FR',
}

worked_last_poll = False

li.leds_off()
while True:
    try:
        work_request_fun = lambda: requests.post(f'{config["endpoint"]}/request_work', json={
            'datacenter_id': config['datacenter_id'],
        })
        col = 'red' if worked_last_poll else 'green'
        work_request = li.with_blinking_do(col, work_request_fun, 0.5, 0.1)
        li.led_on(col)
        work_task = work_request.json()['shell_command']
        if work_task:
            print(f'got work: {work_task}')
            worked_last_poll = True
            li.led_off('green')
            def run_work_task():
                process = subprocess.Popen(work_task, shell=True, stdout=subprocess.PIPE)
                out, err = process.communicate()
                errcode = process.returncode
                return out, err, errcode
            out, err, errcode = li.with_led_do('red', run_work_task, turn_off=False)
            work_response_fun = lambda: requests.post(f'{config["endpoint"]}/request_work', json={
                'datacenter_id': config['datacenter_id'],
                'work_response': out,
                'exit_status': errcode,
            })
            # li.with_led_do('red', work_response_fun, 0.05, 0.05)
            work_response_fun()
        else:
            li.led_off('red')
            worked_last_poll = False
            sleep(1)
    except requests.exceptions.ConnectionError:
        print('Connection error')
        sleep(1)
