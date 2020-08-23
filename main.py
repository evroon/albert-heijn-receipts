from PIL import Image
import pytesseract
import subprocess
import difflib
import json
from flask import Flask, flash, request, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = 'img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'a not so secret key for debugging'

def execute_cmd(command):
    ''' Execute a shell command and print output continuously. '''
    popen = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, universal_newlines=True)

    for stdout_line in iter(popen.stdout.readline, ""):
        print(stdout_line)

    popen.stdout.close()
    popen.wait()


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


def process(filename):
    name = os.path.splitext(filename)[0]
    output_path = 'out/{}.json'.format(name)

    if os.path.exists(output_path):
        with open(output_path, 'r') as f:
            return json.loads(f.read())

    cmd = 'convert -auto-level -sharpen 0x4.0 -contrast img/{filename} tmp/{filename}'.format(filename=filename)
    execute_cmd(cmd)

    text = pytesseract.image_to_string(Image.open('tmp/{}'.format(filename)))
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
    subtotal_price = 0
    total_products = 0

    for item in data:
        subtotal_price += item[2]
        total_products += item[0]

    total_price = lines[fuzzy_find(text.split('\n'), 'pinnen')].split(' ')[1]
    output = {
        'items': data,
        'total': total_price,
        'subtotal': subtotal_price,
    }

    with open(output_path, 'w') as f:
        f.write(json.dumps(output))

    return output


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/img/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    filename = request.args.get('filename')
    data = []

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('upload_file', filename=filename))

    if filename != None:
        data = process(filename)

    files = os.listdir(app.config['UPLOAD_FOLDER'])

    return render_template('main.html', data=data, filename=filename, files=files)
