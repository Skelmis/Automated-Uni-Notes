import cv2
import pytesseract

pytesseract.pytesseract.tesseract_cmd = (
    "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
)

img = cv2.imread("test.png")

text = pytesseract.image_to_string(img)

with open("output.txt", "a") as f:
    f.write(text)
    f.write("\nEnd slide\n-----\n\n")
