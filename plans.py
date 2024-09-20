def plan_with_calib(dets, exp_time, num, calib_file):
    """

    :param dets:
    :param exp_time:
    :param num:
    :param calib_file:
    :return:
    """
    motors = dets[1:]
    yield from _configure_area_det(exp_time)
    plan = count_with_calib(dets, num, calibration_md=calib_file)
    plan = bpp.subs_wrapper(plan, LiveTable(motors))
    yield from plan


def count_with_calib(detectors: list, num: int = 1, delay: float = None, *, calibration_md: dict = None,
                     md: dict = None) -> typing.Generator:
    """
    Take one or more readings from detectors with shutter control and calibration metadata injection.

    Parameters
    ----------
    detectors : list
        list of 'readable' objects

    num : integer, optional
        number of readings to take; default is 1

        If None, capture data until canceled

    delay : iterable or scalar, optional
        Time delay in seconds between successive readings; default is 0.

    calibration_md :
        The calibration data in a dictionary. If not applied, the function is a normal `bluesky.plans.count`.

    md : dict, optional
        metadata

    Notes
    -----
    If ``delay`` is an iterable, it must have at least ``num - 1`` entries or
    the plan will raise a ``ValueError`` during iteration.
    """
    if md is None:
        md = dict()
    if calibration_md is not None:
        md["calibration_md"] = calibration_md

    def _per_shot(_detectors):
        yield from open_shutter_stub()
        yield from bps.one_shot(_detectors)
        yield from close_shutter_stub()
        return

    try:
        plan = bp.count(detectors, num, delay, md=md, per_shot=_per_shot)
        sts = yield from plan
    except Exception as error:
        raise error
    return sts


def ct_motors_plan(det, exp_time, num=1, delay=0, md=None):
    """

    :param det: list of detectors
    :param exp_time: exposure time (in seconds)
    :param num: number of data to take; default is 1
    :param delay: time delay in seconds between successively readings, defautl is 0
    :param md: metadata

    to read temperature controller and motor position and show on LiveTable
    then we can save table to excel file

    det=[area_det, T_controller, motor...]
    """

    (num_frame, acq_time, computed_exposure) = yield from _configure_area_det(exp_time)
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
    plan = bpp.plan_mutator(plan, inner_shutter_control)
    yield from plan


def lineplan(exp_time, xstart, xend, xpoints, motor=sample_y, md=None, det=None):
    """ plan for multiple points along one line

    :param exp_time: total exposure time (in sec)
    :param xstart: start point
    :param xend: end point
    :param xpoints: number of points to measure
    :param motor: motor to move sample
    :param md: metadate
    :param det: extra detector you want to record
    :return:
    """

    if det is None:
        det = []
    (num_frame, acq_time, computed_exposure) = yield from _configure_area_det(exp_time)
    _md = {

        "sp_time_per_frame": acq_time,
        "sp_num_frames": num_frame,
        "sp_requested_exposure": exp_time,
        "sp_computed_exposure": computed_exposure,
    }
    _md.update(md or {})

    area_det = xpd_configuration['area_det']
    det = [motor] + det
    dets = [area_det] + det
    plan = bp.scan(dets, motor, xstart, xend, xpoints, md=_md)
    plan = bpp.subs_wrapper(plan, LiveTable(det))
    plan = bpp.plan_mutator(plan, inner_shutter_control)
    yield from plan


