#! /usr/bin/env python3

import re

from collections import defaultdict
from itertools import product

from mistool.os_use import PPath
from mistool.string_use import between, joinand
from orpyste.data import ReadBlock


# ------------------------ #
# -- INTERNAL CONSTANTS -- #
# ------------------------ #

BASENAME = PPath(__file__).stem.replace("build-", "")
BASENAME = BASENAME.replace("[slow]", "")

THIS_DIR = PPath(__file__).parent
STY_FILE = THIS_DIR / f'{BASENAME}.sty'
TEX_FILE = STY_FILE.parent / (STY_FILE.stem + "[fr].tex")

PATTERN_FOR_PEUF = re.compile("\d+-(.*)")
match            = re.search(PATTERN_FOR_PEUF, STY_FILE.stem)
PEUF_FILE        = STY_FILE.parent / (match.group(1).strip() + ".peuf")

DECO = " "*4


# -------------------------- #
# -- THE CONSTANTS TO ADD -- #
# -------------------------- #

with ReadBlock(
    content = PEUF_FILE,
    mode    = "keyval:: ="
) as data:
    functions = data.mydict("std mini")

    for k, v in functions['no-parameter'].items():
        if not v:
            functions['no-parameter'][k] = k

    for k, v in functions['parameter'].items():
        nbparam, latex, *desc = v.split(";")

        functions['parameter'][k] = {
            'nbparam': nbparam.strip(),
            'latex'  : latex.strip(),
            'desc'   : [d.strip() for d in desc],
        }


# ------------------------------ #
# -- LATEX TEMPLATE TO UPDATE -- #
# ------------------------------ #

with open(
    file     = STY_FILE,
    mode     = 'r',
    encoding = 'utf-8'
) as styfile:
    temp_sty = styfile.read()


with open(
    file     = TEX_FILE,
    mode     = 'r',
    encoding = 'utf-8'
) as docfile:
    temp_tex = docfile.read()


# --------------------- #
# -- UPDATING MACROS -- #
# --------------------- #

text_start, _, text_end = between(
    text = temp_sty,
    seps = [
        "% Classical functions - START",
        "% Classical functions - END"
    ],
    keepseps = True
)

macro_defs = [
    "\n".join(
        r"\DeclareMathOperator{{\{0}}}{{\operatorname{{{1}}}}}".format(
            latexname,
            humanname
        )
        for latexname, humanname in functions['no-parameter'].items()
    ),
    "",
    "\n".join(
        r"\newcommand\{0}[{1[nbparam]}]{{{1[latex]}}}".format(
            name,
            infos
        )
        for name, infos in functions['parameter'].items()
    )
]

macro_defs = "\n".join(macro_defs)
macro_defs = macro_defs.strip()

temp_sty = f"{text_start}\n\n{macro_defs}\n\n{text_end}"


# ----------------------------------------------- #
# -- UPDATING LISTS FOR THE DOC - NO PARAMETER -- #
# ----------------------------------------------- #

text_start, _, text_end = between(
    text = temp_tex,
    seps = [
        "% List of functions without parameter - START",
        "% List of functions without parameter - END"
    ],
    keepseps = True
)

docinfos   = []
lastmacros = []
lastfirst  = ""
lastlenght = -1

for onemacro in list(functions['no-parameter'].keys()) + ["ZZZZ-unsed-ZZZZ"]:
    if lastfirst:
        if lastfirst != onemacro[0] \
        or lastlenght != len(onemacro):
            lastmacros = ", ".join(lastmacros)

            if lastfirst == "f":
                extra ="  où \\quad \\mwhyprefix{{f}}{{rench}}"

            else:
                extra = ""

            docinfos += [
                f"""
\\foreach \\k in {{{lastmacros}}}{{

    \\IDmacro*{{\k}}{{0}}{extra}
}}
                """,
                "\\separation"
                ""
            ]

            lastfirst  = onemacro[0]
            lastlenght = len(onemacro)
            lastmacros = []

    else:
        lastfirst  = onemacro[0]
        lastlenght = len(onemacro)

    lastmacros.append(onemacro)


if docinfos:
# Let's remove the lase separation.
    docinfos = "\n".join(docinfos[:-1])
    docinfos = docinfos.strip()
    docinfos = f"\n{docinfos}\n"

else:
    docinfos = ""

temp_tex = f"{text_start}\n{docinfos}\n{text_end}"


# -------------------------- #
# -- UPDATES OF THE FILES -- #
# -------------------------- #

with open(
    file     = TEX_FILE,
    mode     = 'w',
    encoding = 'utf-8'
) as docfile:
    docfile.write(temp_tex)

with open(
    file     = STY_FILE,
    mode     = 'w',
    encoding = 'utf-8'
) as docfile:
    docfile.write(temp_sty)
