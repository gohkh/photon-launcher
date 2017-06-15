import argparse
import serial
import time

def take_reading(port):
    m = 1
    c = 0
    with serial.Serial(port) as photometer:
        voltage = photometer.readline()
        voltage = voltage.decode('utf-8')
        voltage = m * float(voltage.strip()) + c
    return voltage

def main(port, n, interval, readings, save, printing):
    if n%readings != 0:
        raise ValueError("total number of readings not divisible by readings per time")
    if save:
        data = open(time.strftime('%Y%m%d_%H%M%S'), 'w+')
    while True:
        start = time.time()
        for i in range(readings):
            voltage = take_reading(port)
            if save:
                data.write(str(voltage) + '\n')
            n -= 1
            if printing:
                print(voltage)
            if n > 0 and printing:
                print("%s readings left" % n)
            elif n == 0:
                if printing:
                    print "Done!"
                break
        if interval > 0:
            time.sleep(interval - (time.time()-start))
    if save:
        data.close()

def init():
    parser = argparse.ArgumentParser()
    parser.add_argument('port', nargs = '?', type = str, help = "full path of voltage sensor device; default = \'/dev/ttyACM0\'", default = '/dev/ttyACM0')
    parser.add_argument('n', nargs = '?', type = int, help = "total number of readings to take; 0 for infinite (default)", default = 0)
    parser.add_argument('-t', '--interval', type = float, help = "time interval between readings; default = 0", default = 0)
    parser.add_argument('-n', '--readings', type = float, help = "readings per time if time interval is set to a positive value, default = 1", default = 1)
    parser.add_argument('-s', '--save', action = 'store_true', help = "flag to save data to timestamped file")
    parser.add_argument('-x', '--suppress_printing', action = 'store_false', help = "flag to suppress printing of readings to console")
    args = parser.parse_args()

    main(args.port, args.n, args.interval, args.readings, args.save, args.suppress_printing)

init()
