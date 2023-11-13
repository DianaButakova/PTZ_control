
from time import sleep
import math
import sys
from onvif import ONVIFCamera
import zeep

#speed
XMAX = 1
XMIN = -1
# YMAX = 1
# YMIN = -1


max_speed_onXaxis=18.85
max_speed_onYaxis=10

func_of_presetpoint=1



def get_coordinates():
    try:
        coordinates_input = input()
        #вводим данные и делим их. Зум задается временем. Тут зум задается временем и знаком "-". Допустим 360,45,5    - зум увеличивается 5 сек. Если -5, то уменьшается 5 сек.
        final_point_Xaxis, final_point_Yaxis, Z_time = map(int, coordinates_input.split(','))

        return final_point_Xaxis, final_point_Yaxis, Z_time
    except ValueError:
        print("Invalid input")
        # Возможно это не понадобится, но на всякий
        sys.exit(1)

def calculations(final_point_Xaxis, final_point_Yaxis, X_pos_current, Y_pos_current):
    #Данная функция для движения вместе по Х и У

    delta_X=abs(final_point_Xaxis-X_pos_current)
    delta_Y=abs(final_point_Yaxis-Y_pos_current)

    Xaxis_first_displacement_TIME=delta_X//max_speed_onXaxis

    if delta_X-max_speed_onXaxis*Xaxis_first_displacement_TIME >= max_speed_onXaxis/2:
        Xaxis_first_displacement_TIME+=1

    delta_displX1= abs(delta_X-Xaxis_first_displacement_TIME*max_speed_onXaxis)
    Xaxis_sec_displacement_TIME=delta_displX1//max_speed_onXaxis
    # начало такое же как и в  том коде
    Xaxis_total_TIME=Xaxis_sec_displacement_TIME+Xaxis_first_displacement_TIME
    #тоталмвремя для нахождения скорости по У
    displacement_Xaxis=max_speed_onXaxis*Xaxis_total_TIME

    Speed_on_Yaxis=round(delta_Y/Xaxis_total_TIME, 1)

    displacement_Yaxis=Xaxis_total_TIME*Speed_on_Yaxis
    
    #тут логика в том, что камера на максимальной скорости идет по Х, но в это же время со скоростью Speed_on_Yaxis идет по У. и в итоге достигает назначенной точки
    return Xaxis_first_displacement_TIME,Xaxis_sec_displacement_TIME, Speed_on_Yaxis, displacement_Xaxis, displacement_Yaxis



def zeep_pythonvalue(self, xmlvalue):
    return xmlvalue

def goto_preset(self, num_of_presetpoint):
    self.request.PresetToken = str(num_of_presetpoint)
    self.ptz.GotoPreset(self.request)



def perform_move(ptz, request, timeout):
    ptz.ContinuousMove(request)
    sleep(timeout) 
    ptz.Stop({'ProfileToken': request.ProfileToken})



def move_up_right(ptz, request, timeout,Y_speed):
    print('move up right...')
    request.Velocity.PanTilt.x = XMIN #min
    request.Velocity.PanTilt.y = Y_speed #мин
    perform_move(ptz, request, timeout)

def move_up_left(ptz, request,timeout, Y_speed):
    print('move up left...')
    request.Velocity.PanTilt.x = XMAX
    request.Velocity.PanTilt.y = Y_speed #YMIN
    perform_move(ptz, request, timeout)

def move_down_right(ptz, request, timeout,Y_speed):
    print('move down right...')
    request.Velocity.PanTilt.x = XMIN
    request.Velocity.PanTilt.y = Y_speed #YMAX
    perform_move(ptz, request, timeout)

def move_down_left(ptz, request, timeout,Y_speed):
    print('move down left...')
    request.Velocity.PanTilt.x = XMAX
    request.Velocity.PanTilt.y = Y_speed #YMAX
    perform_move(ptz, request, timeout)
    


def zoom_up(ptz,request,timeout):
    print('zoom up')
    request.Velocity.Zoom.x = 0.1
    request.Velocity.PanTilt.x = 0
    request.Velocity.PanTilt.y = 0
    perform_move(ptz,request,timeout)


def zoom_down(ptz,request,timeout):
    print('zoom down')
    request.Velocity.Zoom.x = -0.1
    request.Velocity.PanTilt.x = 0
    request.Velocity.PanTilt.y = 0
    perform_move(ptz, request, timeout)




