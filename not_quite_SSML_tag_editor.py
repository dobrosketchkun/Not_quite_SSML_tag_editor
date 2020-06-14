
"""
Based on PyEdit 2.1: a Python/tkinter text file editor
"""

Version = '0.1'
PyEdit_version = '2.1'

import re
import urllib.parse
import requests
from time import time

import sys, os                                    # platform, args, run tools
from tkinter import *                             # base widgets, constants
from tkinter.filedialog   import Open, SaveAs     # standard dialogs
from tkinter.messagebox   import showinfo, showerror, askyesno
from tkinter.simpledialog import askstring, askinteger
from tkinter.colorchooser import askcolor

from guimaker import * 


try:
    import textConfig                        # startup font and colors
    configs = textConfig.__dict__            # work if not on the path or bad
except:                                      # define in client app directory 
    configs = {}


helptext = """
Based on PyEdit version 2.1

Small SSML-based tag editor (IBM flavor)

Break = **{500}** = <break time="500ms"> #Pause 500ms

Pitch Hz = [[{150h}...]] = <prosody pitch="150Hz">...</prosody> #Transpose pitch to 150 Hz

or [[{-20h}...]] == <prosody pitch="150Hz">...</prosody> #Lower pitch by 20 Hz from baseline

Pitch st = [[{-12s}...]] == <prosody pitch="-12st">...</prosody> #Lower pitch by 12 semitones from baseline

Rate words = [{50w}...]] ==  <prosody rate="50">...</prosody> #Set speaking rate at 50 words per minute

Rate % = [[{50%}...]] == <prosody rate="+5%">...</prosody> #Increase speaking rate by 5 percent

Number = ##{nu}...## == <say-as interpret-as="cardinal">...</say-as> #three

Ordinal = ##{no}...## == <say-as interpret-as="number" format="ordinal">...</say-as> #third

Tel. - ##{nt}...##== <say-as interpret-as="number" format="telephone">...</say-as> #555-555-5555

Digits = ##{di}...## == <say-as interpret-as="digits">...</say-as> #one two three four

Letters = ##{l}...## == <say-as interpret-as="letters">Hello</say-as>

Date f = ##{dfXXX}...## == <say-as interpret-as="date" format="XXX">...</say-as> #12/17/2005 - XXX: mdy

Date vx = ##{vxd}...## ==   <say-as interpret-as="vxml:date">...</say-as> #20050720, ????0720, 200507??

Currency = ##{vxc}...## == <say-as interpret-as="vxml:currency">...</say-as> #USD45.30

IPA = ##{ipa}...## == <phoneme alphabet="ipa" ph="..."></phoneme> #təmˈɑto
"""


START     = '1.0'                          # index of first char: row=1,col=0
SEL_FIRST = SEL + '.first'                 # map sel tag to index
SEL_LAST  = SEL + '.last'                  # same as 'sel.last'

FontScale = 0                              # use bigger font on Linux
if sys.platform[:3] != 'win':              # and other non-Windows boxes
    FontScale = 3



shorts = {'break': {'pattern': "\*\*{\d*}\*\*", 'left' : '<break time="', 'middle' : 'ms"/>','right' : ''},
			'prosody_pitch_h': {'pattern': "\[\[\{.{0,1}\d{1,4}h(.*?)\]\]", 'left' : '<prosody pitch="', 'middle' : 'Hz">', 'right' : '</prosody>'},
			'prosody_pitch_s': {'pattern': "\[\[\{.{0,1}\d{1,4}s(.*?)\]\]", 'left' : '<prosody pitch="', 'middle' : 'st">', 'right' : '</prosody>'},
			'prosody_rate_w': {'pattern': "\[\[\{.{0,1}\d{1,4}w(.*?)\]\]", 'left' : '<prosody rate="', 'middle' : '">', 'right' : '</prosody>'},
			'prosody_rate_perc': {'pattern': "\[\[\{.{0,1}\d{1,4}\%(.*?)\]\]", 'left' : '<prosody rate="', 'middle' : '%">', 'right' : '</prosody>'},
			'say_as_number': {'pattern': "##\{nu(.*?)##", 'left' : '<say-as interpret-as="cardinal">', 'middle' : '','right' : '</say-as> '},
			'say_as_number_ordinal': {'pattern': "##\{no(.*?)##", 'left' : '<say-as interpret-as="number" format="ordinal">', 'middle' : '','right' : '</say-as>'},
			'say_as_number_tel': {'pattern': "##\{nt(.*?)##", 'left' : '<say-as interpret-as="number" format="telephone">', 'middle' : '','right' : '</say-as>'},
			'say_as_number_digit': {'pattern': "##\{di(.*?)##", 'left' : '<say-as interpret-as="digits">', 'middle' : '','right' : '</say-as>'},
			'say_as_letters': {'pattern': "##\{l(.*?)##", 'left' : '<say-as interpret-as="letters">', 'middle' : '','right' : '</say-as>'},
			'say_as_date': {'pattern': "##\{df\D{1,3}\}(.*)##", 'left' : '<say-as interpret-as="date" format="', 'middle' : '">','right' : '</say-as>'},
			'say_as_currency': {'pattern': "##\{vxc(.*?)##", 'left' : '<say-as interpret-as="vxml:currency">', 'middle' : '','right' : '</say-as>'},
			'say_as_vdate': {'pattern': "##\{vxd(.*?)##", 'left' : '<say-as interpret-as="vxml:currency">', 'middle' : '','right' : '</say-as>'},
			'phoneme': {'pattern': "##\{ipa(.*?)##", 'left' : '<phoneme alphabet="ipa" ph="', 'middle' : '','right' : '"></phoneme>'},}


