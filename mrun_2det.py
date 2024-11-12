import time


def mscan_2det(smplist_pdf, smplist_xrd, posxlist, exp_pdf, exp_xrd, smpl_h=None, delay=1,
               pdf_pos=[0, 255], xrd_pos=[400, 275], num_pdf=1, num_xrd=1, pdf_flt_h=None, pdf_flt=None, xrd_flt=None,
               motorx=sample_x, pdf_frame_acq=None, xrd_frame_acq=None, dets=[pe1_z, sample_x], confirm=True):
    '''
    Multiple samples, do pdf and xrd for one sample, then move to the next sample
    Parameters:
        smplist_pdf: List of sample names for PDF measurement.
        smplist_xrd: List of sample names for XRD measurement.
        posxlist: List of positions of each sample.
        exp_pdf: Total exposure time for PDF measurement (seconds).
        exp_xrd: Total exposure time for XRD measurement (seconds).
        smpl_h: List of high-scattering samples needing special filters for PDF (optional).
        delay: Delay time between each sample during PDF measurements (default: 1 second).
        pdf_pos: Position of the PDF detector [pe1_x, pe1_z].
        xrd_pos: Position of the XRD detector [pe1_x, pe1_z].
        num_pdf: Number of data points to take for PDF measurements.
        num_xrd: Number of data points to take for XRD measurements.
        pdf_flt_h: Filter set for high-scattering PDF samples (default: None).
        pdf_flt: Filter set for normal PDF samples (default: None).
        xrd_flt: Filter set for XRD samples (default: None).
        motorx: Motor to move samples, default is sample_x.
        pdf_frame_acq: Frame acquisition time for PDF detector (default: None).
        xrd_frame_acq: Frame acquisition time for XRD detector (default: None).
        dets: List of detectors and motors to record in the data table.
    '''

    # Validate list lengths for sample list and position list
    if len(smplist_pdf) != len(smplist_xrd) or len(posxlist) != len(smplist_xrd):
        raise ValueError("smplist_pdf, smplist_xrd, posxlist must have the same length")

    # Validate filter settings if high scattering samples are provided
    if smpl_h is not None and (pdf_flt_h is None or pdf_flt is None):
        raise ValueError("If smpl_h is provided, both pdf_flt_h and pdf_flt must also be provided.")

    # Ensure that if pdf_flt is provided, xrd_flt are provided
    if pdf_flt is not None and xrd_flt is None:
        raise ValueError("If pdf_flt is provided, both xrd_flt must also be provided.")

    # Ask the user confirm detector positions
    if confirm is True:
        confirmation = input(
            f"Confirm detector positions:\n"
            f"  - PDF Position = {pdf_pos}\n"
            f"  - XRD Position = {xrd_pos}\n"
            f"Proceed with these settings? (y/n): ").strip().lower()

        if confirmation not in ['y', 'yes']:
            print("User chose not to proceed with the measurements.")
            return  # Exit the function if the user doesn't confirm

    if smpl_h is None:
        smpl_h = []

    for smpl_xrd, smpl_pdf, posx in zip(smplist_xrd, smplist_pdf, posxlist):
        print(f' {smpl_xrd}, {smpl_pdf}, in position {posx}')
        motorx.move(posx)
        time.sleep(delay)
        # Determine the appropriate filter set for PDF
        pdf_flt_selected = pdf_flt_h if smpl_pdf in smpl_h else pdf_flt

        # Run the PDF and XRD measurements using run_2det
        run_2det(
            smpl_pdf=smpl_pdf,
            smpl_xrd=smpl_xrd,
            exp_pdf=exp_pdf,
            exp_xrd=exp_xrd,
            pdf_pos=pdf_pos,
            xrd_pos=xrd_pos,
            num_pdf=num_pdf,
            num_xrd=num_xrd,
            pdf_flt=pdf_flt_selected,
            xrd_flt=xrd_flt,
            dets=dets,
            pdf_frame_acq=pdf_frame_acq,
            xrd_frame_acq=xrd_frame_acq,
            confirm=False
        )

