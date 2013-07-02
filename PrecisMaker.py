#! /usr/bin/env python

'''

PRECIS Maker
by Peter Saint-Andre / stpeter@stpeter.im

This is version 0.1, last updated 2013-06-27.

And yes, this is an experiment in literate programming. :-)

Table of Contents

1.0 Introduction
2.0 Method
3.0 Constructing Our Data
4.0 Running the Algorithm
5.0 Acknowledgements

###

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

###

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

'''

#
### BEGIN CODE ###
#
# Code to import the code libraries we need
import os
import sys
#
# also set a flag for debugging
#
debug = 1;
#
### END CODE ###
#

'''

###

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

In particular, the PRECIS framework specification contains the following
pseudocode (where "cp" stands for codepoint):

   If .cp. .in. Exceptions Then Exceptions(cp);
   Else If .cp. .in. BackwardCompatible Then BackwardCompatible(cp);
   Else If .cp. .in. Unassigned Then UNASSIGNED;
   Else If .cp. .in. ASCII7 Then PVALID;
   Else If .cp. .in. JoinControl Then CONTEXTJ;
   Else If .cp. .in. OldHangulJamo Then DISALLOWED;
   Else If .cp. .in. PrecisIgnorableProperties Then DISALLOWED;
   Else If .cp. .in. Controls Then DISALLOWED;
   Else If .cp. .in. HasCompat Then SAFE_DIS or FREE_PVAL;
   Else If .cp. .in. LetterDigits Then PVALID;
   Else If .cp. .in. OtherLetterDigits Then SAFE_DIS or FREE_PVAL;
   Else If .cp. .in. Spaces Then SAFE_DIS or FREE_PVAL;
   Else If .cp. .in. Symbols Then SAFE_DIS or FREE_PVAL;
   Else If .cp. .in. Punctuation Then SAFE_DIS or FREE_PVAL;
   Else DISALLOWED;

The following sections describe these categories in a bit more detail,
from the perspective of preparing our data.

First, we need to pull in the basic data from the UnicodeData.txt file.
This data provides the basis for most of the decisions we'll make (e.g.,
whether a codepoint is a letter, a digit, a space, a symbol, a control,
a punctuation character).

Almost every line in the UnicodeData.txt file contains a 
semicolon-separated set of data about a codepoint. 

Here is an example, for the letter "P":

0050;LATIN CAPITAL LETTER P;Lu;0;L;;;;;N;;;;0070;

That is, this line provides information about codepoint U+0050, which is
the uppercase version the letter "P" in the Latin alphabet (among other
things, we learn here that the Unicode General Category for this
codepoint is "Lu", short for "Letter, uppercase").

The format is described here:

http://www.unicode.org/reports/tr44/#UnicodeData.txt

Notice that I said "almost every line". There are 24 major exceptions,
and we need some special handling to pull in this data. They all look
like this:

3400;<CJK Ideograph Extension A, First>;Lo;0;L;;;;;N;;;;;
4DB5;<CJK Ideograph Extension A, Last>;Lo;0;L;;;;;N;;;;;

For pairs of lines like these, the initial line defines the start of a
codepoint range, and the second line defines the end of the range. In
this example, all of the codepoints between U+3400 and U+4DB5 fall into
"CJK Ideograph Extension A" and have a General Category of "Lo"
("Letter, other").

'''

#
### BEGIN CODE ###
#
# code to pull in the UnicodeData.txt file
# each line in the file becomes an entry in the dictionary
#
udict = {};
with open('UnicodeData.txt') as f:  
    for line in f: 
        data = line.split(';');
        udict[data[0]] = data;
#
# also create a dictionary of integer equivalents for known codepoints
#
idict = {};
for k in udict.iteritems():
    thiscp = k[0];
    cpint = int(thiscp,16);
    idict[data[0]] = cpint;
#
### END CODE ###
#

