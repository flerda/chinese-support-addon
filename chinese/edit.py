# -*- coding: utf-8 -*-
#
# Copyright © 2012 Thomas TEMPÉ, <thomas.tempe@alysse.org>
# Copyright © 2012 Roland Sieker, <ospalh@gmail.com>
#
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
#
#COPYRIGHT AND PERMISSION NOTICE

#Copyright © 1991-2012 Unicode, Inc. All rights reserved. Distributed under the Terms of Use in http://www.unicode.org/copyright.html.

#Permission is hereby granted, free of charge, to any person obtaining a copy of the Unicode data files and any associated documentation (the "Data Files") or Unicode software and any associated documentation (the "Software") to deal in the Data Files or Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, and/or sell copies of the Data Files or Software, and to permit persons to whom the Data Files or Software are furnished to do so, provided that (a) the above copyright notice(s) and this permission notice appear with all copies of the Data Files or Software, (b) both the above copyright notice(s) and this permission notice appear in associated documentation, and (c) there is clear notice in each modified Data File or in the Software as well as in the documentation associated with the Data File(s) or Software that the data or software has been modified.

#THE DATA FILES AND SOFTWARE ARE PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT OF THIRD PARTY RIGHTS. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR HOLDERS INCLUDED IN THIS NOTICE BE LIABLE FOR ANY CLAIM, OR ANY SPECIAL INDIRECT OR CONSEQUENTIAL DAMAGES, OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THE DATA FILES OR SOFTWARE.

#Except as contained in this notice, the name of a copyright holder shall not be used in advertising or otherwise to promote the sale, use or other dealings in these Data Files or Software without prior written authorization of the copyright holder.


import re

from aqt import mw
from anki.hooks import addHook

import cache
import cjklib.characterlookup

SUFFIXES = ['Hanzi', 'Hanzi Colored', 'Pinyin', 'Pinyin Colored']
STYLES = [
    '',
    'color: red;',
    'color: blue;',
    'color: green;',
    'color: orange;',
    'color: gray;',
]
HANZI_LOOKUP = cjklib.characterlookup.CharacterLookup('C')


CONVERT_CACHE = cache.Empty(25)
IS_CHARACTER_IN_DOMAIN_CACHE = cache.Empty(25)
GET_READING_FOR_CHARACTER_CACHE = cache.Empty(25)



@cache.caching(CONVERT_CACHE)
def convert(*args, **kwargs):
  return HANZI_LOOKUP._getReadingFactory().convert(*args, **kwargs)


@cache.caching(IS_CHARACTER_IN_DOMAIN_CACHE)
def isCharacterInDomain(*args, **kwargs):
  return HANZI_LOOKUP.isCharacterInDomain(*args, **kwargs)


@cache.caching(GET_READING_FOR_CHARACTER_CACHE)
def getReadingForCharacter(*args, **kwargs):
  return HANZI_LOOKUP.getReadingForCharacter(*args, **kwargs)


def lookupField(note, fields, base, suffix):
  if base:
    name = '%s %s' % (base, suffix)
  else:
    name = suffix
  if name in fields:
    return (note[name], fields.index(name))
  return (None, -1)


def getPinyinFor(hanzi):
  return getReadingForCharacter(
      hanzi, 'Pinyin', toneMarkType='numbers')[0]


def generatePinyin(hanzi):
  pinyin = ''
  for ch in hanzi:
    if not isCharacterInDomain(ch):
      colored_hanzi += ch
      continue
    pinyin += getPinyinFor(ch)
  return pinyin


def splitPinyin(pinyin, keep_spaces=False):
  def splitPinyinRec(index):
    if index >= len(pinyin): return []
    start = index
    while index < len(pinyin):
      next = pinyin[index]
      if next in ['1', '2', '3', '4', '5']:
        return [pinyin[start:index + 1]] + splitPinyinRec(index + 1)
      if not next.islower():
        if keep_spaces:
          if index == start:
            return [next] + splitPinyinRec(index + 1)
          else:
            return [pinyin[start:index], next] + splitPinyinRec(index + 1)
        else:
          if index == start:
            return splitPinyinRec(index + 1)
          else:
            return [pinyin[start:index]] + splitPinyinRec(index + 1)
      index += 1
    return [pinyin[start:]]
  return splitPinyinRec(0)

