import sys
import os
import random
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image

class FullForestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Forest Generation")
        self.resize(1000, 700)

        layout = QVBoxLayout()
        self.label = QLabel()
        self.label.setStyleSheet("background: transparent;")  # sky background
        layout.addWidget(self.label)
        self.setLayout(layout)

        pixmap = self.generate_forest_pixmap()
        self.label.setPixmap(pixmap)

    def generate_forest_pixmap(self):
        TREE_FOLDER = "tiles/Forest"

        # Load all PNGs dynamically
        tree_images = []
        for file in os.listdir(TREE_FOLDER):
            if file.lower().endswith(".png"):
                try:
                    img = Image.open(os.path.join(TREE_FOLDER, file)).convert("RGBA")
                    tree_images.append(img)
                except:
                    pass

        if not tree_images:
            raise Exception("No PNG images found in 'trees' folder!")

        WIDTH, HEIGHT = 1000, 700
        canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))

        # Grid cell size (adjust for density)
        CELL_W, CELL_H = 60, 60

        drawn_trees = []

        # Fill the canvas cell by cell
        for i in range(0, WIDTH, CELL_W):
            for j in range(0, HEIGHT, CELL_H):
                # Place 1-3 trees per cell for density
                for _ in range(random.randint(1, 3)):
                    tree = random.choice(tree_images)

                    # Random scale
                    scale = random.uniform(0.7, 1.3)
                    w = int(tree.width * scale)
                    h = int(tree.height * scale)
                    t = tree.resize((w, h), Image.LANCZOS)

                    # Slight rotation
                    angle = random.uniform(-5, 5)
                    t = t.rotate(angle, expand=True)

                    # Random offsets inside cell (can extend outside)
                    x = i + random.randint(-20, 20)
                    y = j + random.randint(-20, 20)

                    # Clamp inside canvas
                    x = max(0, min(WIDTH - t.width, x))
                    y = max(0, min(HEIGHT - t.height, y))

                    # Bottom Y for Z-order
                    bottom_y = y + t.height
                    drawn_trees.append((bottom_y, t, x, y))

        # Sort trees by bottom Y for natural overlap
        drawn_trees.sort(key=lambda item: item[0])

        # Draw trees
        for _, t, x, y in drawn_trees:
            try:
                canvas.alpha_composite(t, (x, y))
            except:
                pass

        # Convert to QPixmap
        data = canvas.tobytes("raw", "RGBA")
        qimage = QImage(data, WIDTH, HEIGHT, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage)
        return pixmap

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = FullForestWindow()
    win.show()
    sys.exit(app.exec_())