def mrun_2det_batch(smplist_pdf, smplist_xrd, posxlist, exp_pdf, exp_xrd, smpl_h=[], delay=1,
                 pdf_pos=[0, 240], xrd_pos=[400, 270], num_pdf=1, num_xrd=1, pdf_flt_h=None, pdf_flt=None, xrd_flt=None,
                 motorx=sample_x, pdf_frame_acq=None, xrd_frame_acq=None, dets=[pe1_z, sample_x], confirm=True):
    '''
    Multiple samples, do pdf measurment for all sample first, then do xrd measuremnt

    Parameters:
        smplist_pdf: List of sample names for PDF measurement.
        smplist_xrd: List of sample names for XRD measurement.
        posxlist: List of positions of each sample.
        exp_pdf: Total exposure time for PDF measurement (seconds).
        exp_xrd: Total exposure time for XRD measurement (seconds).
        smpl_h: List of high-scattering samples needing special filters for PDF (optional).
        delay: Delay time between each sample during PDF measurements (default: 1 second).
        pdf_pos: Position of the PDF detector [pe1_x, pe1_z].
        xrd_pos: Position of the XRD detector [pe1_x, pe1_z].
        num_pdf: Number of data points to take for PDF measurements.
        num_xrd: Number of data points to take for XRD measurements.
        pdf_flt_h: Filter set for high-scattering PDF samples (default: None).
        pdf_flt: Filter set for normal PDF samples (default: None).
        xrd_flt: Filter set for XRD samples (default: None).
        motorx: Motor to move samples, default is sample_x.
        pdf_frame_acq: Frame acquisition time for PDF detector (default: None).
        xrd_frame_acq: Frame acquisition time for XRD detector (default: None).
        dets: List of detectors and motors to record in the data table.


    '''

    # Validate list lengths for sample list and position list
    if len(smplist_pdf) != len(smplist_xrd) or len(posxlist) != len(smplist_xrd):
        raise ValueError("smplist_pdf, smplist_xrd, posxlist must have the same length")

    # Validate filter settings if high scattering samples are provided
    if smpl_h is not None and (pdf_flt_h is None or pdf_flt is None):
        raise ValueError("If smpl_h is provided, both pdf_flt_h and pdf_flt must also be provided.")

    # Ensure that if pdf_flt is provided, xrd_flt are provided
    if pdf_flt is not None and xrd_flt is None:
        raise ValueError("If pdf_flt is provided, both xrd_flt must also be provided.")

    # Ask the user to confirm detector positions
    if confirm is True:
        confirmation = input(
            f"Confirm detector positions:\n"
            f"  - PDF Position = {pdf_pos}\n"
            f"  - XRD Position = {xrd_pos}\n"
            f"Proceed with these settings? (y/n): ").strip().lower()

        if confirmation not in ['y', 'yes']:
            print("User chose not to proceed with the measurements.")
            return  # Exit the function if the user doesn't confirm

    # Disable automatic loading of calibration during batch processing
    glbl["auto_load_calib"] = False

    # Load calibration files for XRD and PDF
    xrd_calib = load_calibration_md('config_base/xrd.poni')
    pdf_calib = load_calibration_md('config_base/pdf.poni')

    pdf_pe1x, pdf_pe1z = pdf_pos
    xrd_pe1x, xrd_pe1z = xrd_pos

    print('pdf scan')

    # Move to the PDF position with the correct sequence
    pe1_z.move(xrd_pe1z)
    pe1_x.move(pdf_pe1x)
    pe1_z.move(pdf_pe1z)

    xpd_configuration['area_det'] = pe1c
    if pdf_frame_acq is not None:
        glbl['frame_acq_time'] = pdf_frame_acq
        time.sleep(5)

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


