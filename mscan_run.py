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
    """ multi-sample scan

    Perform a multi-sample scan by moving samples to specified positions, applying filters, and executing a scan plan.

    This function moves multiple samples to their corresponding positions using a specified motor, applies filter sets
    based on whether the sample is in the special sample list (`smpl_h`), and then runs the specified scan plan for
    each sample. Optionally, a delay can be added between each sample move.

    example:
        >>> samples = [1, 2, 3]
        >>> positions = [10, 20, 30]
        >>> scan_plan = 0
        >>> special_samples = [1, 3]
        >>> special_filter = [1, 0, 0, 0]
        >>> default_filter = [0, 0, 0, 0]
        >>> xpd_mscan(samples, positions, scan_plan, delay=2, smpl_h=special_samples, flt_h=special_filter, flt_l=default_filter)


    parameters:
        sample_list: list of sample IDs in the sample holder
        pos_list: list of sample positions, sample_list and pos_list should be match
        motor: motor name which moves sample holder, default is sample_x
        scanplan: scanplan ID
        delay: delay time in between each sample
        smpl_h: list of samples which needs special filter set
        flt_h: filter set for smpl_h
        flt_l: filter set for rest of the samples
    """
    # Input validation
    assert len(sample_list) == len(pos_list), "sample_list and pos_list must have the same length"

    # Ensure that if smpl_h is provided, both flt_h and flt_l are provided
    if smpl_h is not None and (flt_h is None or flt_l is None):
        raise ValueError("If smpl_h is provided, both flt_h and flt_l must also be provided.")

    if smpl_h is None:
        smpl_h = []

    length = len(sample_list)
    print('Total sample numbers:', length)

    for sample, pos in zip(sample_list, pos_list):
        print(f'Move sample {sample} to position {pos}')
        motor.move(pos)

        # Apply filter if necessary
        if sample in smpl_h:
            if flt_h is not None:
                print(f'Applying special filter set {flt_h} for sample {sample}')
                xpd_flt_set(flt_h)
        else:
            if flt_l is not None:
                print(f'Applying standard filter set {flt_l} for sample {sample}')
                xpd_flt_set(flt_l)

        # Delay between sample movements if specified
        time.sleep(delay)

        # Run the scan plan
        print(f'Running scan plan for sample {sample}')
        xrun(sample, scanplan)

    print('Multi-sample scan complete.')



def xpd_m2dscan(sample_list, posx_list, posy_list, scanplan, delay=0, smpl_h=None, flt_h=None, flt_l=None,
                motorx=sample_x, motory=sample_y):
    """ Perform multi-sample scans by moving samples to predefined x and y positions, applying filters,
    and executing a scan plan.

    Example:

        >>> samples = [1, 2, 3]
        >>> x_positions = [10, 20, 30]
        >>> y_positions = [5, 15, 25]
        >>> scan_plan = 0
        >>> special_samples = [1, 3]
        >>> special_filter = [1, 0, 0, 0]
        >>> default_filter = [0, 0, 0, 0]
        >>> xpd_m2dscan(samples, x_positions, y_positions, scan_plan, delay=2, smpl_h=special_samples, flt_h=special_filter, flt_l=default_filter)
        if all samples use the same filter set which has been set manually
        >>> xpd_m2dscan(samples, x_positions, y_positions, scan_plan, delay=2)

    multi-sample scan plan, parameters:
        sample_list (list): list of all samples in the sample holder
        posx_lis, posy_list: list of sample x and y positions, sample_list, posx_list, posy_list should be match
        motorx, motory: motors which moves sample holder, default is sample_x and sample_y
        scanplan: scanplan index
        delay: delay time in between each sample
        smpl_h: list of samples which needs special filter set flt_h
        flt_h: filter set for samples in smpl_h
        flt_l: filter set for rest of the samples
    """
    # Input validation
    
    if len(sample_list) != len(posx_list) or len(posx_list) != len(posy_list):
        raise ValueError("sample_list, posx_list, and posy_list must have the same length")
    
    # Ensure that if smpl_h is provided, both flt_h and flt_l are provided
    if smpl_h is not None and (flt_h is None or flt_l is None):
        raise ValueError("If smpl_h is provided, both flt_h and flt_l must also be provided.")

    if smpl_h is None:
        smpl_h = []
    length = len(sample_list)
    print('Total sample numbers:', length)

    for sample, posx, posy in zip(sample_list, posx_list, posy_list):
        print(f'Move sample {sample} to position ({posx}, {posy})')
        motorx.move(posx)
        motory.move(posy)
        if sample in smpl_h:
            if flt_h is not None:
                xpd_flt_set(flt_h)
        else:
            if flt_l is not None:
                xpd_flt_set(flt_l)
        # Delay between samples
        time.sleep(delay)
        #run the scan plan
        xrun(sample, scanplan)

        return None

