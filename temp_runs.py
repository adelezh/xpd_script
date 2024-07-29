import time


def xpd_temp_list(smpl, Temp_list, exp_time, delay=1, num=1, delay_num=0, dets=[]):
    '''
    example
        xpd_temp_list(1, [300, 350, 400], 5, delay=1, num=1, dets=[euroterhm.power])
        sample 1, at temperature 300, 350 and 400, take one data, exposure time 5sec,
        wait 1 second after each temperature, record eurotherm power(%) at the same time.

        parameters:
        smpl: sample index ID in sample list
        Temp_list: temperature list
        exp_time : total exposure time for each sample, in seconds
        num: number of data at each temperature
        delay: sleep time after each temperature changes, for temperature controller to stable
        dets: list of motors, temperatures controllers, which will be recorded in table.

    '''

    T_controller = xpd_configuration["temp_controller"]
    area_det = xpd_configuration['area_det']
    det=[area_det, T_controller]+dets
    starttime=time.time()
    if delay_num != 0:
        delay_num=delay_num+exp_time
    for Temp in Temp_list:
        print('temperature moving to' + str(Temp))
        T_controller.move(Temp)
        time.sleep(delay)
        plan = ct_motors_plan(det, exp_time, num=num, delay=delay_num)
        xrun(smpl, plan)
    endtime = time.time()
    save_tb_xlsx(smpl, starttime, endtime)
    return None


def xpd_temp_ramp(smpl, Tstart, Tstop, Tstep, exp_time, delay=1, num=1, delay_num=0, dets=[]):
    '''
    example:
        xpd_temp_ramp(1, 300, 400, 10, 5, delay=1, num=1, delay_num=0, dets=[euroterhm.power])
        sample 1, from 300K to 400K, 10K steps, take one data, exposure time 5sec,
        wait 1 second after each temperature. record eurotherm power(%) at the same time

        parameters:
        smpl: sample index ID in sample list
        Tstart, Tstop, Tstep: temperature range(Tstart, Tend), step size: Tstep
        scanplan : scanplan index ID in scanplan list
        delay: sleep time after each temperature changes, for temperature controller to stable
        dets: list of motors, temperatures controllers, which will be recorded in table.
    '''

    T_controller = xpd_configuration["temp_controller"]
    area_det = xpd_configuration['area_det']
    det=[area_det, T_controller]+dets
    starttime=time.time()
    Tnum=int(abs(Tstart-Tstop)/Tstep)+1
    temp_list=np.linspace(Tstart,Tstop,Tnum)
    if delay_num != 0:
        delay_num=delay_num+exp_time
    for Temp in temp_list:
        print('temperature moving to' + str(Temp))
        T_controller.move(Temp)
        time.sleep(delay)
        plan = ct_motors_plan(det, exp_time, num=num, delay=delay_num)
        xrun(smpl, plan)
    endtime = time.time()
    save_tb_xlsx(smpl, starttime, endtime)
    return None

def xpd_temp_setrun(sample, temp, exp_time, delay=1, dets = []):
    '''
    example:
        xpd_temp_setrun(1, 500, 5, delay=1, dets=[euroterhm.power])
        sample 1, set temperature is 500, continually taking data(exposure time= 5sec) until the set temperature is reached.
        wait 1 sec between each data, record temperature and power(%) at the same time

        parameters:
        sample: sample index ID in sample list
        temp: target temperature
        exp_time : total exposure time of each data
        delay: sleep time between each data
        dets: list of motors, temperatures controllers, which will be recorded in table.
    '''
    T_controller = xpd_configuration["temp_controller"]
    area_det = xpd_configuration['area_det']
    det=[area_det, T_controller]+dets
    starttime=time.time()
    print("take one data with dark image before start to temperature")
    glbl['dk_window'] = 0.1
    plan = ct_motors_plan(det, exp_time)
    xrun(sample, plan)
    glbl['dk_window'] = 1000
    print(f'set temperature to {temp}, start to collect data')
    T_controller.set(Temp)
    while abs(T_controller.get()-Temp) >= 1:
        plan = ct_motors_plan(det, exp_time)
        xrun(smpl, plan)
        time.sleep(delay)
    endtime = time.time()
    save_tb_xlsx(smpl, starttime, endtime)
    return None


def mtemp_ramp(sample_list, pos_list, Tstart, Tstop, Tstep, exp_time, delay=1, num=1, delay_num=0, smpl_h=[],
           flt_h=None, flt_l=None, motor=sample_x, dets =[]):
    '''


    '''
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
            xpd_temp_ramp(sample, Tstart, Tstop, Tstep, exp_time, delay=delay, num=num, delay_num=delay_num, dets=dets)

    else:
        print('sample list and pos_list Must have same length!')
        return None


def mtemp_list(sample_list, pos_list, templist, exp_time, delay=1, num=1, delay_num=0, smpl_h=[],
           flt_h=None, flt_l=None, motor=sample_x, dets=[]):
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
            xpd_temp_list(sample, templist, exp_time, delay=delay, num=num, delay_num=delay_num, dets=dets)

    else:
        print('sample list and pos_list Must have same length!')
        return None


