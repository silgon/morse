import sys
import math
import datetime
import GameLogic

import morse.helpers.middleware

from middleware.pocolibs.controllers.Control_Poster import ors_genpos_poster
from middleware.pocolibs.sensors.Camera_Poster import ors_viam_poster
#from middleware.pocolibs.sensors.Gyro_Poster import ors_pom_poster


class MorsePocolibsClass(morse.helpers.middleware.MorseMiddlewareClass):
	""" Handle communication between Blender and YARP."""

	def __init__(self, obj, parent=None):
		""" Initialize the network and connect to the yarp server."""
		self.blender_obj = obj
		# Will store the id's of posters, indexed by component name
		self._poster_dict = dict()
		self._imported_modules = dict()


	def __del__(self):
		""" Destructor method.
			Close all open posters. """
		#for component_name, poster_id in self._pocolilbs_posters.items():
			#self.finalize(poster_id)


	def register_component(self, component_name,
			component_instance, mw_data):
		""" Open the port used to communicate the specified component.

		The name of the port is postfixed with in/out, according to
		the direction of the communication. """

		# Compose the name of the port
		parent_name = component_instance.robot_parent.blender_obj.name

		# Extract the information for this middleware
		# This will be tailored for each middleware according to its needs
		poster_type = mw_data[1]
		poster_name = mw_data[2]


		# Choose what to do, depending on the poster type
		if poster_type == "genPos":
			poster_id = ors_genpos_poster.locate_poster(poster_name)
			print ("Located 'genPos' poster. ID=%d" % poster_id)
			if poster_id != None:
				self._poster_dict[component_name] = poster_id
				function_name = "read_genpos"
				try:
					# Get the reference to the function
					function = getattr(self, function_name)
				except AttributeError as detail:
					print ("ERROR: %s. Check the 'component_config.py' file for typos" % detail)
					return
				component_instance.output_functions.append(function)
			else:
				print ("Poster 'genPos' not created. Component will not work")

		elif poster_type == "viam":
			poster_id = self._init_viam_poster(component_instance, poster_name)
			self._poster_dict[component_name] = poster_id
			function_name = "write_viam"
			try:
				# Get the reference to the function
				function = getattr(self, function_name)
			except AttributeError as detail:
				print ("ERROR: %s. Check the 'component_config.py' file for typos" % detail)
				return
			component_instance.output_functions.append(function)

		"""
		elif poster_type == "pom":
			poster_id = self._init_viam_poster(component_instance, poster_name)
			self._poster_dict[component_name] = poster_id
			self._poster_dict[component_name] = poster_id
			function_name = "write_pom"
			try:
				# Get the reference to the function
				function = getattr(self, function_name)
			except AttributeError as detail:
				print ("ERROR: %s. Check the 'component_config.py' file for typos" % detail)
				return
			component_instance.output_functions.append(function)
		"""
	



	def read_genpos(self, component_instance):
		""" Read v,w from a genPos poster """
		# Read from the poster specified
		poster_id = self._poster_dict[component_instance.blender_obj.name]
		genpos_speed = ors_genpos_poster.read_genPos_data(poster_id)
		#print ("Tuple type ({0}) returned".format(type(genpos_speed)))
		#print ("Tuple data: (%.4f, %.4f)" % (genpos_speed.v, genpos_speed.w))

		component_instance.local_data['v'] = genpos_speed.v
		component_instance.local_data['w'] = genpos_speed.w


	def write_pom(self, component_instance):
		""" Write the position to a poaster

		The argument must be the instance to a morse gyroscope class. """
		# Get the id of the poster already created
		poster_id = self._poster_dict[component_instance.blender_obj.name]

		# Compute the current time
		pom_date, t = self._compute_date()

		# Get the data from the gyroscope object
		robot = component_instance.robot_parent

		poster_id = self._poster_dict[component_instance.blender_obj.name]
		ors_pom_poster.post_data(poster_id, robot.x, robot.y, robot.z,
				robot.yaw, robot.pitch, robot.roll, pom_date)


	def write_viam(self, component_instance):
		""" Write an image and all its data to a poster """
		# Get the id of the poster already created
		poster_id = self._poster_dict[component_instance.blender_obj.name]
		parent = component_instance.robot_parent

		mainToOrigin = parent.position_3d

		pom_robot_position =  ors_viam_poster.pom_position()
		pom_robot_position.x = mainToOrigin.x
		pom_robot_position.y = mainToOrigin.y
		pom_robot_position.z = mainToOrigin.z
		pom_robot_position.yaw = parent.yaw
		pom_robot_position.pitch = parent.pitch
		pom_robot_position.roll = parent.roll

		# Compute the current time
		pom_date, t = self._compute_date()

		ors_cameras = []
		ors_images = []

		# Cycle throught the cameras on the base
		# In normal circumstances, there will be two for stereo
		for camera_name in component_instance.camera_list:
			camera_instance = GameLogic.componentDict[camera_name]

			sensorToOrigin = camera_instance.position_3d
			mainToSensor = mainToOrigin.transformation3dWith(sensorToOrigin)

			imX = camera_instance.image_size_X
			imY = camera_instance.image_size_Y
			image_string = camera_instance.local_data['image']

			# Fill in the structure with the image information
			camera_data = ors_viam_poster.simu_image()
			camera_data.width = imX
			camera_data.height = imY
			camera_data.pom_tag = pom_date
			camera_data.tacq_sec = t.second
			camera_data.tacq_usec = t.microsecond
			camera_data.sensor = ors_viam_poster.pom_position()
			camera_data.sensor.x = mainToSensor.x
			camera_data.sensor.y = mainToSensor.y
			camera_data.sensor.z = mainToSensor.z
			# XXX +PI rotation is needed but I don't have any idea why !!
			camera_data.sensor.yaw = mainToSensor.yaw + 180.0
			camera_data.sensor.pitch = mainToSensor.pitch
			camera_data.sensor.roll = mainToSensor.roll

			ors_cameras.append(camera_data)
			ors_images.append(image_string)

		# Write to the poster with the data for both images
		posted = ors_viam_poster.post_viam_poster(poster_id, pom_robot_position, component_instance.num_cameras, ors_cameras[0], ors_images[0], ors_cameras[1], ors_images[1])




	def _init_viam_poster(self, component_instance, poster_name):
		""" Prepare the data for a viam poster """
		cameras = []
		pos_cam = []
		# Get the names of the data for the cameras
		for camera_name in component_instance.camera_list:
			camera_instance = GameLogic.componentDict[camera_name]

			# Create an image structure for each camera
			image_init = ors_viam_poster.simu_image_init()
			image_init.camera_name = camera_name
			image_init.width = camera_instance.image_size_X
			image_init.height = camera_instance.image_size_Y
			image_init.focal = camera_instance.image_focal
			pos_cam.append(camera_instance.blender_obj.position)
			cameras.append(image_init)

		baseline = 0
		# This is the case for a stereo camera
		if component_instance.num_cameras == 2:
			baseline = math.sqrt( math.pow(pos_cam[0][0] - pos_cam[1][0], 2) +
								  math.pow(pos_cam[0][1] - pos_cam[1][1], 2) +
								  math.pow(pos_cam[0][2] - pos_cam[1][2], 2))

		# Create the actual poster
		poster_id = ors_viam_poster.init_data(poster_name, "stereo_bank", component_instance.num_cameras, baseline, cameras[0], cameras[1])
		print ("viam poster ID: {0}".format(poster_id))
		if poster_id == None:
			print ("ERROR creating poster. This module may not work")

		return poster_id


	def _compute_date(self):
		""" Compute the current time

		( we only requiere that the date
		increases using a constant step so real time is ok)
		"""
		t = datetime.datetime.now()
		date = int(t.hour * 3600* 1000 + t.minute * 60 * 1000 +
				t.second * 1000 + t.microsecond / 1000)

		return date, t
