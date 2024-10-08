import time


def xpd_temp_list(smpl, Temp_list, exp_time, delay=1, num=1, delay_num=0, dets=None, takeonedark=False):
    """
    example
        xpd_temp_list(1, [300, 350, 400], 5, delay=1, num=1, delay_num=0, dets=[euroterhm.power])
        sample 1, at temperature 300, 350 and 400, take one data, exposure time 5sec,
        wait 1 second after each temperature, record eurotherm power(%) at the same time.

    parameters:
        smpl: sample index ID in sample list
        Temp_list: temperature list
        exp_time : total exposure time for each sample, in seconds
        delay: sleep time after each temperature changes, for temperature controller to stable
        num: number of data at each temperature
        delay_num : sleep time in between each data if multiple data are taken at each temperature
        dets: list of motors, temperatures controllers, which will be recorded in table.

    """

    if dets is None:
        dets = []

    T_controller = xpd_configuration["temp_controller"]
    area_det = xpd_configuration['area_det']
    det = [area_det, T_controller] + dets
    starttime = time.time()
    if takeonedark is True:
        take_one_dark(smpl, det, exp_time)
        
    if num > 1:  # take more than one data
        delay_num1 = delay_num + exp_time
    else:
        delay_num1 = 0
        
    for Temp in Temp_list:
        print(f'temperature moving to {Temp}')
        T_controller.move(Temp)
        time.sleep(delay)
        plan = ct_motors_plan(det, exp_time, num=num, delay=delay_num1)
        xrun(smpl, plan)
    endtime = time.time()
    save_tb_xlsx(smpl, starttime, endtime)
    return None


def xpd_temp_ramp(smpl, Tstart, Tstop, Tstep, exp_time, delay=1, num=1, delay_num=0, dets=None, takeonedark=False):
    """
    example:
        xpd_temp_ramp(1, 300, 400, 10, 5, delay=1, num=1, delay_num=0, dets=[euroterhm.power])
        sample 1, from 300K to 400K, 10K steps, take one data, exposure time 5sec,
        wait 1 second after each temperature. record eurotherm power(%) at the same time

    parameters:
        smpl: sample index ID in sample list
        Tstart, Tstop, Tstep: temperature range(Tstart, Tend), step size: Tstep
        exp_time : total exposure time for each sample, in seconds
        delay: sleep time after each temperature changes, for temperature controller to stable
        num: number of data at each temperature
        delay_num : sleep time in between each data if multiple data are taken at each temperature
        dets: list of motors, temperatures controllers, which will be recorded in table.
    """

    if dets is None:
        dets = []
    T_controller = xpd_configuration["temp_controller"]
    area_det = xpd_configuration['area_det']
    det = [area_det, T_controller] + dets
    starttime = time.time()
    if takeonedark is True:
        take_one_dark(smpl, det, exp_time)
        
    Tnum = int(abs(Tstart - Tstop) / Tstep) + 1
    temp_list = np.linspace(Tstart, Tstop, Tnum)
    if num > 1:  # take more than one data
        delay_num1 = delay_num + exp_time
    else:
        delay_num1 = 0
    for Temp in temp_list:
        print('temperature moving to' + str(Temp))
        T_controller.move(Temp)
        time.sleep(delay)
        plan = ct_motors_plan(det, exp_time, num=num, delay=delay_num1)
        xrun(smpl, plan)
    endtime = time.time()
    save_tb_xlsx(smpl, starttime, endtime)
    return None


def temp_hold(smpl, Temp_list, holdtime_list, exp_time, delay=1, delay_hold=0,
              dets=None, takeonedark=False, cooltoRT=False):
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
        cooltoRT (bool): Whether to cool to room temperature (30C) after finished measurements, 
            then take one data at room temperature.

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
    
    if cooltoRT is True:
        T_controller.move(30)
        plan = ct_motors_plan(det, exp_time, num=1)
        xrun(smpl, plan)
        

