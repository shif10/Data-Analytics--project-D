"""Build the two clustering slides from the SUBMITTED report
(Project_D_Final_Report_Team8, Section 5 and Tables 3, 7, 8).

All numbers are copied from that report so the slides match what was
submitted. Speaker notes are included on both slides.

Run from the repository root:  python src/make_clustering_slides.py
"""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Pt

OUT = Path("project-d/ProjectD_clustering_slides.pptx")

NAVY = RGBColor(0x12, 0x34, 0x3B)     # same dark background as the RQ1/RQ2 deck
DARK = RGBColor(18, 52, 59)
TEAL = RGBColor(44, 110, 99)
MINT = RGBColor(156, 201, 191)
ORANGE = RGBColor(209, 96, 61)
CARD = RGBColor(0xEA, 0xF1, 0xEF)
TRACK = RGBColor(0xD7, 0xE4, 0xE0)
TEXT = RGBColor(31, 42, 46)
GREY = RGBColor(92, 107, 112)
WHITE = RGBColor(255, 255, 255)

SLIDE_W, SLIDE_H = 12192000, 6858000
MARGIN = 548640
CONTENT_W = SLIDE_W - 2 * MARGIN


def text(slide, x, y, w, h, lines, size, bold=False, color=TEXT, font="Calibri",
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, space_after=0):
    box = slide.shapes.add_textbox(Emu(x), Emu(y), Emu(w), Emu(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Emu(0)
    lines = lines if isinstance(lines, list) else [lines]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.name = font
        r.font.color.rgb = color
    return box


def rect(slide, x, y, w, h, color, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, Emu(x), Emu(y), Emu(w), Emu(h))
    s.fill.solid()
    s.fill.fore_color.rgb = color
    s.line.fill.background()
    s.shadow.inherit = False
    return s


def header(slide, kicker, title):
    rect(slide, 0, 0, SLIDE_W, 1250000, NAVY)
    rect(slide, 0, 1250000, SLIDE_W, 45000, TEAL)
    text(slide, MARGIN, 190000, CONTENT_W, 280000, kicker, 15, False, MINT)
    text(slide, MARGIN, 480000, CONTENT_W, 650000, title, 34, True, WHITE, "Cambria",
         anchor=MSO_ANCHOR.MIDDLE)


def footer(slide, left):
    text(slide, MARGIN, 6470000, 9500000, 260000, left, 12, False, GREY)
    text(slide, SLIDE_W - MARGIN - 2000000, 6470000, 2000000, 260000,
         "Project D · Team 8", 12, False, GREY, align=PP_ALIGN.RIGHT)


def banner(slide, y, h, message):
    rect(slide, MARGIN, y, CONTENT_W, h, TEAL)
    text(slide, MARGIN + 300000, y, CONTENT_W - 600000, h, message, 22, True, WHITE,
         "Cambria", anchor=MSO_ANCHOR.MIDDLE)


prs = Presentation()
prs.slide_width = Emu(SLIDE_W)
prs.slide_height = Emu(SLIDE_H)
blank = prs.slide_layouts[6]

# ================================================================ slide 1
s1 = prs.slides.add_slide(blank)
header(s1, "Project D · RQ3 · Topic clustering", "How I grouped the papers by topic")

steps = [
    ("STEP 1", "2,972", "papers to group", "Select the papers",
     ["3,668 papers from Scopus-listed journals",
      "3,095 judged likely relevant",
      "123 clinical papers removed by hand"]),
    ("STEP 2", "5", "groups", "Group by words",
     ["Each title and abstract becomes word scores",
      "Papers with similar words are grouped together",
      "Tried 4 to 10 groups; 5 scored highest, but scores differ little"]),
    ("STEP 3", "123 of 125", "checked papers were off-topic", "Check the groups",
     ["The first run (8 groups) had two clinical groups",
      "I read 125 of their papers",
      "I removed the off-topic ones and grouped again"]),
]
card_w, gap = 3400000, 432000
y0, card_h = 1560000, 3850000
for i, (tag, stat, stat_label, head, body) in enumerate(steps):
    x = MARGIN + i * (card_w + gap)
    rect(s1, x, y0, card_w, card_h, CARD)
    rect(s1, x, y0, card_w, 70000, TEAL)
    pad = 250000
    inner = card_w - 2 * pad
    text(s1, x + pad, y0 + 200000, inner, 260000, tag, 13, True, GREY)
    text(s1, x + pad, y0 + 470000, inner, 640000, stat, 40, True, TEAL, "Cambria",
         anchor=MSO_ANCHOR.MIDDLE)
    text(s1, x + pad, y0 + 1120000, inner, 300000, stat_label, 14, False, GREY)
    text(s1, x + pad, y0 + 1520000, inner, 400000, head, 22, True, DARK, "Cambria")
    text(s1, x + pad, y0 + 2000000, inner, card_h - 2100000, body, 16, False, TEXT,
         space_after=6)
    if i < 2:
        arrow = rect(s1, x + card_w + 66000, y0 + card_h // 2 - 150000, 300000, 300000,
                     ORANGE, MSO_SHAPE.RIGHT_ARROW)

banner(s1, 5640000, 720000, "Result: five broad themes in 2,972 papers")
footer(s1, "Source: Project D final report, Section 5. Method: TF-IDF word scores and KMeans.")

s1.notes_slide.notes_text_frame.text = (
    "Goal: find out what topics the papers are about, and whether the topics follow country.\n\n"
    "Step 1: I started from the 3,668 papers in Scopus-listed journals. 3,095 of them were rated "
    "likely relevant by our keyword screen. After a manual review I removed 123 clinical papers, "
    "which left 2,972 papers.\n\n"
    "Step 2: I turned each title and abstract into word scores (TF-IDF) and used KMeans to put "
    "papers with similar words in the same group. I tried 4 to 10 groups. Five groups had the "
    "highest silhouette score, but the scores for all numbers of groups were close "
    "(0.009 to 0.013), so the number of groups is only weakly determined.\n\n"
    "Step 3: The first run used 8 groups and two of them looked clinical. I read 125 papers from "
    "those two groups and 123 were out of scope. I removed them and ran the clustering again, "
    "which gave the five groups. This review was targeted, so 123 of 125 is not an error rate "
    "for the whole dataset."
)

# ================================================================ slide 2
s2 = prs.slides.add_slide(blank)
header(s2, "Project D · RQ3 · Topic clustering", "What I found: five broad, overlapping themes")

themes = [
    (954, "Generative AI in higher education", "Teachers and students using generative AI", TEAL),
    (832, "Foundations, reviews and policy", "Overviews, literature reviews, policy", TEAL),
    (657, "ML and student performance", "Predicting how students perform", TEAL),
    (319, "Health and clinical ML", "Clinical papers that stayed in the data", ORANGE),
    (210, "Intelligent tutoring", "Adaptive learning systems", TEAL),
]
row_h, row_gap, top = 700000, 100000, 1560000
name_w = 3950000
bar_x = MARGIN + name_w + 100000
bar_max = 2650000
for n, name, desc, color in themes:
    y = top
    text(s2, MARGIN, y + 40000, name_w, 340000, name, 17, True, DARK, "Cambria")
    text(s2, MARGIN, y + 395000, name_w, 280000, desc, 13, False, GREY)
    rect(s2, bar_x, y + 110000, bar_max, 480000, TRACK)
    bw = int(bar_max * n / 954)
    rect(s2, bar_x, y + 110000, bw, 480000, color)
    text(s2, bar_x + bar_max + 120000, y + 110000, 800000, 480000, f"{n:,}", 22, True,
         color, "Cambria", anchor=MSO_ANCHOR.MIDDLE)
    top += row_h + row_gap
# (bar track keeps every bar the same length frame so sizes compare at a glance)

cx, cw = 8480000, SLIDE_W - MARGIN - 8480000
rect(s2, cx, 1560000, cw, 1900000, CARD)
rect(s2, cx, 1560000, 70000, 1900000, ORANGE)
text(s2, cx + 250000, 1680000, cw - 400000, 400000, "Not tied to country", 22, True,
     ORANGE, "Cambria")
text(s2, cx + 250000, 2130000, cw - 400000, 1300000,
     ["Topics barely follow country or community (NMI 0.03).",
      "Collaboration communities do follow country (NMI 0.47)."],
     15, False, TEXT, space_after=5)

rect(s2, cx, 3620000, cw, 1900000, CARD)
rect(s2, cx, 3620000, 70000, 1900000, TEAL)
text(s2, cx + 250000, 3740000, cw - 400000, 400000, "Weak separation", 22, True,
     TEAL, "Cambria")
text(s2, cx + 250000, 4190000, cw - 400000, 1300000,
     ["Silhouette is 0.013, barely above zero.",
      "The themes overlap, so read them as a rough map."],
     15, False, TEXT, space_after=5)

banner(s2, 5640000, 720000, "Topics are shared across the field, not owned by one country")
footer(s2, "NMI = how much two groupings agree (0 = none, 1 = identical). "
           "Source: Project D final report, Section 5.")

s2.notes_slide.notes_text_frame.text = (
    "These are the five themes, with the number of papers in each (2,972 in total). The labels are "
    "my reading of the top words and example titles, not validated categories.\n\n"
    "Generative AI in higher education is the largest group (954). Foundations, reviews and policy "
    "has 832. Machine learning and student performance has 657. Intelligent tutoring is the "
    "smallest (210).\n\n"
    "The orange group, health and clinical ML (319 papers), is a known weakness. Even after the "
    "manual review these papers still read as clinical, so some false positives remain, and "
    "probably in other groups too.\n\n"
    "Two checks on the right. First, topics barely follow country or collaboration community: "
    "the NMI is 0.03, and about 0.01 is what shuffled labels give. The collaboration communities "
    "themselves follow country much more strongly (NMI 0.47). Second, the silhouette is 0.013, "
    "barely above zero, so the themes overlap a lot and are best read as a rough map.\n\n"
    "Answer to RQ3: the field is connected, with several largely national collaboration "
    "communities, and the topics cut across those communities."
)

OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(OUT)
print("Saved", OUT)

