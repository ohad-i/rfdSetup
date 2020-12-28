import os
from serial import Serial
import argparse
from select import select
import time

paramIdDict = {'FORMAT':0,
               'SERIAL_SPEED':1,
               'AIR_SPEED':2,
               'NETID':3,
               'TXPOWER':4, 
               'ECC':5,
               'MAVLINK':6,
               'OPPRESEND':7,
               'MIN_FREQ':8,
               'MAX_FREQ':9,
               'NUM_CHANNELS':10,
               'DUTY_CYCLE':11,
               'LBT_RSSI':12,
               'MANCHESTER':13,
               'RTSCTS':14,
               'MAX_WINDOW':15,
               'ENCRYPTION_LEVEL':16}




parser = argparse.ArgumentParser(description='Config RFD modem')
parser.add_argument('-p', '--port', default='/dev/ttyUSB0', help='RFD modem port, default: /dev/ttyUSB0')
parser.add_argument('-b', '--baudRate', type=int, default=57600, help='Modem baud rate, default: 57600 ')
parser.add_argument('-n', '--netId', type=int, default=None, help='net id 0 - 99')
parser.add_argument('-s', '--showSetup', action='store_true', help='Show modem setup')
parser.add_argument('-a', '--attribute', default=None, help='Modem attribute to set (with value):\n %s'%(paramIdDict.keys()) )
parser.add_argument('-v', '--value', type=int, default=None, help='Modem attribute value' )
parser.add_argument('-r', '--configRemote', action='store_true', default=False, help='Config remote modem, all action will be performed on remote modem' )
parser.add_argument('-c', '--readRSSI', action='store_true', default=False, help='Read mode RSSI' )

args = parser.parse_args()

baud = args.baudRate
port = args.port
ser = Serial(port, baud, timeout=1)

confSucceed = False

initial = 'A' # for local modem configuration
if args.configRemote:
    initial = 'R' # for remote modem configuration (config over rf)



def send_at_command(command):
    ser.write(bytes(command+"\r", encoding='ascii'))
    ser.flush()


def read_command_response():
    try:
        num = ser.inWaiting()
        cnt = 500 # max tries for receiving respnse 
        while num == 0:
            time.sleep(0.1)
            num = ser.inWaiting()
            cnt -= 1
            if cnt == 0:
                print('Failed to get response...')
                break
        ret = ''
        while len(select([ser],[],[],0.1)[0]) > 0:
            ret += ser.read().decode('utf8', errors='ignore')#.strip()
        
        #print(ret)
        #print("\n")
        return ret
    except:
        import traceback
        traceback.print_exc()


def setModemParam(paramId, value):
    global confSucceed
    cmd = "%sTS%d=%d"%(initial, paramId, value)
    send_at_command(cmd)
    ret = read_command_response()
    if ret==cmd:
        send_at_command(cmd)
        ret = read_command_response()
    
    if 'OK' in ret:
        send_at_command("AT&W")
        ret = read_command_response()
        if 'OK' in ret:
            print('EEPROM written successfuly...')
            confSucceed = True
        else:
            print('Failed to write EEPROM\n' + ret)
    else:
        print('Failed to write param\n' + ret)



if __name__=="__main__":
    try:
        while True:
            time.sleep(0.005)
            ser.write(bytes('+++', encoding='ascii'))
            ser.flush()
            ret = read_command_response()
            if ('OK' in ret) or ('+++' in ret):
                print('Log in setup mode successfully...')
                break
            else:
                print('Failed to log in setup mode...')
            time.sleep(0.5)

        if initial == 'R':
            cmd="ATI5"
            send_at_command(cmd)
            ret = read_command_response()
            if ret==cmd:
                send_at_command(cmd)
                ret = read_command_response() 

        if args.showSetup:
            cmd = "%sTI5"%initial
            send_at_command(cmd)
            ret = read_command_response()
            if ret==cmd:
                send_at_command(cmd)
                ret = read_command_response()
            print(ret)

        if args.readRSSI:
            cmd = "%sTI7"%initial
            send_at_command(cmd)
            ret = read_command_response()
            if ret==cmd:
                send_at_command(cmd)
                ret = read_command_response()
            print(ret)



        if args.netId is not None:
            print ('set net id to %d'%args.netId)
            setModemParam(paramIdDict['NETID'], args.netId)

        if args.attribute is not None and args.value is not None:
            if args.attribute in paramIdDict.keys():
                setModemParam(paramIdDict[args.attribute], args.value)


        if confSucceed:
            print('configurstion before reboot device:')
            cmd = "%sTI5"%initial
            send_at_command(cmd)
            ret = read_command_response()
            if ret==cmd:
                send_at_command(cmd)
                ret = read_command_response()
            print(ret)


    except:
        import traceback
        traceback.print_exc()
    finally:
        if initial == 'R':
            ser.write(bytes('%sTZ\r'%initial, encoding='ascii'))
            ser.flush()
        ser.write(bytes('ATZ\r', encoding='ascii'))
        ser.flush()


        print('Done RFD setup')
        #read_command_response()

