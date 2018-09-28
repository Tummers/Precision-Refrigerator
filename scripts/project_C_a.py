import tkinter  #This is for python3
import tkSnack


def setVolume(volume=50):
    """set the volume of the sound system"""

    if volume > 100:
        volume = 100
    elif volume < 0:
        volume = 0
    tkSnack.audio.play_gain(volume)


def playNote(freq, duration):
    """play a note of freq (hertz) for duration (seconds)"""

    snd = tkSnack.Sound()
    filt = tkSnack.Filter('generator', freq, 30000, 0.0, 'sine', int(11500*duration))
    snd.stop()
    snd.play(filter=filt, blocking=1)


def soundStop():
    """stop the sound the hard way"""

    try:
        root = root.destroy()
        filt = None
    except:
        pass


root = tkinter.Tk()   #This is for python3

# have to initialize the sound system, required!!
tkSnack.initializeSnack(root)
# set the volume of the sound system (0 to 100%)
setVolume(50)
# play a note of requency 440 hertz (A4) for a duration of 2 seconds
playNote(440, 2)
# optional
soundStop()

root.withdraw()