def xpd_battery(smpl_list, posx_list, scanplan, cycle=1, delay=0, motor=sample_x):
    """ multi-battery cycling scan plan, all samples at same y position

    Example:
        >>> samples = [1, 2, 3]
        >>> x_positions = [10, 20, 30]
        >>> scan_plan = 0
        >>> xpd_battery(samples, x_positions, scan_plan, cycle=2, delay=2)

    parameters:
        smpl_list (list): List of sample IDs that need to be scanned.
        posx_list (list): List of x positions corresponding to each sample in `smpl_list`.
        scanplan (str): The scan plan to be executed for each sample.
        cycle (int, optional): The number of times to cycle through the samples. Default is 1.
        delay (int or float, optional): Time delay (in seconds) between moving each sample and running the scan.
            Default is 0 (no delay).
        motor (object, optional): Motor object used to move the sample holder along the x-axis. Default is `sample_x`.


    """

    # Input validation
    assert len(smpl_list) == len(posx_list), "smpl_list and posx_list must have the same length"

    length = len(smpl_list)
    print('Total sample numbers:', length)

    for i in range(cycle):

        for smpl, posx in zip(smpl_list, posx_list):
            print(f'Cycle {i+1}, moving sample {smpl} to position {posx}')
            motor.move(posx)
            time.sleep(delay)
            xrun(smpl, scanplan)

    return None


def xpd_batteryxy(smpl_list, posx_list, posy_list, scanplan, cycle=1, delay=0, motorx=sample_x, motory=sample_y):
    """ battery cycling experiment for multiple cells, each at different x and y positions

     Example:
        >>> samples = [1, 2, 3]
        >>> x_positions = [10, 20, 30]
        >>> y_positions = [5, 15, 25]
        >>> scan_plan = 0
        # Perform a battery cycling scan with 2 cycles and a 2-second delay between each sample move
        >>> xpd_batteryxy(samples, x_positions, y_positions, scan_plan, cycle=2, delay=2)

    Parameters:
        smpl_list (list): List of sample IDs that need to be scanned.
        posx_list (list): List of x positions corresponding to each sample in `smpl_list`.
        posy_list (list): List of y positions corresponding to each sample in `smpl_list`.
        scanplan (int): The scan plan to be executed for each sample.
        cycle (int, optional): The number of times to cycle through the samples. Default is 1.
        delay (int or float, optional): Time delay (in seconds) between moving each sample and running the scan.
            Default is 0 (no delay).
        motorx (object, optional): Motor object used to move the sample holder along the x-axis. Default is `sample_x`.
        motory (object, optional): Motor object used to move the sample holder along the y-axis. Default is `sample_y`.


        smpl_list: list of all samples in the sample holder
        posx_list, posy_list: list of sample x and y positions, smpl_list, posx_list, posy_list should be match
        motorx, motory: motors which move sample holder, default is sample_x and sample_y
        scanplan: scanplan index in xpdacq scanplan
        delay: delay time in between each sample
    """

    # Input validation
    if len(smplist) != len(posx_list) or len(posx_list) != len(posy_list):
        raise ValueError("smpl_list, posx_list, and posy_list must have the same length")
    
    length = len(smpl_list)
    print(f'Total sample numbers: {length}')

    for i in range(cycle):
        print(f"Starting cycle {i + 1}/{cycle}")
        # Loop through each sample and perform the scan
        for smpl, posx, posy in zip(smpl_list, posx_list, posy_list):
            print(f'Cycle {i + 1}, moving sample {smpl} to position (x = {posx}, y = {posy})')
            motorx.move(posx)
            motory.move(posy)
            time.sleep(delay)
            xrun(smpl, scanplan)



