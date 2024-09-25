
def temp_hold(smpl, Temp_list, holdtime_list, exp_time, delay=1, delay_hold=0, dets=None, takeonedark=False):
    """
    Controls the temperature change and data collection for a sample experiment.

    Parameters:
        smpl (int): Sample index or ID.
        Temp_list (list): List of target temperatures to set.
        holdtime_list (list): Corresponding list of hold times for each temperature.
        exp_time (float): Exposure time (seconds).
        delay (float): Time to wait for the temperature to stabilize.
        delay_hold (float): Additional delay between measurements.
        dets (list): Optional list of detectors/motors to record.
        takeonedark (bool): Whether to take a dark measurement first.

    """

    if dets is None:
        dets = []

    T_controller = xpd_configuration["temp_controller"]
    area_det = xpd_configuration['area_det']
    det = [area_det, T_controller] + dets

    # log the start time
    starttime = time.time()

    # Optionally take a dark measurement
    if takeonedark is True:
        take_one_dark(smpl, det, exp_time)

    delay_true = delay_hold + exp_time

    # Iterate over each temperature and holdtime
    for Temp, holdtime in zip(Temp_list, holdtime_list):
        print(f'temperature moving to {Temp}, then hold for {holdtime}')
        T_controller.move(Temp)
        
        # Wait for temperature to stabilize.
        time.sleep(delay)

        # Calculate the number of data points to collect at this temperature
        num = int(holdtime / exp_time) + 1
        plan = ct_motors_plan(det, exp_time, num=num, delay=delay_true)
        xrun(smpl, plan)

    # Log the end time
    endtime = time.time()

    # Save data to an Excel file
    save_tb_xlsx(smpl, starttime, endtime)


def move_to_position(motorx, posx, motory, posy):
    """
    Helper function to move the X and Y motors only if they are not already at the desired positions.

    Parameters
    ----------
    motorx : motor
        The motor controlling the X position.

    posx : float
        The desired X position.

    motory : motor
        The motor controlling the Y position.

    posy : float
        The desired Y position.

    Returns
    -------
    None
    """
    current_x = motorx.read()
    current_y = motory.read()

    # Move X motor only if not already at the desired position
    if current_x != posx:
        logging.info(f"Moving motor X from {current_x} to {posx}")
        motorx.move(posx)

    # Move Y motor only if not already at the desired position
    if current_y != posy:
        logging.info(f"Moving motor Y from {current_y} to {posy}")
        motory.move(posy)