def mrun_2det_xypos_batch(smplist_pdf, smplist_xrd, posxlist_pdf, posylist_pdf, posxlist_xrd, posylist_xrd,  exp_pdf, exp_xrd,
                    delay=1, smpl_h=None, pdf_pos=[0, 255], xrd_pos=[400, 275], num_pdf=1, num_xrd=1, pdf_flt_h=None,
                    pdf_flt=None, xrd_flt=None, motorx=sample_x, motory=sample_y, pdf_frame_acq=None, xrd_frame_acq=None,
                    dets=None, confirm=True):
    '''

    Perform XRD measurements for all samples first, followed by PDF measurements.
    The function handles both X and Y positioning for the samples, and some samples may require only PDF or only XRD.

    Parameters:
        smplist_pdf, smplist_xrd : List of sample names for PDF, XRD measurement.
        posxlist_pdf, posylist_pdf: List of x and y positions of each PDF sample.
        posxlist_xrd, posylist_xrd: List of x and y positions of each xrd sample.
        exp_pdf: Total exposure time for PDF measurement (seconds).
        exp_xrd: Total exposure time for XRD measurement (seconds).
        smpl_h: List of high-scattering samples needing special filters for PDF (optional).
        delay: Delay time between each sample during PDF measurements (default: 1 second).
        pdf_pos: Position of the PDF detector [pe1_x, pe1_z].
        xrd_pos: Position of the XRD detector [pe1_x, pe1_z].
        num_pdf: Number of data points to take for PDF measurements.
        num_xrd: Number of data points to take for XRD measurements.
        pdf_flt_h: Filter set for high-scattering PDF samples (default: None).
        pdf_flt: Filter set for normal PDF samples (default: None).
        xrd_flt: Filter set for XRD samples (default: None).
        motorx: Motor to move samples in x direction, default is sample_x.
        motory: Motor to move samples in y direction, default is sample_y
        pdf_frame_acq: Frame acquisition time for PDF detector (default: None).
        xrd_frame_acq: Frame acquisition time for XRD detector (default: None).
        dets: List of detectors and motors to record in the data table.
    '''

    # Validate list lengths for PDF
    if len(smplist_pdf) != len(posxlist_pdf) or len(posxlist_pdf) != len(posylist_pdf):
        raise ValueError("smplist_pdf, posxlist_pdf, and posylist_pdf must have the same length")

    # Validate list lengths for XRD
    if len(smplist_xrd) != len(posxlist_xrd) or len(posylist_xrd) != len(posxlist_xrd):
        raise ValueError("smplist_xrd, posxlist_xrd, and posylist_xrd must have the same length")

    # Validate filter settings if high scattering samples are provided
    if smpl_h is not None and (pdf_flt_h is None or pdf_flt is None):
        raise ValueError("If smpl_h is provided, both pdf_flt_h and pdf_flt must also be provided.")

    # Ensure that if pdf_flt is provided, xrd_flt are provided
    if pdf_flt is not None and xrd_flt is None:
        raise ValueError("If pdf_flt is provided, both xrd_flt must also be provided.")

    if smpl_h is None:
        smpl_h = []
    if dets is None:
        dets = []
    dets = dets + [pe1_Z, motorx, motory]
    
    # Ask the user to double-check the pdf_pos and xrd_pos values
    if confirm is True:
        confirmation = input(
            f"Confirm detector positions:\n"
            f"  - PDF Position = {pdf_pos}\n"
            f"  - XRD Position = {xrd_pos}\n"
            f"Proceed with these settings? (y/n): ").strip().lower()

        if confirmation not in ['y', 'yes']:
            print("User chose not to proceed with the measurements.")
            return  # Exit the function if the user doesn't confirm

    # Disable automatic loading of calibration during batch processing
    glbl["auto_load_calib"] = False

    # Load calibration files for XRD and PDF
    xrd_calib = load_calibration_md('config_base/xrd.poni')
    pdf_calib = load_calibration_md('config_base/pdf.poni')

    pdf_pe1x, pdf_pe1z = pdf_pos
    xrd_pe1x, xrd_pe1z = xrd_pos

    print('Starting xrd scan')
    xpd_configuration['area_det'] = pe2c
    if xrd_frame_acq is not None:
        glbl['frame_acq_time'] = xrd_frame_acq
        time.sleep(5)
    # Move the PE1 detector to XRD position
    pe1_z.move(xrd_pe1z)
    pe1_x.move(xrd_pe1x)
    if xrd_flt is not None:
        xpd_flt_set(xrd_flt)
    for smpl_xrd, posx, posy in zip(smplist_xrd, posxlist_xrd, posylist_xrd):
        print(f' xrd: sample: {smpl_xrd} ,position: {posx}')
        motorx.move(posx)
        motory.move(posy)
        # time.sleep(delay)
        plan = plan_with_calib([pe2c] + dets, exp_xrd, num_xrd, xrd_calib)
        xrun(smpl_xrd, plan)

    print('starting pdf scan')
    xpd_configuration['area_det'] = pe1c
    if pdf_frame_acq is not None:
        glbl['frame_acq_time'] = pdf_frame_acq
        time.sleep(5)
    pe1_z.move(xrd_pe1z)
    pe1_x.move(pdf_pe1x)
    pe1_z.move(pdf_pe1z)
    for smpl_pdf, posx, posy in zip(smplist_pdf, posxlist_pdf, posylist_pdf):
        print(f' PDF: sample: {smpl_pdf} ,position: {posx}')
        motorx.move(posx)
        motory.move(posy)
        if smpl_pdf in smpl_h:
            xpd_flt_set(pdf_flt_h)
        else:
            if pdf_flt is not None:
                xpd_flt_set(pdf_flt)
        time.sleep(delay)
        plan = plan_with_calib([pe1c] + dets, exp_pdf, num_pdf, pdf_calib)
        xrun(smpl_pdf, plan)

    glbl["auto_load_calib"] = True


