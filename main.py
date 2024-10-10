import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QFontDatabase
from gui import MediaGPSExtractorGUI

def main():
    app = QApplication(sys.argv)
    
    font_id = QFontDatabase.addApplicationFont("assets/fonts/Inter-Regular.ttf")
    if font_id != -1:
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        app.setFont(QFont(font_family, 10))
    else:
        print("Error: Failed to load custom font")
    
    ex = MediaGPSExtractorGUI()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()