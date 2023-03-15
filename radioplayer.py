from time import sleep

import vlc

stream_url = "https://c2.hostingcentar.com/streams/radio101rock/"


def play():
    p = vlc.MediaPlayer(stream_url)
    p.play()

    try:
        while True:
            sleep(10)
            print("clean")
            vlc.AudioDrainCb()
            vlc.AudioFlushCb()
            vlc.AudioCleanupCb()
    except KeyboardInterrupt:
        p.stop()