def coloredHanzi(hanzi, pinyin):
  pinyin_list = splitPinyin(pinyin, keep_spaces=True)
  pinyin_index = 0
  colored_hanzi = ''
  for ch in hanzi:
    if not isCharacterInDomain(ch):
      continue
    while pinyin_index < len(pinyin_list):
      p = pinyin_list[pinyin_index]
      if not p[0].islower():
        colored_hanzi += p
        pinyin_index += 1
      else:
        break
    if pinyin_index < len(pinyin_list):
      p = pinyin_list[pinyin_index]
      pinyin_index += 1
      tone = p[-1] if p[-1] in ['1', '2', '3', '4', '5'] else '5'
    else:
      tone = 5
    colored_hanzi += '<span style="%s">%s</span>' % (STYLES[int(tone)], ch)
    while pinyin_index < len(pinyin_list):
      p = pinyin_list[pinyin_index]
      if not p[0].islower():
        colored_hanzi += p
        pinyin_index += 1
      else:
        break
  return colored_hanzi


def coloredPinyin(pinyin):
  colored_pinyin = ''
  for p in splitPinyin(pinyin, keep_spaces=True):
    tone = p[-1] if p[-1] in ['1', '2', '3', '4', '5'] else '5'
    if not p[0].islower():
      colored_pinyin += p
      continue
    if p.endswith(tone):
      p = p[:-1]
    p = convert(
        p + tone, 'Pinyin', 'Pinyin', sourceOptions={'toneMarkType': 'numbers'})
    colored_pinyin += '<span style="%s">%s</span>' % (STYLES[int(tone)], p)
  return colored_pinyin


def setFieldByIndex(note, field_names, index, value):
  note[field_names[index]] = value


def editFocusLost(modified, note, focus_field_index):
    field_names = mw.col.models.fieldNames(note.model())
    focus_field_name = field_names[focus_field_index]
    modified_note = dict(note)

    base_name = None
    for suffix in SUFFIXES:
      if focus_field_name.endswith(suffix):
        base_name = focus_field_name[:-len(suffix)-1]
        break

    if base_name is None:
      return modified

    (hanzi, hanzi_field_index) = lookupField(
        note, field_names, base_name, SUFFIXES[0])
    (hanzi_colored, hanzi_colored_field_index) = lookupField(
        note, field_names, base_name, SUFFIXES[1])
    (pinyin, pinyin_field_index) = lookupField(
        note, field_names, base_name, SUFFIXES[2])
    (pinyin_colored, pinyin_colored_field_index) = lookupField(
        note, field_names, base_name, SUFFIXES[3])

    if hanzi_field_index == focus_field_index and hanzi:
      # User updated the hanzi.
      if not pinyin:
        # Generate if empty.
        pinyin = generatePinyin(hanzi)
      if pinyin_field_index != -1:
        setFieldByIndex(modified_note, field_names, pinyin_field_index, pinyin)
      if hanzi_colored_field_index != -1:
        setFieldByIndex(modified_note, field_names, hanzi_colored_field_index,
            coloredHanzi(hanzi, pinyin))
      if pinyin_colored_field_index != -1:
        setFieldByIndex(modified_note, field_names, pinyin_colored_field_index,
            coloredPinyin(pinyin))
    if pinyin_field_index == focus_field_index and pinyin:
      if hanzi_colored_field_index != -1:
        setFieldByIndex(modified_note, field_names, hanzi_colored_field_index,
            coloredHanzi(hanzi, pinyin))
      if pinyin_colored_field_index != -1:
        setFieldByIndex(modified_note, field_names, pinyin_colored_field_index,
            coloredPinyin(pinyin))

    for field_name in field_names:
        if modified_note[field_name] != note[field_name]:
            note[field_name] = modified_note[field_name]
            modified = True
    
    return modified


addHook('editFocusLost', editFocusLost)