'''

Next we'll delve further into data preparation for each of the rules we
plan to apply.

3.1 Exceptions

As mentioned, both IDNA2008 and PRECIS handle certain codepoints on an 
exception basis. As specified in RFC 5892, the 41 codepoints in question 
are:

00B7 # MIDDLE DOT
00DF # LATIN SMALL LETTER SHARP S
0375 # GREEK LOWER NUMERAL SIGN (KERAIA)
03C2 # GREEK SMALL LETTER FINAL SIGMA
05F3 # HEBREW PUNCTUATION GERESH
05F4 # HEBREW PUNCTUATION GERSHAYIM
0640 # ARABIC TATWEEL
0660 # ARABIC-INDIC DIGIT ZERO
0661 # ARABIC-INDIC DIGIT ONE
0662 # ARABIC-INDIC DIGIT TWO
0663 # ARABIC-INDIC DIGIT THREE
0664 # ARABIC-INDIC DIGIT FOUR
0665 # ARABIC-INDIC DIGIT FIVE
0666 # ARABIC-INDIC DIGIT SIX
0667 # ARABIC-INDIC DIGIT SEVEN
0668 # ARABIC-INDIC DIGIT EIGHT
0669 # ARABIC-INDIC DIGIT NINE
06F0 # EXTENDED ARABIC-INDIC DIGIT ZERO
06F1 # EXTENDED ARABIC-INDIC DIGIT ONE
06F2 # EXTENDED ARABIC-INDIC DIGIT TWO
06F3 # EXTENDED ARABIC-INDIC DIGIT THREE
06F4 # EXTENDED ARABIC-INDIC DIGIT FOUR
06F5 # EXTENDED ARABIC-INDIC DIGIT FIVE
06F6 # EXTENDED ARABIC-INDIC DIGIT SIX
06F7 # EXTENDED ARABIC-INDIC DIGIT SEVEN
06F8 # EXTENDED ARABIC-INDIC DIGIT EIGHT
06F9 # EXTENDED ARABIC-INDIC DIGIT NINE
06FD # ARABIC SIGN SINDHI AMPERSAND
06FE # ARABIC SIGN SINDHI POSTPOSITION MEN
07FA # NKO LAJANYALAN
0F0B # TIBETAN MARK INTERSYLLABIC TSHEG
3007 # IDEOGRAPHIC NUMBER ZERO
302E # HANGUL SINGLE DOT TONE MARK
302F # HANGUL DOUBLE DOT TONE MARK
3031 # VERTICAL KANA REPEAT MARK
3032 # VERTICAL KANA REPEAT WITH VOICED SOUND MARK
3033 # VERTICAL KANA REPEAT MARK UPPER HALF
3034 # VERTICAL KANA REPEAT WITH VOICED SOUND MARK UPPER HA
3035 # VERTICAL KANA REPEAT MARK LOWER HALF
303B # VERTICAL IDEOGRAPHIC ITERATION MARK
30FB # KATAKANA MIDDLE DOT

'''

#
### BEGIN CODE ###
#
# create a Python dictionary of the code points in the Exceptions class
# this dictionary follows the order in RFC 5892
#
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
    ('06F0','CONTEXTO'), 
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
#
# define a function that determines if a codepoint is in Exceptions
#
def isExceptions(cp):
    if cp in exceptions:
        return 1
#
### END CODE ###
#

'''

3.2 BackwardCompatible

Currently, there are no characters in the BackwardCompatible category.
Most people in the i18n community at the IETF seem to be hoping that
this category is always empty. :-)

If the category is ever non-empty, PrecisMaker will be updated.

3.3 Unassigned

Some codepoints are unassigned: i.e., the codepoint exists in Unicode
but so far no character has been assigned to that codepoint. There are
many reason why this might be the case (e.g., a range of codepoints is
being used for a particular script but not all the codepoints in that
range have been used yet). If a codepoint has not yet been assigned, its
derived property is UNASSIGNED in PRECIS. Do note that a status of
unassigned applies to a particular version of Unicode, and a codepoint
that is unassigned in the current version might be assigned in a future
version. (Of course, that's the case with all codepoints: their status 
is always subject to change as Unicode is updated over time.)

The UnicodeData.txt file contains entries for assigned codepoints, but
not for unassigned codepoints. Therefore we need to discover which
codepoints are unassigned through a process of interpolation. This is
slightly inconvenient, but unavoidable (if the UnicodeData.txt file
contained one line for each codepoint, it would have more than one
million lines!).

One way to determine if a codepoint is unassigned is to establish the
complete range of Unicode characters (i.e., from U+0000 to U+10FFFD) and
check to see what codepoints we know about in that range; if the
codepoint can't be found in that list, then it is unassigned.

However, this doesn't always work, because UnicodeData.txt contains some 
shorthand for ranges. Consider:

3400;<CJK Ideograph Extension A, First>;Lo;0;L;;;;;N;;;;;
4DB5;<CJK Ideograph Extension A, Last>;Lo;0;L;;;;;N;;;;;

That means "the range of codepoints from 3400 to 4DB5 defines CJK
Ideograph Extension A, and all of those codepoints have a
General_Category of Lo, i.e., they are 'other letters'."

Currently, the code in PrecisMaker does not handle this case!

'''

