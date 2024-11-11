import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox
import pandas as pd
import os


class MMLGenerator(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.eNB_list_data = []
        self.initUI()

    def initUI(self):
        layout = QtWidgets.QVBoxLayout()

        self.load_btn = QtWidgets.QPushButton("Load eNB List", self)
        self.load_btn.clicked.connect(self.load_file)
        layout.addWidget(self.load_btn)

        self.mml_option_label = QtWidgets.QLabel("MML Type")
        layout.addWidget(self.mml_option_label)

        self.mml_option = QtWidgets.QComboBox(self)
        self.mml_option.addItem("eNB LvL MML")
        self.mml_option.addItem("Cell LvL MML")
        layout.addWidget(self.mml_option)

        self.eNB_count_label = QtWidgets.QLabel("eNB Count: 0")
        layout.addWidget(self.eNB_count_label)

        self.cell_count_label = QtWidgets.QLabel("Local Cell ID Count: 0")
        layout.addWidget(self.cell_count_label)

        self.earfcn_label = QtWidgets.QLabel("Select DL EARFCN")
        layout.addWidget(self.earfcn_label)

        self.selected_earfcn = QtWidgets.QComboBox(self)
        self.selected_earfcn.addItem("All cells")
        layout.addWidget(self.selected_earfcn)

        self.mml_input_label = QtWidgets.QLabel("MML Example/Start")
        layout.addWidget(self.mml_input_label)

        self.mml_input = QtWidgets.QTextEdit()
        layout.addWidget(self.mml_input)

        self.mml_input_end_label = QtWidgets.QLabel("MML End (for Cell LvL MML)")
        layout.addWidget(self.mml_input_end_label)

        self.mml_input_end = QtWidgets.QTextEdit()
        layout.addWidget(self.mml_input_end)

        self.generate_example_btn = QtWidgets.QPushButton("Generate Input Example", self)
        self.generate_example_btn.clicked.connect(self.generate_example)
        layout.addWidget(self.generate_example_btn)

        self.generate_btn = QtWidgets.QPushButton("Generate MML", self)
        self.generate_btn.clicked.connect(self.generate_mml)
        layout.addWidget(self.generate_btn)

        self.setLayout(layout)

        self.setGeometry(300, 300, 600, 600)
        self.setWindowTitle('MML Generator')
        self.show()

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open file",
            "",
            "All files (*.*);;Text files (*.txt);;CSV files (*.csv);;Excel files (*.xlsx)"
        )
        if file_path:
            ext = file_path.split('.')[-1]
            try:
                if ext == 'txt':
                    with open(file_path, 'r') as file:
                        data = file.readlines()
                elif ext == 'csv':
                    data = pd.read_csv(file_path, header=0).values.tolist()
                elif ext == 'xlsx':
                    data = pd.read_excel(file_path, header=0).values.tolist()
                else:
                    QMessageBox.critical(self, "Error", "Unsupported file format.")
                    return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {e}")
                return

            formatted_data = []
            for line in data:
                if isinstance(line, list):
                    formatted_data.append("\t".join(map(str, line)))
                else:
                    formatted_data.append(line.strip())

            self.eNB_list_data = formatted_data
            self.update_counts()
            self.update_earfcn_options()

    def parse_data(self, data):
        parsed_data = []
        for line in data:
            if '\t' in line:
                parsed_data.append(line.split('\t'))
            elif ',' in line:
                parsed_data.append(line.split(','))
            elif ';' in line:
                parsed_data.append(line.split(';'))
            elif ' ' in line:
                parsed_data.append(line.split())
            else:
                parsed_data.append([line])
        return parsed_data

    def update_counts(self):
        parsed_data = self.parse_data(self.eNB_list_data)
        eNB_count = len(set(row[0] for row in parsed_data if row))
        cell_count = len(parsed_data)
        self.eNB_count_label.setText(f"eNB Count: {eNB_count}")
        self.cell_count_label.setText(f"Cell ID Count: {cell_count}")

    def update_earfcn_options(self):
        parsed_data = self.parse_data(self.eNB_list_data)
        earfcn_values = set(
            int(float(row[2])) for row in parsed_data
            if len(row) > 2 and row[2].replace('.', '', 1).isdigit()
        )
        self.selected_earfcn.clear()
        self.selected_earfcn.addItem("All cells")
        for earfcn in sorted(earfcn_values):
            self.selected_earfcn.addItem(str(earfcn))
        self.selected_earfcn.setCurrentText("All cells")

    def generate_example(self):
        example_data = {
            "eNB_ID": ["AL7777", "AL8171", "AL7743"],
            "Cell_ID": [1, 11, 21],
            "DL_EARFCN": [1850, 1652, 500]
        }
        df = pd.DataFrame(example_data)
        example_file, _ = QFileDialog.getSaveFileName(
            self,
            "Save file",
            "",
            "CSV files (*.csv)"
        )
        if example_file:
            df.to_csv(example_file, index=False)
            QMessageBox.information(self, "Success", f"File saved to {example_file}")

    def generate_mml(self):
        mml_type = self.mml_option.currentText()
        if not mml_type:
            QMessageBox.critical(self, "Error", "Please, select MML type.")
            return

        data_str = self.eNB_list_data
        if not data_str:
            QMessageBox.critical(self, "Error", "eNB List is empty.")
            return

        parsed_data = self.parse_data(data_str)
        selected_earfcn_value = self.selected_earfcn.currentText()

        if selected_earfcn_value != "All cells":
            parsed_data = [
                row for row in parsed_data
                if len(row) > 2 and row[2].replace('.', '', 1).isdigit()
                and str(int(float(row[2]))) == selected_earfcn_value
            ]

        output = []
        if mml_type == "eNB LvL MML":
            mml_example = self.mml_input.toPlainText().strip()
            if not mml_example:
                QMessageBox.critical(self, "Error", "MML example is empty.")
                return
            output = [f"{mml_example}{{{row[0]}}}" for row in parsed_data if len(row) > 0]

        elif mml_type == "Cell LvL MML":
            mml_start = self.mml_input.toPlainText().strip()
            mml_end = self.mml_input_end.toPlainText().strip()
            if not mml_start or not mml_end:
                QMessageBox.critical(self, "Error", "MML start or end is empty.")
                return

            for row in parsed_data:
                if len(row) >= 2:
                    eNB, cell_id = row[:2]
                    output.append(f"{mml_start}{cell_id}{mml_end}{{{eNB}}}")
                else:
                    QMessageBox.critical(self, "Error", f"Invalid data format in row: {row}")
                    return

        if not output:
            QMessageBox.critical(self, "Error", "No valid data found to generate MML.")
            return

        self.split_and_save_output(output)

    def split_and_save_output(self, output):
        part_size_bytes = 5 * 1024 * 1024  # 5MB in bytes
        current_part = []
        current_part_size = 0
        base_output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save file",
            "",
            "Text files (*.txt)"
        )

        if not base_output_path:
            return

        base_name, ext = os.path.splitext(base_output_path)
        part_num = 1
        total_parts = 1

        for line in output:
            line_size = len(line.encode('utf-8')) + len('\n'.encode('utf-8'))
            if current_part_size + line_size > part_size_bytes:
                # Save current part to file
                part_file_path = (
                    f"{base_name}_{part_num}{ext}" if total_parts > 1 else base_output_path
                )
                with open(part_file_path, 'w', encoding='utf-8') as file:
                    file.write("\n".join(current_part))
                part_num += 1
                current_part = []
                current_part_size = 0
                total_parts += 1

            current_part.append(line)
            current_part_size += line_size

        # Save the last part
        if current_part:
            part_file_path = (
                f"{base_name}_{part_num}{ext}" if total_parts > 1 else base_output_path
            )
            with open(part_file_path, 'w', encoding='utf-8') as file:
                file.write("\n".join(current_part))

        if total_parts > 1:
            QMessageBox.information(self, "Success", f"Output files saved to {base_name}_*.txt")
        else:
            QMessageBox.information(self, "Success", f"Output file saved to {base_output_path}")

def main():
    app = QtWidgets.QApplication(sys.argv)
    ex = MMLGenerator()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
