#!/usr/bin/env python3
from __future__ import division
from __future__ import print_function  # use python 3 syntax but make it compatible with python 2

import getopt
import logging
import os
import socket
import sys
import threading
import time  # import the time library for the sleep function
from datetime import datetime

import brickpi3  # import the BrickPi3 drivers


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


BP = brickpi3.BrickPi3()  # Create an instance of the BrickPi3 class. BP will be the BrickPi3 object.
BP.set_led(0)  # For successful setup indication, we turn off the LED and turn it on if it's successfully set up

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
LOGGING = False

log = None
log_dir = None
is_master = False
border_upper = None
border_lower = None
border_enabled = False

# Unity program
SERVER_IP = {'exoskeleton1': '192.168.17.52',
             'exoskeleton2': '192.168.17.235'}[socket.gethostname()]
SERVER_PORT = 5013

# Exoskeleton
CLIENT_IP = get_ip_address()
CLIENT_PORT = 5011

# CLIENT_IP = get_ip_address()
# IPS = ['10.16.172.130', '10.16.172.68']
# IPS.remove(CLIENT_IP)
# SERVER_IP = IPS[0]
# CLIENT_PORT, SERVER_PORT = (5011, 5013) if SERVER_IP.endswith('130') else (5013, 5011)

sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_DGRAM)  # UDP
sock.bind((CLIENT_IP, CLIENT_PORT))


def set_motors(elbow, wrist):
    BP.set_motor_position(BP.PORT_A + BP.PORT_C, elbow)
    BP.set_motor_position(BP.PORT_B, wrist)


def release_motors():
    BP.set_motor_power(BP.PORT_A + BP.PORT_B + BP.PORT_C, BP.MOTOR_FLOAT)


def keep_boundaries():
    while border_enabled:
        value_elbow = (BP.get_motor_encoder(BP.PORT_A) + BP.get_motor_encoder(BP.PORT_C)) * -1 / 2
        print(f"Value: {value_elbow}, upper border: {border_upper}, lower border: {border_lower}")
        if value_elbow < border_lower:
            BP.set_motor_position(BP.PORT_A + BP.PORT_C, -border_lower)
            time.sleep(0.1)
            release_motors()
        elif value_elbow > border_upper:
            BP.set_motor_position(BP.PORT_A + BP.PORT_C, -border_upper)
            time.sleep(0.1)
            release_motors()
        time.sleep(0.01)


def message_callback(data):
    global is_master, border_upper, border_lower, border_enabled

    try:
        message = data.decode("utf-8")

        if message.startswith('control'):
            _, elbow, wrist, timestamp = message.split(',')
            control_thread = threading.Thread(target=set_motors, args=(-float(elbow), -float(wrist)))
            control_thread.start()

        if message.startswith('repeat'):
            print(f"Message received: {message}")
            _, mode = message.lower().split(" ")
            if mode.lower() == 'false':
                release_motors()

        elif message.startswith("master"):
            print(f"Message received: {message}")
            _, master_state = message.lower().split(" ")
            is_master = True if master_state == "true" else False
            if is_master:
                release_motors()
            if LOGGING:
                if is_master:
                    log.info("Switched to being master")
                else:
                    log.info("Switched to being follower")

        elif message.startswith('border'):
            print(f"Message received: {message}")
            border_msg = message.lower().split(" ")
            if border_msg[1] == 'upper':
                border_upper = float(border_msg[2].replace(',', '.'))
                if LOGGING:
                    log.info(f"upper border set to {border_upper}")
            elif border_msg[1] == 'lower':
                border_lower = float(border_msg[2].replace(',', '.'))
                if LOGGING:
                    log.info(f"lower border set to {border_lower}")
            elif border_msg[1].lower() == 'true' and is_master:
                border_enabled = True
                border_thread = threading.Thread(target=keep_boundaries, args=())
                border_thread.start()
                if LOGGING:
                    log.info(f"border mode enabled")
            elif border_msg[1].lower() == 'false':
                border_enabled = False
                if LOGGING:
                    log.info(f"border mode disabled")

        elif message.startswith('log') and LOGGING:
            _, new_name = message.lower().split(" ")
            print(f"Switching log file to: {new_name}")
            handler = logging.FileHandler(
                os.path.join(log_dir,
                             f'{new_name}_{"host" if is_master else "follower"}_{datetime.now().strftime("%d.%m_%H:%M")}.log'),
                'w')
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)

            for hdlr in log.handlers[:]:  # remove all old handlers
                log.removeHandler(hdlr)
            log.addHandler(handler)
            log.info("timestamp,value_elbow,value_wrist")

        elif message.startswith('sequence') and LOGGING:
            print(message)
            log.info(message)
    except Exception:
        pass


def receive_msg():
    while True:
        data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
        if addr[0] == SERVER_IP:
            message_callback(data)


def check_input():
    while True:
        pass


def main(argv):
    global LOGGING, log_dir, log
    try:
        opts, args = getopt.getopt(argv, "l:", ["log="])
    except getopt.GetoptError:
        print('test.py [-h] [-l <log_file>] [--log <log_file>]')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('test.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-l", "--log"):
            LOGGING = True
            log = logging.getLogger(__name__)  # root logger
            log.setLevel(logging.DEBUG)

            log_dir = os.path.join(THIS_DIR, arg)
            if not os.path.exists(log_dir):
                os.mkdir(log_dir)
            handler = logging.FileHandler(
                os.path.join(log_dir, f'initial_{datetime.now().strftime("%d.%m_%H:%M")}.log'), 'w')
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            log.addHandler(handler)
            log.info("timestamp,value_elbow,value_wrist")

    try:
        try:
            BP.reset_motor_encoder(BP.PORT_A + BP.PORT_B + BP.PORT_C)
        except IOError as error:
            print(error)

        print(BP.get_motor_encoder(BP.PORT_A))
        print(BP.get_motor_encoder(BP.PORT_B))
        print(BP.get_motor_encoder(BP.PORT_C))

        # Starting a thread which is listening to the UDP messages until the program is closed
        receive_msg_thread = threading.Thread(target=receive_msg, args=())
        receive_msg_thread.daemon = True  # Making the Thread daemon so it stops when the main program has quit
        receive_msg_thread.start()

        # input_thread = threading.Thread(target=check_input, args=())
        # input_thread.daemon = True  # Making the Thread daemon so it stops when the main program has quit
        # input_thread.start()

        BP.set_led(100)  # Light up the LED to show the setup is successful

        old = None
        while True:
            time_stamp = datetime.now().strftime('%H:%M:%S.%f')

            value_wrist = float(-BP.get_motor_encoder(BP.PORT_B))
            value_elbow = (BP.get_motor_encoder(BP.PORT_A) + BP.get_motor_encoder(BP.PORT_C)) * -1 / 2

            if LOGGING:
                log.info(f"{time_stamp},{value_elbow},{value_wrist}")

            if is_master and old != (value_wrist, value_elbow):
                old = (value_wrist, value_elbow)
                msg = f"control,{value_elbow},{value_wrist},{time_stamp}"
                udp_message = str.encode(msg)

                # print(f"Sending: {msg}")
                sock.sendto(udp_message, (SERVER_IP, SERVER_PORT))

            time.sleep(0.01)  # Without sleep the system logs and sends data ~820 times per second (820 Hz)
    finally:
        sock.close()
        print('\nsocket closed')
        BP.reset_all()  # Unconfigure the sensors, disable the motors, restore the LED
        print('program stopped')


if __name__ == "__main__":
    main(sys.argv[1:])