def run_2det(smpl_pdf, smpl_xrd, exp_pdf, exp_xrd, pdf_pos=[0, 255], xrd_pos=[400, 275], num_pdf=1, num_xrd=1,
             pdf_flt=None, xrd_flt=None, pdf_frame_acq=None, xrd_frame_acq=None, dets=None, confirm=True):
    '''
      Perform PDF and XRD measurements for one sample using two detectors.

    Parameters:
        smpl_pdf: sample names for PDF measurement.
        smpl_xrd: sample names for XRD measurement.
        exp_pdf: Total exposure time for PDF measurement (seconds).
        exp_xrd: Total exposure time for XRD measurement (seconds).
        pdf_pos: Position of the PDF detector [pe1_x, pe1_z].
        xrd_pos: Position of the XRD detector [pe1_x, pe1_z].
        num_pdf: Number of data points to take for PDF measurements.
        num_xrd: Number of data points to take for XRD measurements.
        pdf_flt: Filter set for normal PDF samples (default: None).
        xrd_flt: Filter set for XRD samples (default: None).
        motor: Motor to move samples, default is sample_x.
        pdf_frame_acq: Frame acquisition time for PDF detector (default: None).
        xrd_frame_acq: Frame acquisition time for XRD detector (default: None).
        dets: List of detectors and motors to record in the data table.

      Returns:
      --------
      None
    '''

    # Input Validation
    if pdf_flt is not None and xrd_flt is None:
        raise ValueError("If pdf_flt is provided, xrd_flt must be provided.")

    if confirm is True:
        # Ask the user to double-check the pdf_pos and xrd_pos values
        confirmation = input(
            f"Confirm detector positions:\n"
            f"  - PDF Position = {pdf_pos}\n"
            f"  - XRD Position = {xrd_pos}\n"
            f"Proceed with these settings? (y/n): ").strip().lower()

        if confirmation not in ['y', 'yes']:
            print("User chose not to proceed with the measurements.")
            return  # Exit the function if the user doesn't confirm
    
    if dets is None:
        dets=[]
        
    # Disable auto-loading calibration
    glbl["auto_load_calib"] = False

    # Load calibration files for both PDF and XRD
    xrd_calib = load_calibration_md('config_base/xrd.poni')
    pdf_calib = load_calibration_md('config_base/pdf.poni')

    pdf_pe1x, pdf_pe1z = pdf_pos
    xrd_pe1x, xrd_pe1z = xrd_pos

    # PDF Scan
    print('pdf scan')

    xpd_configuration['area_det'] = pe1c
    if pdf_frame_acq is not None:
        glbl['frame_acq_time'] = pdf_frame_acq
        time.sleep(5)
    # Move to the PDF position with the correct sequence
    pe1_z.move(xrd_pe1z)  # Move z to a safe position
    pe1_x.move(pdf_pe1x)  # Move x to the PDF position
    pe1_z.move(pdf_pe1z)  # Finally, move z to the PDF position

    if pdf_flt is not None:
        xpd_flt_set(pdf_flt)  # set filter for pdf if provided
    plan = plan_with_calib([pe1c] + dets, exp_pdf, num_pdf, pdf_calib)
    xrun(smpl_pdf, plan)

    # XRD Scan
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
    # Re-enable auto-loading calibration
    glbl["auto_load_calib"] = True


