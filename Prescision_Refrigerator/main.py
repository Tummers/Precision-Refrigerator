from webiopi.devices.sensor.onewiretemp import DS18B20  # Import thermometer libraries.
from webiopi.devices.sensor.onewiretemp import DS18S20
import sys
import pygame  # Pygame to recieve keyboard input.
from pygame.locals import *
import RPi.GPIO as GPIO
from Cooler import Cooler
from Thermometer import Thermometer
from Fan import Fan


def wait():
    """
    Condition to wait for next input to restart the cooler after a manual switch off.
    """
    while True:
        print("Waiting to restart. press 'c' to continue.")
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == K_c:
                return False


def main():
    GPIO.setwarnings(False)  # Turn of warnings from GPIO.
    pygame.init()

    tmp_aim = 21.5
    # tmp_aim = float(input("Enter the aim temperature: "))
    precision = 0.0625
    mass = 0.05
    v = 3.  # Supply voltage of current chip.
    i = 1.5  # Supply current of cooling chip.
    count = 0
    test_range = 100

    room_tmp = Thermometer(DS18S20(slave="10-000802deb0fc"), GPIO=GPIO, name="room")
    water_tmp = Thermometer(DS18B20(slave="28-000006cb82c6"), GPIO=GPIO, name="water", tmp_aim=tmp_aim,
                            show=True, arr_len=test_range)
    cooler = Cooler(GPIO=GPIO, tmp_aim=tmp_aim, therm=water_tmp, tmp_amb=room_tmp, name="Peltier",
                    precision=precision, input_pin=24)

    print("Keyboard commands:\n    'o' = Turn on cooler.\n    'f' = Turn off cooler.\n    's' = Set aim temperature.\n"
          "    'p' = Set precision of cooler.\n    't' = Show current Temperature.\n")

    while True:  # TODO Change to have a run function to leave main as a set up only once key input has been tested.
        for event in pygame.event.get():  # Receiving input to set the state
            if event.type == KEYDOWN:
                if event.key == K_o:
                    cooler.turn_on()
                    print("Cooler manually turned on.")
                if event.key == K_f:
                    cooler.turn_off()
                    print("Cooler manually turned off.")
                    wait()  # If turned of then don't turn straight back on again.
                if event.key == K_s:
                    tmp = float(input("Set the aim temperature:"))
                    cooler.set_tmp(tmp, pr=True)
                if event.key == K_p:
                    tmp = float(input("Set precision temperature range (i.e. +/- tmp):"))
                    cooler.set_precision(tmp, pr=True)
                if event.key == K_t:
                    water_tmp.print_tmp()
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

        cooler.rate_limit_conv()  # Converges the temperature by switching the state of the cooling chip using several different methods.
        water_tmp.plot_tmp(title="Temperature Varying with Time.", x_lab="Time Step",
                           y_lab="Temperature $^oC$", draw=False, smooth=True)

        rate, avg_rate = water_tmp.convergence_rate()  # Calculates the rate of temperature change.
        water_tmp.plot_rate(title="Rate of Temperature Change.", x_lab="Time Step",
                            y_lab="Rate $^oC / s$", draw=True)

        eff = cooler.efficiency(mass, v, i)  # Calculates the efficiency of the cooling system.
        if eff:  # Waits for temperature to settle around aim temperature.
            count += 1

        if count == test_range:  # When temperature settled calculate the convergence method score.
            water_tmp.conv_score(precision, start=0, stop=test_range)


main()
