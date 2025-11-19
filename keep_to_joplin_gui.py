import os
import sys
from typing import Optional

# Suppress macOS Text Services Manager warnings
class StderrFilter:
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
    
    def write(self, message):
        if 'TSMSendMessageToUIServer' not in message:
            self.original_stderr.write(message)
    
    def flush(self):
        self.original_stderr.flush()

# Redirect stderr to filter out macOS warnings
if sys.platform == 'darwin':
    sys.stderr = StderrFilter(sys.stderr)

from PyQt6 import QtCore, QtWidgets

from keep_to_joplin import convert_keep_notes


class ConversionWorker(QtCore.QObject):
    log = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal(dict)
    error = QtCore.pyqtSignal(str)

    def __init__(self, input_dir: str, output_dir: str, dry_run: bool, verbose: bool):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.dry_run = dry_run
        self.verbose = verbose

    @QtCore.pyqtSlot()
    def run(self) -> None:
        try:
            stats = convert_keep_notes(
                self.input_dir,
                self.output_dir,
                dry_run=self.dry_run,
                verbose=self.verbose,
                log_callback=self.log.emit,
            )
            self.finished.emit(stats)
        except Exception as exc:
            self.error.emit(str(exc))


class HelpWindow(QtWidgets.QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("How to Use - Keep to Joplin")
        self.setMinimumSize(700, 600)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # Scrollable text area
        text_area = QtWidgets.QTextBrowser()
        text_area.setOpenExternalLinks(True)  # Enable clicking on links
        text_area.setHtml(self._get_help_text())
        layout.addWidget(text_area)
        
        # Close button
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.accept)
        layout.addWidget(button_box)
    
    def _get_help_text(self) -> str:
        return """
        <h1>How to Migrate from Google Keep to Joplin</h1>
        
        <h2>Step 1: Export Your Google Keep Data</h2>
        <ol>
            <li>Go to <a href="https://takeout.google.com/">Google Takeout</a></li>
            <li>Sign in with your Google account</li>
            <li>Click "Deselect all" to uncheck everything</li>
            <li>Scroll down and check only "Keep"</li>
            <li>Click "Next step"</li>
            <li>Choose your preferred settings:
                <ul>
                    <li>Delivery method: Email or Add to Drive</li>
                    <li>File type: .zip</li>
                    <li>Frequency: Export once</li>
                </ul>
            </li>
            <li>Click "Create export"</li>
            <li>Wait for Google to prepare your export (this may take a few minutes to several hours depending on the size of your data)</li>
            <li>You'll receive an email when the export is ready, or find it in your Google Drive</li>
        </ol>
        
        <h2>Step 2: Download the Export File</h2>
        <ol>
            <li>Check your email for the download link, or go to Google Drive if you chose that option</li>
            <li>Click the download link to download the .zip file</li>
            <li>Note the location where the file was saved</li>
        </ol>
        
        <h2>Step 3: Extract the ZIP File</h2>
        
        <h3>On macOS:</h3>
        <ol>
            <li>Double-click the .zip file in Finder</li>
            <li>It will automatically extract to the same location</li>
            <li>You should see a folder named something like "takeout-YYYY-MM-DD"</li>
        </ol>
        
        <h3>On Windows:</h3>
        <ol>
            <li>Right-click the .zip file</li>
            <li>Select "Extract All..."</li>
            <li>Choose a destination folder and click "Extract"</li>
            <li>You should see a folder named something like "takeout-YYYY-MM-DD"</li>
        </ol>
        
        <h3>On Linux:</h3>
        <ol>
            <li>Open a terminal in the directory containing the .zip file</li>
            <li>Run: <code>unzip takeout-*.zip</code></li>
            <li>You should see a folder named something like "takeout-YYYY-MM-DD"</li>
        </ol>
        
        <h2>Step 4: Locate the Keep Folder</h2>
        <ol>
            <li>Navigate into the extracted folder</li>
            <li>Open the "Takeout" folder</li>
            <li>Inside, you should find a "Keep" folder</li>
            <li>This folder contains all your Google Keep notes as JSON files</li>
            <li><strong>Remember this path</strong> - you'll need it in the next step</li>
        </ol>
        
        <h2>Step 5: Convert Using This Tool</h2>
        <ol>
            <li>In this application, click "Browse..." next to "Path to Takeout/Keep"</li>
            <li>Navigate to and select the "Keep" folder from Step 4</li>
            <li>Click "Browse..." next to "Path to output directory"</li>
            <li>Select or create a folder where you want the converted Markdown files to be saved</li>
            <li>(Optional) Check "Dry run" to preview what will be converted without actually creating files</li>
            <li>(Optional) Check "Verbose logging" to see detailed progress information</li>
            <li>Click "Start conversion"</li>
            <li>Wait for the conversion to complete - you'll see progress in the log area</li>
            <li>When finished, you'll see a summary of processed and exported notes</li>
        </ol>
        
        <h2>Step 6: Import into Joplin</h2>
        <ol>
            <li>Open Joplin</li>
            <li>Go to <strong>File</strong> → <strong>Import</strong> → <strong>MD - Markdown (Directory)</strong></li>
            <li>Navigate to and select the output directory you specified in Step 5</li>
            <li>Click "Open" or "Select Folder"</li>
            <li>Joplin will import all the converted notes</li>
            <li>Your notes should now appear in Joplin with all their content, labels, and metadata preserved</li>
        </ol>
        
        <h2>Tips</h2>
        <ul>
            <li>By default, trashed and archived notes are <strong>not</strong> exported. If you want to include them, you'll need to use the command-line version with <code>--include-trashed</code> and <code>--include-archived</code> flags.</li>
            <li>The conversion preserves note colors, labels, creation dates, and modification dates</li>
            <li>Checklist items are converted to Markdown checkboxes</li>
            <li>If you have attachments in your Keep notes, they'll be copied to a "resources" subfolder in the output directory</li>
            <li>If you encounter any issues, try running with "Verbose logging" enabled to see detailed error messages</li>
        </ul>
        
        <h2>Need Help?</h2>
        <p>If you encounter any problems during the conversion, check the log output for error messages. Common issues include:</p>
        <ul>
            <li>Invalid or corrupted JSON files in the Keep folder</li>
            <li>Insufficient disk space in the output directory</li>
            <li>Permission errors when writing files</li>
        </ul>
        """


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Keep to Joplin")
        self.setMinimumSize(640, 480)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        
        # Help button at the top
        help_layout = QtWidgets.QHBoxLayout()
        help_layout.addStretch()
        help_button = QtWidgets.QPushButton("How to Use...")
        help_button.clicked.connect(self._show_help)
        help_layout.addWidget(help_button)
        layout.addLayout(help_layout)

        input_layout = QtWidgets.QHBoxLayout()
        self.input_edit = QtWidgets.QLineEdit()
        self.input_edit.setPlaceholderText("Path to Takeout/Keep")
        input_layout.addWidget(self.input_edit)
        input_button = QtWidgets.QPushButton("Browse...")
        input_button.clicked.connect(self._choose_input_dir)
        input_layout.addWidget(input_button)
        layout.addLayout(input_layout)

        output_layout = QtWidgets.QHBoxLayout()
        self.output_edit = QtWidgets.QLineEdit()
        self.output_edit.setPlaceholderText("Path to output directory")
        output_layout.addWidget(self.output_edit)
        output_button = QtWidgets.QPushButton("Browse...")
        output_button.clicked.connect(self._choose_output_dir)
        output_layout.addWidget(output_button)
        layout.addLayout(output_layout)

        options_layout = QtWidgets.QHBoxLayout()
        self.dry_run_checkbox = QtWidgets.QCheckBox("Dry run")
        self.verbose_checkbox = QtWidgets.QCheckBox("Verbose logging")
        options_layout.addWidget(self.dry_run_checkbox)
        options_layout.addWidget(self.verbose_checkbox)
        options_layout.addStretch()
        layout.addLayout(options_layout)

        self.start_button = QtWidgets.QPushButton("Start conversion")
        self.start_button.clicked.connect(self._start_conversion)
        layout.addWidget(self.start_button)

        self.log_area = QtWidgets.QPlainTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)

        self.status_label = QtWidgets.QLabel("Idle")
        layout.addWidget(self.status_label)

        self.thread: Optional[QtCore.QThread] = None
        self.worker: Optional[ConversionWorker] = None

    def _show_help(self) -> None:
        help_window = HelpWindow(self)
        help_window.exec()

    def _choose_input_dir(self) -> None:
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Google Keep JSON directory"
        )
        if directory:
            self.input_edit.setText(directory)

    def _choose_output_dir(self) -> None:
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select output directory"
        )
        if directory:
            self.output_edit.setText(directory)

    def _start_conversion(self) -> None:
        input_dir = self.input_edit.text().strip()
        if not input_dir:
            QtWidgets.QMessageBox.warning(
                self, "Input required", "Select an input directory."
            )
            return
        if not os.path.isdir(input_dir):
            QtWidgets.QMessageBox.warning(
                self, "Input missing", "The selected input directory does not exist."
            )
            return

        output_dir = self.output_edit.text().strip()
        if not output_dir:
            QtWidgets.QMessageBox.warning(
                self, "Output required", "Select an output directory."
            )
            return

        self.start_button.setEnabled(False)
        self.status_label.setText("Running…")
        self.log_area.clear()

        self.thread = QtCore.QThread()
        self.worker = ConversionWorker(
            input_dir,
            output_dir,
            dry_run=self.dry_run_checkbox.isChecked(),
            verbose=self.verbose_checkbox.isChecked(),
        )
        self.worker.moveToThread(self.thread)
        self.worker.log.connect(self._append_log)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def _append_log(self, message: str) -> None:
        self.log_area.appendPlainText(message)

    def _on_finished(self, stats: dict) -> None:
        self._append_log("Conversion complete.")
        self._append_log(
            f"Processed: {stats['processed']}, exported: {stats['exported']}, errors: {stats['errors']}"
        )
        self._finalize_run("Done")

    def _on_error(self, message: str) -> None:
        self._append_log(f"Error: {message}")
        self._finalize_run("Error")

    def _finalize_run(self, status: str) -> None:
        self.status_label.setText(status)
        self.start_button.setEnabled(True)
        if self.thread:
            self.thread.quit()
            self.thread.wait()
            self.thread = None
        self.worker = None


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
