import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

def make_omr(filename, answers, name="Student", roll="001", num_q=30, opts=4):
    W, H = 794, 1123
    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)

    draw.rectangle([30, 30, W-30, 130], outline="black", width=2)
    draw.text((W//2, 50), "JEE MAIN — ANSWER SHEET", fill="black", anchor="mt")
    draw.text((60, 80), f"Name: {name}", fill="black")
    draw.text((60, 105), f"Roll No: {roll}    Subject: Physics", fill="black")
    draw.text((W-200, 80), "Section A (30 Questions)", fill="black")

    draw.rectangle([30, 140, W-30, 175], fill="#f0f0f0", outline="#aaa")
    draw.text((W//2, 157), "Fill the bubble completely.", fill="#333", anchor="mm")

    OPTION_LABELS = ["A","B","C","D"][:opts]
    COLS = 2
    Q_PER_COL = num_q // COLS
    COL_W = (W - 80) // COLS

    START_Y = 195
    ROW_H = 27
    BUBBLE_R = 9

    for qi in range(num_q):
        col = qi // Q_PER_COL
        row = qi % Q_PER_COL
        x0 = 40 + col * COL_W
        y0 = START_Y + row * ROW_H

        qnum = qi + 1
        ans = answers.get(f"Q{qnum}", None)

        draw.text((x0, y0 + 13), f"Q{qnum:02d}.", fill="black", anchor="lm")

        for oi, opt in enumerate(OPTION_LABELS):
            cx = x0 + 55 + oi * 38
            cy = y0 + 13

            if ans == opt:
                draw.ellipse([cx-BUBBLE_R, cy-BUBBLE_R, cx+BUBBLE_R, cy+BUBBLE_R],
                             fill="black", outline="black")
                draw.text((cx, cy), opt, fill="white", anchor="mm")
            else:
                draw.ellipse([cx-BUBBLE_R, cy-BUBBLE_R, cx+BUBBLE_R, cy+BUBBLE_R],
                             fill="white", outline="#333", width=1)
                draw.text((cx, cy), opt, fill="#555", anchor="mm")

    img.save(filename)
    print(f"Saved: {filename}")

arpit_answers = {
    "Q1":"A","Q2":"C","Q3":"B","Q4":"D","Q5":"A"
}

rahul_answers = {
    "Q1":"A","Q2":"B","Q3":"B","Q4":"D","Q5":"C"
}

out = "static/sample_files/omr"

make_omr(f"{out}/jee_omr_arpit.png", arpit_answers, "Arpit Sharma", "2024001")
make_omr(f"{out}/jee_omr_rahul.png", rahul_answers, "Rahul Verma", "2024002")

print("All OMR files generated!")