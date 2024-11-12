"""Plan to run a XRD map "fly-scan" over a large sample."""
import datetime
import pprint
import time as ttime
import uuid

import numpy as np
import itertools
import bluesky.preprocessors as bpp
import bluesky.plan_stubs as bps
import bluesky.plans as bp
from bluesky.utils import short_uid

import bluesky_darkframes
from ophyd import Signal
from ophyd.status import Status


# vendored, simplified, and made public from bluesky_darkframes
class SnapshotShell:
    """
    Shell to hold snapshots
    This enables us to hot-swap Snapshot instances in the middle of a Run.
    We hand this object to the RunEngine, so it sees one consistent
    instance throughout the Run.
    """

    def __init__(self):
        self.__snapshot = None

    def set_snaphsot(self, snapshot):
        self.__snapshot = snapshot

    def __getattr__(self, key):
        return getattr(self.__snapshot, key)


def _extract_motor_pos(mtr):
    ret = yield from bps.read(mtr)
    if ret is None:
        return None
    return next(
        itertools.chain(
            (ret[k]["value"] for k in mtr.hints.get("fields", [])),
            (v["value"] for v in ret.values()),
        )
    )


def xrd_line(
    dets,
    shutter,
    fly_motor,
    fly_start,
    fly_stop,
    fly_pixels,
    dwell_time,
    repeats,
    *,
    dark_plan=None,
    md=None,
    backoff=0,
    snake=True,
):
    """
    Collect a 2D XRD map by "flying" in one direction.
    Parameters
    ----------
    dets : List[OphydObj] area_det is the xpd_configuration['area_det']
    shutter : Movable  xpd: fs
        Assumed to have "Open" and "Close" as the commands
        open : bps.mv(fs, -20)
        close: bps.mv(fs, 20)
    fly_motor : Movable
       The motor that will be moved continuously during collection
       (aka "flown")
    fly_start, fly_stop : float
       The start and stop position of the "fly" direction
    fly_pixels : int
       The target number of pixels in the "fly" direction

    dwell_time : float
       How long in s to dwell in each pixel.  combined with *fly_pixels*
       this will be used to compute the motor velocity
    dark_plan : Plan or None
       The expected signature is ::
          def dp(det : Detector, shell : SnapshotShell):
             ...
        It only needs to handle one detector and is responsible for generating
        the messages to generate events.  The logic of _if_ a darkframe should
        be taken is handled else where.
    md : Optional[Dict[str, Any]]
       User-supplied meta-data
    backoff : float
       How far to move beyond the fly dimensions to get up to speed
    snake : bool
       If we should "snake" or "typewriter" the fly axis
    """
    # TODO input validation
    # rename here to use better internal names (!!)
    req_dwell_time = dwell_time
    del dwell_time
    acq_time = glbl['frame_acq_time']


    plan_args_cache = {
        k: v
        for k, v in locals().items()
        if k not in ("dets", "fly_motor", "dark_plan", "shutter")
    }

    (ad,) = (d for d in dets if hasattr(d, "cam"))
    #(num_frame, acq_time, computed_dwell_time) = yield from configure_area_det(
    #    ad, req_dwell_time,acq_time
    #)
    (num_frame, acq_time, computed_dwell_time) = yield from configure_area_det(
        ad, req_dwell_time)

    # set up metadata
    sp = {
        "time_per_frame": acq_time,
        "num_frames": num_frame,
        "requested_exposure": req_dwell_time,
        "computed_exposure": computed_dwell_time,
        "type": "ct",
        "uid": str(uuid.uuid4()),
        "plan_name": "map_scan",
    }
    _md = {
        "detectors": [det.name for det in dets],
        "plan_args": plan_args_cache,
        "hints": {},
        "sp": sp,
        "extents": [(fly_start, fly_stop)],
        **{f"sp_{k}": v for k, v in sp.items()},
    }
    _md.update(md or {})
    _md["hints"].setdefault(
        "dimensions",
        [((f"start_{fly_motor.name}",), "primary")],
    )
    #_md["hints"].setdefault(
    #    "extents", [(fly_start, fly_stop), (step_stop, step_start)],
    #)

    # soft signal to use for tracking pixel edges
    # TODO put better metadata on these
    px_start = Signal(name=f"start_{fly_motor.name}", kind="normal")
    px_stop = Signal(name=f"stop_{fly_motor.name}", kind="normal")

    # TODO either think more carefully about how to compute this
    # or get the gating working below.
    #current_fly_motor_speed = fly_motor.velocity.get()
    speed = abs(fly_stop - fly_start) / (fly_pixels * computed_dwell_time)
    print(speed)
    shell = SnapshotShell()

    @bpp.reset_positions_decorator([fly_motor.velocity])
    @bpp.set_run_key_decorator(f"xrd_map_{uuid.uuid4()}")
    @bpp.stage_decorator(dets)
    @bpp.run_decorator(md=_md)
    def inner():
        _fly_start, _fly_stop = fly_start, fly_stop
        _backoff = backoff

        # yield from bps.mv(fly_motor.velocity, speed)
        for i in range(repeats):
            yield from bps.checkpoint()
            # TODO maybe go to a "move velocity here?
            yield from bps.mv(fly_motor.velocity, 10)
            pre_fly_group = short_uid("pre_fly")
            yield from bps.abs_set(
                fly_motor, _fly_start - _backoff, group=pre_fly_group
            )
            # take the dark while we might be waiting for motor movement
            if dark_plan:
                yield from bps.mv(shutter, "Close")
                yield from bps.sleep(0.5)
                yield from dark_plan(ad, shell)
            # wait for the pre-fly motion to stop
            yield from bps.wait(group=pre_fly_group)
            yield from bps.mv(shutter, "Open")

            yield from bps.sleep(0.5)
            yield from bps.mv(fly_motor.velocity, speed)
            fly_group = short_uid("fly")
            yield from bps.abs_set(fly_motor, _fly_stop + _backoff, group=fly_group)
            # TODO gate starting to take data on motor position
            for j in range(fly_pixels):
                print(time.time())
                fly_pixel_group = short_uid("fly_pixel")
                for d in dets:
                    yield from bps.trigger(d, group=fly_pixel_group)

                # grab motor position right after we trigger
                start_pos = yield from _extract_motor_pos(fly_motor)
                yield from bps.mv(px_start, start_pos)
                # wait for frame to finish
                yield from bps.wait(group=fly_pixel_group)

                # grab the motor position
                stop_pos = yield from _extract_motor_pos(fly_motor)
                yield from bps.mv(px_stop, stop_pos)
                # generate the event
                yield from bps.create("primary")
                for obj in dets + [px_start, px_stop]:
                    yield from bps.read(obj)
                yield from bps.save()
                print(time.time)
            yield from bps.checkpoint()
            yield from bps.mv(shutter, "Close")

            yield from bps.wait(group=fly_group)
            yield from bps.checkpoint()
            if snake:
                # if snaking, flip these for the next pass through
                _fly_start, _fly_stop = _fly_stop, _fly_start
                _backoff = -_backoff

    yield from inner()