#
### BEGIN CODE ###
#
# check if a particular codepoint is in our dictionary of known
# codepoints
#
def isUnassigned(cp):
# FIXME -- see text above!!!
    if cp in udict:
        return 0
    else:
        return 1
#
### END CODE ###
#

'''

3.4 ASCII7

For our purposes, an ASCII7 character is a codepoint between U+0021 and
U+007E inclusive. We don't need to read in any data from the Unicode 
Character Database to determine that such a codepoint is PVALID.
Probably the easiest way to do this is to see if the integer (base 10)
equivalent of the codepoint number in hexadecimal (base 16) is between
33 and 126 inclusive.

'''

#
### BEGIN CODE ###
#
# code to determine if a codepoint is in the ASCII7 category
#
def isASCII7(cp):
    udec = int(cp,16)
    if 33 <= udec <= 126:
        return 1
#
### END CODE ###
#

'''

3.5 JoinControl

According to RFC 5892, only two codepoints are in the JoinControl
category:

200C # ZERO WIDTH NON-JOINER
200D # ZERO WIDTH JOINER

I haven't been able to discover a rule-based way of determining whether
a codepoint is a JoinControl (and thus CONTEXJ). For now I hardcode
those two codepoints to CONTEXTJ.

By the way there is an IANA registry for CONTEXTJ and CONTEXTO:

http://www.iana.org/assignments/idna-tables-6.0.0/

Both U+200C and U+200D have a lookup result of "True" in the IDNA
Contextual Rules registry and thus are CONTEXTJ (the other codepoints in
that registry have a lookup result of "False" and thus are CONTEXTO).

'''

#
### BEGIN CODE ###
#
# code to determine if a codepoint is in the JoinControl category
#
def isJoinControl(cp):
    if cp in ('200C', '200D'):
        return 1
#
### END CODE ###
#

'''

3.6 PrecisIgnorableProperties

A codepoint is in the PrecisIgnorableProperties category if is a
"Default_Ignorable_Code_Point" or "Noncharacter_Code_Point" in Unicode.
These properties can be discovered from the DerivedCoreProperties.txt
file in the Unicode Character Database.

The DerivedCoreProperties.txt file is a bit hard to parse, but for our
purposes we can do as we did for the UnicodeData.txt file: split each
line on the semicolon character. 

'''

#
### BEGIN CODE ###
#
# code to pull in the DerivedCoreProperties.txt file
# each line in the file becomes an entry in the dictionary
#
dcpdict = {};
with open('DerivedCoreProperties.txt') as f:  
    for line in f: 
        data = line.split(';');
        dcpdict[data[0]] = data;
#
# define a function to determine if a codepoint is in
# PrecisIgnorableProperties
#
# we care only about lines that define Default_Ignorable_Code_Point
#
# therefore we create a list of such codepoints
# 
dicp = [];
for v in dcpdict.itervalues():
   if len(v) > 1:
       secondvalue = v[1] + "";
       if secondvalue.startswith(' Default_Ignorable_Code_Point #'):
           firstvalue = v[0] + "";
           firstvalue = firstvalue.strip();
           therange = firstvalue.split('..');
           if len(therange) == 1:
               cpint = int(therange[0],16);
               dicp.append(cpint)
           else:
               rangestart = therange[0];
               rangeend = therange[1];
               intbottom = int(rangestart,16);
               inttop = int(rangeend,16) + 1;
               thisrange = range(intbottom, inttop, 1);
               for i in thisrange:
                   dicp.append(i)
