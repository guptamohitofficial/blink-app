# Face Analysis

This project is a real-time face analysis system that uses a webcam to detect eye blinking and saves it periodically into local db.

## Features
- **Enhanced Blink Detection**: Improved accuracy of blink detection using rolling average and cooldown mechanism
- **Precise Distance Estimation**: Calibrated distance calculation with better accuracy and real-time warnings when too close to screen
- **Performance Monitoring**: 
  - Real-time CPU usage (smoothed 1-second average)
  - Memory usage
- **Permanent storage with SQLite3 DB**:
  - Creates a local DB in its home directory anmed matrics.db
- **Http server serving saved metrics and blinkcounts**:
  - Accessible on 0.0.0.0:8080/metrics
- **Automatic Camera Selection**:
  - If you want to override the automatic selection, you can modify the `find_working_camera()` function in `utils.py`
- **Build Using Pyinstaller**:
  - Run `pyinstaller --onefile app.py --add-binary /<path_to_project_folder>/shape_predictor_68_face_landmarks.dat:.`

## Code Structure Improvements
- Reorganized into modular components
- Separated face analysis logic into dedicated class
- Enhanced error handling and safety checks
- SQLite DB module integrated
- Improved code readability and documentation
- Added configuration constants for easy tuning

## Getting Started

### Prerequisites
Ensure you have the following installed on your system:
- Python 3.7+
- A webcam or video capture device

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/guptamohitofficial/blink-app
   cd blink-app
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Download the `shape_predictor_68_face_landmarks.dat` file from [dlib's model zoo](http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2) and place it in the project directory.

For Mac ARM users, you may need to install the dependencies using conda:
1. Install conda: https://docs.anaconda.com/miniconda/install/#quick-command-line-install 
2. Add conda to your path: https://docs.anaconda.com/miniconda/install/#add-conda-to-your-path-macos-and-linux
3. Get Python 3.9 - 3.12 (for compatibility with Pytorch): https://pytorch.org/get-started/locally/
4. Create a conda environment:
   ```bash
   conda create -n blink_app python=3.11
   ```
5. Activate the environment:
   ```bash
   conda activate blink_app
   ```
6. Install the dependencies:
   ```bash
   conda install -c conda-forge opencv numpy scipy psutil dlib opencv Flask pyinstaller
   ```

### Running the Program
Execute the `app.py` script to start the face analysis system:
```bash
python app.py
```
For Mac ARM users, you will need to provide camera access to your terminal/code editor using Settings -> Privacy -> Camera.

If you are using a different camera, you can change the camera index in the `blink_app/capture.py` file:
   'cap = cv2.VideoCapture(1)' to 'cap = cv2.VideoCapture(0)'

### Usage
- The system will open a window displaying the webcam feed with metrics overlaid
- Real-time metrics are displayed in semi-transparent overlays:
  - Top-left: Performance metrics (FPS, Blinks, Distance, Frowns)
  - Bottom-right: System metrics (Runtime, CPU, Memory) and Quit button
- Press **Q** or click the Quit button to exit the program

## Project Structure
- **app.py**: The main app script for running the face analysis system
- **blink_app/**: Module containing DB, api server, logging code
- **requirements.txt**: Lists all the Python dependencies required
- **runtime.log**: A log file that records performance metrics and final statistics
- **shape_predictor_68_face_landmarks.dat**: Pre-trained dlib model for facial landmarks detection (not included)

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request for any improvements or additional features.

## Troubleshooting
If you encounter issues:
- Ensure the `shape_predictor_68_face_landmarks.dat` file is in the correct directory
- Verify that your webcam is working correctly
- Check the logs in `runtime.log` for errors