def linescan(smpl, exp_time, xstart, xend, xpoints, motor=sample_y, md=None, det=None):

    """  line scan by moving a motor between `xstart` and `xend` in `xpoints` steps and recording measurements.

    Example:
        >>> linescan(1, 5.0, 0, 10, 5, motor=sample_y)

    Parameters
        smpl (int): Sample ID to be measured.
        exp_time (float): Total exposure time (in seconds) for each measurement point.
        xstart (float): Starting position of the line scan.
        xend (float): End position of the line scan.
        xpoints (int): Number of points to measure along the line.
        motor (object, optional): Motor object used to move the sample. Default is `sample_y`.
        md (dict, optional): Metadata to be associated with the scan. Default is None.
        det (list, optional): List of extra detectors to record during the scan. Default is None.

    """
    # Log the scan details
    print(f'Starting line scan for sample {smpl}')
    print(f'Line scan parameters: xstart={xstart}, xend={xend}, xpoints={xpoints}, exp_time={exp_time}s')

    # Create the scan plan
    plan = lineplan(exp_time, xstart, xend, xpoints, motor=motor, md=md, det=det)
    xrun(smpl, plan)


def mlinescan(smplist, poslist, exp_time, lstart, lend, lpoints, pos_motor=sample_x, lmotor=sample_y,
              smpl_h=None, flt_l=None, flt_h=None, det=None, md=None):
    """ Perform line scans for multiple samples. For each sample, the function moves the sample to a specified position
     and measures multiple points along a line using a motor.

     Example:
         >>> samples = [1, 2, 3]
         >>> positions = [10, 20, 30]
         >>> mlinescan(samples, positions, 5.0, 0, 10, 5)

     Parameters
         smplist (list): List of sample IDs to be measured.
         poslist (list): List of sample positions corresponding to `smplist`.
         exp_time (float): Total exposure time (in seconds) for each measurement point.
         lstart (float): Starting position of the line scan.
         lend (float): End position of the line scan.
         lpoints (int): Number of points to measure along the line.
         pos_motor (object, optional): Motor object used to move samples to their positions. Default is `sample_x`.
         lmotor (object, optional): Motor object used to perform the line scan. Default is `sample_y`.
         smpl_h (list, optional): List of samples requiring special filter sets. Default is None.
         flt_h (list, optional): Filter set for the samples in `smpl_h`. Default is None.
         flt_l (list, optional): Filter set for all other samples. Default is None.
         det (list, optional): List of extra detectors to record during the scan. Default is None.
         md (dict, optional): Metadata to be associated with the scan. Default is None.

     """
    # Input validation
    assert len(smplist) == len(poslist), "sample_list and pos_list must have the same length"

    # Ensure that if smpl_h is provided, both flt_h and flt_l are provided
    if smpl_h is not None and (flt_h is None or flt_l is None):
        raise ValueError("If smpl_h is provided, both flt_h and flt_l must also be provided.")

    if det is None:
        det = []
    if smpl_h is None:
        smpl_h = []

    # Combine the position motor with other detectors if any
    dets = [pos_motor] + det
    length = len(smplist)
    print(f'Total sample numbers:{length}')

    for smpl, pos in zip(smplist, poslist):
        print(f'Moving sample {smpl} to position {pos}')
        pos_motor.move(pos)

        # Apply filters if necessary
        if sample in smpl_h:
            if flt_h is not None:
                xpd_flt_set(flt_h)
        else:
            if flt_l is not None:
                xpd_flt_set(flt_l)

        plan = lineplan(exp_time, lstart, lend, lpoints, motor=lmotor, md=md, det=dets)
        xrun(smpl, plan)




