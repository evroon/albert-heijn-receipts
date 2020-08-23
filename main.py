from PIL import Image
import pytesseract
import subprocess
import difflib
import numpy as np

name = 'test'

def execute_cmd(command):
    ''' Execute a shell command and print output continuously. '''
    popen = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, universal_newlines=True)

    for stdout_line in iter(popen.stdout.readline, ""):
        print(stdout_line)

    popen.stdout.close()
    code = popen.wait()


def fuzzy_find(lines, keyword, accuracy=0.7):
    """
    Returns the index of the first line in lines that contains a keyword.
    It runs a fuzzy match if 0 < accuracy < 1.0
    Source: https://tech.trivago.com/2015/10/06/python_receipt_parser/
    """
    for i, line in enumerate(lines):
        words = line.split()
        # Get the single best match in line
        matches = difflib.get_close_matches(keyword, words, 1, accuracy)
        if matches:
            return i

    return None


def main():
    cmd = 'convert -auto-level -sharpen 0x4.0 -contrast img/{name}.jpg tmp/{name}.jpg'.format(name=name)
    execute_cmd(cmd)

    text = pytesseract.image_to_string(Image.open('tmp/{}.jpg'.format(name)))
    text = text.lower()
    text = text.replace(',', '.')
    text = text.replace('\n\n', '\n')
    lines = text.split('\n')
    table_start = fuzzy_find(lines, 'omschrijving')
    table_end = fuzzy_find(lines, 'subtotaal')

    if table_start is None or table_end is None:
        print('Could not parse receipt.')
        return

    table = lines[table_start:table_end]
    data = []

    def isfloat(value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    for i in range(len(table)):
        split = table[i].split(' ')
        if 'kg' in split[0]:
            split[0] = split[0].replace('kg', '')

        if not isfloat(split[0]):
            table[i] = ''
            continue

        amount = int(float(split[0]))
        product = ' '.join(split[1:-1])
        price = split[-1]

        if price.startswith('.'):
            price = ''.join(split[-2:])
            product = ' '.join(split[1:-2])
        elif '.' not in price:
            price = ''.join(split[-2:-1])
            product = ' '.join(split[1:-2])

        price = abs(float(price))
        amount = abs(amount)
        if amount < 1:
            amount = 1

        data.append([amount, product, price])
        table[i] = '{};{};{}'.format(product, amount, price)

    table = [x for x in table if x is not '']
    result = '\n'.join(table)
    total_amount = 0
    total_products = 0

    for item in data:
        total_amount += item[2]
        total_products += item[0]

    total_amount = lines[fuzzy_find(text.split('\n'), 'pinnen')].split(' ')[1]
    result += '\n;;\nTotal;{};{}'.format(total_products, total_amount)
    print('Total: ' + total_amount)

    with open('out/{}.csv'.format(name), 'w') as f:
        f.write(result)


main()
