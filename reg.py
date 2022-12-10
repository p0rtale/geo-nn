from selenium import webdriver
import pickle
import argparse
from geotastic_bot import get_driver
import time
def main(name):
    browser = get_driver()
    time.sleep(2)
    browser.get('https://geotastic.net')

    input()
    pickle.dump( browser.get_cookies() , open(name,"wb"))
    browser.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", dest="cookie_name", required=True, type=str)
    args = parser.parse_args()
    main(args.cookie_name)

