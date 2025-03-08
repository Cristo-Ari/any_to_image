import sys
import os
import numpy as np
import hashlib
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog, QMessageBox, \
    QRadioButton
from PyQt5.QtGui import QImage
from PyQt5.QtCore import Qt


def calculate_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_unique_folder_name(base_path, file_name):
    counter = 1
    while True:
        folder_name = os.path.join(base_path, f"copy_{counter}_{file_name}")
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            return folder_name
        counter += 1


def file_to_image(file_path):
    with open(file_path, "rb") as f:
        data = f.read()

    data_length = len(data)
    side = int(np.ceil(np.sqrt(data_length / 3)))

    padded_data = data + bytes(side * side * 3 - data_length)
    img_array = np.frombuffer(padded_data, dtype=np.uint8).reshape((side, side, 3))
    img = QImage(img_array, side, side, QImage.Format_RGB888)

    folder_path = get_unique_folder_name(os.path.dirname(file_path), os.path.basename(file_path))
    output_path = os.path.join(folder_path, os.path.basename(file_path) + ".png")
    img.save(output_path)
    print(f"Файл сохранен в: {output_path}")
    return output_path, calculate_hash(file_path)


def image_to_file(image_path):
    img = QImage(image_path)
    if img.isNull():
        print("Ошибка: изображение не загружено")
        return

    width, height = img.width(), img.height()
    data = bytearray()

    for y in range(height):
        for x in range(width):
            pixel = img.pixel(x, y)
            data.extend([(pixel >> 16) & 0xFF, (pixel >> 8) & 0xFF, pixel & 0xFF])

    folder_path = get_unique_folder_name(os.path.dirname(image_path), os.path.basename(image_path).replace(".png", ""))
    output_path = os.path.join(folder_path, os.path.basename(image_path).replace(".png", ""))
    with open(output_path, "wb") as f:
        f.write(data)

    print(f"Файл восстановлен в: {output_path}")
    return output_path, calculate_hash(output_path)


class DragDropWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setAcceptDrops(True)
        self.setWindowTitle("File <-> Image Converter")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()
        self.label = QLabel("Перетащите сюда файл", self)
        self.label.setAlignment(Qt.AlignCenter)

        self.radio_save = QRadioButton("Создать картинку")
        self.radio_load = QRadioButton("Считать из картинки")
        self.radio_save.setChecked(True)

        layout.addWidget(self.radio_save)
        layout.addWidget(self.radio_load)
        layout.addWidget(self.label)

        self.setLayout(layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if os.path.isfile(file_path):
                if self.radio_save.isChecked():
                    img_path, file_hash = file_to_image(file_path)
                    QMessageBox.information(self, "Сохранено", f"Файл сохранен в: {img_path}\nХеш: {file_hash}")
                else:
                    restored_path, restored_hash = image_to_file(file_path)
                    response = QMessageBox.question(self, "Проверить целостность?", "Хотите проверить хеш?",
                                                    QMessageBox.Yes | QMessageBox.No)
                    if response == QMessageBox.Yes:
                        orig_file, _ = QFileDialog.getOpenFileName(self, "Выберите оригинальный файл")
                        if orig_file:
                            orig_hash = calculate_hash(orig_file)
                            if orig_hash == restored_hash:
                                QMessageBox.information(self, "Результат", "Файл целостен")
                            else:
                                QMessageBox.warning(self, "Результат", "Файл поврежден!")


def main():
    app = QApplication(sys.argv)
    window = DragDropWidget()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
