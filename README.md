# Prometheus Client for OctoPrint  
Forked from Scott Baker https://github.com/sbelectronics/octoprint-prometheus

## Purpose ##

This plugin implements a Prometheus client inside of OctoPrint. This is native endpoint served up directly from the OctoPrint. This allows you to monitor your 3D printer using the combination of Prometheus and Grafana.

This plugin will export the following data:
* Progress
* Heat bed temperature
* Tool (extruder) temperatures
* X, Y, Z, E coordinates
* Print Information (file name, location)
* Print time
* Print time remaining

It will also monitor several built in prometheus python client variables, such as process start time, cpu seconds, virtual memory, open file descriptors, etc.

The reason I chose to do this is I already have Prometheus/Grafana for monitoring the environment in my office. Having OctoPrint data available lets me keep track of printer utilization using the same toolchain, and to correlate printer usage with environmental changes.

## Dependencies ##

This package depends upon `prometheus_client`, which should be automatically installed as necessary by pip. 

## Installation ##

Either of the following commands can be used to install the package from the command line:

* `pip install octoprint-prometheus`
* `pip install https://github.com/jpweber/octoprint-prometheus/archive/master.zip`

Additionally, you can install this using the Octoprint GUI by using Plugin Manager --> Get More --> from URL, and entering the URL `https://github.com/jpweber/octoprint-prometheus/archive/master.zip`.

## Configuration ##

The printer by default exposes an endpoint on port 8000. This port may be changed using the plugin's setup page in the OctoPrint UI.

## Testing ##

You can use `curl` or a web browser to view the Prometheus endpoint and ensure it is producting data. For example, 

