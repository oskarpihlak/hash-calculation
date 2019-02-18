# multiproc_test.py
import hashlib
import json
import multiprocessing
import pprint
import re
import time
from collections import namedtuple
import os
import keyboard as keyboard
import csv

now = time.time()

previous = 'cdac1f5a6b2d5fcd32bf9287702446dc0637644860809f1fa294e00eed00a254'
current = 'fadaa78054ac10b5967cd0dd8d7886029a2f4e98ca378a71a5621b42a6126dd3'
nonce = ''
prog = re.compile(r"^0+")
largest_zero_count = 0


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


cores = 8
if not os.path.exists('hash_data.csv'):
    def get_computation_range(i):
        return (((16 ** 32) // cores) * i) - 1


    computation_ranges = {"1": {
        "unit":1,
        "start": 0,
        "end": get_computation_range(1),
        "largest_zero_count": 0,
        "best_nonce": '',
        "best_hash": ''
    }}
    for i in range(2, 9):
        computation_ranges[i] = {
            "unit": i,
            "start": get_computation_range(i - 1),
            "end": get_computation_range(i),
            "largest_zero_count": 0,
            "best_nonce": '',
            "best_hash": ''
        }
else:
    computation_ranges = {}
    with open('hash_data.csv', newline='\n') as csvfile:
        hash_data = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in hash_data:
            computation_ranges[row[0]] = {
                "unit": row[0],
                "largest_zero_count": row[1],
                "best_nonce": row[2],
                "best_hash": row[3],
                "start": row[4],
                "end": row[5]
            }

    f = open('hash_data.csv', 'w+')
    f.truncate(0)
    f.close()

    pprint.pprint(computation_ranges)
def to_hms(seconds):
    st_time = namedtuple('time', 'hours minutes seconds')
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return st_time(hours, minutes, seconds)


def print_time(computation):
    global largest_zero_count
    global best_hash
    global best_nonce

    unit = computation['unit']
    largest_zero_count = int(computation['largest_zero_count'])
    best_hash = computation['best_hash']
    best_nonce = computation['best_nonce']
    start, end = int(computation['start']), int(computation['end'])

    for i in range(start, end):
        nonce = "{:032x}".format(i)
        main_hash = hashlib.sha256(('%s%s%s' % (previous, current, nonce)).encode('utf-8')).hexdigest()
        m = prog.match(main_hash)
        if m:
            if keyboard.is_pressed('q'):
                print(
                    f'Proccess {bcolors.FAIL}{unit}{bcolors.ENDC}: {bcolors.OKGREEN}finished - {largest_zero_count} zeroes{bcolors.ENDC}\n'
                    f'iteration:  {bcolors.OKGREEN}{i}{bcolors.ENDC}\n'
                    f'currentHash:{bcolors.OKGREEN}{"{:032x}".format(i)}{bcolors.ENDC}\n'
                    f'best hash   {bcolors.OKGREEN}{largest_zero_count} zeroes: {best_hash}{bcolors.ENDC}\n'
                    f'best nonce  {bcolors.OKGREEN}{largest_zero_count}{best_nonce}{bcolors.ENDC}\n'
                    f'end:        {bcolors.OKGREEN}{end}{bcolors.ENDC}\n'
                    f'end hash    {bcolors.OKGREEN}{"{:032x}".format(end)}{bcolors.ENDC}\n\n\n'
                )
                myCsvRow = f'{unit},{largest_zero_count},{best_nonce},{best_hash},{i},{end}\n'
                with open('hash_data.csv', 'a') as fd:
                    fd.write(myCsvRow)
                break
            if m.end() > largest_zero_count:
                largest_zero_count = m.end()
                best_hash = main_hash
                best_nonce = nonce
                countdown = to_hms(int(time.time() - now))
                hash_time = f"{bcolors.OKGREEN}{countdown.hours} hour(s) {countdown.minutes} minute(s) {countdown.seconds} second(s){bcolors.ENDC}"
                status_text = f'\n{hash_time} - Process {bcolors.OKGREEN}{unit}{bcolors.ENDC}' \
                    f'\nNumber of 0s: {bcolors.FAIL}{largest_zero_count}{bcolors.ENDC}' \
                    f'\nHash:         {bcolors.OKBLUE}{best_hash}{bcolors.ENDC}' \
                    f'\nNonce:        {bcolors.OKBLUE}{best_nonce}{bcolors.ENDC}' \
                    f'\nProgress      {bcolors.OKBLUE}{str((((int(nonce, 16) - start) / 20000000000000000000000000000000) * 100))} % {bcolors.ENDC}'
                print(status_text)


if __name__ == "__main__":
    jobs = []
    for range in computation_ranges:
        print('lolq',computation_ranges[range])
        process = multiprocessing.Process(target=print_time, args=(computation_ranges[range],))
        jobs.append(process)

    # Start the processes (i.e. calculate the random number lists)
    for j in jobs:
        j.start()

    # Ensure all of the processes have finished
    for j in jobs:
        j.join()

    print("Hash range mapped!")
