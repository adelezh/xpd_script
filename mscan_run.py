# -*- coding: utf-8 -*-
"""
Created on Thu Aug 13 15:58:10 2020

@author: hzhong
"""

# -*- coding: utf-8 -*-
"""
Plan to run multiple sample under remote condition
This plan uses xpdacq protocol
"""

from xpdacq.beamtime import _configure_area_det
from xpdacq.beamtime import open_shutter_stub, close_shutter_stub
from collections import ChainMap, OrderedDict
import pandas as pd
import datetime
import functools
import time
from bluesky.callbacks import LiveFit
from bluesky.callbacks.mpl_plotting import LiveFitPlot
import numpy as np
from urllib import request
import json
from os import chmod
from pandas.core.common import flatten


def xpd_mscan(sample_list, pos_list, scanplan, delay=0, smpl_h=None, flt_h=None, flt_l=None, motor=sample_x):
    """
    xpd_mscan(sample_list, pos_list,  scanplan, delay=0, smpl_h=[1,4], flt_h=[1,0,0,0], flt_l=[0,0,0,0],motor=sample_x)

    multi-sample scan plan, parameters:
        sample_list: list of all samples in the sample holder
        pos_list: list of sample positions, double check make sure sample_list
        and pos_list are match
        motor: motor name which moves sample holder, default is sample_x
        scanplan: scanplan index in xpdacq scanplan
        delay: delay time in between each sample
        smpl_h: list of samples which needs special filter set
        flt_h: filter set for smpl_h
        flt_l: filter set for rest of the samples
    """
    if smpl_h is None:
        smpl_h = []
    length = len(sample_list)
    print('Total sample numbers:', length)
    if len(sample_list) == len(pos_list):
        for sample, pos in zip(sample_list, pos_list):
            print('Move sample: ', sample, 'to position: ', pos)
            motor.move(pos)
            if sample in smpl_h:
                xpd_flt_set(flt_h)
            else:
                if flt_l != None:
                    xpd_flt_set(flt_l)
            time.sleep(delay)
            xrun(sample, scanplan)

    else:
        print('sample list and pos_list Must have same length!')
        return None


def xpd_m2dscan(sample_list, posx_list, posy_list, scanplan, delay=0, smpl_h=None, flt_h=None, flt_l=None,
                motorx=sample_x, motory=sample_y):
    """
    xpd_m2dscan(sample_list, posx_list, posy_list, scanplan, delay=10, smpl_h=[1,4], flt_h=[1,0,0,0], flt_l=[0,0,0,0],
    motorx=sample_x, motory=sample_y)

    multi-sample scan plan, parameters:
        sample_list: list of all samples in the sample holder
        posx_list, posy_list: list of sample x and y positions, double check make sure sample_list
        and posx_list, posy_list are match
        motorx, motory: motors which moves sample holder, default is sample_x and sample_y
        scanplan: scanplan index in xpdacq scanplan
        delay: delay time in between each sample
        smpl_h: list of samples which needs special filter set flt_h
        flt_h: filter set for smpl_h
        flt_l: filter set for rest of the samples
    """

    if smpl_h is None:
        smpl_h = []
    length = len(sample_list)
    print('Total sample numbers:', length)
    if all(len(lst) == length for lst in [sample_list, posx_list, posy_list]):
        for sample, posx, posy in zip(sample_list, posx_list, posy_list):
            print('Move sample: ', sample, 'to position: ', posx, posy)
            motorx.move(posx)
            motory.move(posy)
            if sample in smpl_h:
                xpd_flt_set(flt_h)
            else:
                if flt_l != None:
                    xpd_flt_set(flt_l)
            time.sleep(delay)
            xrun(sample, scanplan)

    else:
        print('sample list and posx_list, posy_list Must have same length!')
        return None


def xpd_battery(smpl_list, posx_list, scanplan, cycle=1, delay=0, motor=sample_x):
    """ multi-battery cycling scan plan,
    xpd_battery(smpl_list, posx_list, scanplan, cycle=1, delay=0, motor=sample_x)

    parameters:
        smpl_list: list of all samples in the sample holder
        posx_list, list of sample x positions, smpl_list and posx_list should be match
        motorx, motor which moves sample holder, default is sample_x
        scanplan: scanplan index in xpdacq scanplan
        delay: delay time in between each sample
    """

    if len(smpl_list) == len(posx_list):
        for i in range(cycle):
            for smpl, posx in zip(smpl_list, posx_list):
                motor.move(posx)
                time.sleep(delay)
                xrun(smpl, scanplan)
    else:
        print('please check the length of sample lists and pos_list')
        return None


