import numpy as np
import matplotlib.pyplot as plt
import time
from scipy.interpolate import spline


class Thermometer(object):
    def __init__(self, address, GPIO, name, tmp_aim=False, arr_len=500, show=False):
        """
        Thermometer class controlling a thermometer unit.
        :param address: Slave address of thermometer.
        :param GPIO: (class) GPIO class from RPi.GPIO library.
        :param name: (string) Thermometer name i.e. "room temperature".
        :param tmp_aim: (float) The aim temperature in degrees Celsius.
        :param arr_len: (int) Length of display array stored.
        :param show: (boolean) If plots are to be displayed.
        """
        self.name = name
        self.therm = address
        self.tmp_arr = np.full(arr_len, self.print_tmp())  # changes from np.zeros so the full array is the initial tmp
        self.time_arr = np.arange(arr_len)  # Update with curr time every time the tmp is updated
        self.rate_arr = np.zeros(arr_len)
        self.tmp_aim = tmp_aim
        self.min_precision = 0.0625
        self.last_time = 0
        self.init_out_file = False

        if show:
            plt.ion()  # Initialize figure to be drawn on.
            self.fig = plt.figure()
            self.ax1 = self.fig.add_subplot(211)
            self.ax2 = self.fig.add_subplot(212)

    def cels_to_K(self, cels):
        return cels + 273

    def K_to_cels(self, k):
        return k - 273

    def print_tmp(self):
        tmp = self.therm.getCelsius()
        print("Current %s temperature is at %.2f degrees celsius." % (self.name, tmp))
        return tmp

    def get_tmp(self):
        """
        Records the current temperature of the thermometer in the last element of the temperature array and rolls
        the rest of the array back: [1,2,3,4] -> add 5 [2,3,4,5]
        :return: (float) Current temperature, degrees celsius.
        """
        self.tmp_arr = np.roll(self.tmp_arr, -1)  # Rolls array back one position.
        tmp = self.therm.getCelsius()  # Get current temperature.
        self.last_time = time.time()
        self.tmp_arr[len(self.tmp_arr) - 1] = tmp  # New tmp in last position of the array.
        return tmp

    def get_rate_avg(self, range=3):
        """Return the avg rate over the last range time steps."""
        return np.average(self.rate_arr[-range:])

    def plot_tmp(self, title="", x_lab="", y_lab="", draw=True, smooth=0):
        """
        Clears previous plot and plots temperate vs time on an ion canvas with the aim temperature shown in red.
        This has the advantage over FuncAnimation as the window can remain open while other operations are carried out.
        :param draw: (boolean) Displays updated plot.
        :param smooth: (int) 0: Plots raw data, 1: plots smoothed data, 2: plots both smooth and raw data together.
        """
        self.ax1.clear()
        self.ax1.set_title(title)
        self.ax1.set_xlabel(x_lab + " (Red line = Aim Temperature)")
        self.ax1.set_ylabel(y_lab)
        if smooth == 1 or smooth == 2:
            new = np.linspace(self.time_arr[0], self.time_arr[-1], 150)
            sm = spline(self.time_arr, self.tmp_arr, new)  # Creates smoothed data.
            self.ax1.plot(new, sm)  # Plots smoothed data.
        if smooth == 0 or smooth == 2:
            self.ax1.plot(self.time_arr, self.tmp_arr)  # Plots raw data.
        if self.tmp_aim:
            self.ax1.axhline(y=self.tmp_aim, color=(1, 0, 0), linewidth=.8)  # Shows aim temperature as red horizontal line.
        if draw:
            plt.tight_layout()
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()

    def convergence_rate(self):
        """
        Calculates the rate of convergence on the aim temperature in degrees per second.
        :return: Current rate of convergence and average rate of convergence over whole array.
        """
        self.rate_arr = np.roll(self.rate_arr, -1)  # Rolls the array back by one [1,2,3] -> [2,3,4]
        elapsed_time = time.time() - self.last_time
        tmp_dif = self.tmp_arr[-1] - self.tmp_aim
        last_tmp_dif = self.tmp_arr[-2] - self.tmp_aim  # compares temperature difference to tmp_aim with current tmp_dif.
        change = tmp_dif - last_tmp_dif
        rate = change / elapsed_time  # Rate given by the change in temperature divided by the time taken for the change.
        self.rate_arr[len(self.rate_arr) - 1] = rate
        return rate, np.average(self.rate_arr[-5:])

    def plot_rate(self,  title="", x_lab="", y_lab="", draw=True, smooth=0):
        """
        Clears previous plot and plots temperature change rate vs time on an ion canvas with the aim temperature
        shown in red. This has the advantage over FuncAnimation as the window can remain open while other operations
        are carried out.
        :param draw: (boolean) Displays updated plot.
        :param smooth: (int) 0: Plots raw data, 1: plots smoothed data, 2: plots both smooth and raw data together.
        """
        self.ax2.clear()
        self.ax2.axhline(y=np.average(self.rate_arr), color=(1, 0, 0), linewidth=.8)
        self.ax2.set_title(title)
        self.ax2.set_xlabel(x_lab + " (Red line = Average Rate)")
        self.ax2.set_ylabel(y_lab)
        if smooth == 1 or smooth == 2:
            new = np.linspace(self.time_arr[0], self.time_arr[-1], 150)
            sm = spline(self.time_arr, self.rate_arr, new)  # Creates smoothed data.
            self.ax2.plot(new, sm)  # Plots smoothed data.
        if smooth == 0 or smooth == 2:
            self.ax2.plot(self.time_arr, self.rate_arr)  # Plots raw data.
        if draw:
            plt.tight_layout()
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()

    def conv_score(self, precision, start=0, stop=50):
        """
        Calculates a score based on how long the temperature was within the precision range of the aim temperature.
        Score = number within acceptable rance / total number tested.
        :param precision: (float) Acceptable range around aim temperature. tmp +/- precision.
        :param start: (int) Start of test range.
        :param stop: (int) End of test range.
        :return: (float) Calculated Score
        """
        ran_low = self.tmp_aim - precision
        ran_high = self.tmp_aim + precision
        count = 0
        for tmp in self.tmp_arr[start:stop]:
            if tmp > ran_high or tmp < ran_low:
                count += 1
        test_range = stop - start
        score = count / test_range
        return score

    def store_data(self, out_file="cooling_data_hyst.txt"):
        if not self.init_out_file:
            f = open(out_file, 'w')
            # f.write("Tempreature data from precision refrigerator measured in degreese celcius.")
            f.write("Converge\nTempreature data from precision refrigerator measured in degreese celcius over a prolonged cooling phase.\n\
                     Hysteretic_cov\n\
                     Start room temperature = 23.62") 

            self.init_out_file = True
        else:
            f = open(out_file, 'a')
        f.write("\n%f" % (self.tmp_arr[-1]))
        f.close()
