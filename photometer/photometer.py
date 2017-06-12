import argparse
import serial
import time

m = 1
c = 0

def main(port, readings, interval, save, printing):
    if save:
        data = open(time.strftime('%Y%m%d_%H%M%S'), 'w+')
    try:
        with serial.Serial(port) as photometer:
            while True:
                start = time.time()
                voltage = photometer.readline()
                voltage = m * float(voltage.strip()) + c
                data.write(str(voltage) + '\n')
                readings -= 1
                if printing:
                    print(voltage)
                if readings < 0:
                    print("%s readings left" % readings)
                elif readings == 0:
                    break
                if interval > 0:
                    time.sleep(interval - (time.time()-start))
        data.close()
    except NameError:
        pass

def init():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type = str, help = "full path of voltage sensor device; default = \'/dev/ttyACM0\'", default = '/dev/ttyACM0')
    parser.add_argument('-n', '--readings', type = int, help = "total number of readings to take; 0 for infinite (default)", default = 0)
    parser.add_argument('-t', '--interval', type = float, help = "time interval between readings; default = 0", default = 0)
    parser.add_argument('-s', '--save', action = 'store_true', help = "flag to save data to a file")
    parser.add_argument('-o', '--output', action = 'store_false', help = "flag to suppress printing of readings to console")
    args = parser.parse_args()

    main(args.port)

init()