def xpd_batteryxy(smpl_list, posx_list, posy_list, scanplan, cycle=1, delay=0, motorx=sample_x, motory=sample_y):
    """ battery cycler experiment for multiple cells, each cell has different x and y positions
    example:
    xpd_batteryxy(smpl_list, posx_list, posy_list, scanplan, cycle=100, delay=0, motorx=sample_x, motory=sample_y)

    parameters:
        smpl_list: list of all samples in the sample holder
        posx_list, posy_list: list of sample x and y positions, smpl_list, posx_list, posy_list should be match
        motorx, motory: motors which move sample holder, default is sample_x and sample_y
        scanplan: scanplan index in xpdacq scanplan
        delay: delay time in between each sample
    """
    length = len(smpl_list)
    if all(len(lst) == length for lst in [smpl_list, posx_list, posy_list]):
        for i in range(cycle):
            for smpl, posx, posy in zip(smpl_list, posx_list, posy_list):
                motorx.move(posx)
                motory.move(posy)
                time.sleep(delay)
                xrun(smpl, scanplan)
    else:
        print('please check the length of sample lists and pos_list')
        return None


def linescan(smpl, exp_time, xstart, xend, xpoints, motor=sample_y, md=None, det=None):

    """  Measure multiple points along one line
    :param smpl: sample ID
    :param exp_time: total exposure time (in sec)
    :param xstart: start point
    :param xend: end point
    :param xpoints: number of points to measure
    :param motor: motor to move sample
    :param md: metadate
    :param det: extra detector you want to record
    :return:
    """

    plan = lineplan(exp_time, xstart, xend, xpoints, motor=motor, md=md, det=det)
    xrun(smpl, plan)


def mlinescan(smplist, poslist, exp_time, lstart, lend, lpoints, pos_motor=sample_x, lmotor=sample_y,
              smpl_h=None, flt_l=None, flt_h=None, det=None, md=None):

    """  Multiple samples, for each sample, measure multiple points along one line
    :param smplist: list of sample ID to be measured
    :param poslist: list of sample positions
    :param exp_time: total exposure time (in sec)
    :param lstart: line scan start point
    :param lend: line scan end point
    :param lpoints: line scan number of points to measure
    :param pos_motor: motor to move sample to the position
    :param lmotor: line scan motor
    :param smpl_h: list of sample which need special filters 
    :param flt_h: filter set for samples in the smpl_h
    :param flt_l: filter set for all other samples
    :param md: metadate
    :param det: extra detector you want to record
    :return:
    """
    if det is None:
        det = []
    if smpl_h is None:
        smpl_h = []
    dets = [pos_motor] + det
    length = len(sample_list)
    print('Total sample numbers:', length)
    if len(smplist) == len(poslist):
        for smpl, pos in zip(smplist, poslist):
            print('Move sample: ', sample, 'to position: ', pos)
            pos_motor.move(pos)
            if sample in smpl_h:
                xpd_flt_set(flt_h)
            else:
                if flt_l != None:
                    xpd_flt_set(flt_l)
            plan = lineplan(exp_time, lstart, lend, lpoints, motor=lmotor, md=md, det=dets)
            xrun(smpl, plan)

    else:
        print('sample list and pos_list Must have same length!')
        return None


