from morse.builder import *

class LpMan(Robot):
    """
    A template robot model for theman, with a motion controller and a pose sensor.
    """
    def __init__(self, filename="lpman",name = None, debug = True):

        # theman.blend is located in the data/robots directory
        Robot.__init__(self, filename, name)
        self.properties(classpath = "morse.robots.lpman.LpMan")

        ###################################
        # Actuators
        ###################################


        # (v,w) motion controller
        # Check here the other available actuators:
        # http://www.openrobots.org/morse/doc/stable/components_library.html#actuators
        # self.motion = MotionVW()
        # self.append(self.motion)

        # Optionally allow to move the robot with the keyboard
        # if debug:
        #     keyboard = Keyboard()
        #     keyboard.properties(ControlType = 'Position')
        #     self.append(keyboard)

        ###################################
        # Sensors
        ###################################

        # self.pose = Pose()
        # self.append(self.pose)