#
# define a function to determine if a codepoint is
# Default_Ignorable_Code_Point
#
def isPrecisIgnorableProperties(cp):
    item = udict[cp]
    itemint = int(item[0],16)
    if itemint in dicp:
        #print cp + " is ignorable!"
        return 1
#
### END CODE ###
#

'''

When we run the algorithm, we'll need
to search through the resulting data to find what we need.

3.7 Controls

A Controls character is any codepoint with a Unicode General_Category of
"Cc". We can figure this out from the "udict" structure that we created 
above. Specifically, we need to check if the third entry in the udict
structure is "Cc" for this codepoint.

'''

#
### BEGIN CODE ###
#
# code to determine if a codepoint is in the Controls category
#
def isControls(cp):
    item = udict[cp]
    if item[2] in ('Cc',):
        return 1
#
### END CODE ###
#

'''

3.8 OldHangulJamo

The OldHangulJamo characters are older Korean characters that are no
longer used in modern Korean. The data we need here can be found in the
HangulSyllableType.txt file from the Unicode Character Database.


'''

#
### BEGIN CODE ###
#
# code to pull in the HangulSyllableType.txt file
# each line in the file becomes an entry in the dictionary
#
hstdict = {};
with open('HangulSyllableType.txt') as f:  
    for line in f: 
        data = line.split(';');
        hstdict[data[0]] = data;
# 
# we care only about lines that define Hangul Syllable Types of 
# Leading_Jamo, Vowel_Jamo, and Trailing_Jamo
#
# therefore we create a list of such codepoints
# 
ohj = [];
for v in hstdict.itervalues():
   if len(v) > 1:
       secondvalue = v[1] + "";
       if secondvalue.startswith(' L #') or secondvalue.startswith(' V #') or secondvalue.startswith(' T #'):
           firstvalue = v[0] + "";
           firstvalue = firstvalue.strip();
           therange = firstvalue.split('..');
           rangestart = therange[0];
           rangeend = therange[1];
           intbottom = int(rangestart,16);
           inttop = int(rangeend,16) + 1;
           thisrange = range(intbottom, inttop, 1);
           for i in thisrange:
               ohj.append(i)
#
# define a function to determine if a codepoint is OldHangulJamo
#
def isOldHangulJamo(cp):
    item = udict[cp]
    itemint = int(item[0],16)
    if itemint in ohj:
        return 1
#
### END CODE ###
#

'''

3.9 LetterDigits

A LetterDigits character is any codepoint with a Unicode General_Category of
"Ll", "Lu", "Lm", "Lo", "Mn", "Mc", or "Nd". We can figure this out from the 
"udict" structure that we created above.

'''

#
### BEGIN CODE ###
#
# define a function to determine if a codepoint is in LetterDigits
#
def isLetterDigits(cp):
    item = udict[cp]
    if item[2] in ('Ll', 'Lu', 'Lm', 'Lo', 'Mn', 'Mc', 'Nd'):
        return 1
#
### END CODE ###
#

'''

3.10 OtherLetterDigits

An OtherLetterDigits character is any codepoint with a Unicode 
General_Category of "Lt", "Nl", "No", or "Me". We can figure this out from 
the "udict" structure that we created above.

'''

#
### BEGIN CODE ###
#
# define a function to determine if a codepoint is in OtherLetterDigits
#
def isOtherLetterDigits(cp):
    item = udict[cp]
    if item[2] in ('Lt', 'Nl', 'No', 'Me'):
        return 1
#
### END CODE ###
#

'''

3.11 Spaces

A Spaces character is any codepoint with a Unicode General_Category of
"Zs". We can figure this out from the "udict" structure that we created 
above.

'''

#
### BEGIN CODE ###
#
# define a function to determine if a codepoint is in Spaces
#
def isSpaces(cp):
    item = udict[cp]
    if item[2] in ('Zs',):
        return 1
#
### END CODE ###
#

'''

3.12 Symbols

A Symbols character is any codepoint with a Unicode General_Category of
"Sm", "Sc", "Sk", or "So". We can figure this out from the "udict" 
structure that we created above.

'''

#
### BEGIN CODE ###
#
# define a function to determine if a codepoint is in Symbols
#
def isSymbols(cp):
    item = udict[cp]
    if item[2] in ('Sm', 'Sc', 'Sk', 'So'):
        return 1
