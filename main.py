import random
import time
import threading

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

from PyDMXControl.controllers import OpenDMXController
from PyDMXControl.profiles.Generic import Dimmer

dmx = OpenDMXController()

servo_body = dmx.add_fixture(Dimmer, start_channel=1)
servo_arm = dmx.add_fixture(Dimmer, start_channel=2)
servo_head = dmx.add_fixture(Dimmer, start_channel=3)
servo_eye_l = dmx.add_fixture(Dimmer, start_channel=4)
servo_eye_r = dmx.add_fixture(Dimmer, start_channel=5)
laser_eye_l = dmx.add_fixture(Dimmer, start_channel=6)
laser_eye_r = dmx.add_fixture(Dimmer, start_channel=7)

def print_handler(address, *args):
    print(f"{address}: {args}")

def default_handler(address, *args):
    print(f"DEFAULT {address}: {args}")

tick = 0
arm_speed = 0
arm_position = 0
arm_forward = True

def update_arm():
    global arm_speed, arm_position, arm_forward
    while True:
        if arm_forward:
            arm_position += arm_speed / 30.0

            if arm_position > 1.0:
                arm_position = 1.0 - (arm_position - 1.0)
                arm_forward = False
        else:
            arm_position -= arm_speed / 30.0

            if arm_position < 0:
                arm_position = -arm_position
                arm_forward = True
        
        # servo_arm.dim(round(arm_position * 150) + 90, round(1000 / 30.0))
        servo_arm.dim(round(arm_position * 255), round(1000 / 30.0))
        time.sleep(1 / 30.0)


arm_timer = threading.Thread(target = update_arm)
arm_timer.daemon = True
arm_timer.start()

laser_mode = 0

def bpm_handler(address, *args):
    bpm = args[0]
    global arm_position, arm_forward, tick, arm_speed, laser_mode

    arm_speed = 1.0 / (60 / args[0]) / 1.0
    if tick % 4 == 0:
        arm_position = 0
        arm_forward = True
        print("arm zero")

    # print(f"BPM {address}: {args}")

    if laser_mode == 0: 
        laser_on = True    
    else:
        laser_on = tick % 2 == 0
        
    # laser_eye_l.on() if laser_on else laser_eye_l.off()
    # laser_eye_r.on() if laser_on else laser_eye_r.off()
    
    print("laser", laser_on)

    servo_arm.dim(255 if tick % 2 == 0 else 0, round(1000 / (bpm / 60)))

    if random.randint(0, 10) == 0:
        head_pos = random.randint(0, 255)
        # servo_head.dim(head_pos, 500)
        print("head to", head_pos)

    if tick % 4 == 0:
        switch_laser_mode = random.randint(0, 5) == 0
        if switch_laser_mode:
            laser_mode = 1 if laser_mode == 0 else 0
            print("switch laser mode", laser_mode)

        eyes_rand = random.randint(0, 5)
        if eyes_rand == 0:
            eye_pos = random.randint(0, 255)
            # servo_eye_l.dim(eye_pos, 200)
            # servo_eye_r.dim(eye_pos, 200)
            print("eyes to", eye_pos)
        else:
            # servo_eye_l.dim(20, 200)
            # servo_eye_r.dim(20, 200)
            print("eyes to", 20)

    tick += 1

dispatcher = Dispatcher()
dispatcher.map("/*", bpm_handler)

ip = "127.0.0.1"
port = 1337

server = BlockingOSCUDPServer((ip, port), dispatcher)
server.serve_forever()  # Blocks forever