```bash
pi@octopi:~ $ curl http://localhost:8000/
# HELP octoprint_extrusion_total Filament extruded total
# TYPE octoprint_extrusion_total counter
octoprint_extrusion_total 0.0
# TYPE octoprint_extrusion_created gauge
octoprint_extrusion_created 1.568835504371376e+09
# HELP octoprint_movement_x Movement of X axis from G0 or G1 gcode
# TYPE octoprint_movement_x gauge
octoprint_movement_x 0.0
# HELP octoprint_temperature_bed_actual Actual Temperature in Celsius of Bed
# TYPE octoprint_temperature_bed_actual gauge
octoprint_temperature_bed_actual 31.4
# HELP octoprint_temperature_tool1_target octoprint_temperature_tool1_target
# TYPE octoprint_temperature_tool1_target gauge
octoprint_temperature_tool1_target 0.0
# HELP octoprint_temperature_tool2_actual octoprint_temperature_tool2_actual
# TYPE octoprint_temperature_tool2_actual gauge
octoprint_temperature_tool2_actual 0.0
# HELP octoprint_temperature_tool2_target octoprint_temperature_tool2_target
# TYPE octoprint_temperature_tool2_target gauge
octoprint_temperature_tool2_target 0.0
# HELP octoprint_temperature_bed_target octoprint_temperature_bed_target
# TYPE octoprint_temperature_bed_target gauge
octoprint_temperature_bed_target 0.0
# HELP octoprint_zchange octoprint_zchange
# TYPE octoprint_zchange gauge
octoprint_zchange 0.0
# HELP octoprint_movement_e Movement of Extruder from G0 or G1 gcode
# TYPE octoprint_movement_e gauge
octoprint_movement_e 0.0
# HELP python_info Python platform information
# TYPE python_info gauge
python_info{implementation="CPython",major="2",minor="7",patchlevel="13",version="2.7.13"} 1.0
# HELP octoprint_temperature_tool3_actual octoprint_temperature_tool3_actual
# TYPE octoprint_temperature_tool3_actual gauge
octoprint_temperature_tool3_actual 0.0
# HELP octoprint_extrusion_print Filament extruded this print
# TYPE octoprint_extrusion_print gauge
octoprint_extrusion_print 0.0
# HELP octoprint_movement_speed Speed setting from G0 or G1 gcode
# TYPE octoprint_movement_speed gauge
octoprint_movement_speed 0.0
# HELP octoprint_temperature_tool1_actual octoprint_temperature_tool1_actual
# TYPE octoprint_temperature_tool1_actual gauge
octoprint_temperature_tool1_actual 0.0
# HELP octoprint_movement_y Movement of Y axis from G0 or G1 gcode
# TYPE octoprint_movement_y gauge
octoprint_movement_y 0.0
# HELP octoprint_print_time Time passing of print
# TYPE octoprint_print_time gauge
octoprint_print_time 0.0
# HELP octoprint_temperature_tool0_actual Actual Temperature in Celsius of Extruder Hot End
# TYPE octoprint_temperature_tool0_actual gauge
octoprint_temperature_tool0_actual 32.8
# HELP octoprint_movement_z Movement of Z axis from G0 or G1 gcode
# TYPE octoprint_movement_z gauge
octoprint_movement_z 0.0
# HELP octoprint_print_info Filename information about print
# TYPE octoprint_print_info gauge
octoprint_print_info 1.0
# HELP octoprint_printer_state State of printer
# TYPE octoprint_printer_state gauge
octoprint_printer_state{octoprint_printer_state="init"} 1.0
octoprint_printer_state{octoprint_printer_state="printing"} 0.0
octoprint_printer_state{octoprint_printer_state="done"} 0.0
octoprint_printer_state{octoprint_printer_state="failed"} 0.0
octoprint_printer_state{octoprint_printer_state="cancelled"} 0.0
octoprint_printer_state{octoprint_printer_state="idle"} 0.0
# HELP octoprint_print_time_left Time left of print
# TYPE octoprint_print_time_left gauge
octoprint_print_time_left 0.0
# HELP octoprint_print_fan_speed octoprint_print_fan_speed
# TYPE octoprint_print_fan_speed gauge
octoprint_print_fan_speed 0.0
# HELP octoprint_temperature_tool0_target octoprint_temperature_tool0_target
# TYPE octoprint_temperature_tool0_target gauge
octoprint_temperature_tool0_target 0.0
# HELP octoprint_temperature_tool3_target octoprint_temperature_tool3_target
# TYPE octoprint_temperature_tool3_target gauge
octoprint_temperature_tool3_target 0.0
# HELP octoprint_progress Progress percentage of print
# TYPE octoprint_progress gauge
octoprint_progress 0.0
# HELP process_virtual_memory_bytes Virtual memory size in bytes.
# TYPE process_virtual_memory_bytes gauge
process_virtual_memory_bytes 3.039232e+08
# HELP process_resident_memory_bytes Resident memory size in bytes.
# TYPE process_resident_memory_bytes gauge
process_resident_memory_bytes 6.6506752e+07
# HELP process_start_time_seconds Start time of the process since unix epoch in seconds.
# TYPE process_start_time_seconds gauge
process_start_time_seconds 1.56883549398e+09
# HELP process_cpu_seconds_total Total user and system CPU time spent in seconds.
# TYPE process_cpu_seconds_total counter
process_cpu_seconds_total 53.54
# HELP process_open_fds Number of open file descriptors.
# TYPE process_open_fds gauge
process_open_fds 35.0
# HELP process_max_fds Maximum number of open file descriptors.
# TYPE process_max_fds gauge
process_max_fds 1024.0
# HELP octoprint_printing 1 if printing, 0 otherwise
# TYPE octoprint_printing gauge
octoprint_printing 0.0
```

Note that certain fields will not appear until you've connected to your printer. 

## Installing Prometheus and Grafana ##

Install Prometheus and Grafana on another machine or another pi, as you'll be maintaining a database.

Personally I install it using helm and kubernetes, but there are many different ways to install these tools. Using the helm chart, I add a datasource to Prometheus as follows:

```yaml
      scrape_configs:
        # 3dprinter
        - job_name: '3dprinter'
          metrics_path: /metrics
          scrape_interval: 10s
          static_configs:
            - targets:
              - 198.0.0.246:8000
```

How to install Prometheus and Grafana is beyond the scope of this README. The following links may be helpful to you:

* https://medium.com/@at_ishikawa/install-prometheus-and-grafana-by-helm-9784c73a3e97
* https://www.digitalocean.com/community/tutorials/how-to-install-prometheus-on-ubuntu-16-04
* http://docs.grafana.org/installation/debian/
* https://github.com/carlosedp/arm-monitoring