def dark_plan(detector, shell, *, stream_name="dark"):
    # Restage to ensure that dark frames goes into a separate file.
    yield from bps.unstage(detector)
    yield from bps.stage(detector)

    # The `group` parameter passed to trigger MUST start with
    # bluesky-darkframes-trigger.
    grp = short_uid("bluesky-darkframes-trigger")
    yield from bps.trigger(detector, group=grp)
    yield from bps.wait(grp)
    yield from bps.read(detector)
    snapshot = bluesky_darkframes.SnapshotDevice(detector)
    shell.set_snaphsot(snapshot)

    # emit the event to the dark stream
    yield from bps.stage(shell)
    yield from bps.trigger_and_read(
        [shell], name=stream_name,
    )
    yield from bps.unstage(shell)

    # Restage.
    yield from bps.unstage(detector)
    yield from bps.stage(detector)

def take_one_dark(sample, det, exp_time):
    """ take one data with dark image, then set dark window to 1000 minutes

    parameter:
    sample (int): sample name(index) in sample list
    det (list): list of detectors
    exp_time (float): exposure time in seconds

    """
    glbl['dk_window'] = 0.1
    plan = ct_motors_plan(det, exp_time)
    xrun(sample, plan)
    glbl['dk_window'] = 1000

def linescan(smpl, exp_time, xstart, xend, xpoints, motor=sample_y, md=None, det=None, takeonedark=False):

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
    dets = xpd_configuration['area_det']+det
    if takeonedark is True:
        take_one_dark(smpl, dets, exp_time)
    # Create the scan plan
    plan = lineplan(exp_time, xstart, xend, xpoints, motor=motor, md=md, det=det)
    xrun(smpl, plan)