def decode(text):

	isNotIdentical = True
	temp_text = ''

	while isNotIdentical:
		temp_text = text
		for key in shorts.keys():
			result = re.search(shorts[key]['pattern'], text)
			#print('result',result)
			if result:
				s_left, s_right = result.span()
				left, part, right = text[:s_left], text[s_left:s_right][2:-2], text[s_right:]
				# print([left, part, right])
				#print(part)
				new_part, additional = part.split('}')
				
				if 'break' in key:
					# new_part = new_part[1:]
					new_part = shorts[key]['left'] + new_part[1:] + shorts[key]['middle'] + additional + shorts[key]['right']
					text = left + new_part + right
				if 'prosody' in key:
					new_part = new_part[:-1]
					new_part = shorts[key]['left'] + new_part[1:] + shorts[key]['middle'] + additional + shorts[key]['right']
					text = left + new_part + right
				if 'say_as' in key:
					new_part = shorts[key]['left'] + shorts[key]['middle'] + additional + shorts[key]['right']
					text = left + new_part + right
				if 'phoneme' in key:
					new_part = shorts[key]['left'] + shorts[key]['middle'] + additional + shorts[key]['right']
					text = left + new_part + right
		if text == temp_text:
			isNotIdentical = False

	voice = 'en-US_AllisonV3Voice' # Specific TTS voice

	url = "https://text-to-speech-demo.ng.bluemix.net/api/v3/synthesize?text=" +\
			urllib.parse.quote(text) +\
			"&voice=" + voice + "&ssmlLabel=SSML&download=true&accept=audio%2Fmp3"

	print('url: ', url, '\n')

	r = requests.get(url, allow_redirects=True)

	with open(str(int(time())) + '.mp3', 'wb+') as f:
		f.write(r.content)
	
	return text




################################################################################
# Main class: implements editor GUI, actions
# requires a flavor of GuiMaker to be mixed in by more specific subclasses;
# not a direct subclass of GuiMaker because that class takes multiple forms.
################################################################################

