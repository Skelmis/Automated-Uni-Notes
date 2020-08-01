import time

import cv2
import pytesseract
import pyautogui
from pyautogui import ImageNotFoundException

from pathlib import Path

from exceptions import *

pytesseract.pytesseract.tesseract_cmd = (
    "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
)


class Locator:
    LEFT = 0
    TOP = 0
    WIDTH = 250
    HEIGHT = 60

    SLIDESLEEPTIME = 15
    DEFAULTIMAGEFILENAME = "image.png"
    DEFAULTOUTPUTFILENAME = "Lecture Notes.txt"

    INITIALIZED = False

    def __init__(
        self,
        initialImage,
        *,
        outputFilename=None,
        slideSleepTime=None,
        defaultImageFilename=None,
    ):
        self.current_image = initialImage

        self.output_filename = outputFilename or self.DEFAULTOUTPUTFILENAME
        self.image_filename = defaultImageFilename or self.DEFAULTIMAGEFILENAME
        self.slide_sleep_time = slideSleepTime or self.SLIDESLEEPTIME

        self.left = self.LEFT
        self.top = self.TOP
        self.width = self.WIDTH
        self.height = self.HEIGHT

        self.confidence = 0.85
        self.repeatedSlideCount = 0  # Times the slide has been seen in a row

        self.initialized = self.INITIALIZED
        self.cwd = self.GetCwd()

    @staticmethod
    def GetCwd():
        """
        A function to get the current path main.py
        """
        cwd = Path(__file__).parents[0]
        cwd = str(cwd)
        return cwd

    def IsInitialized(self):
        """
        Is simply used to check whether or not this instance
        has been initialized or not yet
        :return: -> None
        """
        if not self.initialized:
            raise InstanceNotInitialized

    def Initialize(self):
        """
        This should be called before using this class for the
        first time, this just sets up the relevant cords etc
        :return:
        """
        self.left, self.top, self.width, self.height = self.LocateSlideAreaTopCords(
            self.current_image
        )
        self.initialized = True

        print("Processing Initialization screenshot")
        text = self.ImageToText()
        with open(f"{self.cwd}\\{self.output_filename}", "w") as f:
            f.write(text)
            f.write("\n<--->\nEnd Slide\n-----\n\n")

        self.StartVideo()
        self.MuteVideo()

    def Executor(self):
        """
        This is the main loop of the program, calling this will continue
        to run the loop until it is kicked out of 
        :return:
        """
        self.IsInitialized()

        while True:
            """
            This loop aims to check every 15 seconds if there is a new 
            lecture slide, if there is take a screenshot of it and 
            create a transcription before looping again
            """
            print(f"\n---\nCurrent repeated slide count: {self.repeatedSlideCount}")
            time.sleep(self.slide_sleep_time)

            if self.repeatedSlideCount >= 25:  # Change to 25 in production
                print("Trying to change lecture")
                # We can assume the lecture is over as the slide has not changed in 6.25 mins
                try:
                    closeTabX, closeTabY = pyautogui.locateCenterOnScreen(
                        f"{self.cwd}/images/static/close tab.png",
                        confidence=self.confidence,
                    )
                    if closeTabX is None or closeTabY is None:
                        raise ExitError("Failed to close tab due to invalid location")
                except TypeError:
                    desktop = pyautogui.locateOnScreen(
                        f"{self.cwd}/images/static/desktop partial background.png",
                        confidence=self.confidence,
                    )
                    if desktop is not None:
                        print("Desktop found, exiting software.")
                        return

                # We can assume we have found where the close tab button is
                pyautogui.click(closeTabX, closeTabY)
                check = self.ProcessNewSlideScreenshot()
                if not check:
                    raise ExitError("Failed to change lecture")

                with open(f"{self.cwd}\\{self.output_filename}", "a") as f:
                    f.write("\n-----\nEnd Lecture\n-----\n\n\n")

                self.StartVideo()  # Just make sure the video is playing
                self.MuteVideo()  # Just make sure the video is muted
                continue
            else:
                print("Not trying to change lecture")
                imageLocation = pyautogui.locateOnScreen(
                    f"{self.cwd}/images/{self.current_image}",
                    confidence=self.confidence,
                )
                if imageLocation is not None:
                    # We are still on the same slide
                    print("We are still on the same slide")
                    self.repeatedSlideCount += 1
                    continue

                print("We are on a new slide")
                # We are on a new slide
                self.ProcessNewSlideScreenshot()

    def LocateSlideAreaTopCords(self, imgName):
        """
        Used to locate and get the cords of the area on the
        current screen, essentially allows for dynamic checking
        of the current slide
        :return:
        """
        imageLocation = pyautogui.locateOnScreen(
            f"{self.cwd}/images/{imgName}", confidence=self.confidence
        )
        if imageLocation is None:
            raise SlideNotFound

        return imageLocation

    def TakeNewSlideScreenshot(self):
        """
        Handles taking a new screenshot of the new slide
        in the current lecture
        :return:
        """
        self.IsInitialized()

        try:
            pyautogui.screenshot(
                f"{self.cwd}\\images\\{self.image_filename}",
                region=(self.left, self.top, self.width, self.height),
            )
            self.current_image = self.image_filename
            return True
        except Exception as e:
            raise e

    def ImageToText(self):
        """
        Takes an image name (Assuming its in images dir) and
        then returns the text for the image
        :return:
        """
        self.IsInitialized()

        img = cv2.imread(f"{self.cwd}/images/{self.current_image}")

        text = pytesseract.image_to_string(img)
        return text

    def ProcessNewSlideScreenshot(self):
        """
        A function designed to process taking a new
        slide screenshot and then get the text for it
        before saving it to our file and returning
        :return:
        """
        print("Processing new slide screenshot")
        try:
            check = self.TakeNewSlideScreenshot()
            if not check:
                return False

            text = self.ImageToText()
            with open(f"{self.cwd}\\{self.output_filename}", "a") as f:
                f.write(text)
                f.write("\n<--->\nEnd Slide\n-----\n\n")
            self.repeatedSlideCount = 0
            return True
        except Exception as e:
            raise e

    def StartVideo(self):
        """
        This function is used to find and figure out
        if we the program need to start a lecture or
        if the video has already started.

        It is assumed that once this function returns,
        the video will be playing. This is non crucial
        :return:
        """
        try:
            panoptoPlayButtonX, panoptoPlayButtonY = pyautogui.locateCenterOnScreen(
                f"{self.cwd}/images/static/panopto play button.png",
                confidence=self.confidence,
            )
            if panoptoPlayButtonX is not None and panoptoPlayButtonY is not None:
                # We can assume that we now need to start the lecture
                pyautogui.click(panoptoPlayButtonX, panoptoPlayButtonY)
        except TypeError:
            # Video must already be started
            pass

    def MuteVideo(self):
        """
        This function is used to find and figure out
        if we need to mute the lecture audio or not.

        It is assumed that once this function returns,
        the video will be muted. This is non cruicial
        :return:
        """
        try:
            panoptoMuteButtonX, panoptoMuteButtonY = pyautogui.locateCenterOnScreen(
                f"{self.cwd}/images/static/panopto unmuted button.png",
                confidence=self.confidence,
            )
            if panoptoMuteButtonX is not None and panoptoMuteButtonY is not None:
                # We can assume that we now need to mute the lecture
                pyautogui.click(panoptoMuteButtonX, panoptoMuteButtonY)
        except TypeError:
            # Video must already be muted
            pass

    def Run(self):
        """
        This is a wrapper around the executor method
        as I feel I may change how it is implemented
        further on down the line
        :return:
        """
        self.Initialize()

        self.IsInitialized()

        self.Executor()


if __name__ == "__main__":
    print("Program started")
    time.sleep(2.5)
    instance = Locator(initialImage="img5.png")
    print("Instance initialized, beginning execution.")

    instance.Run()
