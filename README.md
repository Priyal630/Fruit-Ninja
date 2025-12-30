🥷 Fruit Ninja – Hand Gesture Game (Python)

A real-time **Fruit Ninja style game** built using **Python**, where fruits are sliced using **index finger hand gestures** captured through a webcam.
No mouse, no touch screen — just natural hand movement.

This project focuses on **computer vision, gesture control, and real-time game mechanics**.

---

## ✨ Features

* 🎥 **Webcam-based hand tracking** (Index finger slicing)
* ⚡ **Low-latency pointer** with smooth motion
* 🍎 **Fruits fall from the top** (1–2 at a time)
* 💥 **Bombs** that end the game instantly
* ❄️ **Freeze power-up** (slows everything temporarily)
* ✖️ **Double score power-up**
* ❤️ **Lives system**
* 📈 **High score saved locally**
* 🎮 **Difficulty modes** (Easy / Medium / Hard)
* ⏸️ **Gesture-controlled Pause / Resume**
* 🔊 **Sound effects** for slicing, bombs, and game over
* 🧼 **Clean UI** (no webcam feed shown)

---

## 🖐️ Gesture Controls

| Gesture               | Action         |
| --------------------- | -------------- |
| Index finger movement | Slice fruits   |
| Fist (hold)           | Pause game     |
| Two fingers (hold)    | Resume game    |
| OK sign (hold)        | Return to Menu |

> Gestures are **debounced** to avoid accidental triggers.

---

## 🛠️ Tech Stack

* **Python 3.11**
* **OpenCV**
* **MediaPipe**
* **cvzone**
* **pygame**
* **NumPy**

---

## 📁 Project Structure

```
Fruit-Ninja-Hand-Gesture/
│
├── assets/
│   ├── images/
│   │   ├── apple.png
│   │   ├── banana.png
│   │   ├── watermelon.png
│   │   ├── bomb.png
│   │   ├── freeze.png
│   │   └── double.png
│   │
│   └── sounds/
│       ├── slice.wav
│       ├── bomb.wav
│       ├── miss.wav
│       ├── start.wav
│       └── gameover.wav
│
├── fruit_ninja.py
├── highscore.txt
└── README.md
```

---

## 🚀 How to Run

### 1️⃣ Install Dependencies

```bash
python -m pip install opencv-python mediapipe cvzone pygame numpy
```

### 2️⃣ Run the Game

```bash
python fruit_ninja.py
```

> Make sure your webcam is connected and not used by another app.

---

## 🏆 High Score

* Stored in **highscore.txt**
* Just contains a single number, for example:

```
15
```

---

## 🎯 Learning Outcomes

* Real-time hand gesture tracking
* Coordinate mapping between camera and game window
* Game physics (gravity, collision detection)
* Performance optimization for smooth gameplay
* Gesture debouncing and state management
* Building a complete interactive game system

---

## 💡 Future Improvements

* Fruit slicing animation (two halves + juice splash)
* Combo scoring system
* Background themes
* Multiplayer mode
* Mobile version using camera sensors

---

## 🙌 Credits

* Inspired by **Fruit Ninja**
* Hand tracking powered by **MediaPipe**
* Game engine built using **pygame**

---

## 👩‍💻 Author

**Priyal Sharma**
B.Tech (AI & ML)
UPES Dehradun
