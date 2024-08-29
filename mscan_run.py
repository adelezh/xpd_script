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


def xpd_mscan(sample_list, pos_list, scanplan, delay=0, smpl_h=[], flt_h=None, flt_l=None, motor=sample_x):
    """
    xpd_mscan(sample_list, pos_list,  scanplan, delay=0, smpl_h=[1,4], flt_h=[1,0,0,0], flt_l=[0,0,0,0],motor=sample_x)

    multi-sample scan plan, parameters:
        sample_list: list of all samples in the sample holder
        pos_list: list of sample positions, double check make sure sample_list
        and pos_list are match
        motor: motor name which moves sample holder, default is sample_x
        scanplan: scanplan index in xpdacq scanplan
        delay: dalay time in between each sample
        smpl_h: list of samples which needs special filter set
        flt_h: filter set for smpl_h
        flt_l: filter set for rest of the samples
    """

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


def xpd_m2dscan(sample_list, posx_list, posy_list, scanplan, delay=0, smpl_h=[], flt_h=None, flt_l=None,
                motorx=sample_x, motory=sample_y):
    """
    xpd_m2dscan(sample_list, posx_list, posy_list, scanplan, delay=10, smpl_h=[1,4], flt_h=[1,0,0,0], flt_l=[0,0,0,0],motorx=sample_x, motory=sample_y)

    multi-sample scan plan, parameters:
        sample_list: list of all samples in the sample holder
        posx_list, posy_list: list of sample x and y positions, double check make sure sample_list
        and posx_list, posy_list are match
        motorx, motory: motors which moves sample holder, default is sample_x and sample_y
        scanplan: scanplan index in xpdacq scanplan
        delay: dalay time in between each sample
        smpl_h: list of samples which needs special filter set flt_h
        flt_h: filter set for smpl_h
        flt_l: filter set for rest of the samples
    """

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
    """
    xpd_battery(smpl_list, posx_list, scanplan, cycle=1, delay=0, motor=sample_x)

    multi-battery cycling scan plan, parameters:
        smpl_list: list of all samples in the sample holder
        posx_list, list of sample x positions, double check make sure smpl_list
        and posx_list are match
        motorx, motor which moves sample holder, default is sample_x
        scanplan: scanplan index in xpdacq scanplan
        delay: dalay time in between each sample
    """

    if len(smpl_list) == len(posx_list):
        for i in range(cycle):
            for smpl, posx in zip(smpl_list, posx_list):
                motor.move(posx)
                time.sleep(delay)
                xrun(smpl, scanplan)
    else:
        print('please check the lenght of sample lists and pos_list')
        return None


def xpd_batteryxy(smpl_list, posx_list, posy_list, scanplan, cycle=1, delay=0, motorx=sample_x, motory=sample_y):
    """ battery cycler experiment for multiple cells, each cell has different x and y positions
    xpd_batteryxy(smpl_list, posx_list, posy_list, scanplan, cycle=1, delay=0, motorx=sample_x, motory=sample_y)

    multi-battery cycling scan plan, parameters:
        smpl_list: list of all samples in the sample holder
        posx_list, posy_list: list of sample x and y positions, double check make sure smpl_list
        and posx_list, posy_list are match
        motorx, motory: motors which move sample holder, default is sample_x and sample_y
        scanplan: scanplan index in xpdacq scanplan
        delay: dalay time in between each sample
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
        print('please check the lenght of sample lists and pos_list')
        return None


def linescan(smpl, exp_time, xstart, xend, xpoints, motor=sample_y, md=None, dets=[sample_y]):

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

    plan = lineplan(exp_time, xstart, xend, xpoints, motor=motor, md=md, dets=dets)
    xrun(smpl, plan)


def mlinescan(smplist, poslist, exp_time, lstart, lend, lpoints, pos_motor=sample_x, lmotor=sample_y,
                smpl_h=[], flt_l=None, flt_h=None, det=[], md=None):

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
    dets = [pos_motor, lmotor] + det
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
            plan = lineplan(exp_time, lstart, lend, lpoints, motor=lmotor, md=md, dets=dets)
            xrun(smpl, plan)

    else:
        print('sample list and pos_list Must have same length!')
        return None


def gridscan(smpl, exp_time, xstart, xstop, xpoints, ystart, ystop, ypoints, motorx=sample_x, motory=sample_y, md=None):
    
    """ grid scan for one sample:
    :param smpl: sample ID
    :param exp_time: total exposure time (in second)
    :param xstart: (motorx (fast motor) start point
    :param xstop: (motorx (fast motor) stop point
    :param xpoints: (motorx (fast motor) number of points
    :param ystart: (motory (slower motor) start point
    :param ystop: (motory (slower motor) stop point
    :param ypoints: (motory (slower motor) number of points
    :param motorx: fast motor to move sample
    :param motory: slower motor to move sample
    :param md: metadata
    :param det: extra detector you want to record
    :return:
    """
    plan = gridplan(exp_time, xstart, xstop, xpoints, ystart, ystop, ypoints, motorx=motorx, motory=motory, md=md)
    xrun(smpl, plan)


def mgridscan(smplist, exp_time, xcenter_list, xrange, xpoints, ycenter_list, yrange, ypoints,
              motorx=sample_x, motory=sample_y, smpl_h=[], flt_l=None, flt_h=None, md=None, det=None):
    """ grid scan for multiple sample:
    :param smplist: list of sample ID to be measured
    :param poslist: list of sample positions
    :param exp_time: total exposure time (in sec)
    :param xstart: (motorx (fast motor) start point
    :param xstop: (motorx (fast motor) stop point
    :param xpoints: (motorx (fast motor) number of points
    :param ystart: (motory (slower motor) start point
    :param ystop: (motory (slower motor) stop point
    :param ypoints: (motory (slower motor) number of points
    :param motorx: fast motor to move sample
    :param motory: slower motor to move sample
    :param smpl_h: list of sample which need special filters 
    :param flt_h: filter set for samples in the smpl_h
    :param flt_l: filter set for all other samples
    :param md: metadata
    :param det: extra detector you want to record
        :return:
        """
    
    length = len(smplist)
    if all(len(lst) == length for lst in [smplist, xcenter_list, ycenter_list]):
        for smpl, xcenter, ycenter in zip(smplist, xcenter_list, ycenter_list):
            print(f'move sample: {smpl} to center position {xcenter}, {ycenter}')
            motorx.move(xcenter)
            motory.move(ycenter)
            xstart = xcenter - xrange / 2
            xstop = xcenter + xrange / 2
            ystart = ycenter - yrange / 2
            ystop = ycenter - yrange / 2
            if sample in smpl_h:
                xpd_flt_set(flt_h)
            else:
                if flt_l != None:
                    xpd_flt_set(flt_l)
            time.sleep(delay)
            plan = gridplan(exp_time, xstart, xstop, xpoints, ystart, ystop, ypoints, motorx=motorx, motory=motory,
                            md=md)
            xrun(smpl, plan)


def xyposscan(smpl, exp_time, posxlist, posylist, motorx=sample_x, motory=sample_y, md=None):
    plan = xyposplan(exp_time, posxlist, posylist, motorx=motorx, motory=motory, md=md)
    xrun(smpl, plan)
