import datetime
import hashlib
import multiprocessing
import pprint
import re
import time
from collections import namedtuple
import os
from keyboard import is_pressed
import csv
import sqlite3

now = time.time()

previous = 'cdac1f5a6b2d5fcd32bf9287702446dc0637644860809f1fa294e00eed00a254'
current = 'fadaa78054ac10b5967cd0dd8d7886029a2f4e98ca378a71a5621b42a6126dd3'
nonce = ''
largest_zero_count = 0
cores = 8
database = []


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def to_hms(seconds):
    st_time = namedtuple('time', 'hours minutes seconds')
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return st_time(hours, minutes, seconds)


def print_time(computation):
    print(f'Process {computation[0]} starting: {computation}')
    global largest_zero_count
    global best_hash
    global best_nonce

    id = computation[0]
    largest_zero_count = int(computation[1])
    prog = re.compile(rf"^0{{{largest_zero_count if largest_zero_count != 0 else 1},}}")
    best_hash = computation[3] if int(computation[3], 16) > 0 else hashlib.sha256(('%s%s%s' % (previous, current, "{:032x}".format(0))).encode('utf-8')).hexdigest()
    best_nonce = computation[2]
    start, end = int(computation[4]), int(computation[5])

    for i in range(start, end):

        nonce = "{:032x}".format(i)
        main_hash = hashlib.sha256(('%s%s%s' % (previous, current, nonce)).encode('utf-8')).hexdigest()

        if bool(prog.match(main_hash)):

            m = prog.match(main_hash)

            if m.end() >= largest_zero_count:
                if int(main_hash, 16) < int(best_hash, 16):
                    if m.end() == largest_zero_count:
                        print(f'\n\n{bcolors.FAIL}found a smaller one!{bcolors.ENDC}')
                    largest_zero_count = m.end()
                    best_hash = main_hash
                    best_nonce = nonce
                    countdown = to_hms(int(float(computation[6]) + float(time.time() - now)))
                    prog = re.compile(rf"^0{{{largest_zero_count if largest_zero_count != 0 else 1},}}")
                    hash_time = f"{bcolors.OKGREEN}{countdown.hours} hour(s) {countdown.minutes} minute(s) {countdown.seconds} second(s){bcolors.ENDC}"
                    status_text = f'\n{hash_time} - Process {bcolors.OKGREEN}{id}{bcolors.ENDC}' \
                        f'\nNumber of 0s: {bcolors.FAIL}{largest_zero_count}{bcolors.ENDC}' \
                        f'\nHash:         {bcolors.OKBLUE}{best_hash}{bcolors.ENDC}' \
                        f'\nNonce:        {bcolors.OKBLUE}{best_nonce}{bcolors.ENDC}' \
                        f'\nProgress      {bcolors.OKBLUE}{str((((int(nonce, 16) - start) / 20000000000000000000000000000000) * 100))} % {bcolors.ENDC}' \
                        f'\nHash rate     {bcolors.OKBLUE}{(i - (0 if id == 1 else ((((16 ** 32) // 8) * (id - 1)) - 1))) / int(float(computation[6]) + float(time.time() - now))}{bcolors.ENDC}'
                    print(status_text)
                    print(prog)

        if is_pressed('q'):
            print(
                f'Proccess {bcolors.FAIL}{id}{bcolors.ENDC}: {bcolors.OKGREEN}finished - {largest_zero_count} zeroes{bcolors.ENDC}\n'
                f'iteration:  {bcolors.OKGREEN}{i}{bcolors.ENDC}\n'
                f'currentHash:{bcolors.OKGREEN}{"{:032x}".format(i)}{bcolors.ENDC}\n'
                f'best hash   {bcolors.OKGREEN}{largest_zero_count} zeroes: {best_hash}{bcolors.ENDC}\n'
                f'best nonce  {bcolors.OKGREEN}{largest_zero_count}{best_nonce}{bcolors.ENDC}\n'
                f'end:        {bcolors.OKGREEN}{end}{bcolors.ENDC}\n'
                f'end hash    {bcolors.OKGREEN}{"{:032x}".format(end)}{bcolors.ENDC}\n\n\n')
            conn = sqlite3.connect('hash_data.db')
            c = conn.cursor()
            update_string = '''UPDATE hash_data SET largest_zero_count={largest_zero_count}, best_hash='{best_hash}', start='{start}', ending='{ending}', best_nonce='{best_nonce}', total_proccessing_time={total_proccessing_time} WHERE id={id};'''.format(
                largest_zero_count=largest_zero_count,
                best_hash=str(best_hash),
                best_nonce=str(best_nonce),
                start=str(i),
                ending=str(end),
                id=id,
                total_proccessing_time=float(computation[6]) + (time.time() - now))
            print(update_string)
            with conn:
                c.execute(update_string)
            break


if __name__ == "__main__":

    conn = sqlite3.connect('hash_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS hash_data(
    id numeric not null primary key , 
    largest_zero_count numeric ,
    best_nonce varchar ,
    best_hash varchar,
    start varchar(255) ,
    ending varchar(255),
    total_proccessing_time varchar
    )''')
    with conn:
        c.execute("SELECT * FROM hash_data")
        if len(c.fetchall()) < 8:
            def hash_insert(id, largest_zero_count, best_nounce, best_hash, start, ending):
                query = '''INSERT INTO hash_data VALUES ({id},{largest_zero_count},'{best_nounce}','{best_hash}','{start}','{ending}','{total_proccessing_time}')''' \
                    .format(id=id, largest_zero_count=largest_zero_count, best_nounce=best_nounce, best_hash=best_hash,
                            start=start, ending=ending, total_proccessing_time='0')
                print(query)
                c.execute(query)


            def get_computation_range(i):
                l = (((16 ** 32) // 8) * i) - 1
                print(l, str(l))
                return l


            hash_insert(1, 0, '0', '0', '0', str(get_computation_range(1)))
            for i in range(2, 9):
                hash_insert(i, 0, '0', '0', str(get_computation_range(i - 1)), str(get_computation_range(i)))

    with conn:
        c.execute("SELECT * FROM hash_data")
        database = c.fetchall()

    jobs = []
    for core in database:
        process = multiprocessing.Process(target=print_time, args=(core,))
        jobs.append(process)

    # Start the processes (i.e. calculate the random number lists)
    for j in jobs:
        j.start()

    # Ensure all of the processes have finished
    for j in jobs:
        j.join()

    print("Hash range mapped!")
