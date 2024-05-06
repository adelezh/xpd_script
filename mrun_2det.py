def mscan_2det(smplist_pdf, smplist_xrd, posxlist, exp_pdf, exp_xrd, smpl_h=[], delay=1,
                 pdf_pos=[0, 240], xrd_pos=[400, 270], num_pdf=1, num_xrd=1, pdf_flt_h=None, pdf_flt=None, xrd_flt=None,
                 motorx=sample_x, pdf_frame_acq=None, xrd_frame_acq=None, dets=[pe1_z, sample_x]):
    '''
    Multiple samples, do pdf and xrd for one sample, then move to the next sample
    :param smplist_pdf: list of sample names for PDF measurement
    :param smplist_xrd: list of sample names for XRD measurement
    :param posxlist: list of positions of each samples
    :param exp_pdf: total exposure time for PDF measurement, in sec.
    :param exp_xrd: total exposure time for XRD measurement, in sec. make sure exp_pdf and exp_xrd are not the same.
    :param smpl_h: list of high scattering samples which need special filters for PDF measurement
    :param delay: delay time between each sample, PDF measurement only
    :param pdf_pos: det1 position[pe1_x, pe1_z] for pdf
    :param xrd_pos: det1 position[pe1_x, pe1_z] for xrd, make sure pe1_Z is safe for PE1 to move out
    :param num_pdf: number of data to take for PDF measurement
    :param num_xrd: number of data to take for XRD measurement
    :param pdf_flt_h: filter set for high scattering PDF samples in smpl_h, default is None, No samples in smpl_h
    :param pdf_flt: filter set for normal PDF samples, default is None, use current filter set.
    :param xrd_flt: filter set for all XRD samples, default is None, use current filter set.
    :param motorx: motor to move samples, default is sample_x
    :param pdf_frame_acq: frame_acq_time for PE1 detector, default is none, use same current frame acq time for both det
    :param xrd_frame_acq: frame_acq_time for PE2 detector,default is none, use same current frame acq time for both det
    :param dets: list of motors, temperatures controllers, which will be recorded in table
    :return:
    '''
    for smpl_xrd, smpl_pdf, posx in zip(smplist_xrd, smplist_pdf, posxlist):
        print(f' {smpl_xrd}, {smpl_pdf}, in position {posx}')
        motorx.move(posx)
        time.sleep(delay)
        if smpl_pdf in smpl_h:
            run_2det(smpl_pdf, smpl_xrd, exp_pdf, exp_xrd, pdf_pos=pdf_pos, xrd_pos=xrd_pos,
                 num_pdf=num_pdf, num_xrd=num_xrd, pdf_flt=pdf_flt_h, xrd_flt=xrd_flt, dets=dets,
                 pdf_frame_acq=pdf_frame_acq, xrd_frame_acq=xrd_frame_acq )
        else:
            run_2det(smpl_pdf, smpl_xrd, exp_pdf, exp_xrd, pdf_pos=pdf_pos, xrd_pos=xrd_pos,
                 num_pdf=num_pdf, num_xrd=num_xrd, pdf_flt=pdf_flt, xrd_flt=xrd_flt, dets=dets,
                 pdf_frame_acq=pdf_frame_acq, xrd_frame_acq=xrd_frame_acq )


