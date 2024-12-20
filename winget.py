import sys
from urllib.request import urlopen, Request
import asyncio
import concurrent.futures
import functools
import urllib.request
import os
import threading

def parser(args):
    args = args[1:]
    if len(args) > 3:
        print("Incorrect usage. Try --help")
        sys.exit()
    
    silent, url, filename = False, None, None
    if args:
        if args[0] in ('-h', '--help'):
            print("""
              Usage: winget.py [OPTION] URL [FILENAME]
              Скачать файл лежащий в URL под названием FILENAME.
              Если FILENAME не указан, файл сохранится с названием в URL.
              Если URL не указан, будет запущен stdin, файл сохранится с названием в URL.

              OPTIONS:
                -h --help Показывает это сообщение
                -s --silent  Прячет прогрессбар""")
            sys.exit()
        elif args[0] in ('-s', '--silent'):
            silent = True
            args = args[1:]
    
    if args:
        url = args[0]
        args = args[1:]
    else:
        url = input("URL: ")
    
    if args:
        filename = args[0]
    else:
        filename = filename = url.split('/')[-1]

    return silent, url, filename

downloaded_bytes = 0
downloaded_lock = threading.Lock()

async def get_size(url):
    with urlopen(url) as response:
        size = int(response.headers['content-length'])
    return size

def download_range(silent, url, start, end, output, file_size):
    global downloaded_bytes
    headers = {'Range': f'bytes={start}-{end}'}
    req = Request(url, headers=headers)
    
    with urlopen(req) as response:
        with open(output, 'wb') as f:
            while True:
                chunk = response.read(1024)
                if not chunk:
                    break
                f.write(chunk)
                with downloaded_lock:
                    downloaded_bytes += len(chunk)
                    if not(silent): print_progress(downloaded_bytes, file_size)


def print_progress(downloaded, file_size):
    bar = 100
    percent = int(downloaded * bar / file_size)
    print(end='\r', flush=True)
    print(f'[{f'{percent}%':>^{percent}}{('ⴾ'*(bar-percent))}]', end='\r', flush=True)

async def download(silent, run, loop, url, output, chunk_size=1024*1024):
    file_size = await get_size(url)
    chunks = range(0, file_size, chunk_size)

    tasks = [
        run(
            download_range,
            silent,
            url,
            start,
            start + chunk_size - 1,
            f'{output}.part{i}',
            file_size
        )
        for i, start in enumerate(chunks)
    ]

    await asyncio.wait(tasks)

    with open(output, 'wb') as o:
        for i in range(len(chunks)):
            chunk_path = f'{output}.part{i}'

            with open(chunk_path, 'rb') as s:
                o.write(s.read())

            os.remove(chunk_path)
    print(flush=True)
    

if __name__ == '__main__':
    silent, url, filename = parser(sys.argv)

    executor = concurrent.futures.ThreadPoolExecutor()
    loop = asyncio.new_event_loop()
    run = functools.partial(loop.run_in_executor, executor)

    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(
            download(silent, run, loop, url, filename)
        )
    finally:
        loop.close()