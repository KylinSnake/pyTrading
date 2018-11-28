from Management import *
import os

if __name__ == '__main__':
	if os.name == 'nt':
		main(['script','c:\\workstation\\config\\config.dos.yaml'])
	else:
		main(['script','../config/config.linux.yaml'])
