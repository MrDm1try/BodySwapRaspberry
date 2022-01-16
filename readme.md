This is the repository for the python implementation of the Body Swap project created by Sebastian Hoppe and Dumitru Racicovschii.

The repository and readme for the Raspberry Pi implementation is located at https://github.com/Hoppe2808/BodySwapUnity.

# Setup

* Install BrickPi3 on your device by running the following command:
```bash
curl -kL dexterindustries.com/update_brickpi3 | bash
```

In case of any problems, consult [this](https://www.dexterindustries.com/BrickPi/brickpi3-getting-started-step-4-program-brickpi-robot/brickpi3-getting-started-program-python/) link.

* Connect the wrist motor to port **B** of the BrickPI, and the elbow motors to ports **A** and **C** of the BrickPI.

# Running

The program should be run directly from the console:
```python3
python3 exoskeleton_udp.py [(-l|--log) log_folder_name]
```
If a log folder name is provided, a folder with the mentioned name will be created, and all log files will be put into this folder.

Note that the scripts on two exoskeletons do not need to be started simultaneously, however, in order to be synchronized, both exoskeleton programs should be started when the exoskeletons are in the same predefined position.