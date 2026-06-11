#!/usr/bin/env python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pyvirtualdisplay import Display		# newly added
from time import sleep
from PIL import Image
import datetime
import boto3
import sys

from selenium.webdriver.common import action_chains, keys
"""
Using selenium logs into cloudwatch and gets screenshot of widget element
for Redshift-PercentageDiskSpaceUsedLine and Redshift-PercentageDiskSpaceUsedNumber
dashboards and uploads to s3.
"""
print('Loading functions')
# For Firefox:
# https://github.com/mozilla/geckodriver/releases/tag/v0.14.0
# extract geckodriver
# cp ~/Downloads/geckodriver /usr/local/bin

def upload_to_s3(filename, path, destbucket):
	"Uploads files to s3"

	s3 = boto3.client('s3', 'us-east-1')
	print("Copying file \"%s\" into S3 bucket..." % filename)

	s3.upload_file(path, destbucket, filename,
                         {'ACL': 'public-read','ContentType': "image/png"})		# Setting content type and making object public
	print("Successfully uploaded \"%s\" into s3://%s" % (filename, destbucket))

def take_screenshot(driver, name, url,  time_interval):
	"""
	Lauches the url for dashboard, in a new window each, then sets the
	time_interval for the widget after locating the presence of the
	element. Takes the screenshot and stores it locally. Using Image
	from PIL and location of the widget crops and replaces the image
	and calls upload_to_s3 function.
	"""

	print("Opening new window...")
	driver.execute_script("window.open()")
	driver.switch_to_window(driver.window_handles[-1])
	print("Driver.get URL {}".format(url))
	driver.get(url)
	print("Window opened")
	waiting_for_element = "smallprint"
	print("Waiting until 'presence of element by ID `{}`'...".format(waiting_for_element))
	# WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, waiting_for_element)))
	try:
	    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, waiting_for_element)))
	except TimeoutException:
	    print("Element was not found... maybe we're already logged in... ignoring...")
	    pass

	if driver.title == 'Amazon Web Services Sign-In':
		login_namestr = 'service.utils'
		passwordstr = 't-mp{hhN#5d&'
		print('Logging into AWS cloudwatch...')
		# Sometimes the driver goes to login page
		driver.find_element_by_id('username').send_keys(login_namestr)	# instead of the dashboard which, stops
		driver.find_element_by_id('password').send_keys(passwordstr)	# the code, this checks the title and if
		driver.find_element_by_id('signin_button').click()				# on login page logs into the site.

	print("Waiting 10s...")
	# waiting_for_element = time_interval
	# print("Waiting until 'presence of element by CSS_SELECTOR `{}`'...".format(waiting_for_element))
        # WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, waiting_for_element))).click()

	print('Taking screenshot of %s...' % name)

	sleep(10)
	screenshot_name = '%s_%s.png' % (name, datetime.datetime.now().strftime('%Y-%m-%d'))	# set name using widget name and date
	path = '' + screenshot_name	# set path

	driver.execute_script("document.querySelector('.react-grid-item').style.height = '800px';")
	widget = driver.find_element_by_css_selector('.cwdb-chart-container-background')
	location = widget.location
	size = widget.size

	driver.save_screenshot(path)
	im = Image.open(path)
	left   = int(location['x'])# * 2
	top    = int(location['y'])# * 2
	right  = int(location['x'] + size['width'])# * 2
	bottom = int(location['y'] + size['height'])# * 2

	#print(widget, location, size, im, left, top, right, bottom)

	im = im.crop((left, top, right, bottom))
	im.save(path)
	upload_to_s3(path=path, filename=screenshot_name, destbucket='static.annalect.com')

def sign_in():
	"""
	Sets up driver, logs into AWS console and calls take_screenshot function, for
	Redshift-PercentageDiskSpaceUsedLine and Redshift-PercentageDiskSpaceUsedNumber dashboards.
	"""
        print('Loading sign_in functions')
	display = Display(visible=0, size=(1500, 1000))
	display.start()
        #Xvfb :99 -ac &
        #export DISPLAY=:99

	driver = webdriver.Firefox()

	login_namestr = 'service.utils'
	passwordstr = 't-mp{hhN#5d&'

	driver.get('https://annalect-infrastructure.signin.aws.amazon.com/console')

	print('Signing in ...')

	signedIn = False
	maxretries = 10
	while not signedIn:
		try:
			WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, 'username'))).send_keys(login_namestr)
			WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(passwordstr)
			WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, 'signin_button'))).click()
			signedIn = True
		except Exception as e:
			maxretries -= 1
			print 'Error logging in... retrying in 3s'
			print e
			signedIn = False
			if maxretries == 0:
				sys.exit('Could not log in after {} retries'.format(maxretries))
			sleep(3)


	print('Loading...')

	# Screenshot for Redshift-PercentageDiskSpaceUsedLine
	take_screenshot(driver=driver, name='Redshift-PercentageDiskSpaceUsedLine',
					url='https://console.aws.amazon.com/cloudwatch/home?region=us-e'
						'ast-1#dashboards:name=Redshift-PercentageDiskSpaceUsedLine',
				    time_interval='li.cwui-datepicker-quickpick:nth-child(6) > a:nth-child(1)')#'//a[@data-reactid=".1.1.0.0.0.6.0.0.0.0.$5.0"]')

	# Screenshot for Redshift-PercentageDiskSpaceUsedNumber
	take_screenshot(driver=driver, name='Redshift-PercentageDiskSpaceUsedNumber',
					url='https://console.aws.amazon.com/cloudwatch/home?region=us-ea'
						'st-1#dashboards:name=Redshift-PercentageDiskSpaceUsedNumber',
     					time_interval="li.cwui-datepicker-quickpick:nth-child(1) > a:nth-child(1)")

	print('Exiting...')
	driver.quit()
        display.stop()

#if __name__ == "__main__": sign_in()
sign_in()
