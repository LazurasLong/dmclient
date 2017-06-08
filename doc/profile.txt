dmclient needs to collect info about the user's machine (installed hardware, current usage)

use the following:

platform.architecture() # python interpreter info
platform.machine() # machine type
platform.processor() # "real processor name"
platform.python_compiler() # 
platform.python_version() # detailed python version
platform.win32_ver()
platform.mac_ver()
platform.linux_distribution()

psutil.cpu_times()

psutil.swap_memory()

#psutil.disc_usage(path)
 # Supply 'mountpoint' from disk_partitions()
psutil.disc_io_counters()

