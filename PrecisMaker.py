" " "

PRECIS Maker
by Peter Saint-Andre / stpeter@stpeter.im

This is version 0.1, last updated 2013-05-08.

And yes, this is an experiment in literate programming. :-)

" " "

Introduction

Internationalization is hard. Heck, even the word itself is hard, which 
is why people shorten it to "i18n" (the letter "i", followed by 18 more
letters, followed by the letter "n"). I even wrote a big presentation 
about it once: "Internationalization, A Guide for the Perplexed".

Anyway, folks at the Internet Engineering Task Force (IETF) have been
working to make internationalization easier, building on the foundation
laid by the Unicode Consortium. The IETF work is focused on enabling
Internet protocols like email and the Domain Name System (DNS) to
include characters outside the ASCII range. Personally, I care about
this topic because the instant messaging technology I work on, called
Jabber or XMPP, also supports fully internationalized identifiers for
people, servers, and other components on the network.

The DNS work came in two phases (called IDNA2003 and IDNA2008).  One
spinoff from IDNA2003 was a generalized framework for i18n called
"stringprep". Unfortunately, stringprep didn't work so well in practice,
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

" " "

### CODE ###
# Code to invoke the Python interpreter
#!/usr/bin/env python
### CODE ###

" " "

Method

The PRECIS framework specification defines our procedure:

https://datatracker.ietf.org/doc/draft-ietf-precis-framework/

Here's what we need to do: for each codepoint in Unicode, determine
whether it is valid, disallowed, or unassigned for PRECIS in general,
whether a contextual rule is required to determine the status of the
codepoint, or whether the codepoint is valid or disallowed for a
particular string class.

There are two string classes in PRECIS: the IdentifierClass and the
FreeformClass. The IdentifierClass is a restricted class that allows
only letters and digits (plus all of the characters from the ASCII
range). The FreeformClass is more loose, since it disallows only control
characters and some other so-called ignorable code points.

Since there are only two string classes and the IdentifierClass is a
strict subset of the FreeformClass, a codepoint is valid for all of
PRECIS if it is valid for the IdentifierClass and a codepoint is
disallowed if it is disallowed for the FreeformClass. Therefore, we
really need to determine whether a codepoint is one of the following:
protocol-valid (PVAL), disallowed, unassigned, contextual (which can be
either CONTEXTJ or CONTEXTO), or protocol-valid for the FreeformClass
(FREE_PVAL) and thus disallowed for the IdentifierClass.

In order to achieve those goals, we will need to read information from 
various files in the Unicode Character Database ("ucd"), slice and dice
that information in various ways to determine the properties of each
codepoint, and output an XML file that matches the format produced by
the createtables script.

Thankfully, the Python language contains core libraries that enable
those functions. Therefore we import the relevant libraries.

" " "

### CODE ###
# Code to import the code libraries we need
import os
import sys
import xml.dom.minidom
### CODE ###

" " "