#
### END CODE ###
#

'''

3.13 Punctuation

A Punctuation character is any codepoint with a Unicode General_Category 
of "Pc", "Pd", "Ps", "Pe", "Pi", "Pf", or "Po". We can figure this out 
from the "udict" structure that we created above.

'''

#
### BEGIN CODE ###
#
# define a function to determine if a codepoint is in Punctuation
#
def isPunctuation(cp):
    item = udict[cp]
    if item[2] in ('Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po'):
        return 1
#
### END CODE ###
#

'''

3.14 HasCompat

It's complicated. ;-) However, we can determine whether a character has
a compatibility equivalent from the "udict" structure that we created
above.

One way to determine if a character has a compatibility equivalent is to
run the NFKC normalization routine on the character: if the output of
NFKC (which might be one or more codepoints) is different from the 
codepoint we used as input, then the character is in HasCompat.

However, using Unicode Normalization Form KC (NFKC) is dependent on
having an NFKC function. For the purposes of PrecisMaker, we prefer to
use only the raw files from the Unicode Character Database (ucd).

Thankfully, we can figure out if a code point has a compatibility
equivalent by looking in the "udict" structure. Consider the character
"VULGAR FRACTION ONE QUARTER" (why it's vulgar I have no idea). The line
in UnicodeData.txt for this codepoint starts out like so:

00BC;VULGAR FRACTION ONE QUARTER;No;0;ON;<fraction> 0031 2044 0034;

The sixth entry in this line tells us that codepoint 00BC is 
compatibly equivalent to the codepoints 0031 2044 0034, i.e.:

0031;DIGIT ONE
2044;FRACTION SLASH
0034;DIGIT FOUR

This entry also tells us the specific type of compatibility equivalence, 
in this case "<fraction>". In addition to the generic "<compat>" type,
there are several specific types:

o <circle>
o <final>
o <font>
o <fraction>
o <initial>
o <isolated>
o <medial>
o <noBreak>
o <narrow>
o <small>
o <square>
o <super>
o <sub>
o <vertical>
o <wide>

Thus a crude way to guess if a codepoint is compatibly equivalent to
another codepoint (or sequence of codepoints) is to to look for the
compatibility type in the sixth entry of each line. That's what we do in
PrecisMaker right now, although the method might be improved in a future
version after we've carefully checked the output of the current version.

'''

#
### BEGIN CODE ###
#
# define a function to determine if a codepoint is in HasCompat
#
def isHasCompat(cp):
    item = udict[cp]
    if item[5].startswith('<'):
        return 1
#
### END CODE ###
#

'''

###

4. Running the Algorithm

Now that we have the data we need, we can run the algorithm. Here is the
pseudocode from the PRECIS framework specification.

   If .cp. .in. Exceptions Then Exceptions(cp);
   Else If .cp. .in. BackwardCompatible Then BackwardCompatible(cp);
   Else If .cp. .in. Unassigned Then UNASSIGNED;
   Else If .cp. .in. ASCII7 Then PVALID;
   Else If .cp. .in. JoinControl Then CONTEXTJ;
   Else If .cp. .in. OldHangulJamo Then DISALLOWED;
   Else If .cp. .in. PrecisIgnorableProperties Then DISALLOWED;
   Else If .cp. .in. Controls Then DISALLOWED;
   Else If .cp. .in. HasCompat Then SAFE_DIS or FREE_PVAL;
   Else If .cp. .in. LetterDigits Then PVALID;
   Else If .cp. .in. OtherLetterDigits Then SAFE_DIS or FREE_PVAL;
   Else If .cp. .in. Spaces Then SAFE_DIS or FREE_PVAL;
   Else If .cp. .in. Symbols Then SAFE_DIS or FREE_PVAL;
   Else If .cp. .in. Punctuation Then SAFE_DIS or FREE_PVAL;
   Else DISALLOWED;

'''

