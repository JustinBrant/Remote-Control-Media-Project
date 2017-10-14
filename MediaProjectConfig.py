# Button mapping
# Button indices start at 0 at the bottom of the remote, opposite the IR blaster
# i.e. The unlit button is 0
# The indices must be from 0 to 5 only
Button_HDMI        = 5
Button_ChannelUp   = 4
Button_ChannelDown = 3
Button_TvOnOff     = 2
Button_Mute        = 1
Button_Extra       = 0

# Volume control
# 1200 ticks per dial revolution
TicksPerVolumeCommand = 12
DeadzoneTicks = 30
DeadzoneResetTimeMilliseconds = 200
PositiveVolumeDirection = "CW" # Can be "CW" or "CCW" for clockwise and counterclockwise

# LEDs
ButtonBrightnessPercent_ON = 60 # Percent between 0 and 100
ButtonBrightnessPercent_DIM = 15 # Percent between 0 and 100
ButtonDimTimeoutSeconds = 10 # Number of seconds before buttons dim after no activity
VolumeDialBrightensLEDs = 1 # Controls whether volume dial activity brightens buttons - Can be 0 or 1
ButtonOffWhenPressedTimeSeconds = 0.5 # Number of seconds a button LED turns off for when pressed - Set to 0 to disable
