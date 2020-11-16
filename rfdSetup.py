import os
from serial import Serial
import argparse
from select import select
import time

parser = argparse.ArgumentParser(description='Config RFD modem')
parser.add_argument('-p', '--port', default='/dev/ttyUSB0', help='RFD modem port')
parser.add_argument('-b', '--baudRate', type=int, default=57600, help='Modem baud rate')
parser.add_argument('-n', '--netId', type=int, default=None, help='net id 0 - 99')

args = parser.parse_args()

baud = args.baudRate
port = args.port
ser = Serial(port, baud, timeout=1)



def send_at_command(command):
    ser.write(bytes(command+"\r", encoding='ascii'))
    ser.flush()
    time.sleep(0.05)


def read_command_response():
    try:
        num = ser.inWaiting()
        cnt = 20
        while num == 0:
            time.sleep(0.1)
            num = ser.inWaiting()
            cnt -= 1
            if cnt == 0:
                break
        ret = ''
        while len(select([ser],[],[],0.1)[0]) > 0:
            ret += ser.read(num).decode('utf8', errors='ignore').strip()
        
        #print(ret)
        #print("\n")
        return ret
    except:
        import traceback
        traceback.print_exc()

while True:
    time.sleep(0.5)
    ser.write(bytes('+++', encoding='ascii'))
    ser.flush()
    ret = read_command_response()
    if ret=='OK' or ret == '+++':
        break


if args.netId is not None:
    print ('set net id to %d'%args.netId)
    send_at_command("ATS3=%d"%args.netId)
    ret = read_command_response()
    
    if 'OK' in ret:
        print('net setup is Ok, writing EEPROM')
        send_at_command("AT&W")
        ret = read_command_response()
        if 'OK' in ret:
            print('EEPROM written successfuly...')


print('configurstion before reboot device:')
send_at_command("ATI5")
ret = read_command_response()
print(ret)



ser.write(bytes('ATZ\r', encoding='ascii'))
ser.flush()
print('Done RFD setup')
#read_command_response()