class TextEditor:                        # mix with menu/toolbar Frame class
    startfiledir = '.'                   # for dialogs
    editwindows  = []                    # for process-wide quit check

    # Unicode configurations
    # imported in class to allow overrides in subclass or self
    if __name__ == '__main__':
        from textConfig import (               # my dir is on the path
            opensAskUser, opensEncoding,
            savesUseKnownEncoding, savesAskUser, savesEncoding)
    else:
        from .textConfig import (              # 2.1: always from this package
            opensAskUser, opensEncoding,
            savesUseKnownEncoding, savesAskUser, savesEncoding)

    ftypes = [('All files',     '*'),                 # for file open dialog
              ('Text files',   '.txt')]               # customize in subclass


    colors = [{'fg':'black',      'bg':'white'},      # color pick list
              {'fg':'yellow',     'bg':'black'},      # first item is default
              {'fg':'white',      'bg':'blue'},       # tailor me as desired
              {'fg':'black',      'bg':'beige'},      # or do PickBg/Fg chooser
              {'fg':'yellow',     'bg':'purple'},
              {'fg':'black',      'bg':'brown'},
              {'fg':'lightgreen', 'bg':'darkgreen'},
              {'fg':'darkblue',   'bg':'orange'},
              {'fg':'orange',     'bg':'darkblue'}]

    fonts  = [('courier',    9+FontScale, 'normal'),  # platform-neutral fonts
              ('courier',   12+FontScale, 'normal'),  # (family, size, style)
              ('courier',   10+FontScale, 'bold'),    # or pop up a listbox
              ('courier',   10+FontScale, 'italic'),  # make bigger on Linux
              ('times',     10+FontScale, 'normal'),  # use 'bold italic' for 2
              ('helvetica', 10+FontScale, 'normal'),  # also 'underline', etc.
              ('ariel',     10+FontScale, 'normal'),
              ('system',    10+FontScale, 'normal'),
              ('courier',   20+FontScale, 'normal')]

    def __init__(self, loadFirst='', loadEncode=''):
        if not isinstance(self, GuiMaker):
            raise TypeError('TextEditor needs a GuiMaker mixin')
        self.setFileName(None)
        self.lastfind   = None
        self.openDialog = None
        self.saveDialog = None
        self.knownEncoding = None                   # 2.1 Unicode: till Open or Save
        self.text.focus()                           # else must click in text
        if loadFirst:
            self.update()                           # 2.1: else @ line 2; see book
            self.onOpen(loadFirst, loadEncode)

    def start(self):                                # run by GuiMaker.__init__
        self.menuBar = [                            # configure menu/toolbar
            ('File', 0,                             # a GuiMaker menu def tree
                 [('Open...',    0, self.onOpen),   # build in method for self
                  ('Save',       0, self.onSave),   # label, shortcut, callback
                  ('Save As...', 5, self.onSaveAs),
                  ('New',        0, self.onNew),
                  'separator',
                  ('Quit...',    0, self.onQuit)]
            ),
            ('Edit', 0,
                 [('Undo',       0, self.onUndo),
                  ('Redo',       0, self.onRedo),
                  'separator',
                  ('Cut',        0, self.onCut),
                  ('Copy',       1, self.onCopy),
                  ('Paste',      0, self.onPaste),
                  'separator',
                  ('Delete',     0, self.onDelete),
                  ('Select All', 0, self.onSelectAll)]
            ),
            ('Search', 0,
                 [('Goto...',    0, self.onGoto),
                  ('Find...',    0, self.onFind),
                  ('Refind',     0, self.onRefind),
                  ('Change...',  0, self.onChange)#,('Grep...',    3, self.onGrep)
                  ]
            ),
            ('Tools', 0,
                 [('Pick Font...', 6, self.onPickFont),
                  ('Font List',    0, self.onFontList),
                  'separator',
                  ('Pick Bg...',   3, self.onPickBg),
                  ('Pick Fg...',   0, self.onPickFg),
                  ('Color List',   0, self.onColorList),
                  'separator',
                  ('Info...',      0, self.onInfo),
                  ('Clone',        1, self.onClone)#,('Run Code',     0, self.onRunCode)
                  ]
            )]
        self.toolBar = [
            ('Break', self.break_tag,  {'side': LEFT}),

            ('Pitch Hz',  self.prosody_pitch_h,   {'side': LEFT}),
            ('Pitch st',  self.prosody_pitch_s,   {'side': LEFT}),
            ('Rate words',  self.prosody_pitch_w,   {'side': LEFT}),
            ('Rate %',  self.prosody_pitch_r,   {'side': LEFT}),

            ('Number',  self.say_as_nu,   {'side': LEFT}),
            ('Ordinal',  self.say_as_no,   {'side': LEFT}),
            ('Tel.',  self.say_as_nt,   {'side': LEFT}),
            ('Digits',  self.say_as_di,   {'side': LEFT}),
            ('Letters',  self.say_as_l,   {'side': LEFT}),
            ('Date f',  self.say_as_df,   {'side': LEFT}),
            ('Date vx',  self.say_as_vxd,   {'side': LEFT}),
            ('Currency',  self.say_as_vxc,   {'side': LEFT}),
            ('IPA',  self.say_as_ipa,   {'side': LEFT}),

            # 'separator',
            ('TTS',  self.decode_and_download, {'side': RIGHT}),
            # 'separator',
            ('Help',  self.help,     {'side': RIGHT}),
            ('Quit',  self.onQuit,   {'side': RIGHT})]

    def makeWidgets(self):                          # run by GuiMaker.__init__
        name = Label(self, bg='black', fg='white')  # add below menu, above tool
        name.pack(side=TOP, fill=X)                 # menu/toolbars are packed
                                                    # GuiMaker frame packs itself
        vbar  = Scrollbar(self)
        hbar  = Scrollbar(self, orient='horizontal')
        text  = Text(self, padx=5, wrap='word')        # disable line wrapping
        text.config(undo=1, autoseparators=1)          # 2.0, default is 0, 1

        vbar.pack(side=RIGHT,  fill=Y)
        hbar.pack(side=BOTTOM, fill=X)                 # pack text last
        text.pack(side=TOP,    fill=BOTH, expand=YES)  # else sbars clipped

        text.config(yscrollcommand=vbar.set)    # call vbar.set on text move
        text.config(xscrollcommand=hbar.set)
        vbar.config(command=text.yview)         # call text.yview on scroll move
        hbar.config(command=text.xview)         # or hbar['command']=text.xview

        # 2.0: apply user configs or defaults
        startfont = configs.get('font', self.fonts[0])
        startbg   = configs.get('bg',   self.colors[0]['bg'])
        startfg   = configs.get('fg',   self.colors[0]['fg'])
        text.config(font=startfont, bg=startbg, fg=startfg)
        if 'height' in configs: text.config(height=configs['height'])
        if 'width'  in configs: text.config(width =configs['width'])
        self.text = text
        self.filelabel = name


    ############################################################################
    # File menu commands
    ############################################################################

    def my_askopenfilename(self):      # objects remember last result dir/file
        if not self.openDialog:
           self.openDialog = Open(initialdir=self.startfiledir,
                                  filetypes=self.ftypes)
        return self.openDialog.show()

    def my_asksaveasfilename(self):    # objects remember last result dir/file
        if not self.saveDialog:
           self.saveDialog = SaveAs(initialdir=self.startfiledir,
                                    filetypes=self.ftypes)
        return self.saveDialog.show()

    def onOpen(self, loadFirst='', loadEncode=''):
        """
        2.1: total rewrite for Unicode support; open in text mode with 
        an encoding passed in, input from the user, in textconfig, or  
        platform default, or open as binary bytes for arbitrary Unicode
        encodings as last resort and drop \r in Windows end-lines if 
        present so text displays normally; content fetches are returned
        as str, so need to  encode on saves: keep encoding used here;

        tests if file is okay ahead of time to try to avoid opens;
        we could also load and manually decode bytes to str to avoid 
        multiple open attempts, but this is unlikely to try all cases;

        encoding behavior is configurable in the local textConfig.py:
        1) tries known type first if passed in by client (email charsets)
        2) if opensAskUser True, try user input next (prefill wih defaults)
        3) if opensEncoding nonempty, try this encoding next: 'latin-1', etc.
        4) tries sys.getdefaultencoding() platform default next
        5) uses binary mode bytes and Tk policy as the last resort
        """

        if self.text_edit_modified():    # 2.0
            if not askyesno('SSMLtagEdit', 'Text has changed: discard changes?'):
                return

        file = loadFirst or self.my_askopenfilename()
        if not file: 
            return
        
        if not os.path.isfile(file):
            showerror('SSMLtagEdit', 'Could not open file ' + file)
            return

        # try known encoding if passed and accurate (e.g., email)
        text = None     # empty file = '' = False: test for None!
        if loadEncode:
            try:
                text = open(file, 'r', encoding=loadEncode).read()
                self.knownEncoding = loadEncode
            except (UnicodeError, LookupError, IOError):         # lookup: bad name
                pass

        # try user input, prefill with next choice as default
        if text == None and self.opensAskUser:
            self.update()  # else dialog doesn't appear in rare cases
            askuser = askstring('SSMLtagEdit', 'Enter Unicode encoding for open',
                                initialvalue=(self.opensEncoding or 
                                              sys.getdefaultencoding() or ''))
            self.text.focus() # else must click
            if askuser:
                try:
                    text = open(file, 'r', encoding=askuser).read()
                    self.knownEncoding = askuser
                except (UnicodeError, LookupError, IOError):
                    pass

        # try config file (or before ask user?)
        if text == None and self.opensEncoding:
            try:
                text = open(file, 'r', encoding=self.opensEncoding).read()
                self.knownEncoding = self.opensEncoding
            except (UnicodeError, LookupError, IOError):
                pass

        # try platform default (utf-8 on windows; try utf8 always?)
        if text == None:
            try:
                text = open(file, 'r', encoding=sys.getdefaultencoding()).read()
                self.knownEncoding = sys.getdefaultencoding()
            except (UnicodeError, LookupError, IOError):
                pass

        # last resort: use binary bytes and rely on Tk to decode
        if text == None:
            try:
                text = open(file, 'rb').read()         # bytes for Unicode
                text = text.replace(b'\r\n', b'\n')    # for display, saves
                self.knownEncoding = None
            except IOError:
                pass

        if text == None:
            showerror('SSMLtagEdit', 'Could not decode and open file ' + file)
        else:
            self.setAllText(text)
            self.setFileName(file)
            self.text.edit_reset()             # 2.0: clear undo/redo stks
            self.text.edit_modified(0)         # 2.0: clear modified flag

    def onSave(self):
        self.onSaveAs(self.currfile)  # may be None

    def onSaveAs(self, forcefile=None):
        """
        2.1: total rewrite for Unicode support: Text content is always 
        returned as a str, so we must deal with encodings to save to
        a file here, regardless of open mode of the output file (binary
        requires bytes, and text must encode); tries the encoding used
        when opened or saved (if known), user input, config file setting,
        and platform default last; most users can use platform default; 

        retains successful encoding name here for next save, because this
        may be the first Save after New or a manual text insertion;  Save
        and SaveAs may both use last known encoding, per config file (it
        probably should be used for Save, but SaveAs usage is unclear);
        gui prompts are prefilled with the known encoding if there is one;
        
        does manual text.encode() to avoid creating file; text mode files
        perform platform specific end-line conversion: Windows \r dropped 
        if present on open by text mode (auto) and binary mode (manually);
        if manual content inserts, must delete \r else duplicates here;
        knownEncoding=None before first Open or Save, after New, if binary Open;

        encoding behavior is configurable in the local textConfig.py:
        1) if savesUseKnownEncoding > 0, try encoding from last open or save
        2) if savesAskUser True, try user input next (prefill with known?)
        3) if savesEncoding nonempty, try this encoding next: 'utf-8', etc
        4) tries sys.getdefaultencoding() as a last resort
        """

        filename = forcefile or self.my_asksaveasfilename()
        if not filename:
            return

        text = self.getAllText()      # 2.1: a str string, with \n eolns,
        encpick = None                # even if read/inserted as bytes 

        # try known encoding at latest Open or Save, if any
        if self.knownEncoding and (                                  # enc known?
           (forcefile     and self.savesUseKnownEncoding >= 1) or    # on Save?
           (not forcefile and self.savesUseKnownEncoding >= 2)):     # on SaveAs?
            try:
                text.encode(self.knownEncoding)
                encpick = self.knownEncoding
            except UnicodeError:
                pass

        # try user input, prefill with known type, else next choice
        if not encpick and self.savesAskUser:
            self.update()  # else dialog doesn't appear in rare cases
            askuser = askstring('SSMLtagEdit', 'Enter Unicode encoding for save',
                                initialvalue=(self.knownEncoding or 
                                              self.savesEncoding or 
                                              sys.getdefaultencoding() or ''))
            self.text.focus() # else must click
            if askuser:
                try:
                    text.encode(askuser)
                    encpick = askuser
                except (UnicodeError, LookupError):    # LookupError:  bad name 
                    pass                               # UnicodeError: can't encode

        # try config file
        if not encpick and self.savesEncoding:
            try:
                text.encode(self.savesEncoding)
                encpick = self.savesEncoding
            except (UnicodeError, LookupError):
                pass

        # try platform default (utf8 on windows)
        if not encpick:
            try:
                text.encode(sys.getdefaultencoding())
                encpick = sys.getdefaultencoding()
            except (UnicodeError, LookupError):
                pass

        # open in text mode for endlines + encoding
        if not encpick:
            showerror('SSMLtagEdit', 'Could not encode for file ' + filename)
        else:
            try:
                file = open(filename, 'w', encoding=encpick)
                file.write(text)
                file.close()
            except:
                showerror('SSMLtagEdit', 'Could not write file ' + filename)
            else:
                self.setFileName(filename)          # may be newly created
                self.text.edit_modified(0)          # 2.0: clear modified flag
                self.knownEncoding = encpick        # 2.1: keep enc for next save
                                                    # don't clear undo/redo stks!
    def onNew(self):
        """
        start editing a new file from scratch in current window;
        see onClone to pop-up a new independent edit window instead;
        """
        if self.text_edit_modified():    # 2.0
            if not askyesno('SSMLtagEdit', 'Text has changed: discard changes?'):
                return
        self.setFileName(None)
        self.clearAllText()
        self.text.edit_reset()                 # 2.0: clear undo/redo stks
        self.text.edit_modified(0)             # 2.0: clear modified flag
        self.knownEncoding = None              # 2.1: Unicode type unknown

    def onQuit(self):
        """
        on Quit menu/toolbar select and wm border X button in toplevel windows;
        2.1: don't exit app if others changed;  2.0: don't ask if self unchanged;
        moved to the top-level window classes at the end since may vary per usage:
        a Quit in GUI might quit() to exit, destroy() just one Toplevel, Tk, or 
        edit frame, or not be provided at all when run as an attached component;
        check self for changes, and if might quit(), main windows should check
        other windows in the process-wide list to see if they have changed too; 
        """
        assert False, 'onQuit must be defined in window-specific sublass' 

    def text_edit_modified(self):
        """
        2.1: this now works! seems to have been a bool result type issue in tkinter;
        2.0: self.text.edit_modified() broken in Python 2.4: do manually for now; 
        """
        return self.text.edit_modified()
       #return self.tk.call((self.text._w, 'edit') + ('modified', None))


    ############################################################################
    # Edit menu commands
    ############################################################################

    def onUndo(self):                           # 2.0
        try:                                    # tk8.4 keeps undo/redo stacks
            self.text.edit_undo()               # exception if stacks empty
        except TclError:                        # menu tear-offs for quick undo
            showinfo('SSMLtagEdit', 'Nothing to undo')

    def onRedo(self):                           # 2.0: redo an undone
        try:
            self.text.edit_redo()
        except TclError:
            showinfo('SSMLtagEdit', 'Nothing to redo')

    def onCopy(self):                           # get text selected by mouse, etc.
        if not self.text.tag_ranges(SEL):       # save in cross-app clipboard
            showerror('SSMLtagEdit', 'No text selected')
        else:
            text = self.text.get(SEL_FIRST, SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(text)

    def onDelete(self):                         # delete selected text, no save
        if not self.text.tag_ranges(SEL):
            showerror('SSMLtagEdit', 'No text selected')
        else:
            self.text.delete(SEL_FIRST, SEL_LAST)

    def onCut(self):
        if not self.text.tag_ranges(SEL):
            showerror('SSMLtagEdit', 'No text selected')
        else:
            self.onCopy()                       # save and delete selected text
            self.onDelete()

    def onPaste(self):
        try:
            text = self.selection_get(selection='CLIPBOARD')
        except TclError:
            showerror('SSMLtagEdit', 'Nothing to paste')
            return
        self.text.insert(INSERT, text)          # add at current insert cursor
        self.text.tag_remove(SEL, '1.0', END)
        self.text.tag_add(SEL, INSERT+'-%dc' % len(text), INSERT)
        self.text.see(INSERT)                   # select it, so it can be cut


    def onSelectAll(self):
        self.text.tag_add(SEL, '1.0', END+'-1c')   # select entire text
        self.text.mark_set(INSERT, '1.0')          # move insert point to top
        self.text.see(INSERT)                      # scroll to top


    ############################################################################
    # SSML tags and TTS functhins
    ############################################################################
    def break_tag(self):

            text = '**{50}**'
            self.text.insert(INSERT, text)          # add at current insert cursor
            self.text.tag_remove(SEL, '1.0', END)
            self.text.tag_add(SEL, INSERT+'-%dc' % len(text), INSERT)
            self.text.see(INSERT)                   # select it, so it can be cut


    def prosody_pitch_h(self):
        if not self.text.tag_ranges(SEL):       # save in cross-app clipboard
            showerror('SSMLtagEdit', 'No text selected')
        else:
            text = self.text.get(SEL_FIRST, SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(text)

            self.onDelete()

            text = '[[{150h}' + self.selection_get(selection='CLIPBOARD') + ']]'
            self.text.insert(INSERT, text)          # add at current insert cursor
            self.text.tag_remove(SEL, '1.0', END)
            self.text.tag_add(SEL, INSERT+'-%dc' % len(text), INSERT)
            self.text.see(INSERT)                   # select it, so it can be cut


    def prosody_pitch_s(self):
        if not self.text.tag_ranges(SEL):       # save in cross-app clipboard
            showerror('SSMLtagEdit', 'No text selected')
        else:
            text = self.text.get(SEL_FIRST, SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(text)

            self.onDelete()

            text = '[[{150s}' + self.selection_get(selection='CLIPBOARD') + ']]'
            self.text.insert(INSERT, text)          # add at current insert cursor
            self.text.tag_remove(SEL, '1.0', END)
            self.text.tag_add(SEL, INSERT+'-%dc' % len(text), INSERT)
            self.text.see(INSERT)                   # select it, so it can be cut


    def prosody_pitch_w(self):
        if not self.text.tag_ranges(SEL):       # save in cross-app clipboard
            showerror('SSMLtagEdit', 'No text selected')
        else:
            text = self.text.get(SEL_FIRST, SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(text)

            self.onDelete()

            text = '[[{150w}' + self.selection_get(selection='CLIPBOARD') + ']]'
            self.text.insert(INSERT, text)          # add at current insert cursor
            self.text.tag_remove(SEL, '1.0', END)
            self.text.tag_add(SEL, INSERT+'-%dc' % len(text), INSERT)
            self.text.see(INSERT)                   # select it, so it can be cut



    def prosody_pitch_r(self):
        if not self.text.tag_ranges(SEL):       # save in cross-app clipboard
            showerror('SSMLtagEdit', 'No text selected')
        else:
            text = self.text.get(SEL_FIRST, SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(text)

            self.onDelete()

            text = '[[{150%}' + self.selection_get(selection='CLIPBOARD') + ']]'
            self.text.insert(INSERT, text)          # add at current insert cursor
            self.text.tag_remove(SEL, '1.0', END)
            self.text.tag_add(SEL, INSERT+'-%dc' % len(text), INSERT)
            self.text.see(INSERT)                   # select it, so it can be cut



    def say_as_nu(self):

        if not self.text.tag_ranges(SEL):       # save in cross-app clipboard
            showerror('SSMLtagEdit', 'No text selected')
        else:
            text = self.text.get(SEL_FIRST, SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(text)

            self.onDelete()

            text = '##{nu}' + self.selection_get(selection='CLIPBOARD') + '##'
            self.text.insert(INSERT, text)          # add at current insert cursor
            self.text.tag_remove(SEL, '1.0', END)
            self.text.tag_add(SEL, INSERT+'-%dc' % len(text), INSERT)
            self.text.see(INSERT)                   # select it, so it can be cut


    def say_as_no(self):

        if not self.text.tag_ranges(SEL):       # save in cross-app clipboard
            showerror('SSMLtagEdit', 'No text selected')
        else:
            text = self.text.get(SEL_FIRST, SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(text)

            self.onDelete()

            text = '##{no}' + self.selection_get(selection='CLIPBOARD') + '##'
            self.text.insert(INSERT, text)          # add at current insert cursor
            self.text.tag_remove(SEL, '1.0', END)
            self.text.tag_add(SEL, INSERT+'-%dc' % len(text), INSERT)
            self.text.see(INSERT)                   # select it, so it can be cut

    def say_as_nt(self):

        if not self.text.tag_ranges(SEL):       # save in cross-app clipboard
            showerror('SSMLtagEdit', 'No text selected')
        else:
            text = self.text.get(SEL_FIRST, SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(text)

            self.onDelete()

            text = '##{nt}' + self.selection_get(selection='CLIPBOARD') + '##'
            self.text.insert(INSERT, text)          # add at current insert cursor
            self.text.tag_remove(SEL, '1.0', END)
            self.text.tag_add(SEL, INSERT+'-%dc' % len(text), INSERT)
            self.text.see(INSERT)                   # select it, so it can be cut



    def say_as_di(self):

        if not self.text.tag_ranges(SEL):       # save in cross-app clipboard
            showerror('SSMLtagEdit', 'No text selected')
        else:
            text = self.text.get(SEL_FIRST, SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(text)

            self.onDelete()

            text = '##{di}' + self.selection_get(selection='CLIPBOARD') + '##'
            self.text.insert(INSERT, text)          # add at current insert cursor
            self.text.tag_remove(SEL, '1.0', END)
            self.text.tag_add(SEL, INSERT+'-%dc' % len(text), INSERT)
            self.text.see(INSERT)                   # select it, so it can be cut


    def say_as_l(self):

        if not self.text.tag_ranges(SEL):       # save in cross-app clipboard
            showerror('SSMLtagEdit', 'No text selected')
        else:
            text = self.text.get(SEL_FIRST, SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(text)

            self.onDelete()

            text = '##{l}' + self.selection_get(selection='CLIPBOARD') + '##'
            self.text.insert(INSERT, text)          # add at current insert cursor
            self.text.tag_remove(SEL, '1.0', END)
            self.text.tag_add(SEL, INSERT+'-%dc' % len(text), INSERT)
            self.text.see(INSERT)                   # select it, so it can be cut


    def say_as_df(self):

        if not self.text.tag_ranges(SEL):       # save in cross-app clipboard
            showerror('SSMLtagEdit', 'No text selected')
        else:
            text = self.text.get(SEL_FIRST, SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(text)

            self.onDelete()

            text = '##{dfXXX}' + self.selection_get(selection='CLIPBOARD') + '##'
            self.text.insert(INSERT, text)          # add at current insert cursor
            self.text.tag_remove(SEL, '1.0', END)
            self.text.tag_add(SEL, INSERT+'-%dc' % len(text), INSERT)
            self.text.see(INSERT)                   # select it, so it can be cut

    def say_as_vxc(self):

        if not self.text.tag_ranges(SEL):       # save in cross-app clipboard
            showerror('SSMLtagEdit', 'No text selected')
        else:
            text = self.text.get(SEL_FIRST, SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(text)

            self.onDelete()

            text = '##{vxc}' + self.selection_get(selection='CLIPBOARD') + '##'
            self.text.insert(INSERT, text)          # add at current insert cursor
            self.text.tag_remove(SEL, '1.0', END)
            self.text.tag_add(SEL, INSERT+'-%dc' % len(text), INSERT)
            self.text.see(INSERT)                   # select it, so it can be cut

    def say_as_vxd(self):

        if not self.text.tag_ranges(SEL):       # save in cross-app clipboard
            showerror('SSMLtagEdit', 'No text selected')
        else:
            text = self.text.get(SEL_FIRST, SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(text)

            self.onDelete()

            text = '##{vxd}' + self.selection_get(selection='CLIPBOARD') + '##'
            self.text.insert(INSERT, text)          # add at current insert cursor
            self.text.tag_remove(SEL, '1.0', END)
            self.text.tag_add(SEL, INSERT+'-%dc' % len(text), INSERT)
            self.text.see(INSERT)                   # select it, so it can be cut


    def say_as_ipa(self):

        if not self.text.tag_ranges(SEL):       # save in cross-app clipboard
            showerror('SSMLtagEdit', 'No text selected')
        else:
            text = self.text.get(SEL_FIRST, SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(text)

            self.onDelete()

            text = '##{ipa}' + self.selection_get(selection='CLIPBOARD') + '##'
            self.text.insert(INSERT, text)          # add at current insert cursor
            self.text.tag_remove(SEL, '1.0', END)
            self.text.tag_add(SEL, INSERT+'-%dc' % len(text), INSERT)
            self.text.see(INSERT)                   # select it, so it can be cut




    def decode_and_download(self):
        text = self.getAllText()

        self.text.tag_add(SEL, '1.0', END+'-1c')   # select entire text
        self.text.mark_set(INSERT, '1.0')          # move insert point to top
        self.text.see(INSERT)                      # scroll to top

        self.clipboard_append(text)

        self.onDelete()

        text = decode(text)


        self.text.insert(INSERT, text)          # add at current insert cursor
        self.text.tag_remove(SEL, '1.0', END)
        self.text.tag_add(SEL, INSERT+'-%dc' % len(text), INSERT)
        self.text.see(INSERT)                   # select it, so it can be cut


    ############################################################################
    # Search menu commands
    ############################################################################

    def onGoto(self, forceline=None):
        line = forceline or askinteger('SSMLtagEdit', 'Enter line number')
        self.text.update()
        self.text.focus()
        if line is not None:
            maxindex = self.text.index(END+'-1c')
            maxline  = int(maxindex.split('.')[0])
            if line > 0 and line <= maxline:
                self.text.mark_set(INSERT, '%d.0' % line)      # goto line
                self.text.tag_remove(SEL, '1.0', END)          # delete selects
                self.text.tag_add(SEL, INSERT, 'insert + 1l')  # select line
                self.text.see(INSERT)                          # scroll to line
            else:
                showerror('SSMLtagEdit', 'Bad line number')

    def onFind(self, lastkey=None):
        key = lastkey or askstring('SSMLtagEdit', 'Enter search string')
        self.text.update()
        self.text.focus()
        self.lastfind = key
        if key:                                                    # 2.0: nocase
            nocase = configs.get('caseinsens', True)               # 2.0: config
            where = self.text.search(key, INSERT, END, nocase=nocase)
            if not where:                                          # don't wrap
                showerror('SSMLtagEdit', 'String not found')
            else:
                pastkey = where + '+%dc' % len(key)           # index past key
                self.text.tag_remove(SEL, '1.0', END)         # remove any sel
                self.text.tag_add(SEL, where, pastkey)        # select key
                self.text.mark_set(INSERT, pastkey)           # for next find
                self.text.see(where)                          # scroll display

    def onRefind(self):
        self.onFind(self.lastfind)

    def onChange(self):
        """
        non-modal find/change dialog 
        2.1: pass per-dialog inputs to callbacks, may be > 1 change dialog open
        """
        new = Toplevel(self)
        new.title('SSMLtagEdit - change')
        Label(new, text='Find text?', relief=RIDGE, width=15).grid(row=0, column=0)
        Label(new, text='Change to?', relief=RIDGE, width=15).grid(row=1, column=0)
        entry1 = Entry(new)
        entry2 = Entry(new)
        entry1.grid(row=0, column=1, sticky=EW)
        entry2.grid(row=1, column=1, sticky=EW)

        def onFind():                         # use my entry in enclosing scope   
            self.onFind(entry1.get())         # runs normal find dialog callback

        def onApply():
            self.onDoChange(entry1.get(), entry2.get())

        Button(new, text='Find',  command=onFind ).grid(row=0, column=2, sticky=EW)
        Button(new, text='Apply', command=onApply).grid(row=1, column=2, sticky=EW)
        new.columnconfigure(1, weight=1)      # expandable entries

    def onDoChange(self, findtext, changeto):
        # on Apply in change dialog: change and refind
        if self.text.tag_ranges(SEL):                      # must find first
            self.text.delete(SEL_FIRST, SEL_LAST)          
            self.text.insert(INSERT, changeto)             # deletes if empty
            self.text.see(INSERT)
            self.onFind(findtext)                          # goto next appear
            self.text.update()                             # force refresh

    ############################################################################
    # Tools menu commands
    ############################################################################

    def onFontList(self):
        self.fonts.append(self.fonts[0])           # pick next font in list
        del self.fonts[0]                          # resizes the text area
        self.text.config(font=self.fonts[0])

    def onColorList(self):
        self.colors.append(self.colors[0])         # pick next color in list
        del self.colors[0]                         # move current to end
        self.text.config(fg=self.colors[0]['fg'], bg=self.colors[0]['bg'])

    def onPickFg(self):
        self.pickColor('fg')                       # added on 10/02/00

    def onPickBg(self):                            # select arbitrary color
        self.pickColor('bg')                       # in standard color dialog

    def pickColor(self, part):                     # this is too easy
        (triple, hexstr) = askcolor()
        if hexstr:
            self.text.config(**{part: hexstr})

    def onInfo(self):
        """
        pop-up dialog giving text statistics and cursor location;
        caveat (2.1): Tk insert position column counts a tab as one 
        character: translate to next multiple of 8 to match visual?
        """  
        text  = self.getAllText()                  # added on 5/3/00 in 15 mins
        bytes = len(text)                          # words uses a simple guess:
        lines = len(text.split('\n'))              # any separated by whitespace
        words = len(text.split())                  # 3.x: bytes is really chars
        index = self.text.index(INSERT)            # str is unicode code points
        where = tuple(index.split('.'))
        showinfo('SSMLtagEdit Information',
                 'Current location:\n\n' +
                 'line:\t%s\ncolumn:\t%s\n\n' % where +
                 'File text statistics:\n\n' +
                 'chars:\t%d\nlines:\t%d\nwords:\t%d\n' % (bytes, lines, words))

    def onClone(self, makewindow=True):                  
        """
        open a new edit window without changing one already open (onNew);
        inherits quit and other behavior of the window that it clones;
        2.1: subclass must redefine/replace this if makes its own popup, 
        else this creates a bogus extra window here which will be empty;
        """
        if not makewindow:
             new = None                 # assume class makes its own window
        else:
             new = Toplevel()           # a new edit window in same process
        myclass = self.__class__        # instance's (lowest) class object
        myclass(new)                    # attach/run instance of my class


    def onPickFont(self):
        """
        2.0 non-modal font spec dialog
        2.1: pass per-dialog inputs to callback, may be > 1 font dialog open
        """
        from formrows import makeFormRow
        popup = Toplevel(self)
        popup.title('SSMLtagEdit - font')
        var1 = makeFormRow(popup, label='Family', browse=False)
        var2 = makeFormRow(popup, label='Size',   browse=False)
        var3 = makeFormRow(popup, label='Style',  browse=False)
        var1.set('courier')
        var2.set('12')              # suggested vals
        var3.set('bold italic')     # see pick list for valid inputs
        Button(popup, text='Apply', command=
               lambda: self.onDoFont(var1.get(), var2.get(), var3.get())).pack()

    def onDoFont(self, family, size, style):
        try:  
            self.text.config(font=(family, int(size), style))
        except:
            showerror('SSMLtagEdit', 'Bad font specification')


    ############################################################################
    # Utilities, useful outside this class
    ############################################################################

    def isEmpty(self):
        return not self.getAllText()

    def getAllText(self):
        return self.text.get('1.0', END+'-1c')    # extract text as str string
    def setAllText(self, text):
        """
        caller: call self.update() first if just packed, else the
        initial position may be at line 2, not line 1 (2.1; Tk bug?)
        """
        self.text.delete('1.0', END)              # store text string in widget
        self.text.insert(END, text)               # or '1.0'; text=bytes or str
        self.text.mark_set(INSERT, '1.0')         # move insert point to top
        self.text.see(INSERT)                     # scroll to top, insert set
    def clearAllText(self):
        self.text.delete('1.0', END)              # clear text in widget

    def getFileName(self):
        return self.currfile
    def setFileName(self, name):                  # see also: onGoto(linenum)
        self.currfile = name  # for save
        self.filelabel.config(text=str(name))

    def setKnownEncoding(self, encoding='utf-8'): # 2.1: for saves if inserted
        self.knownEncoding = encoding             # else saves use config, ask?

    def setBg(self, color):
        self.text.config(bg=color)                # to set manually from code
    def setFg(self, color):
        self.text.config(fg=color)                # 'black', hexstring
    def setFont(self, font):
        self.text.config(font=font)               # ('family', size, 'style')

    def setHeight(self, lines):                   # default = 24h x 80w
        self.text.config(height=lines)            # may also be from textCongif.py
    def setWidth(self, chars):
        self.text.config(width=chars)

    def clearModified(self):
        self.text.edit_modified(0)                # clear modified flag
    def isModified(self):
        return self.text_edit_modified()          # changed since last reset?

    def help(self):
        showinfo('About SSMLtagEdit', helptext)# % ((Version,)*2))



class TextEditorMain(TextEditor, GuiMakerWindowMenu):
    """
    main SSMLtagEdit windows that quit() to exit app on a Quit in GUI, and build
    a menu on a window;  parent may be default Tk, explicit Tk, or Toplevel: 
    parent must be a window, and probably should be a Tk so this isn't silently
    destroyed and closed with a parent;  all main SSMLtagEdit windows check all other
    SSMLtagEdit windows open in the process for changes on a Quit in the GUI, since 
    a quit() here will exit the entire app;  the editor's frame need not occupy 
    entire window (may have other parts: see PyView), but its Quit ends program;
    onQuit is run for Quit in toolbar or File menu, as well as window border X;
    """
    def __init__(self, parent=None, loadFirst='', loadEncode=''):
        # editor fills whole parent window
        GuiMaker.__init__(self, parent)                  # use main window menus
        TextEditor.__init__(self, loadFirst, loadEncode) # GuiMaker frame packs self
        self.master.title('SSMLtagEdit ' + Version)           # title, wm X if standalone
        self.master.iconname('SSMLtagEdit')
        self.master.protocol('WM_DELETE_WINDOW', self.onQuit)
        TextEditor.editwindows.append(self)

    def onQuit(self):                              # on a Quit request in the GUI
        close = not self.text_edit_modified()      # check self, ask?, check others
        if not close:
            close = askyesno('SSMLtagEdit', 'Text changed: quit and discard changes?')
        if close:
            windows = TextEditor.editwindows
            changed = [w for w in windows if w != self and w.text_edit_modified()]
            if not changed:
                GuiMaker.quit(self) # quit ends entire app regardless of widget type
            else:
                numchange = len(changed)
                verify = '%s other edit window%s changed: quit and discard anyhow?'
                verify = verify % (numchange, 's' if numchange > 1 else '')
                if askyesno('SSMLtagEdit', verify):
                    GuiMaker.quit(self)


################################################################################
# standalone program run
################################################################################


def main():                                           # may be typed or clicked
    try:                                              # or associated on Windows
        fname = sys.argv[1]                           # arg = optional filename
    except IndexError:                                # build in default Tk root
        fname = None
    TextEditorMain(loadFirst=fname).pack(expand=YES, fill=BOTH)   # pack optional
    mainloop()

if __name__ == '__main__':                            # when run as a script
    main()                                            # run .pyw for no DOS box