def continuous_move(final_point_Xaxis, final_point_Yaxis, Z_time, init_point_Xaxis, init_point_Yaxis):
    
    mycam = ONVIFCamera('192.168.0.240', 80, 'admin', '123456')
    # Create media service object
    media = mycam.create_media_service()
    # Create ptz service object
    ptz = mycam.create_ptz_service()

    # Get target profile
    zeep.xsd.simple.AnySimpleType.pythonvalue = zeep_pythonvalue
    media_profile = media.GetProfiles()[0]

    # Get PTZ configuration options for getting continuous move range
    request = ptz.create_type('GetConfigurationOptions')
    request.ConfigurationToken = media_profile.PTZConfiguration.token
    ptz_configuration_options = ptz.GetConfigurationOptions(request)

    request = ptz.create_type('ContinuousMove')
    request.ProfileToken = media_profile.token
    ptz.Stop({'ProfileToken': media_profile.token})

    if request.Velocity is None:
        request.Velocity = ptz.GetStatus({'ProfileToken': media_profile.token}).Position
        request.Velocity = ptz.GetStatus({'ProfileToken': media_profile.token}).Position
        request.Velocity.PanTilt.space = ptz_configuration_options.Spaces.ContinuousPanTiltVelocitySpace[0].URI
        request.Velocity.Zoom.space = ptz_configuration_options.Spaces.ContinuousZoomVelocitySpace[0].URI

    # Get range of pan and tilt
    # NOTE: X and Y are velocity vector
    global XMAX, XMIN, YMAX, YMIN
    XMAX = ptz_configuration_options.Spaces.ContinuousPanTiltVelocitySpace[0].XRange.Max
    XMIN = ptz_configuration_options.Spaces.ContinuousPanTiltVelocitySpace[0].XRange.Min
    YMAX = ptz_configuration_options.Spaces.ContinuousPanTiltVelocitySpace[0].YRange.Max
    YMIN = ptz_configuration_options.Spaces.ContinuousPanTiltVelocitySpace[0].YRange.Min

    #displacement_Xaxis, displacement_Yaxis  это настоящее движение. Допустим мы задали 90 градусов. Скорость камеры не позволит добраться прям до этой точки.Камера двинется на 4 секунды, 
    # то есть на 74 градуса, потом докрутит еще некоторое время. В итоге получается не 90 полных градуса, [90-1.8, 90] градуса
    #погрешность максимум 1.8 градуса. 
    Xaxis_first_displacement_TIME,Xaxis_sec_displacement_TIME, Speed_on_Yaxis, displacement_Xaxis, displacement_Yaxis = calculations(final_point_Xaxis, final_point_Yaxis, init_point_Xaxis, init_point_Yaxis)

    if final_point_Xaxis>=init_point_Xaxis and final_point_Xaxis>=init_point_Yaxis:
        move_up_right(ptz, request,Xaxis_first_displacement_TIME,-Speed_on_Yaxis )   
        move_up_right(ptz, request,Xaxis_sec_displacement_TIME,-Speed_on_Yaxis )  

    elif final_point_Xaxis<=init_point_Xaxis and final_point_Xaxis>=init_point_Yaxis:    
        move_up_left(ptz, request, Xaxis_first_displacement_TIME,-Speed_on_Yaxis)
        move_up_left(ptz, request, Xaxis_sec_displacement_TIME,-Speed_on_Yaxis)

    elif final_point_Xaxis<=init_point_Xaxis and final_point_Xaxis<=init_point_Yaxis:    
        move_down_left(ptz, request, Xaxis_first_displacement_TIME,Speed_on_Yaxis)
        move_down_left(ptz, request, Xaxis_sec_displacement_TIME,Speed_on_Yaxis)  
          
    elif final_point_Xaxis>=init_point_Xaxis and final_point_Xaxis<=init_point_Yaxis:    
        move_down_right(ptz, request, Xaxis_first_displacement_TIME,Speed_on_Yaxis)
        move_down_right(ptz, request, Xaxis_sec_displacement_TIME,Speed_on_Yaxis)  

    

    if Z_time>0:
        zoom_up(ptz,request,Z_time)
    else:
        zoom_down(ptz,request,abs(Z_time))
    
    init_point_Xaxis = displacement_Xaxis
    init_point_Yaxis = displacement_Yaxis
    return init_point_Xaxis, init_point_Yaxis

    


if __name__ == '__main__':
    init_point_Xaxis, init_point_Yaxis = 0, 0  
    final_point_Xaxis, final_point_Yaxis, Z_time = get_coordinates()
    init_point_Xaxis, init_point_Yaxis = continuous_move(final_point_Xaxis, final_point_Yaxis, Z_time, init_point_Xaxis, init_point_Yaxis)
