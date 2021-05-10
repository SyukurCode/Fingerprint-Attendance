import sys
from PyQt5.QtWidgets import QMainWindow,QApplication
from PyQt5 import QtCore, QtMultimedia



if __name__ == '__main__':
    app = QApplication(sys.argv)
    sound_file = 'success.wav'
    sound = QtMultimedia.QSoundEffect()
    sound.setSource(QtCore.QUrl.fromLocalFile(sound_file))
    #sound.setLoopCount(QtMultimedia.QSoundEffect.Infinite)
    sound.setVolume(100)
    sound.play()
    app.exec()
    sys.exit(app.exec())


