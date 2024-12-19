import sys
from urllib.request import urlretrieve, urlopen

def parser(args):
    args = args[1:]
    if len(args) < 1 or len(args) > 3:
        print("Incorrect usage. Try --help")
        sys.exit()
    
    option, url, filename = True, None, None
    if args[0] in ('-h', '--help'):
        print("""
              Usage: winget.py [OPTION] URL [FILENAME]
              Скачать файл лежащий в URL под названием FILENAME.
              Если FILENAME не указан, файл сохранится с названием в URL.
              
              OPTIONS:
                -h --help Показывает это сообщение
                -s --silent  Прячет прогрессбар""")
        sys.exit()
    elif args[0] in ('-s', '--silent'):
        option = False
        args = args[1:]
    url = args[0]
    args = args[1:]
    if args:
        filename = args[0]
    else:
        filename = url.split('/')[-1]
    return option, url, filename

def filegetter(option, url, filename):
    try:
        with urlopen(url) as response:
            length = float(response.headers['content-length'])
            downloaded = 0.0
            data_blocks = []
            
            while True:
                block = response.read(1024)
                data_blocks.append(block)
                downloaded += len(block)
                percent = int(downloaded * 100 / length)
                if option:
                    print(end='\r', flush=True)
                    print(f'[{f'{percent}%':>^{percent}}{('-'*(100-int(percent)))}]', end='\r', flush=True)

                if not len(block):
                    if option: print('\n')
                    break
            data = b''.join(data_blocks)
            response.close()
            if option: print('Загрузка выполнена!')
        with open(filename, 'wb') as f:
            f.write(data)

    except ValueError:
        print("Неправильно введен URL. --help")
    except Exception as e:
        print("Ошибка сети.", e.__cause__)
    
if __name__ == '__main__':
    option, url, filename = parser(sys.argv)
    filegetter(option, url, filename)