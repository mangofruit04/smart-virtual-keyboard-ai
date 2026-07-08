import cv2
import numpy as np
from cvzone.HandTrackingModule import HandDetector
import time

# ---------------- Camera Setup ----------------
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

# ---------------- Hand Detector ----------------
detector = HandDetector(detectionCon=0.8, maxHands=2)

# ---------------- Common Words Dictionary ----------------
WORD_SUGGESTIONS = {
    'h': ['hello', 'help', 'how', 'have', 'here'],
    'he': ['hello', 'help', 'here', 'heaven', 'heart'],
    'hel': ['hello', 'help', 'helmet'],
    'hell': ['hello'],
    'w': ['what', 'when', 'where', 'why', 'welcome'],
    'wh': ['what', 'when', 'where', 'why', 'which'],
    'wha': ['what', 'whale'],
    't': ['the', 'this', 'that', 'there', 'thank'],
    'th': ['the', 'this', 'that', 'there', 'thank'],
    'tha': ['that', 'thank', 'thanks'],
    'i': ['i', 'is', 'it', 'if', 'in'],
    'a': ['and', 'are', 'about', 'all', 'as'],
    'an': ['and', 'any', 'answer'],
    'y': ['you', 'your', 'yes', 'yet'],
    'yo': ['you', 'your', 'young'],
    'you': ['you', 'your', 'yourself'],
    'p': ['please', 'python', 'project'],
    'pl': ['please', 'play', 'plan'],
    'ple': ['please'],
    'c': ['can', 'code', 'create', 'computer'],
    'co': ['code', 'computer', 'cool', 'could'],
    'g': ['good', 'great', 'get', 'give'],
    'go': ['good', 'going', 'got'],
    'goo': ['good'],
    'n': ['not', 'now', 'new', 'need'],
    'l': ['like', 'love', 'look', 'let'],
    's': ['see', 'say', 'she', 'some'],
    'f': ['for', 'from', 'find', 'feel'],
    'b': ['be', 'but', 'by', 'because'],
    'm': ['me', 'my', 'make', 'more'],
}

# ---------------- Keyboard Layout ----------------
keys = [
    ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
    ["A", "S", "D", "F", "G", "H", "J", "K", "L", "DEL"],
    ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"],
    ["Space", "Clear"]
]