#
### BEGIN CODE ###
#
# code to determine the status of each codepoint
#
# first create a dictionary specifying the status of each codepoint
#
status = {};
#
# create a range of all possible codepoints (even the ones that have not
# yet been assigned); note that the range is a range of integers, so we
# will need to convert them back to hex below...
#
firstcp = "0000";
lastcp = "10FFFD";
intfirst = int(firstcp,16);
intlast = int(lastcp,16);
urange = range(intfirst, intlast, 1);
#
# here we iterate through all the codepoints and, for each one, call a
# series of functions that tell us whether the codepoint is in the 
# relevant PRECIS category
#
for p in urange:
    # convert each integer to hex
    phex = hex(p);
    # for Unicode purposes we don't want the leading "0x"
    phex = phex.replace('0x','');
    # also, our codepoint numbers need at least 4 digits
    phex = phex.rjust(4,'0')
    # just to be safe, make sure all alpha characters are uppercase
    cp = phex.swapcase();
    # now that we have the codepoint, check each PRECIS category
    if isExceptions(cp) == 1:
        status[cp] = exceptions[cp]
        if debug == 1: print "U+" + cp + " is " + status[cp] + " (Exceptions)";
    #elif isBackwardCompatible(cp) == 1:        # no-op for now
    elif isUnassigned(cp) == 1:
        status[cp] = "UNASSIGNED"
        if debug == 1: print "U+" + cp + " is " + status[cp];
    elif isASCII7(cp) == 1:
        status[cp] = "PVALID"
        if debug == 1: print "U+" + cp + " is " + status[cp] + " (ASCII7)";
    elif isJoinControl(cp) == 1:
        status[cp] = "CONTEXTJ"
        if debug == 1: print "U+" + cp + " is " + status[cp] + " (JoinControl)";
    #
    # NOTE: PrecisMaker provisionally performs OldHangulJamo checking before
    # PrecisIgnorableProperties checking. This order is different from the 
    # PRECIS framework specification. I have raised this issue on the
    # precis@ietf.org discussion list.
    #
    elif isOldHangulJamo(cp) == 1:
        status[cp] = "DISALLOWED"
        if debug == 1: print "U+" + cp + " is " + status[cp] + " (OldHangulJamo)";
    elif isPrecisIgnorableProperties(cp) == 1:
        status[cp] = "DISALLOWED"
        if debug == 1: print "U+" + cp + " is " + status[cp] + " (PrecisIgnorableProperties)";
    elif isControls(cp) == 1:
        status[cp] = "DISALLOWED"
        if debug == 1: print "U+" + cp + " is " + status[cp] + " (Controls)";
    #
    # NOTE: PrecisMaker provisionally performs HasCompat checking before
    # LetterDigits. This order is different from the PRECIS framework
    # specification, which performs HasCompat checking last. The results
    # using the specified order seem wrong. I have raised this issue on
    # the precis@ietf.org discussion list.
    #
    elif isHasCompat(cp) == 1:
        status[cp] = "FREE_PVAL"
        # additional lines for debugging
        item = udict[cp]
        compat = item[5]
        cdata = compat.split('>');
        ctype = cdata[0]
        cpoints = cdata[1]
        if debug == 1: print "U+" + cp + " is " + status[cp] + " (compatibility equivalence of type " + ctype + "> to the codepoint(s)" + cpoints + ")";
    elif isLetterDigits(cp) == 1:
        status[cp] = "PVALID"
        if debug == 1: print "U+" + cp + " is " + status[cp] + " (LetterDigits)";
    elif isOtherLetterDigits(cp) == 1:
        status[cp] = "FREE_PVAL"
        if debug == 1: print "U+" + cp + " is " + status[cp] + " (OtherLetterDigits)";
    elif isSpaces(cp) == 1:
        status[cp] = "FREE_PVAL"
        if debug == 1: print "U+" + cp + " is " + status[cp] + " (Spaces)";
    elif isSymbols(cp) == 1:
        status[cp] = "FREE_PVAL"
        if debug == 1: print "U+" + cp + " is " + status[cp] + " (Symbols)";
    elif isPunctuation(cp) == 1:
        status[cp] = "FREE_PVAL"
        if debug == 1: print "U+" + cp + " is " + status[cp] + " (Punctuation)";
    else:
        status[cp] = "DISALLOWED"
        if debug == 1: print "U+" + cp + " is " + status[cp] + " by default";
#
### END CODE ###
#

'''

###

5. Acknowledgements

Many thanks to Lance Stout for his suggestions regarding Python syntax
and style.

'''

# THE END 
