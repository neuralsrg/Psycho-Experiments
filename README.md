# Software for conducting psychoexperiments
______________________________________________________________________________________________________________

### Experiments details
- The subject listens to bimodal stimuli consisting of audio and images.
- For each stimulus, the reaction of the subject (pressing a key) is detected.
- The application collects data on reactions: pressing time and type of reaction and saves it in *.csv format.
______________________________________________________________________________________________________________
### Details
- Tested for Windows 10 and Ubuntu 20.04 with Python 3.8 installed.
- Running:
Linux:
```sh
cd Psycho-Experiments
python ./src/server.py  # test server  (or run your own alternatively)
python ./src/main.py
```
Windows:
Install packages using
```sh
python -m pip install --upgrade pip
pip install --upgrade wheel
pip install -r requirements.txt
```
To run application
```sh
cd Psycho-Experiments

python ./src/server.py  # test server FOR A SINGLE EXPERIMENT  (or run your own alternatively)

python ./src/iterator.py # HIGHLY RECOMMENDED WAY
or
python ./src/main.py <PATH_TO_YOUR_CSV> # for a single run (not recommended)
```
