from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Code referenced from https://gist.github.com/gyglim/1f8dfb1b5c82627ae3efcfbbadb9f514
import os
import time
import sys
import torch
USE_TENSORBOARD = True

class Logger(object):
    def __init__(self, filename):
        if not os.path.exists('./log'):
            os.mkdir('./log')
        self.filename = os.path.join('./log', filename)
        if os.path.exists(self.filename):
            os.remove(self.filename)
        file = open(self.filename, 'w')
        file.close()
    
    def write(self, str=''):
        file = open(self.filename, 'a')
        file.write(str)
        file.write('\n')
        file.close()
        print(str)
