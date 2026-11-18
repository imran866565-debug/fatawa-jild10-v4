#!/usr/bin/env python3
"""Merge Fatawa Razviya Jild 10 easy-Urdu tashreeh v4 chunks into jild-10.json.

Reads the 18 chunk files listed in chunks-manifest-v4-jild10.json,
concatenates them in order 01 -> 18, derives start_page = min(pages)
where the field is absent, normalises page markers, validates, and
writes {"masail": [...]} to jild-10.json.

ORDER -- chunk order is the order (no quirk, unlike Jild 1 Part 2):
  The v3 merged file ~/workspace/fatawa-app/content/tashreeh/jild-10.json
  has ID order == concatenation order of the v4 chunks 01..18 (verified
  locally by the coordinator: all 278 ids match the v3 sequence exactly).
  Do NOT sort or reorder. Within each chunk, items keep file order.

NO RENAME QUIRK in Jild 10: the v3 merged file has 278 UNIQUE ids — the
  book numbers no masala twice in this jild (unlike Jild 5, which had
  two masail 263 and two masail 304, and Jild 6, which had two masail
  774). Chunk ids are used exactly as written; the merge asserts
  duplicate-free ids instead of renaming anything.
  NOTE: v3 has split files 02a/02b, 05a/05b, 10a/10b — each pair was
  combined into ONE leaf chunk by the workers (leaf 02 = 02a + 02b,
  leaf 05 = 05a + 05b, leaf 10 = 10a + 10b). Leaf 05 DEDUP: masala-87
  appears in BOTH 05a (p.245) and 05b (p.246); the merged v3 has it
  ONCE with pages [245, 246], sp 245 — the v4 leaf chunk writes it
  ONCE with pages [245, 246] and all 3 v3 notes + 1 added merge note.
  Those are v3 ids, kept exactly — they are NOT merge renames.
  Likewise the combined-range ids jild10-masala-8-11 (leaf 01),
  jild10-masala-91-102, jild10-masala-109-110, jild10-masala-117-118
  (leaf 05) and the single-item leaf 13 (masala-262, 49 pages) are
  v3 ids, kept exactly.

START_PAGE: every one of the 18 v4 chunks carries start_page ==
  min(pages) for all its items (verified by the coordinator). The
  derivation code below stays as a safety net; it is expected to
  derive 0 items.

MARKER NORMALISATION (the only text transformation): page markers, if
  present, are normalised to the single form [safha N] written with the
  Urdu word for page:
  - lenticular-bracket form (U+3010/U+3011 around the Urdu word for
    page + number) -> [safha N]
  - [short form] -> [safha N]
  - [safha N] stays as-is
  Applied to every string field of every item (jawab, sawal, title,
  notes). The 18 v4 chunks contain ZERO markers of any form (verified
  locally), so normalisation is expected to be a no-op here; the code
  stays so the merge is robust and the "none remain" assertions still
  run. No other text is touched and no markers are invented.
  NOTE: the literal lenticular-bracket characters are written here only
  as U+3010/U+3011 escapes, never as literal characters in this file.

VALIDATION (fails loudly on any violation):
  278 items; ID sequence EXACTLY == the v3 merged file's ID sequence
  (embedded below as V3_IDS, copied verbatim from
  ~/workspace/fatawa-app/content/tashreeh/jild-10.json); pages per item
  identical to v3 (embedded as V3_PAGES, same source, verified against
  the v3 file before pushing); 756 unique pages (min 9, max 835);
  volume_ids == {50}; start_page == min(pages) for every item (after
  derivation); zero empty tashreeh_jawab; no lenticular / short markers
  remain; first id jild10-p9, last id jild10-p829.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = "chunks-manifest-v4-jild10.json"

# Concatenation order: chunk files 01 -> 18, in order.
CHUNK_ORDER = [f"jild-10-chunk-{n:02d}.json" for n in range(1, 19)]

EXPECTED_ITEMS = 278
EXPECTED_PAGES = 756
EXPECTED_MIN_PAGE = 9
EXPECTED_MAX_PAGE = 835
EXPECTED_VOLUME_IDS = {50}
EXPECTED_FIRST_ID = "jild10-p9"
EXPECTED_LAST_ID = "jild10-p829"

# v3 ID sequence, verbatim from content/tashreeh/jild-10.json.
V3_IDS = ['jild10-p9', 'jild10-masala-1', 'jild10-masala-2', 'jild10-masala-3', 'jild10-masala-4', 'jild10-masala-5', 'jild10-masala-6', 'jild10-masala-7', 'jild10-masala-8-11', 'jild10-masala-12', 'jild10-masala-13', 'jild10-masala-14', 'jild10-masala-15', 'jild10-p104', 'jild10-p113', 'jild10-p117', 'jild10-p129', 'jild10-p130', 'jild10-masala-18', 'jild10-masala-19', 'jild10-masala-20', 'jild10-masala-21', 'jild10-masala-22', 'jild10-masala-23', 'jild10-masala-24', 'jild10-masala-25', 'jild10-masala-26-27', 'jild10-masala-28-31', 'jild10-masala-32', 'jild10-masala-33', 'jild10-masala-34', 'jild10-masala-35', 'jild10-masala-36-37', 'jild10-masala-38', 'jild10-masala-39', 'jild10-masala-40', 'jild10-masala-41-43', 'jild10-masala-44', 'jild10-masala-45-47', 'jild10-masala-48', 'jild10-masala-49', 'jild10-masala-50', 'jild10-masala-51', 'jild10-masala-52-54', 'jild10-masala-55', 'jild10-masala-56', 'jild10-masala-57', 'jild10-masala-58', 'jild10-masala-59', 'jild10-masala-60-62', 'jild10-masala-63-64', 'jild10-masala-65', 'jild10-masala-66', 'jild10-masala-67', 'jild10-masala-68', 'jild10-masala-69', 'jild10-masala-71', 'jild10-masala-72', 'jild10-masala-73', 'jild10-masala-74', 'jild10-masala-75-77', 'jild10-masala-78', 'jild10-masala-79', 'jild10-masala-80', 'jild10-masala-81-82', 'jild10-masala-83', 'jild10-masala-84', 'jild10-masala-85', 'jild10-masala-86', 'jild10-masala-87', 'jild10-masala-88', 'jild10-masala-89', 'jild10-masala-90', 'jild10-masala-91-102', 'jild10-masala-103', 'jild10-masala-104', 'jild10-masala-105', 'jild10-masala-106', 'jild10-masala-107', 'jild10-masala-108', 'jild10-masala-109-110', 'jild10-masala-111', 'jild10-masala-112', 'jild10-masala-113', 'jild10-masala-114', 'jild10-masala-115', 'jild10-masala-116', 'jild10-masala-117-118', 'jild10-masala-119', 'jild10-masala-120', 'jild10-masala-121', 'jild10-masala-122', 'jild10-masala-123', 'jild10-masala-124', 'jild10-masala-125', 'jild10-masala-126', 'jild10-masala-127', 'jild10-masala-128', 'jild10-masala-129', 'jild10-masala-130', 'jild10-masala-131', 'jild10-masala-132', 'jild10-masala-133', 'jild10-masala-134-135', 'jild10-masala-136', 'jild10-masala-137', 'jild10-masala-138', 'jild10-masala-139', 'jild10-masala-140', 'jild10-masala-142-143', 'jild10-masala-144', 'jild10-masala-145', 'jild10-masala-146', 'jild10-masala-147-149', 'jild10-masala-150', 'jild10-masala-151', 'jild10-masala-152', 'jild10-masala-153', 'jild10-masala-154', 'jild10-masala-155', 'jild10-masala-156', 'jild10-masala-157', 'jild10-masala-158', 'jild10-masala-159', 'jild10-masala-160', 'jild10-masala-161', 'jild10-masala-162', 'jild10-masala-163', 'jild10-masala-164', 'jild10-masala-165', 'jild10-masala-166', 'jild10-masala-167', 'jild10-masala-168', 'jild10-masala-169', 'jild10-masala-170', 'jild10-masala-171', 'jild10-masala-172', 'jild10-masala-173', 'jild10-masala-174', 'jild10-masala-175', 'jild10-masala-176', 'jild10-masala-179', 'jild10-masala-180', 'jild10-masala-181', 'jild10-masala-182', 'jild10-masala-185', 'jild10-masala-194', 'jild10-masala-195', 'jild10-masala-196', 'jild10-masala-197', 'jild10-masala-198', 'jild10-masala-199', 'jild10-masala-201', 'jild10-masala-202', 'jild10-masala-203', 'jild10-p431', 'jild10-masala-204', 'jild10-masala-205', 'jild10-masala-206', 'jild10-masala-207', 'jild10-masala-208', 'jild10-masala-209', 'jild10-masala-213', 'jild10-masala-214', 'jild10-masala-215', 'jild10-masala-216', 'jild10-p466', 'jild10-masala-217', 'jild10-masala-220', 'jild10-masala-222', 'jild10-masala-223', 'jild10-masala-224', 'jild10-masala-225', 'jild10-masala-226', 'jild10-masala-227', 'jild10-masala-228', 'jild10-masala-229', 'jild10-masala-230', 'jild10-masala-231', 'jild10-masala-232', 'jild10-masala-233', 'jild10-masala-234', 'jild10-masala-235', 'jild10-masala-236', 'jild10-masala-248', 'jild10-masala-249', 'jild10-masala-250', 'jild10-masala-251', 'jild10-masala-252', 'jild10-masala-253', 'jild10-masala-255', 'jild10-masala-256', 'jild10-masala-257', 'jild10-masala-258', 'jild10-masala-261', 'jild10-masala-262', 'jild10-masala-263', 'jild10-masala-264', 'jild10-masala-265', 'jild10-masala-266', 'jild10-masala-267', 'jild10-masala-268', 'jild10-masala-269', 'jild10-masala-271', 'jild10-masala-272', 'jild10-masala-273', 'jild10-masala-274', 'jild10-masala-275', 'jild10-masala-276', 'jild10-masala-277', 'jild10-masala-278', 'jild10-masala-281', 'jild10-masala-282', 'jild10-masala-283', 'jild10-masala-284', 'jild10-masala-285', 'jild10-masala-289', 'jild10-masala-290', 'jild10-masala-292', 'jild10-masala-293', 'jild10-masala-294', 'jild10-masala-296', 'jild10-masala-297', 'jild10-masala-299', 'jild10-masala-300', 'jild10-masala-301', 'jild10-masala-302', 'jild10-masala-303', 'jild10-masala-304', 'jild10-masala-305', 'jild10-masala-306', 'jild10-masala-308', 'jild10-masala-309', 'jild10-masala-310', 'jild10-masala-311', 'jild10-masala-312', 'jild10-masala-313', 'jild10-masala-315', 'jild10-masala-316', 'jild10-p731', 'jild10-p732', 'jild10-p735', 'jild10-p737', 'jild10-p738', 'jild10-p740', 'jild10-p741', 'jild10-p743', 'jild10-p745', 'jild10-p747', 'jild10-p749', 'jild10-p750', 'jild10-p751', 'jild10-p753', 'jild10-p756', 'jild10-p759', 'jild10-p760', 'jild10-p761', 'jild10-p762', 'jild10-p763', 'jild10-p765', 'jild10-p766', 'jild10-p768', 'jild10-p769', 'jild10-p770', 'jild10-p771', 'jild10-p774', 'jild10-p776', 'jild10-p781', 'jild10-p784', 'jild10-p788', 'jild10-p792', 'jild10-p795', 'jild10-p795-wajibat', 'jild10-p798', 'jild10-p803', 'jild10-p804', 'jild10-p818', 'jild10-p829']

# v3 pages per item id, verbatim from content/tashreeh/jild-10.json.
V3_PAGES = {
"jild10-p9": [9, 10, 11, 12],
"jild10-masala-1": [67, 68, 69],
"jild10-masala-2": [69, 70, 71, 72, 73],
"jild10-masala-3": [73, 74],
"jild10-masala-4": [74, 75],
"jild10-masala-5": [76],
"jild10-masala-6": [76],
"jild10-masala-7": [77],
"jild10-masala-8-11": [77, 78],
"jild10-masala-12": [79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89],
"jild10-masala-13": [89, 90, 91, 92],
"jild10-masala-14": [92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102],
"jild10-masala-15": [103],
"jild10-p104": [104, 105, 106, 107, 108, 109, 110, 111, 112, 113],
"jild10-p113": [113, 114, 115, 116, 117],
"jild10-p117": [117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128],
"jild10-p129": [129, 130],
"jild10-p130": [130, 131, 132],
"jild10-masala-18": [132, 133],
"jild10-masala-19": [133, 134],
"jild10-masala-20": [134, 135, 136],
"jild10-masala-21": [136, 137],
"jild10-masala-22": [137],
"jild10-masala-23": [137, 138],
"jild10-masala-24": [138],
"jild10-masala-25": [138, 139, 140],
"jild10-masala-26-27": [140, 141, 142, 143],
"jild10-masala-28-31": [143],
"jild10-masala-32": [143, 144],
"jild10-masala-33": [144],
"jild10-masala-34": [144],
"jild10-masala-35": [145],
"jild10-masala-36-37": [145, 146, 147],
"jild10-masala-38": [147, 148],
"jild10-masala-39": [147, 148],
"jild10-masala-40": [148],
"jild10-masala-41-43": [148, 149],
"jild10-masala-44": [149],
"jild10-masala-45-47": [149, 150, 151, 152],
"jild10-masala-48": [152, 153, 154, 155, 156, 157],
"jild10-masala-49": [157, 158],
"jild10-masala-50": [158, 159],
"jild10-masala-51": [159],
"jild10-masala-52-54": [159, 160],
"jild10-masala-55": [160, 161],
"jild10-masala-56": [161, 162],
"jild10-masala-57": [162],
"jild10-masala-58": [162],
"jild10-masala-59": [162, 163],
"jild10-masala-60-62": [163, 164],
"jild10-masala-63-64": [164, 165],
"jild10-masala-65": [165],
"jild10-masala-66": [166, 167, 168, 169, 170],
"jild10-masala-67": [170, 171],
"jild10-masala-68": [171],
"jild10-masala-69": [171, 172, 173],
"jild10-masala-71": [173],
"jild10-masala-72": [175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187],
"jild10-masala-73": [187],
"jild10-masala-74": [188, 189],
"jild10-masala-75-77": [189, 190],
"jild10-masala-78": [190],
"jild10-masala-79": [191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206],
"jild10-masala-80": [206, 207],
"jild10-masala-81-82": [207],
"jild10-masala-83": [207],
"jild10-masala-84": [207, 208],
"jild10-masala-85": [208, 209, 210, 211, 212, 213, 214, 215, 216],
"jild10-masala-86": [217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245],
"jild10-masala-87": [245, 246],
"jild10-masala-88": [246, 247, 248, 249, 250],
"jild10-masala-89": [250, 251, 252, 253, 254],
"jild10-masala-90": [254, 255],
"jild10-masala-91-102": [255, 256],
"jild10-masala-103": [256, 257],
"jild10-masala-104": [257],
"jild10-masala-105": [257],
"jild10-masala-106": [257, 258],
"jild10-masala-107": [258, 259],
"jild10-masala-108": [259],
"jild10-masala-109-110": [259, 260, 261, 262],
"jild10-masala-111": [262, 263],
"jild10-masala-112": [264, 265],
"jild10-masala-113": [265],
"jild10-masala-114": [265],
"jild10-masala-115": [265, 266],
"jild10-masala-116": [266],
"jild10-masala-117-118": [266, 267],
"jild10-masala-119": [267, 268],
"jild10-masala-120": [268],
"jild10-masala-121": [269, 270],
"jild10-masala-122": [270],
"jild10-masala-123": [270, 271],
"jild10-masala-124": [270, 271],
"jild10-masala-125": [271],
"jild10-masala-126": [271, 272],
"jild10-masala-127": [272, 273, 274],
"jild10-masala-128": [275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290],
"jild10-masala-129": [290, 291, 292, 293, 294],
"jild10-masala-130": [294],
"jild10-masala-131": [294],
"jild10-masala-132": [294, 295],
"jild10-masala-133": [295],
"jild10-masala-134-135": [295, 296],
"jild10-masala-136": [296, 297],
"jild10-masala-137": [297, 298],
"jild10-masala-138": [298, 299],
"jild10-masala-139": [299],
"jild10-masala-140": [299],
"jild10-masala-142-143": [299, 300],
"jild10-masala-144": [300],
"jild10-masala-145": [300, 301],
"jild10-masala-146": [301, 302, 303, 304, 305],
"jild10-masala-147-149": [305, 306],
"jild10-masala-150": [306],
"jild10-masala-151": [306, 307, 308],
"jild10-masala-152": [308],
"jild10-masala-153": [309, 310],
"jild10-masala-154": [310, 311, 312],
"jild10-masala-155": [312, 313, 314, 315],
"jild10-masala-156": [315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331],
"jild10-masala-157": [331],
"jild10-masala-158": [331, 332],
"jild10-masala-159": [332, 333, 334],
"jild10-masala-160": [335],
"jild10-masala-161": [335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348],
"jild10-masala-162": [348, 349, 350, 351],
"jild10-masala-163": [351],
"jild10-masala-164": [351, 352, 353],
"jild10-masala-165": [353, 354],
"jild10-masala-166": [354, 355],
"jild10-masala-167": [355],
"jild10-masala-168": [355],
"jild10-masala-169": [355, 356],
"jild10-masala-170": [356, 357, 358, 359, 360, 361, 362],
"jild10-masala-171": [363, 364, 365, 366, 367, 368, 369, 370, 371],
"jild10-masala-172": [371, 372],
"jild10-masala-173": [372, 373],
"jild10-masala-174": [373, 374, 375],
"jild10-masala-175": [375],
"jild10-masala-176": [376, 377],
"jild10-masala-179": [377, 378],
"jild10-masala-180": [378, 379],
"jild10-masala-181": [379, 380],
"jild10-masala-182": [380, 381, 382],
"jild10-masala-185": [382, 383, 384, 385, 386],
"jild10-masala-194": [386, 387],
"jild10-masala-195": [387, 388, 389, 390, 391, 392],
"jild10-masala-196": [392, 393],
"jild10-masala-197": [393, 394, 395, 396, 397, 398],
"jild10-masala-198": [398, 399, 400, 401],
"jild10-masala-199": [401, 402, 403, 404],
"jild10-masala-201": [404, 405, 406],
"jild10-masala-202": [406, 407],
"jild10-masala-203": [409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430],
"jild10-p431": [431, 432, 433, 434],
"jild10-masala-204": [434, 435],
"jild10-masala-205": [435, 436],
"jild10-masala-206": [436, 438, 439, 440, 441],
"jild10-masala-207": [441, 442],
"jild10-masala-208": [442, 443, 444, 445],
"jild10-masala-209": [445, 446, 447, 448, 449],
"jild10-masala-213": [449, 450],
"jild10-masala-214": [450, 451],
"jild10-masala-215": [451, 452],
"jild10-masala-216": [454, 455, 456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 466],
"jild10-p466": [466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 477, 478, 479, 480, 481, 482, 483, 484, 485],
"jild10-masala-217": [487, 488, 489, 490, 491],
"jild10-masala-220": [491, 492],
"jild10-masala-222": [492],
"jild10-masala-223": [492, 493],
"jild10-masala-224": [493],
"jild10-masala-225": [495, 496, 497, 498, 499, 500, 501, 502, 504, 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 515, 516, 517],
"jild10-masala-226": [517, 518],
"jild10-masala-227": [520, 521, 522, 523],
"jild10-masala-228": [523, 524],
"jild10-masala-229": [524, 525],
"jild10-masala-230": [525],
"jild10-masala-231": [526],
"jild10-masala-232": [526],
"jild10-masala-233": [527],
"jild10-masala-234": [527],
"jild10-masala-235": [528],
"jild10-masala-236": [530, 531, 532, 533, 534, 535, 536, 537, 538, 539, 540, 541, 542, 543, 544, 545, 546, 547, 548, 549, 550, 551, 552, 553],
"jild10-masala-248": [554, 555],
"jild10-masala-249": [555],
"jild10-masala-250": [555],
"jild10-masala-251": [555, 556],
"jild10-masala-252": [558],
"jild10-masala-253": [558, 559, 560],
"jild10-masala-255": [561],
"jild10-masala-256": [561, 562, 563, 564, 565, 566],
"jild10-masala-257": [566],
"jild10-masala-258": [568, 569, 570],
"jild10-masala-261": [570, 571, 572],
"jild10-masala-262": [573, 574, 575, 576, 577, 578, 579, 580, 581, 582, 583, 584, 585, 586, 587, 588, 589, 590, 591, 592, 593, 594, 595, 596, 597, 598, 599, 600, 601, 602, 603, 604, 605, 606, 607, 608, 609, 610, 611, 612, 613, 614, 615, 616, 617, 618, 619, 620, 621],
"jild10-masala-263": [622, 624, 625, 626, 627, 628, 629, 630, 631],
"jild10-masala-264": [631],
"jild10-masala-265": [631, 632],
"jild10-masala-266": [632],
"jild10-masala-267": [632, 633],
"jild10-masala-268": [633, 634],
"jild10-masala-269": [634, 635],
"jild10-masala-271": [635, 636],
"jild10-masala-272": [637, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 648, 649, 650, 651],
"jild10-masala-273": [652, 654, 655],
"jild10-masala-274": [655, 656, 657, 658, 659],
"jild10-masala-275": [659, 660],
"jild10-masala-276": [660, 661],
"jild10-masala-277": [662],
"jild10-masala-278": [662, 664],
"jild10-masala-281": [664],
"jild10-masala-282": [664, 665],
"jild10-masala-283": [665, 666],
"jild10-masala-284": [667],
"jild10-masala-285": [667, 668],
"jild10-masala-289": [668, 669],
"jild10-masala-290": [669, 670, 671, 672],
"jild10-masala-292": [672, 673, 674, 675],
"jild10-masala-293": [675, 676],
"jild10-masala-294": [676],
"jild10-masala-296": [677, 678],
"jild10-masala-297": [678, 679],
"jild10-masala-299": [679, 680, 681, 682],
"jild10-masala-300": [683, 684, 685, 686, 687, 688, 689, 690, 691, 692, 693, 694, 695, 696, 697, 698, 699, 700, 701, 702, 703, 704],
"jild10-masala-301": [705, 706, 707],
"jild10-masala-302": [707, 708, 709],
"jild10-masala-303": [710, 711],
"jild10-masala-304": [711, 712],
"jild10-masala-305": [712, 713, 714],
"jild10-masala-306": [714, 715],
"jild10-masala-308": [715, 716],
"jild10-masala-309": [716, 717],
"jild10-masala-310": [717],
"jild10-masala-311": [718, 720, 721],
"jild10-masala-312": [721],
"jild10-masala-313": [721, 722, 723],
"jild10-masala-315": [723, 724],
"jild10-masala-316": [724, 725, 726, 727, 728, 729, 730],
"jild10-p731": [731, 732],
"jild10-p732": [732, 733, 734],
"jild10-p735": [735, 736, 737],
"jild10-p737": [737, 738],
"jild10-p738": [738, 739],
"jild10-p740": [740, 741],
"jild10-p741": [741, 742, 743],
"jild10-p743": [743, 744],
"jild10-p745": [745, 746],
"jild10-p747": [747, 748],
"jild10-p749": [749, 750],
"jild10-p750": [750, 751],
"jild10-p751": [751, 752, 753],
"jild10-p753": [753, 754, 755, 756],
"jild10-p756": [756, 757, 758],
"jild10-p759": [759, 760],
"jild10-p760": [760, 761],
"jild10-p761": [761, 762],
"jild10-p762": [762, 763],
"jild10-p763": [763, 764],
"jild10-p765": [765, 766],
"jild10-p766": [766, 767],
"jild10-p768": [768],
"jild10-p769": [769, 770],
"jild10-p770": [770, 771],
"jild10-p771": [771, 772, 773],
"jild10-p774": [774, 775],
"jild10-p776": [776, 778, 779, 780],
"jild10-p781": [781, 782, 783, 784],
"jild10-p784": [784, 785, 786, 787, 788],
"jild10-p788": [788, 789, 790, 791, 792],
"jild10-p792": [792, 793, 794, 795],
"jild10-p795": [795],
"jild10-p795-wajibat": [795, 796, 797, 798],
"jild10-p798": [798, 799, 800, 801, 802, 803],
"jild10-p803": [803, 804],
"jild10-p804": [804, 805, 806, 807, 808, 809, 810, 811, 812, 813, 814, 815, 816, 817, 818],
"jild10-p818": [818, 819, 820, 821, 822, 823, 824, 825, 826, 827, 828, 829],
"jild10-p829": [829, 830, 831, 832, 833, 834, 835],
}

# The Urdu word for "page" is safha; the canonical marker is [safha N].
# Lenticular brackets are U+3010 (open) and U+3011 (close); the short
# form is "[safha-initial N]" with the single-letter abbreviation.
# All three patterns are built from escapes so this file never contains
# a literal lenticular-bracket pair.
SAFHA = "\u0635\u0641\u062d\u06c1"  # the Urdu word for page
RE_LENTICULAR = re.compile("\u3010" + SAFHA + " (\\d+)\u3011")
RE_SHORT = re.compile("\\[\u0635 (\\d+)\\]")
RE_FULL = re.compile("\\[" + SAFHA + " \\d+\\]")
LENTICULAR_PREFIX = "\u3010" + SAFHA  # for the "none remain" check
SHORT_PREFIX_RE = re.compile("\\[\u0635 \\d+\\]")

# Canonical output key order for every item (the JSON contract).
ITEM_KEYS = ["id", "title", "volume_id", "pages", "start_page",
             "tashreeh_sawal", "tashreeh_jawab", "notes"]


def normalise_markers(text):
    """Normalise page markers in one string. Returns (new_text, counts)."""
    counts = {"lenticular": 0, "short": 0, "full_before": 0}
    counts["full_before"] = len(RE_FULL.findall(text))
    text, n1 = RE_LENTICULAR.subn("[" + SAFHA + " \\1]", text)
    counts["lenticular"] = n1
    text, n2 = RE_SHORT.subn("[" + SAFHA + " \\1]", text)
    counts["short"] = n2
    return text, counts


def normalise_item(item):
    """Normalise markers in every string field of one item (recursively
    through lists/dicts). Returns per-form counts for this item."""
    totals = {"lenticular": 0, "short": 0, "full_before": 0}

    def walk(value):
        if isinstance(value, str):
            new, c = normalise_markers(value)
            for k in totals:
                totals[k] += c[k]
            return new
        if isinstance(value, list):
            return [walk(v) for v in value]
        if isinstance(value, dict):
            return {k: walk(v) for k, v in value.items()}
        return value

    for key in list(item.keys()):
        item[key] = walk(item[key])
    return totals


def main():
    assert len(V3_IDS) == EXPECTED_ITEMS, "embedded V3_IDS length mismatch"
    assert set(V3_PAGES) == set(V3_IDS), "embedded V3_PAGES keys != V3_IDS"
    assert sum(len(v) for v in V3_PAGES.values()) >= EXPECTED_PAGES

    manifest = json.load(open(os.path.join(BASE, MANIFEST), encoding="utf-8"))
    entries = manifest["chunks"]
    assert len(entries) == 18, f"expected 18 manifest entries, got {len(entries)}"
    assert all(e.get("status") == "done" for e in entries), "not all chunks done"
    by_file = {e["file"]: e for e in entries}
    assert set(by_file) == set(CHUNK_ORDER), (
        f"manifest files != CHUNK_ORDER: "
        f"missing={set(CHUNK_ORDER) - set(by_file)} "
        f"extra={set(by_file) - set(CHUNK_ORDER)}"
    )

    all_items = []
    derived = []
    for fname in CHUNK_ORDER:
        path = os.path.join(BASE, fname)
        d = json.load(open(path, encoding="utf-8"))
        items = d["masail"]
        entry = by_file[fname]
        assert len(items) == entry["items"], (
            f"{fname}: {len(items)} items, manifest says {entry['items']}"
        )
        # Marker normalisation, with before/after counts per chunk.
        before = {"lenticular": 0, "short": 0, "full_before": 0}
        for it in items:
            c = normalise_item(it)
            for k in before:
                before[k] += c[k]
        after_full = sum(
            len(RE_FULL.findall(json.dumps(it, ensure_ascii=False)))
            for it in items
        )
        print(
            f"{fname}: {len(items)} items | markers before: "
            f"lenticular={before['lenticular']} short={before['short']} "
            f"full={before['full_before']} | after: full={after_full}"
        )
        assert after_full == (
            before["lenticular"] + before["short"] + before["full_before"]
        ), f"{fname}: marker count changed by normalisation!"
        # Derive start_page = min(pages) where absent (none expected: all chunks carry start_page).
        for it in items:
            if "start_page" not in it:
                it["start_page"] = min(it["pages"])
                derived.append(it["id"])
        all_items.extend(items)

    # NO RENAME QUIRK in Jild 10: the v3 merged file has 278 UNIQUE
    # ids — the book numbers no masala twice in this jild. Chunk ids
    # are used exactly as written.
    assert len(all_items) == len({it["id"] for it in all_items}), (
        f"DUPLICATE IDS before validation: "
        f"{[i for i in [it['id'] for it in all_items] if [it['id'] for it in all_items].count(i) > 1]}"
    )
    print("renames applied: [] (no duplicate masala numbers in Jild 10)")

    print(f"concatenated: {len(all_items)} items")
    print(f"start_page derived for {len(derived)} items (expected 0: all chunks carry start_page)")
    assert len(all_items) == EXPECTED_ITEMS, (
        f"expected {EXPECTED_ITEMS} items, got {len(all_items)}"
    )

    # Rebuild each item in the canonical key order (the JSON contract).
    canonical = []
    for it in all_items:
        assert set(it.keys()) == set(ITEM_KEYS), (
            f"{it.get('id')}: keys {sorted(it.keys())} != {sorted(ITEM_KEYS)}"
        )
        canonical.append({k: it[k] for k in ITEM_KEYS})
    all_items = canonical

    # Validation.
    ids = [it["id"] for it in all_items]
    assert ids == V3_IDS, (
        f"ID sequence != v3: first diff at "
        f"{next((i for i, (a, b) in enumerate(zip(ids, V3_IDS)) if a != b), min(len(ids), len(V3_IDS)))}"
    )
    assert len(ids) == len(set(ids)), (
        f"DUPLICATE IDS: {[i for i in ids if ids.count(i) > 1]}"
    )
    empty = [it["id"] for it in all_items if not it.get("tashreeh_jawab")]
    assert not empty, f"EMPTY JAWAB: {empty}"
    vols = set(it.get("volume_id") for it in all_items)
    assert vols == EXPECTED_VOLUME_IDS, f"volume_ids {vols} != {EXPECTED_VOLUME_IDS}"
    pages = set()
    for it in all_items:
        assert it["pages"] == V3_PAGES[it["id"]], (
            f"{it['id']}: pages {it['pages']} != v3 {V3_PAGES[it['id']]}"
        )
        pages.update(it["pages"])
    assert len(pages) == EXPECTED_PAGES, (
        f"expected {EXPECTED_PAGES} unique pages, got {len(pages)}"
    )
    assert min(pages) == EXPECTED_MIN_PAGE, f"min page {min(pages)}"
    assert max(pages) == EXPECTED_MAX_PAGE, f"max page {max(pages)}"
    exceptions = {
        it["id"] for it in all_items if it["start_page"] != min(it["pages"])
    }
    assert not exceptions, f"start_page != min(pages): {sorted(exceptions)}"
    assert ids[0] == EXPECTED_FIRST_ID, f"first id {ids[0]}"
    assert ids[-1] == EXPECTED_LAST_ID, f"last id {ids[-1]}"

    out = {"masail": all_items}
    out_text = json.dumps(out, ensure_ascii=False, indent=1)
    assert LENTICULAR_PREFIX not in out_text, "lenticular markers remain in output!"
    assert not SHORT_PREFIX_RE.search(out_text), "short markers remain in output!"
    total_markers = len(RE_FULL.findall(out_text))
    print(
        f"VALIDATION PASSED: {len(all_items)} items, {len(pages)} unique pages "
        f"(min {min(pages)}, max {max(pages)}), volume_ids {sorted(vols)}, "
        f"first {ids[0]}, last {ids[-1]}, start_page == min(pages) for all, "
        f"derived start_page for {len(derived)} items, markers {total_markers}"
    )

    with open(os.path.join(BASE, "jild-10.json"), "w", encoding="utf-8") as f:
        f.write(out_text)
    print(f"WROTE jild-10.json: {len(out_text.encode('utf-8'))} bytes")


if __name__ == "__main__":
    main()