def gridscan(smpl, exp_time, xstart, xstop, xpoints, ystart, ystop, ypoints,
             motorx=sample_x, motory=sample_y, md=None, det=None):
    """
        Perform a grid scan by moving a sample across a grid of x and y points.

        Example:
            >>> gridscan(1, 5, 0, 10, 5, 0, 10, 5)
        Parameters:
            smpl (int): Sample ID to be measured.
            exp_time (float): Total exposure time (in seconds) for each measurement point.
            xstart (float): Starting position on the x-axis.
            xstop (float): End position on the x-axis.
            xpoints (int): Number of points to measure along the x-axis.
            ystart (float): Starting position on the y-axis.
            ystop (float): End position on the y-axis.
            ypoints (int): Number of points to measure along the y-axis.
            motorx (object, optional): Motor object used to move the sample along the x-axis. Default is `sample_x`.
            motory (object, optional): Motor object used to move the sample along the y-axis. Default is `sample_y`.
            md (dict, optional): Metadata to be associated with the scan. Default is None.
            det (list, optional): List of extra detectors to record during the scan. Default is None.

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

    """ Perform grid scan for multiple samples.

        Example:
            >>> samples = [1, 2, 3]
            >>> x_centers = [10, 20, 30]
            >>> y_centers = [5, 15, 25]
            >>> mgridscan(samples, 5.0, x_centers, 10, 5, y_centers, 10, 5)

        Parameters:
            smplist (list): List of sample IDs to be measured.
            exp_time (float): Total exposure time (in seconds) for each measurement point.
            xcenter_list (list): List of x-axis center positions for samples.
            xrange (float): Range to scan along the x-axis.
            xpoints (int): Number of points along the x-axis.
            ycenter_list (list): List of y-axis center positions for samples.
            yrange (float): Range to scan along the y-axis.
            ypoints (int): Number of points along the y-axis.
            delay (int or float, optional): Time delay (in seconds) between each sample. Default is 1 second.
            motorx (object, optional): Motor object to move the sample along the x-axis. Default is `sample_x`.
            motory (object, optional): Motor object to move the sample along the y-axis. Default is `sample_y`.
            smpl_h (list, optional): List of samples requiring special filters. Default is None.
            flt_h (list, optional): Filter set for the samples in `smpl_h`. Default is None.
            flt_l (list, optional): Filter set for all other samples. Default is None.
            md (dict, optional): Metadata to be associated with the scan. Default is None.
            det (list, optional): Extra detectors to record during the scan. Default is None.

        """

    # Input validation
    if len(smplist) != len(xcenter_list) or len(xcenter_list) != len(ycenter_list):
        raise ValueError("smplist, xcenter_list, and ycenter_list must have the same length")

    # Ensure that if smpl_h is provided, both flt_h and flt_l are provided
    if smpl_h is not None and (flt_h is None or flt_l is None):
        raise ValueError("If smpl_h is provided, both flt_h and flt_l must also be provided.")

    if smpl_h is None:
        smpl_h = []

    length = len(smplist)
    print(f'Total number of samples: {length}')

    for smpl, xcenter, ycenter in zip(smplist, xcenter_list, ycenter_list):
        print(f'Moving sample {smpl} to center position (x = {xcenter}, y = {ycenter})')
        motorx.move(xcenter)
        motory.move(ycenter)

        # Define x and y start/stop positions for the grid scan
        xstart = xcenter - xrange / 2
        xstop = xcenter + xrange / 2
        ystart = ycenter - yrange / 2
        ystop = ycenter + yrange / 2

        # Apply filters based on sample
        if smpl in smpl_h:
            if flt_h is not None:
                print(f'Applying special filter set {flt_h} for sample {smpl}')
                xpd_flt_set(flt_h)
        else:
            if flt_l is not None:
                print(f'Applying default filter set {flt_l} for sample {smpl}')
                xpd_flt_set(flt_l)

        # Add delay after moving the sample and setting filters
        time.sleep(delay)

        # Log the scanning process
        print(f"Starting grid scan for sample {smpl}...")
        print(f"X-axis: from {xstart} to {xstop}, points: {xpoints}")
        print(f"Y-axis: from {ystart} to {ystop}, points: {ypoints}")
        print(f"Exposure time per point: {exp_time} seconds")

        # Create the grid scan plan and execute the scan
        plan = gridplan(exp_time, xstart, xstop, xpoints, ystart, ystop, ypoints, motorx=motorx, motory=motory, md=md,
                        det=det)
        xrun(smpl, plan)


def xyposscan(smpl, exp_time, posxlist, posylist, motorx=sample_x, motory=sample_y, md=None, det=None):

    """ Perform a multiple points scan for one sample by moving to predefined x and y positions.

        Parameters:
            smpl (str or int): Sample ID.
            exp_time (float): Total exposure time (in seconds) for each measurement.
            posxlist (list): List of x positions for the sample.
            posylist (list): List of y positions for the sample.
            motorx (object, optional): Motor object to move the sample along the x-axis. Default is `sample_x`.
            motory (object, optional): Motor object to move the sample along the y-axis. Default is `sample_y`.
            md (dict, optional): Metadata to be associated with the scan. Default is None.
            det (list, optional): Extra detectors to record during the scan. Default is None.

        Example:
            >>> xyposscan(1, 5.0, [0, 10, 20], [0, 15, 25])

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
