# Automated Uni Notes

---

This project is devoted to creating a program which removes the need for me to take notes 
whilst watching my lectures for university.

It is built using pyautogui for slide and lecture detection as well as various misc features 
such as:
- Auto playing new lectures
- Capturing slide screenshots & detecting slide changes
- Ending the program after all lectures are finished

It is also built using tesseract for usage with image text to actual text where
it takes the screenshot and then gets a transcription which is saved to the 
lecture notes text file