# ---------------- Button Class ----------------
class Button:
    def __init__(self, pos, text, size=[85, 85]):
        self.pos = pos
        self.size = size
        self.text = text
        self.baseColor = (60, 60, 60)
        self.hoverColor = (100, 200, 255)
        self.clickColor = (50, 255, 150)
        self.color = self.baseColor
        self.shadowOffset = 5
        self.cooldown = 0

    def draw(self, img):
        x, y = self.pos
        w, h = self.size

        # Shadow effect
        shadow_color = (20, 20, 20)
        cv2.rectangle(img, (x + self.shadowOffset, y + self.shadowOffset),
                      (x + w + self.shadowOffset, y + h + self.shadowOffset),
                      shadow_color, cv2.FILLED)

        # Main button with gradient effect
        overlay = img.copy()

        cv2.rectangle(overlay, (x, y), (x + w, y + h), self.color, cv2.FILLED)

        gradient_color = tuple(min(c + 30, 255) for c in self.color)
        pts = np.array([[x, y], [x + w, y], [x + w // 2, y + h // 2]])
        cv2.fillPoly(overlay, [pts], gradient_color)

        cv2.addWeighted(overlay, 0.3, img, 0.7, 0, img)

        border_color = (100, 100, 100) if self.color == self.baseColor else self.color
        cv2.rectangle(img, (x, y), (x + w, y + h), border_color, 2)

        # Draw text or icon
        if self.text == "DEL":
            self.drawDustbin(img, x, y, w, h)
        elif self.text == "Clear":
            cv2.putText(img, "CLR", (x + 10, y + 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 100, 100), 3)
        elif self.text == "Space":
            cv2.putText(img, "SPACE", (x + w // 2 - 80, y + 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        else:
            text_size = cv2.getTextSize(self.text, cv2.FONT_HERSHEY_SIMPLEX, 2, 4)[0]
            text_x = x + (w - text_size[0]) // 2
            text_y = y + (h + text_size[1]) // 2

            cv2.putText(img, self.text, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4)

    def drawDustbin(self, img, x, y, w, h):
        binColor = (255, 100, 100)
        cv2.rectangle(img, (x + 30, y + 30), (x + w - 30, y + h - 15), binColor, 3)
        cv2.rectangle(img, (x + 25, y + 20), (x + w - 25, y + 30), binColor, cv2.FILLED)
        cv2.ellipse(img, (x + w // 2, y + 15), (10, 8), 0, 0, 180, binColor, 3)
        for i in range(3):
            lx = x + 40 + i * 15
            cv2.line(img, (lx, y + 35), (lx, y + h - 20), binColor, 2)

    def isOver(self, x, y):
        bx, by = self.pos
        bw, bh = self.size
        return bx < x < bx + bw and by < y < by + bh


# ---------------- Suggestion Box Class ----------------
class SuggestionBox:
    def __init__(self, pos, text, index):
        self.pos = pos
        self.text = text
        self.index = index
        self.size = [180, 50]
        self.baseColor = (80, 80, 80)
        self.hoverColor = (120, 180, 255)
        self.color = self.baseColor
        self.cooldown = 0

    def draw(self, img):
        x, y = self.pos
        w, h = self.size

        cv2.rectangle(img, (x + 3, y + 3), (x + w + 3, y + h + 3), (20, 20, 20), cv2.FILLED)
        cv2.rectangle(img, (x, y), (x + w, y + h), self.color, cv2.FILLED)
        cv2.rectangle(img, (x, y), (x + w, y + h), (150, 150, 150), 2)

        cv2.circle(img, (x + 25, y + 25), 15, (50, 150, 255), cv2.FILLED)
        cv2.putText(img, str(self.index + 1), (x + 19, y + 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.putText(img, self.text, (x + 50, y + 33),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    def isOver(self, x, y):
        bx, by = self.pos
        bw, bh = self.size
        return bx < x < bx + bw and by < y < by + bh


# ---------------- Get Suggestions Function ----------------
def get_suggestions(text):
    if not text:
        return []

    words = text.lower().split()
    if not words:
        return []

    current_word = words[-1]
    suggestions = WORD_SUGGESTIONS.get(current_word, [])
    suggestions = [s for s in suggestions if s != current_word]

    return suggestions[:5]


# ---------------- Distance Calculator ----------------
def calculate_distance(p1, p2):
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


# ---------------- Create Buttons ----------------
buttonList = []
for i, row in enumerate(keys):
    for j, key in enumerate(row):
        if key == "Space":
            buttonList.append(Button([100, 400], key, size=[500, 85]))
        elif key == "Clear":
            buttonList.append(Button([620, 400], key, size=[180, 85]))
        else:
            buttonList.append(Button([100 * j + 50, 100 * i + 50], key))

# ---------------- Typing Variables ----------------
finalText = ""
clickCooldown = 0
COOLDOWN_TIME = 15  # frames
suggestions = []
suggestionBoxes = []
lastHoveredButton = None
hoverFrameCount = 0
HOVER_THRESHOLD = 8  # frames to confirm hover

# ---------------- FPS Counter ----------------
prev_frame_time = 0

# ---------------- Main Loop ----------------
while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)

    # Dark background with grid
    background = np.zeros_like(img)
    background[:] = (25, 25, 35)

    for i in range(0, img.shape[1], 40):
        cv2.line(background, (i, 0), (i, img.shape[0]), (30, 30, 40), 1)
    for i in range(0, img.shape[0], 40):
        cv2.line(background, (0, i), (img.shape[1], i), (30, 30, 40), 1)

    img = cv2.addWeighted(img, 0.3, background, 0.7, 0)

    hands, img = detector.findHands(img, draw=True, flipType=True)

    hoveredButton = None
    hoveredSuggestion = None
    x, y = 0, 0
    isPinching = False

    if hands:
        hand = hands[0]
        lmList = hand["lmList"]
        x, y = lmList[8][:2]  # Index fingertip
        thumb_tip = lmList[4][:2]  # Thumb tip

        # Calculate pinch distance
        pinch_distance = calculate_distance((x, y), thumb_tip)
        isPinching = pinch_distance < 40  # Pinch detected

        # Draw finger pointer
        if isPinching:
            cv2.circle(img, (x, y), 18, (0, 255, 0), 4)
            cv2.circle(img, (x, y), 10, (50, 255, 50), cv2.FILLED)
            cv2.line(img, (x, y), thumb_tip, (0, 255, 0), 3)
        else:
            cv2.circle(img, (x, y), 15, (0, 255, 255), 3)
            cv2.circle(img, (x, y), 8, (255, 255, 0), cv2.FILLED)

    # ---------------- Cooldown Management ----------------
    if clickCooldown > 0:
        clickCooldown -= 1

    # ---------------- Draw buttons with hover detection ----------------
    for button in buttonList:
        if hands and button.isOver(x, y):
            button.color = button.hoverColor
            hoveredButton = button
        else:
            button.color = button.baseColor

        button.draw(img)

    # ---------------- Hover Confirmation ----------------
    if hoveredButton == lastHoveredButton and hoveredButton is not None:
        hoverFrameCount += 1
    else:
        hoverFrameCount = 0

    lastHoveredButton = hoveredButton

    # ---------------- Pinch to Type ----------------
    if isPinching and clickCooldown == 0 and hoverFrameCount >= HOVER_THRESHOLD:
        if hoveredButton:
            hoveredButton.color = hoveredButton.clickColor

            if hoveredButton.text == "Space":
                finalText += " "
            elif hoveredButton.text == "DEL":
                finalText = finalText[:-1]
            elif hoveredButton.text == "Clear":
                finalText = ""
            else:
                finalText += hoveredButton.text.lower()

            clickCooldown = COOLDOWN_TIME
            hoverFrameCount = 0

    # ---------------- Update Suggestions ----------------
    suggestions = get_suggestions(finalText)
    suggestionBoxes = []

    if suggestions:
        for i, suggestion in enumerate(suggestions):
            box = SuggestionBox([50 + i * 200, 520], suggestion, i)
            suggestionBoxes.append(box)

            if hands and box.isOver(x, y):
                box.color = box.hoverColor
                hoveredSuggestion = box

            box.draw(img)

    # ---------------- Pinch on Suggestion ----------------
    if isPinching and clickCooldown == 0 and hoveredSuggestion:
        words = finalText.split()
        if words:
            words[-1] = hoveredSuggestion.text
            finalText = ' '.join(words) + ' '
        else:
            finalText = hoveredSuggestion.text + ' '

        clickCooldown = COOLDOWN_TIME

    # ---------------- Typing Display Box ----------------
    typing_box_y = 600
    cv2.rectangle(img, (50, typing_box_y), (1200, typing_box_y + 100), (40, 40, 50), cv2.FILLED)
    cv2.rectangle(img, (50, typing_box_y), (1200, typing_box_y + 100), (100, 100, 120), 3)

    cv2.putText(img, "Your Text:", (60, typing_box_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 200, 255), 2)

    maxChars = 50
    display_text = finalText if len(finalText) <= 100 else "..." + finalText[-97:]
    lines = [display_text[i:i + maxChars] for i in range(0, len(display_text), maxChars)]

    for i, line in enumerate(lines[:2]):
        cv2.putText(img, line, (60, typing_box_y + 35 + i * 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # ---------------- FPS Display ----------------
    new_frame_time = time.time()
    fps = 1 / (new_frame_time - prev_frame_time) if prev_frame_time != 0 else 0
    prev_frame_time = new_frame_time

    cv2.putText(img, f"FPS: {int(fps)}", (1100, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # ---------------- Instructions ----------------
    instruction_text = "PINCH (thumb + index) to type!"
    if isPinching:
        instruction_text = "PINCHING - Hold steady!"

    cv2.putText(img, instruction_text, (380, 500),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 200, 100), 2)

    # ---------------- Hover Progress Bar ----------------
    if hoveredButton and hoverFrameCount > 0:
        progress = min(hoverFrameCount / HOVER_THRESHOLD, 1.0)
        bar_width = int(200 * progress)
        cv2.rectangle(img, (540, 485), (540 + bar_width, 495), (100, 255, 100), cv2.FILLED)
        cv2.rectangle(img, (540, 485), (740, 495), (100, 100, 100), 2)

    # ---------------- Title ----------------
    cv2.putText(img, "SMART VIRTUAL KEYBOARD", (350, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (100, 200, 255), 3)

    cv2.imshow("Smart Virtual Keyboard", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()