def gridscan(smpl, exp_time, xstart, xstop, xpoints, ystart, ystop, ypoints,
             motorx=sample_x, motory=sample_y, md=None, det=None):
    
    """ grid scan for one sample:
    :param smpl: sample ID
    :param exp_time: total exposure time (in second)
    :param xstart: motorx (fast motor) start point
    :param xstop: motorx (fast motor) stop point
    :param xpoints: motorx (fast motor) number of points
    :param ystart: motory (slower motor) start point
    :param ystop: motory (slower motor) stop point
    :param ypoints: motory (slower motor) number of points
    :param motorx: fast motor to move sample
    :param motory: slower motor to move sample
    :param md: metadata
    :param det: extra detector you want to record
    :return:
    """
    #log the scannig process
    print(f"Starting grid scan for sample {smpl}...")
    print(f"X-axis: from {xstart} to {xstop}, points: {xpoints}")
    print(f"Y-axis: from {ystart} to {ystop}, points: {ypoints}")
    print(f"Exposure time per point: {exp_time} seconds")

    # Create the grid scan plan and execute
    plan = gridplan(exp_time, xstart, xstop, xpoints, ystart, ystop, ypoints, motorx=motorx, motory=motory, md=md, det=det)
    xrun(smpl, plan)


def mgridscan(smplist, exp_time, xcenter_list, xrange, xpoints, ycenter_list, yrange, ypoints, delay=1,
              motorx=sample_x, motory=sample_y, smpl_h=None, flt_l=None, flt_h=None, md=None, det=None):
    """ grid scan for multiple sample:
    :param smplist: list of sample ID to be measured
    :param poslist: list of sample positions
    :param exp_time: total exposure time (in sec)
    :param xcenter_list: list of x-axis center positions for samples
    :param xrange: x-axis scan range
    :param xpoints: number of points along the x-axis
    :param ycenter_list: list of y-axis center positions for samples
    :param yrange: y-axis scan range
    :param ypoints: number of points along the y-axis
    :param motorx: fast motor to move sample, default is sample_x
    :param motory: slower motor to move sample, default is sample_y
    :param smpl_h: list of sample which need special filters 
    :param flt_h: filter set for samples in the smpl_h
    :param flt_l: filter set for all other samples
    :param md: metadata
    :param det: extra detector you want to record
        :return:
        """

    if smpl_h is None:
        smpl_h = []

    # Check if the input lists (smplist, xcenter_list, ycenter_list) are of the same length
    length = len(smplist)
    if all(len(lst) == length for lst in [smplist, xcenter_list, ycenter_list]):
        for smpl, xcenter, ycenter in zip(smplist, xcenter_list, ycenter_list):
            print(f'move sample: {smpl} to center position {xcenter}, {ycenter}')
            motorx.move(xcenter)
            motory.move(ycenter)

            # Define x and y start/stop positions
            xstart = xcenter - xrange / 2
            xstop = xcenter + xrange / 2
            ystart = ycenter - yrange / 2
            ystop = ycenter + yrange / 2

            # Apply filter if necessary
            if sample in smpl_h:
                xpd_flt_set(flt_h)
            else:
                if flt_l is not None:
                    xpd_flt_set(flt_l)
            # Add delay after moving the sample and setting filters
            time.sleep(delay)
            # log the scannig process
            print(f"Starting grid scan for sample {smpl}...")
            print(f"X-axis: from {xstart} to {xstop}, points: {xpoints}")
            print(f"Y-axis: from {ystart} to {ystop}, points: {ypoints}")
            print(f"Exposure time per point: {exp_time} seconds")

            # Create the grid scan plan and execute the scan
            plan = gridplan(exp_time, xstart, xstop, xpoints, ystart, ystop, ypoints, motorx=motorx, motory=motory,
                            md=md, det=det)
            xrun(smpl, plan)


def xyposscan(smpl, exp_time, posxlist, posylist, motorx=sample_x, motory=sample_y, md=None, det=None):

    """ multiple points scan for one sample:
    :param smpl: sample ID
    :param exp_time: total exposure time (in second)
    :param posxlist: list of sample x positions
    :param posylist: list of sample y positions
    :param motorx: motor to move sample x position
    :param motory: motor to move sample y position
    :param md: metadata
    :param det: extra detector you want to record
    :return:
    """
    # Ensure posxlist and posylist have the same length
    if len(posxlist) != len(posylist):
        raise ValueError("posxlist and posylist must have the same length")

    # Logging the initial information
    print(f"Starting XY position scan for sample {smpl}...")
    print(f"Number of positions: {len(posxlist)}")
    print(f"Exposure time per position: {exp_time} seconds")

    # Create the plan using xyposplan and execute the plan using xrun
    plan = xyposplan(exp_time, posxlist, posylist, motorx=motorx, motory=motory, md=md, det=det)
    xrun(smpl, plan)
