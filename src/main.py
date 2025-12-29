import cv2
import mediapipe as mp
import customtkinter as ctk
import numpy as np


def main():
    print("--- LungeGuard System Check ---")

    # Test OpenCV
    print(f"OpenCV Version: {cv2.__version__}")

    # Test MediaPipe
    try:
        mp_pose = mp.solutions.pose
        print("MediaPipe: OK")
    except Exception as e:
        print(f"MediaPipe Error: {e}")

    # Test CustomTkinter
    print(f"CustomTkinter Version: {ctk.__version__}")

    print("System gotowy do pracy!")


if __name__ == "__main__":
    main()