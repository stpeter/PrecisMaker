#! /usr/bin/env python

"""

PRECIS Maker
by Peter Saint-Andre / stpeter@stpeter.im

This is version 0.1, last updated 2013-06-17.

And yes, this is an experiment in literate programming. :-)

Table of Contents

1.0 Introduction
2.0 Method
3.0 Constructing Our Data

1.0 Introduction

Internationalization is hard. Heck, even the word itself is hard, which 
is why people shorten it to 'i18n' (the letter 'i', followed by 18 more
letters, followed by the letter 'n'). I even wrote a big presentation 
about it once, entitled Internationalization, A Guide for the Perplexed:

https://stpeter.im/files/i18n-intro.pdf

Anyway, folks at the Internet Engineering Task Force (IETF) have been
working to make internationalization easier, building on the foundation
laid by the Unicode Consortium. The IETF work is focused on enabling
Internet protocols like email and the Domain Name System (DNS) to
include characters outside the ASCII range. Personally, I care about
this topic because the instant messaging technology I work on, called
Jabber or XMPP, also supports fully internationalized identifiers for
people, servers, and other entities on the network.

The DNS work came in two phases (called IDNA2003 and IDNA2008). One
spinoff from IDNA2003 was a generalized framework for i18n called
'stringprep'. Unfortunately, stringprep didn't work so well in practice,
in large part because it was limited to a specific version of Unicode.
As a result, our IETF friends went back to the drawing board and came up
with a new generalized framework, called PRECIS.

The PRECIS framework specification (of which I am an author) enables an
application to handle Unicode characters based on metadata about the
character, not based on a lookup in a big table. This means that if the
metadata about a character changes in a new version of Unicode, the
application will automatically handle the character in the right way (or
so we hope!).

This little script doesn't solve all those problems. Instead, it has a 
more modest goal: given input in the form of all the data files from
a specific version of Unicode, provide output that describes how each
Unicode codepoint would be handled under PRECIS. Thus PRECIS Maker is
similar to the createtables script that Patrik Faltstrom wrote in Ruby
for IDNA and stringprep, which has been patched by Yoshiro Yoneya and
Takahiro Nemoto to handle PRECIS.

PRECIS Maker is written in the Python programming language. Therefore we
invoke the Python interpreter in the following code.

2.0 Method

The PRECIS framework specification defines our procedure:

https://datatracker.ietf.org/doc/draft-ietf-precis-framework/

Here's what we need to do: for each codepoint in Unicode, determine
whether it is valid, disallowed, or unassigned for PRECIS in general,
whether a contextual rule is required to determine the status of the
codepoint, or whether the codepoint is valid or disallowed for a
particular string class.

There are two string classes in PRECIS: the IdentifierClass and the
FreeformClass. The IdentifierClass is a restricted class that allows
only letters and digits (although it also 'grandfathers' all of the 
characters from the ASCII range, even if they are symbols or whatnot). 
The FreeformClass is more loose, since it disallows only control
characters and some other so-called ignorable code points.

Since there are only two string classes and the IdentifierClass is a
strict subset of the FreeformClass, a codepoint is valid for all of
PRECIS if it is valid for the IdentifierClass and a codepoint is
disallowed for all of PRECIS if it is disallowed for the FreeformClass. 
Therefore, we really need to determine whether a codepoint is one of 
the following: protocol-valid (PVAL), disallowed, unassigned, contextual 
(which can be either CONTEXTJ or CONTEXTO), or protocol-valid for the 
FreeformClass (FREE_PVAL) and thus disallowed for the IdentifierClass.

In order to achieve those goals, we will need to read information from 
various files in the Unicode Character Database ('ucd'), slice and dice
that information in various ways to determine the properties of each
codepoint, and output an XML file that matches the format produced by
the createtables script.

Thankfully, the Python language contains core libraries that enable
us to complete those tasks. Therefore we import the relevant libraries.

"""

### BEGIN CODE ###
# Code to import the code libraries we need
import os
import sys
import xml.dom.minidom
### END CODE ###