def mrun_2det_batch(smplist_pdf, smplist_xrd, posxlist, exp_pdf, exp_xrd, smpl_h=[], delay=1,
                 pdf_pos=[0, 240], xrd_pos=[400, 270], num_pdf=1, num_xrd=1, pdf_flt_h=None, pdf_flt=None, xrd_flt=None,
                 motorx=sample_x, pdf_frame_acq=None, xrd_frame_acq=None, dets=[pe1_z, sample_x]):
    '''
    Multiple samples, do pdf measurment for all sample first, then do xrd measuremnt

    :param smplist_pdf: list of sample names for PDF measurement
    :param smplist_xrd: list of sample names for XRD measurement
    :param posxlist: list of positions of each samples
    :param exp_pdf: total exposure time for PDF measurement, in sec.
    :param exp_xrd: total exposure time for XRD measurement, in sec. make sure exp_pdf and exp_xrd are not the same.
    :param smpl_h: list of high scattering samples which need special filters for PDF measurement
    :param delay: delay time between each sample, PDF measurement only
    :param pdf_pos: det1 position[pe1_x, pe1_z] for pdf
    :param xrd_pos: det1 position[pe1_x, pe1_z] for xrd, make sure pe1_Z is safe for PE1 to move out
    :param num_pdf: number of data to take for PDF measurement
    :param num_xrd: number of data to take for XRD measurement
    :param pdf_flt_h: filter set for high scattering PDF samples in smpl_h, default is None, No samples in smpl_h
    :param pdf_flt: filter set for normal PDF samples, default is None, use current filter set.
    :param xrd_flt: filter set for all XRD samples, default is None, use current filter set.
    :param motorx: motor to move samples, default is sample_x
    :param pdf_frame_acq: frame_acq_time for PE1 detector, default is none, use same current frame acq time for both det
    :param xrd_frame_acq: frame_acq_time for PE2 detector,default is none, use same current frame acq time for both det
    :param dets: list of motors, temperatures controllers, which will be recorded in table

    '''

    glbl["auto_load_calib"] = False
    xrd_calib = load_calibration_md('config_base/xrd.poni')
    pdf_calib = load_calibration_md('config_base/pdf.poni')

    pdf_pe1x, pdf_pe1z = pdf_pos
    xrd_pe1x, xrd_pe1z = xrd_pos

    print('pdf scan')
    xpd_configuration['area_det'] = pe1c
    if pdf_frame_acq is not None:
        glbl['frame_acq_time'] = pdf_frame_acq
        time.sleep(5)
    pe1_z.move(xrd_pe1z)
    pe1_x.move(pdf_pe1x)
    pe1_z.move(pdf_pe1z)
    for smpl_pdf, posx in zip(smplist_pdf, posxlist):
        print(f' PDF: sample: {smpl_pdf} ,position: {posx}')
        motorx.move(posx)
        if smpl_pdf in smpl_h:
            xpd_flt_set(pdf_flt_h)
        else:
            if pdf_flt is not None:
                xpd_flt_set(pdf_flt)
        time.sleep(delay)
        plan = plan_with_calib([pe1c] + dets, exp_pdf, num_pdf, pdf_calib)
        xrun(smpl_pdf, plan)

    print('xrd scan')
    xpd_configuration['area_det'] = pe2c
    if xrd_frame_acq is not None:
        glbl['frame_acq_time'] = xrd_frame_acq
        time.sleep(5)
    pe1_z.move(xrd_pe1z)
    pe1_x.move(xrd_pe1x)
    if xrd_flt is not None:
        xpd_flt_set(xrd_flt)
    for smpl_xrd, posx in zip(smplist_xrd, posxlist):
        print(f' PDF: sample: {smpl_xrd} ,position: {posx}')
        motorx.move(posx)
        # time.sleep(delay)
        plan = plan_with_calib([pe2c] + dets, exp_xrd, num_xrd, xrd_calib)
        xrun(smpl_xrd, plan)

    glbl["auto_load_calib"] = current_calib_status


def run_2det(smpl_pdf, smpl_xrd, exp_pdf, exp_xrd, pdf_pos=[0, 210], xrd_pos=[400, 240], num_pdf=3, num_xrd=1,
             pdf_flt=None, xrd_flt=None, pdf_frame_acq=None, xrd_frame_acq=None, dets=[pe1_z]):

    '''
    PDF and XRD measure for one sample.

    :param smpl_pdf: sample name for pdf measurement
    :param smpl_xrd: sample name for xrd measurement
    :param exp_pdf: total exposure time for PDF measurement
    :param exp_xrd: total exposure time for XRD measurement, in sec. make sure exp_pdf and exp_xrd are not the same.
    :param pdf_pos: det1 position[pe1_x, pe1_z] for pdf
    :param xrd_pos: det1 position[pe1_x, pe1_z] for xrd, make sure pe1_Z is safe for PE1 to move out
    :param num_pdf: number of data to take for PDF measurement
    :param num_xrd: number of data to take for XRD measurement
    :param pdf_flt: filter set for PDF samples
    :param xrd_flt: filter set for XRD samples
    :param pdf_frame_acq: frame_acq_time for PE1 detector
    :param xrd_frame_acq: frame_acq_time for PE2 detector
    :param dets:
    :return:
    '''

    glbl["auto_load_calib"] = False

    xrd_calib = load_calibration_md('config_base/xrd.poni')
    pdf_calib = load_calibration_md('config_base/pdf.poni')

    pdf_pe1x, pdf_pe1z = pdf_pos
    xrd_pe1x, xrd_pe1z = xrd_pos

    print('pdf scan')
    xpd_configuration['area_det'] = pe1c
    if pdf_frame_acq is not None:
        glbl['frame_acq_time'] = pdf_frame_acq
        time.sleep(5)
    pe1_z.move(xrd_pe1z)
    pe1_x.move(pdf_pe1x)
    pe1_z.move(pdf_pe1z)
    if pdf_flt is not None:
        xpd_flt_set(pdf_flt)
    plan = plan_with_calib([pe1c] + dets, exp_pdf, num_pdf, pdf_calib)
    xrun(smpl_pdf, plan)

    print('xrd scan')
    xpd_configuration['area_det'] = pe2c
    if xrd_frame_acq is not None:
        glbl['frame_acq_time'] = xrd_frame_acq
        time.sleep(5)
    pe1_z.move(xrd_pe1z)
    pe1_x.move(xrd_pe1x)
    if xrd_flt is not None:
        xpd_flt_set(xrd_flt)
    plan = plan_with_calib([pe2c] + dets, exp_xrd, num_xrd, xrd_calib)
    xrun(smpl_xrd, plan)

    glbl["auto_load_calib"] = True