def gridplan(exp_time, xstart, xstop, xpoints, ystart, ystop, ypoints, motorx=sample_x, motory=sample_y, md=None,
             det=None):
    """

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
    if det is None:
        det = []
    (num_frame, acq_time, computed_exposure) = yield from _configure_area_det(exp_time)
    _md = {

        "sp_time_per_frame": acq_time,
        "sp_num_frames": num_frame,
        "sp_requested_exposure": exp_time,
        "sp_computed_exposure": computed_exposure,
    }
    _md.update(md or {})
    det = [motory, motorx] + det
    area_det = xpd_configuration['area_det']
    dets = [area_det] + det

    plan = bp.grid_scan(dets, motory, ystart, ystop, ypoints, motorx, xstart, xstop, xpoints, True, md=_md)
    plan = bpp.subs_wrapper(plan, LiveTable(det))
    plan = bpp.plan_mutator(plan, inner_shutter_control)
    yield from plan


def xyposplan(exp_time, posxlist, posylist, motorx=sample_x, motory=sample_y, md=None, det=None):

    """
    example: measure three points at position (10, 1.2), (13, 1.3), (20, 1.4)
    xyposplan(5, [10, 13, 20], [1.2, 1.3, 1.4])

    :param exp_time: total exposure time (in seconds)
    :param posxlist: list of xpositions
    :param posylist: list of y positions
    :param motorx: motor to move sample in x direction, default is sample_x
    :param motory: motor to move sample in y direction, default is sample_y
    :param md: metadata
    :return:
    """
    if det is None:
        det = []
    (num_frame, acq_time, computed_exposure) = yield from _configure_area_det(exp_time)
    _md = {

        "sp_time_per_frame": acq_time,
        "sp_num_frames": num_frame,
        "sp_requested_exposure": exp_time,
        "sp_computed_exposure": computed_exposure,
    }
    _md.update(md or {})
    area_det = xpd_configuration['area_det']

    plan = bp.list_scan([area_det]+det, motorx, posxlist, motory, posylist, md=_md)
    plan = bpp.subs_wrapper(plan, LiveTable([motorx, motory]+det))
    plan = bpp.plan_mutator(plan, inner_shutter_control)
    yield from plan

def take_one_dark(sample, det, exp_time):
    """ take one data with dark image, then set dark window to 1000 minutes

    parameter:
    sample: sample name(index) in sample list
    det: list of detectors
    exp_time: exposure time in seconds

    """

    glbl['dk_window'] = 0.1
    plan = ct_motors_plan(det, exp_time)
    xrun(sample, plan)
    glbl['dk_window'] = 1000
# ------------------------------------------------------------------------------------------------------------------------
from packaging import version


def append_compatible(df, new_data, sort=False):
    """
    Append new_data to df in a way that's compatible with different pandas versions.

    Parameters:
        df (DataFrame): The original DataFrame to append data to.
        new_data (DataFrame): The new data to append to the original DataFrame.
        sort (bool): Whether to sort columns or not (for pandas <= 1.4.x).

    Returns:
        DataFrame: The resulting DataFrame after appending new_data.
    """
    pandas_version = pd.__version__

    if version.parse(pandas_version) >= version.parse("2.0.0"):
        # For pandas >= 2.0.0
        return df._append(new_data, sort=sort)
    else:
        # For pandas < 2.0.0
        return df.append(new_data, sort=sort)

def save_tb_xlsx(sample_name, starttime, endtime, readable_time=False):
    data_dir = "./tiff_base/"
    if not readable_time:
        startstring = datetime.datetime.fromtimestamp(float(starttime)).strftime('%Y-%m-%d %H:%M:%S')
        endstring = datetime.datetime.fromtimestamp(float(endtime)).strftime('%Y-%m-%d %H:%M:%S')
    else:
        startstring = starttime
        endstring = endtime
    hdrs = db(since=startstring, until=endstring)
    timestamp = time.time()
    timestring_filename = datetime.datetime.fromtimestamp(float(timestamp)).strftime('%Y%m%d_%H%M%S')
    file_name = data_dir + 'sample_' + str(sample_name) + '_' + timestring_filename + ".xlsx"
    print(len(list(hdrs)))
    for idx, hdr in enumerate(hdrs):
        tb = hdr.table()
        uid6 = hdr.start['uid'][0:6]
        tb['uid6'] = uid6
        if idx == 0:
            DBout = tb
        else:
            #DBout = DBout._append(tb, sort=False)
            append_compatible(DBout, tb, sort=False)
    writer = pd.ExcelWriter(file_name)
    DBout.to_excel(writer, sheet_name='Sheet1')
    writer.save()
    return


def save_position_to_sample_list(smpl_list, pos_list, filename):
    # file_name='300001_sample.xlsx'

    file_dir = './Import/'
    ind_list = [x + 1 for x in smpl_list]
    pos_str = [str(x) for x in pos_list]
    file_name = file_dir + filename
    f_out = file_name
    f = pd.read_excel(file_name)
    tags = pd.DataFrame(f, columns=['User supplied tags']).fillna(0)
    tags = tags.values
    for i, ind in enumerate(ind_list):
        if tags[ind][0] != 0:
            tag_str = str(tags[ind][0])
            tags[ind][0] = tag_str + ',pos=' + str(pos_str[i])
        else:
            tags[ind][0] = 'pos=' + str(pos_str[i])
    tags = list(flatten(tags))

    new_f = pd.DataFrame({'User supplied tags': tags})
    f.update(new_f)
    writer = pd.ExcelWriter(f_out)
    f.to_excel(writer, index=False)
    writer.save()
    return None


def xpd_flt_set(flt_p):
    if flt_p[0] == 0:
        fb.flt1.set('Out')
    else:
        fb.flt1.set('In')
    if flt_p[1] == 0:
        fb.flt2.set('Out')
    else:
        fb.flt2.set('In')
    if flt_p[2] == 0:
        fb.flt3.set('Out')
    else:
        fb.flt3.set('In')
    if flt_p[3] == 0:
        fb.flt4.set('Out')
    else:
        fb.flt4.set('In')

    print('filter bank setting:', fb.flt1.get(), fb.flt2.get(), fb.flt3.get(), fb.flt4.get())

    return None


def xpd_flt_read():
    flt_p = [0, 0, 0, 0]
    if fb.flt1.get() == 'Out':
        flt_p[0] = 0
    else:
        flt_p[0] = 1
    if fb.flt2.get() == 'Out':
        flt_p[1] = 0
    else:
        flt_p[1] = 1

    if fb.flt3.get() == 'Out':
        flt_p[2] = 0
    else:
        flt_p[2] = 1
    if fb.flt4.get() == 'Out':
        flt_p[3] = 0
    else:
        flt_p[3] = 1

    return flt_p
