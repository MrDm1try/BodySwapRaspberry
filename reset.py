import brickpi3  # import the BrickPi3 drivers

BP = brickpi3.BrickPi3()  # Create an instance of the BrickPi3 class. BP will be the BrickPi3 object.

BP.set_motor_power(BP.PORT_A, 0)
BP.set_motor_power(BP.PORT_B, 0)
BP.set_motor_power(BP.PORT_C, 0)
BP.set_motor_power(BP.PORT_D, 0)

BP.reset_all()