"""

3.0 Constructing Our Data

As mentioned, all the data we need is contained in the Unicode Character
Database (or ucd):

http://www.unicode.org/ucd/

To get the latest version, you can download all of the files here:

http://www.unicode.org/Public/UCD/latest/ucd/

PrecisMaker assumes that you will run the script in a directory that
contains all of those text files. These are not included as part of 
PrecisMaker since you should be able to run PrecisMaker against any
(recent) version of the Unicode Character Database.

The PRECIS spec requires us to use the following files:

o UnicodeData.txt
o DerivedCoreProperties.txt
o HangulSyllableType.txt

Let's see exactly why we need those files, and what data we'll pull 
from them...

First, the PRECIS framework specification borrows some existing
codepoint categories from IDNA208, and also defines a number of new
categories (we'll delve into more details later on):

(A) LetterDigits - The character is a lowercase letter, an uppercase
letter, a modifier letter, an 'other letter', a non-spacing mark, a
spacing mark, or a decimal number.  Each of these character types is
flagged for us in the UnicodeData.txt file. 

(B) Unstable - Used in IDNA2008 but not in PRECIS.

(C) IgnorableProperties - Used in IDNA2008 but not in PRECIS.

(D) IgnorableBlocks - Used in IDNA2008 but not in PRECIS.

(E) LDH - Used in IDNA2008 but not in PRECIS.

(F) Exceptions - This category, which lists 41 codepoints that handled
in special ways, was defined for IDNA2008 and is re-used in PRECIS.
Since this is merely a list of codepoints, we don't even need any of the
Unicode files to implement this category. Instead, we can simply create
a list (actually, in Python, a 'dictionary') of the codepoint numbers
and the derived property for each.

(G) BackwardCompatible - This category is reserved for future use so
that IDNA2008 (and PRECIS) can correctly handle characters whose
property values change between versions of Unicode. First defined in
IDNA2008. So far this category is empty.

(H) JoinControl - Characters that are not in LetterDigits but that are 
still required in strings under some circumstances. First defined in
IDNA2008.

(I) OldHangulJamo - The conjoining Hangul Jamo codepoints (Leading Jamo,
Vowel Jamo, and Trailing Jamo). The HangulSyllableType.txt file contains 
the data we need for this category. First defined in IDNA2008.

(J) Unassigned - Codepoints that are not yet assigned in the version of
Unicode for which PrecisMaker is run. First defined in IDNA2008.

(K) ASCII7 - Codepoints in the ASCII range (U+0021 - U+007E). These are
grandfathered into PRECIS.

(L) Controls - The codepoint is a control character. The main
UnicodeData.txt file gives us this information.

(M) PrecisIgnorableProperties - Certain codepoints that are not
recommended in PRECIS string classes. The DerivedCoreProperties.txt file
provides this information.

(N) Spaces - The codepoint is a space character (in Unicode, a 'space
separator' as opposed to a line separator or a paragraph separator).

(O) Symbols - The code point is a math symbol, currency symbol, modifier
symbol, or some other symbol character.

(P) Punctuation - The code point is some form of punctuation character
(connector, dash, quote, etc.).

(Q) HasCompat - Codepoints that have compatibility equivalents as 
explained in Chapter 2 and Chapter 3 of the Unicode standard. We'll look
at these in more detail below.

(R) OtherLetterDigits - The codepoint is a letter or digit other
than the 'traditional' letters and digits grouped under the 
LetterDigits (A) class.  These are titlecase letters, 'letter numbers',
'other numbers', and enclosing marks.

In case you're wondering how these categories are used, the short story
is that the PRECIS IdentifierClass allows LetterDigits characters 
(Category A) and ASCII7 characters (Category K), and disallows
everything else; by contrast, the FreeformClass disallows only Controls 
characters (Category L) and PrecisIgnorableProperties characters
(Category M) and allows everything else.  However, in addition to
DISALLOWED and protocol-valid (PVALID), there are several other possible
values for the derived property: UNASSIGNED, CONTEXTJ, CONTEXTO, and
four values for PVALID or DISALLOWED in relation to a particular string
class (thus ID_PVAL, ID_DIS, FREE_PVAL, and FREE_DIS).

"""

### BEGIN CODE ###
# create a Python dictionary of the code points in the Exceptions class
# this dictionary follows the order in RFC 5892
exceptions = dict([ 
    ('00DF','PVALID'), 
    ('03C2','PVALID'), 
    ('06FD','PVALID'), 
    ('06FE','PVALID'), 
    ('0F0B','PVALID'), 
    ('3007','PVALID'), 
    ('00B7','CONTEXTO'), 
    ('0375','CONTEXTO'), 
    ('05F3','CONTEXTO'), 
    ('05F4','CONTEXTO'), 
    ('30FB','CONTEXTO'), 
    ('0660','CONTEXTO'), 
    ('0661','CONTEXTO'), 
    ('0662','CONTEXTO'), 
    ('0663','CONTEXTO'), 
    ('0664','CONTEXTO'), 
    ('0665','CONTEXTO'), 
    ('0666','CONTEXTO'), 
    ('0667','CONTEXTO'), 
    ('0668','CONTEXTO'), 
    ('0669','CONTEXTO'), 
    ('06F1','CONTEXTO'), 
    ('06F2','CONTEXTO'), 
    ('06F3','CONTEXTO'), 
    ('06F4','CONTEXTO'), 
    ('06F5','CONTEXTO'), 
    ('06F6','CONTEXTO'), 
    ('06F7','CONTEXTO'), 
    ('06F8','CONTEXTO'), 
    ('06F9','CONTEXTO'), 
    ('0640','DISALLOWED'), 
    ('07FA','DISALLOWED'), 
    ('302E','DISALLOWED'), 
    ('302F','DISALLOWED'), 
    ('3031','DISALLOWED'), 
    ('3032','DISALLOWED'), 
    ('3033','DISALLOWED'), 
    ('3034','DISALLOWED'), 
    ('3035','DISALLOWED'), 
    ('303B','DISALLOWED')
])
### END CODE ###

"""

4. Running the Algorithm

"""

# END 