def set_xrd(xrd_pos=[400, 280]):
    '''
    set xpdacq for xrd measurement: move out PE1 detector,
                            xpd_configure['area_det'] = pe2c
                            glbl['frame_acq_time'] = 0.2
    :param xrd_pos: safe pos to move PE1 out
    :return:
    '''
    xrd_pe1x, xrd_pe1z = xrd_pos
    pe1_z.move(xrd_pe1z)
    pe1_x.move(xrd_pe1x)
    xpd_configuration['area_det'] = pe2c
    glbl['frame_acq_time'] = 0.2


def set_pdf(pdf_pos=[0, 240], safe_out=280):
    '''
    set xpdacq for xrd measurement: move PE1 detector in position,
                            xpd_configure['area_det'] = pe1c
                            glbl['frame_acq_time'] = 0.2
    :param pdf_pos:  PE1 position for PDF measurement
    :param safe_out: pe1_z position to safely move PE1 in position
    :return:
    '''
    pdf_pe1x, pdf_pe1z = pdf_pos
    pe1_z.move(safe_out)
    pe1_x.move(pdf_pe1x)
    pe1_z.move(pdf_pe1z)
    xpd_configuration['area_det'] = pe1c
    glbl['frame_acq_time'] = 0.2


def run_xrd(smpl, exp_xrd, num=1, xrd_pos=[400, 280], calib_file='config_base/xrd.poni', frame_acq_time = 0.2, dets=[]):
    '''
    run one xrd measurement : move out PE1 detector,
                            xpd_configure['area_det'] = pe2c
                            glbl['frame_acq_time'] = 0.2
    :param smpl: sample index
    :param exp_xrd: total exposure time(in seconds)
    :param xrd_pos:  PE1 position for xrd measurement
    :param calib_file: calibration file for xrd measurement
    :param frame_acq_time: frame acq time, default=0.2
    :param dets: extra dets want to read in meta and table, such as temperature controller, motor positions
    :return:
    '''
    xrd_pe1x, xrd_pe1z = xrd_pos
    glbl["auto_load_calib"] = False
    pe1_z.move(xrd_pe1z)
    pe1_x.move(xrd_pe1x)
    xrd_calib = load_calibration_md(calib_file)
    xpd_configuration['area_det'] = pe2c
    glbl['frame_acq_time'] = frame_acq_time
    time.sleep(1)
    plan = plan_with_calib([pe2c] + dets, exp_xrd, num, xrd_calib)
    xrun(smpl, plan)

    glbl["auto_load_calib"] = True


def run_pdf(smpl, exp_pdf, num=1, pdf_pos=[0, 240], safe_out=275, calib_file='config_base/pdf.poni', dets=[pe1_z]):
    '''
    run one pdf measurement : move PE1 detector in position,
                            xpd_configure['area_det'] = pe1c
                            glbl['frame_acq_time'] = 0.2
    :param smpl: sample index
    :param exp_xrd: total exposure time(in seconds)
    :param pdf_pos:  PE1 position for PDF measurement
    :param safe_out: pe1_z position to safely move PE1 in position
    :param calib_file: calibration file for xrd measurement
    :param frame_acq_time: frame acq time, default=0.2
    :param dets: extra dets want to read in meta and table, such as temperature controller, motor positions
    :return:
    '''
    pdf_pe1x, pdf_pe1z = pdf_pos
    glbl["auto_load_calib"] = False
    pe1_z.move(safe_out)
    pe1_x.move(pdf_pe1x)
    pe1_z.move(pdf_pe1z)

    pdf_calib = load_calibration_md(calib_file)
    xpd_configuration['area_det'] = pe1c
    plan = plan_with_calib([pe1c] + dets, exp_pdf, num, pdf_calib)
    xrun(smpl, plan)
    glbl["auto_load_calib"] = True


def plan_with_calib(dets, exp_time, num, calib_file, delay=1):
    '''

    '''
    motors = dets[1:]
    yield from _configure_area_det(exp_time)
    plan = count_with_calib(dets, num, delay=delay, calibration_md=calib_file)
    plan = bpp.subs_wrapper(plan, LiveTable(motors))
    #plan = bpp.plan_mutator(plan, inner_shutter_control)
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