def set_xrd(xrd_pos=[400, 280], frame_acq_time=0.2, confirm=True):

    ''' Set the acquisition system for XRD measurements.

    This function moves the PE1 detector out of the way by adjusting the x and z positions and
    configures the XPD system to use the PE2C detector with the specified frame acquisition time.

    Parameters:
        xrd_pos (list): Position of the PE1 detector [pe1_x, pe1_z] for XRD measurement Default is [400, 280].
        frame_acq_time (float): frame acquisition time. Default is 0.2
    '''
    xrd_pe1x, xrd_pe1z = xrd_pos

    if confirm is True:
        # Ask the user to double-check the pdf_pos and xrd_pos values
        confirmation = input(
            f"Confirm detector positions:\n"
            f"  - XRD Position = {xrd_pos}\n"
            f"Proceed with these settings? (y/n): ").strip().lower()
        
        if confirmation not in ['y', 'yes']:
            print("User chose not to proceed with the measurements.")
            return  # Exit the function if the user doesn't confirm

    pe1_z.move(xrd_pe1z)
    pe1_x.move(xrd_pe1x)

    xpd_configuration['area_det'] = pe2c
    glbl['frame_acq_time'] = frame_acq_time

def set_pdf(pdf_pos=[0, 255], safe_out=280, frame_acq_time=0.2, confirm=True):

    ''' Set up the acquisition system for PDF (Pair Distribution Function) measurements.

    This function moves the PE1 detector to the specified positions for PDF measurements
    and updates the XPD configuration to use PE1C as the area detector with the specified
    frame acquisition time.

    Parameters:
        pdf_pos (list): Position of the PE1 detector [pe1_x, pe1_z] for PDF measurement, Default is [0, 255].
        safe_out (float): The safe z position to move PE1 to before adjusting x and z. Default is 280.
        frame_acq_time (float): The frame acquisition time to set in the global configuration. Default is 0.2 seconds.

    '''
    if confirm is True:
        # Ask the user to double-check the pdf_pos and xrd_pos values
        confirmation = input(
            f"Confirm detector positions:\n"
            f"  - PDF Position = {pdf_pos}\n"
            f"  - safe z out = {safe_out}\n"
            f"Proceed with these settings? (y/n): ").strip().lower()
        if confirmation not in ['y', 'yes']:
            print("User chose not to proceed with the measurements.")
            return  # Exit the function if the user doesn't confirm

    pdf_pe1x, pdf_pe1z = pdf_pos

    pe1_z.move(safe_out)
    pe1_x.move(pdf_pe1x)
    pe1_z.move(pdf_pe1z)
    xpd_configuration['area_det'] = pe1c
    glbl['frame_acq_time'] = frame_acq_time


