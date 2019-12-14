'''
/*
 * Copyright 2019 ground0state. All Rights Reserved.
 * Released under the MIT license
 * https://opensource.org/licenses/mit-license.php
/
'''

import numpy as np


class AR1():
    def __init__(self):
        self.const = 1
        self.phi = 0.5
        self.sigma = 1
        self.present_value = 0

    def get_value(self, p=0.01):
        self.present_value = self.const + self.phi * \
            self.present_value + self.sigma*np.random.randn()

        if p > np.random.rand():
            # pの確率で起きる事象
            return self.present_value*100
        else:
            return self.present_value


class MA1():
    def __init__(self):
        self.theta_0 = 1
        self.theta_1 = 0.5
        self.sigma = 1
        self.previous_error = 0.3

    def get_value(self, p=0.01):
        present_error = self.sigma*np.random.randn()

        y = self.theta_0 + present_error + self.theta_1*self.previous_error
        self.previous_error = present_error

        if p > np.random.rand():
            # pの確率で起きる事象
            return y*100
        else:
            return y


class ARIMA111():
    def __init__(self):
        self.theta_0 = 1
        self.theta_1 = 0.5
        self.previous_error = 0.7

        self.const = -1
        self.phi = 0.5
        self.sigma = 1
        self.present_value = 0

    def get_value(self, p=0.01):
        present_error = self.sigma*np.random.randn()
        self.present_value = self.const + self.phi * \
            self.present_value + self.sigma*np.random.randn() + self.theta_0 + present_error + \
            self.theta_1*self.previous_error
        self.previous_error = present_error

        if p > np.random.rand():
            # pの確率で起きる事象
            return self.present_value*100
        else:
            return self.present_value