def lineplan(exp_time, xstart, xend, xpoints, motor=sample_y, md=None, det=None):
    """ plan for 1D line scan by moving a motor between two positions and recording measurements at multiple points.

    Parameters:
        exp_time (float): Total exposure time (in seconds) for each measurement point.
        xstart (float): Starting position for the motor.
        xend (float): Ending position for the motor.
        xpoints (int): Number of points to measure along the line.
        motor (object, optional): Motor object to move the sample along the line. Default is `sample_y`.
        md (dict, optional): Additional metadata to attach to the scan.
        det (list, optional): List of extra detectors to record during the scan.

    Example:
        lineplan(5.0, 0, 10, 5, motor=sample_y)

    """

    if det is None:
        det = []
    # Configure the area detector
    (num_frame, acq_time, computed_exposure) = yield from _configure_area_det(exp_time)

    # Metadata handling
    _md = {

        "sp_time_per_frame": acq_time,
        "sp_num_frames": num_frame,
        "sp_requested_exposure": exp_time,
        "sp_computed_exposure": computed_exposure,
    }
    _md.update(md or {})

    area_det = xpd_configuration['area_det']

    plan = bp.scan([area_det] + det, motor, xstart, xend, xpoints, md=_md)
    plan = bpp.subs_wrapper(plan, LiveTable([motor] + det))
    #plan = bpp.plan_mutator(plan, inner_shutter_control)
    yield from plan

def ct_motors_plan(det, exp_time, num=1, delay=0, md=None):
    """plan for performing multiple readings of detectors (e.g., temperature controller, motor positions) and display results
    in real-time using LiveTable.

    Parameters:
        det (list): List of detectors to be read during the scan (e.g., area detector, temperature controller, motors).
        exp_time (float): Exposure time (in seconds) for each reading.
        num (int, optional): Number of readings to take. Default is 1.
        delay (float, optional): Delay (in seconds) between successive readings. Default is 0.
        md (dict, optional): Additional metadata to attach to the scan. Default is None.

    Example:
        ct_motors_plan([area_det, T_controller, motor], 5.0, num=10, delay=1)

    """
    # Configure the area detector
    (num_frame, acq_time, computed_exposure) = yield from _configure_area_det(exp_time)

    # Metadata handling
    _md = {

        "sp_time_per_frame": acq_time,
        "sp_num_frames": num_frame,
        "sp_requested_exposure": exp_time,
        "sp_computed_exposure": computed_exposure,
    }

    _md.update(md or {})

    motors = det[1:]
    plan = bp.count(det, num, delay, md=_md)
    plan = bpp.subs_wrapper(plan, LiveTable(motors))
    #plan = bpp.plan_mutator(plan, inner_shutter_control)
    yield from plan

def simple_set_run(smpl, exp_time, num, xstart, xend, motor, repeats=1, motor_v=1, md = None, takeonedark=Flase):

    det = [pe1c, motor]
    if takeonedark is True:
        take_one_dark(smpl, dets, exp_time)

    for i in range(repeats):
        #move motor to start point with 10mm/s velocity
        motor.velocity.move(10)
        motor.move(xstart)
        # change the motor velocity to motor_v
        motor.velocity.move(motor_v)
        #set motor to end position and then start to take data, and record motor position
        motor.set(xend)
        plan = ct_motors_plan(det, exp_time, num=num, delay=0, md=md)
        xrun(smpl, plan)