def run_xrd(smpl, exp_xrd, num=1, xrd_pos=[400, 280], calib_file='config_base/xrd.poni',
            frame_acq_time=0.2, dets=None, confirm=True):
    ''' Run one XRD measurement with specified calib_file,
        setup xrd configuration first if was not in xrd configuration yet.

    Parameters:
        smpl (int): Sample index to run the XRD measurement on.
        exp_xrd (float): Total exposure time (in seconds).
        num (int, optional): Number of measurements to take. Default is 1.
        xrd_pos (list, optional): List of PE1 x and z positions. Default is [400, 280].
        calib_file (str, optional): Path to the calibration file for XRD measurement. Default is 'config_base/xrd.poni'.
        frame_acq_time (float, optional): Frame acquisition time. Default is 0.2.
        dets (list, optional): Extra detectors (e.g., temperature controller, motor positions) to read. Default is None.


    '''

    if dets is None:
        dets = []

    xrd_pe1x, xrd_pe1z = xrd_pos

    if pe1_x.position == xrd_pe1x:
        print("PE2C detector is already configured, and PE1 is in the correct position.")
        # already xpd configuration
        xpd_configuration['area_det'] = pe2c
        if glbl['frame_acq_time'] != frame_acq_time:
            glbl['frame_acq_time'] = frame_acq_time
            time.sleep(3)
    else:
        print(f"Setting up PE2 detector for XRD measurement. Moving PE1 to position {xrd_pos}.")
        set_xrd(xrd_pos=xrd_pos, frame_acq_time=frame_acq_time, confirm=confirm)

    # Disable automatic calibration loading
    glbl["auto_load_calib"] = False

    # Load the calibration file
    try:
        xrd_calib = load_calibration_md(calib_file)
        print(f"Calibration file {calib_file} loaded successfully.")
    except FileNotFoundError:
        raise FileNotFoundError(f"Calibration file '{calib_file}' not found.")
    except Exception as e:
        raise RuntimeError(f"Failed to load calibration file: {e}")

    # Run the measurement plan with calibration
    plan = plan_with_calib([pe2c] + dets, exp_xrd, num, xrd_calib)
    xrun(smpl, plan)

    # Re-enable automatic calibration loading
    glbl["auto_load_calib"] = True


def run_pdf(smpl, exp_pdf, num=1, pdf_pos=[0, 255], safe_out=280, calib_file='config_base/pdf.poni',
            frame_acq_time=0.2, dets=[pe1_z], confirm=True):

    ''' Run one PDF measurement, moving the PE1 detector to the specified position
        and configuring the system for PDF measurements.

    Parameters:
        smpl (int): Sample index to run the PDF measurement on.
        exp_pdf (float): Total exposure time (in seconds).
        num (int, optional): Number of measurements to take. Default is 1.
        pdf_pos (list, optional): List of PE1 x and z positions for the PDF measurement. Default is [0, 255].
        safe_out (float, optional): The safe z position to move PE1 to before adjusting x and z. Default is 280.
        calib_file (str, optional): Path to the calibration file for the PDF measurement. Default is 'config_base/pdf.poni'.
        frame_acq_time (float, optional): Frame acquisition time. Default is 0.2 seconds.
        dets (list, optional): Extra detectors (e.g., temperature controller, motor positions). Default is [pe1_z].

    '''
    # Extract PDF x and z positions
    pdf_pe1x, pdf_pe1z = pdf_pos

    # Check if PE1 is already configured
    if pe1_x.position == pdf_pe1x and pe1_z.position == pdf_pe1z:
        print("PE1 detector is already in the correct position.")
        xpd_configuration['area_det'] = pe1c
        if glbl['frame_acq_time'] != frame_acq_time:
            glbl['frame_acq_time'] = frame_acq_time
            time.sleep(3)
    else:
        print(f"Setting up PE1 detector for PDF measurement. Moving PE1 to position {pdf_pos}.")
        set_pdf(pdf_pos=pdf_pos, safe_out=safe_out, frame_acq_time=frame_acq_time, confirm=confirm)

    # Disable automatic calibration loading
    glbl["auto_load_calib"] = False

    # Load the calibration file
    try:
        pdf_calib = load_calibration_md(calib_file)
        print(f"Calibration file {calib_file} loaded successfully.")
    except FileNotFoundError:
        raise FileNotFoundError(f"Calibration file '{calib_file}' not found.")
    except Exception as e:
        raise RuntimeError(f"Failed to load calibration file: {e}")

    # Run the measurement plan with calibration
    plan = plan_with_calib([pe1c] + dets, exp_pdf, num, pdf_calib)
    xrun(smpl, plan)

    # Re-enable automatic calibration loading
    glbl["auto_load_calib"] = True


def plan_with_calib(dets, exp_time, num, calib_file, delay=1):
    '''

    '''
    motors = dets[1:]
    yield from _configure_area_det(exp_time)
    plan = count_with_calib(dets, num, delay=delay, calibration_md=calib_file)
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
