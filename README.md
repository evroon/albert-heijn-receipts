# Albert Heijn Receipts
Scans and parses receipts from the Albert Heijn supermarket using tesseract

## Usage
1. Install [tesseract](https://tesseract-ocr.github.io/tessdoc/Home.html).
2. Install the Python dependencies: `python3 -m pip install Pillow pytesseract`
3. Put an image in the `img` directory
4. Execute the main.py script, a csv file with the receipt's contents will be put in the `out` directory.