def xpd_temp_setrun(smpl, temp, exp_time, delay=1, hold_time=1, dets=None, cooltoRT=False, takeonedark=Flase):
    """
    example:
        xpd_temp_setrun(1, 500, 5, delay=1, hold_time=1, dets=[euroterhm.power])
        sample 1, set temperature is 500, continuously taking data(exposure time= 5sec) until the set temperature is reached.
        wait 1 sec between each data, record temperature and power(%) at the same time

    parameters:
        sample: sample index ID in sample list
        temp: target temperature
        exp_time : total exposure time of each data
        delay: sleep time between each data
        hold_time: hold time to maintain the targe temperature, continuously taking data during the hold time.
        dets: list of motors, temperatures controllers, which will be recorded in table.
    """
    if dets is None:
        dets = []
    T_controller = xpd_configuration["temp_controller"]
    area_det = xpd_configuration['area_det']
    det = [area_det, T_controller] + dets
    starttime = time.time()
    if takeonedark is True:
        take_one_dark(smpl, det, exp_time)
    print(f'set temperature to {temp}, start to collect data')
    T_controller.set(temp)
    while abs(T_controller.get() - temp) >= 1:
        plan = ct_motors_plan(det, exp_time)
        xrun(smpl, plan)
        time.sleep(delay)
    print(f'reach the temperature, hold for {hold_time}')  
    hold_num = int(hold_time/(exp_time+delay))+1
    for i in range(hold_num):
        plan = ct_motors_plan(det, exp_time)
        xrun(smpl, plan)
        time.sleep(delay)
        
    endtime = time.time()    
    save_tb_xlsx(smpl, starttime, endtime)
    
    if cooltoRT is True:
        RT=30
        T_controller.set(RT)
        print('set temperature to RT, please wait for cool down')
        while abs(T_controller.get() - RT) <= 1:
            plan = ct_motors_plan(det, exp_time)
            xrun(smpl, plan)
            time.sleep(delay)
    return None


def xpd_mtemp_ramp(sample_list, pos_list, Tstart, Tstop, Tstep, exp_time, delay=1, num=1, delay_num=0, smpl_h=None,
                   flt_h=None, flt_l=None, motor=sample_x, dets=None, takeonedark=False):
    """
    example
        xpd_mtemp_ramp([1,2,3],[10, 20, 30],  300, 400, 10, 5, delay=1, num=1, delay_num=0, smpl_h=[1],
        flt_h=[1,0,0,0], flt_l=[0,0,0,0], dets=[euroterhm.power])
        3 samples [1, 2,3], sample_x positions at [10, 20, 30], 
        sample 1 will need filter [1,0,0,0], others([2,3]) does not need filters [0,0,0,0]
        for each sample, from 300K to 400K, 10K steps, take one data at each temperature, exposure time is 5sec
        wait 1 second after each temperature, record eurotherm power(%) at the same time.

    parameters:
        sample_list: list of sample index IDs in sample list
        pos_list: list of sample positions 
        Tstart, Tstop, Tstep: temperature range(Tstart, Tend), step size: Tstep
        exp_time : total exposure time for each sample, in seconds
        delay: sleep time after each temperature changes, for temperature to stable
        num: number of data at each temperature
        delay_num : sleep time in between each data if multiple data are taken at each temperature
        smpl_h: list of samples which need special filter sets
        flt_h: filter set for the sample in the smpl_h
        flt_l: filter set for all other samples in the sample_list. !!! flt_l has to be set if flt_h is set!!!
        dets: list of motors, temperatures controllers, which will be recorded in table.

    """
    if dets is None:
        dets = []
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
            time.sleep(1)
            xpd_temp_ramp(sample, Tstart, Tstop, Tstep, exp_time, delay=delay, num=num, 
                          delay_num=delay_num, dets=dets,takeonedark=takeonedark)

    else:
        print('sample list and pos_list Must have same length!')
        return None


def xpd_mtemp_list(sample_list, pos_list, templist, exp_time, delay=1, num=1, delay_num=0, smpl_h=[],
                   flt_h=None, flt_l=None, motor=sample_x, dets=[], takeonedark=False):
    """
    example
        xpd_mtemp_list([1,2,3],[10, 20, 30],  [300, 350, 400], 5, delay=1, num=1, delay_num=0, smpl_h=[1],
        flt_h=[1,0,0,0], flt_l=[0,0,0,0], dets=[euroterhm.power])
        3 samples [1, 2,3], sample_x positions at [10, 20, 30], 
        sample 1 will need filter [1,0,0,0], others([2,3]) does not need filters [0,0,0,0]
        take one data at temperature 300, 350 and 400, exposure time 5sec,
        wait 1 second after each temperature, record eurotherm power(%) at the same time.

        parameters:
        sample_list: list of sample index IDs in sample list
        pos_list: list of sample positions 
        Temp_list: temperature list
        exp_time : total exposure time for each sample, in seconds
        delay: sleep time after each temperature changes, for temperature controller to stable
        num: number of data at each temperature
        delay_num : sleep time in between each data if multiple data are taken at each temperature
        smpl_h: list of samples which need special filter sets
        flt_h: filter set for the sample in the smpl_h
        flt_l: filter set for all other samples in the sample_list. !!! flt_l has to be set if flt_h is set!!!
        dets: list of motors, temperatures controllers, which will be recorded in table.
    
    
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
            time.sleep(1)
            xpd_temp_list(sample, templist, exp_time, delay=delay, num=num, 
                          delay_num=delay_num, dets=dets, takeonedark=takeonedark)

    else:
        print('sample list and pos_list Must have same length!')
        return None
