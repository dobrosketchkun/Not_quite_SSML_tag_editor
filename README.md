## What is it?

Shitty text editor / tag editor primarely based on [PyEditor](https://resources.oreilly.com/examples/9780596158118/tree/a5bcfbf9b81157d6dbbea72c00fa11b5f38dd9c9/PP4E-Examples-1.4/Examples/PP4E/Gui/TextEditor).

## What it can do?

It can paste my wrapper-tags around text and then download mp3 file from IBM TTS. Also can download mp3 with generated speach from [IBM TTS](https://text-to-speech-demo.ng.bluemix.net/)

## Why?

Original tags are just way to hard to read and manualy insert

-------

### List of buttons and tags

* Break = \**{500}** = <break time="500ms"> #Pause 500ms   

* Pitch Hz = [[{150h}...]] = <prosody pitch="150Hz">...</prosody> #Transpose pitch to 150 Hz  [[{-20h}...]] = <prosody pitch="150Hz">...</prosody> #Lower pitch by 20 Hz from baseline   

* Pitch st = [[{-12s}...]] = <prosody pitch="-12st">...</prosody> #Lower pitch by 12 semitones from baseline   

* Rate words = [{50w}...]] =  <prosody rate="50">...</prosody> #Set speaking rate at 50 words per minute   

* Rate % = [[{50%}...]] = <prosody rate="+5%">...</prosody> #Increase speaking rate by 5 percent   

* Number = ##{nu}...## = <say-as interpret-as="cardinal">...</say-as> #three   

* Ordinal = ##{no}...## = <say-as interpret-as="number" format="ordinal">...</say-as> #third   

* Tel. - ##{nt}...##= <say-as interpret-as="number" format="telephone">...</say-as> #555-555-5555   

* Digits = ##{di}...## = <say-as interpret-as="digits">...</say-as> #one two three four   

* Letters = ##{l}...## = <say-as interpret-as="letters">Hello</say-as> #h e l l o    

* Date f = ##{dfXXX}...## = <say-as interpret-as="date" format="XXX">...</say-as> #12/17/2005 - XXX: mdy   

* Date vx = ##{vxd}...## =   <say-as interpret-as="vxml:date">...</say-as> #20050720, ????0720, 200507??   

* Currency = ##{vxc}...## = <say-as interpret-as="vxml:currency">...</say-as> #USD45.30   

* IPA = ##{ipa}...## = <phoneme alphabet="ipa" ph="..."></phoneme> #təmˈɑto   

* TTS = Download mp3
