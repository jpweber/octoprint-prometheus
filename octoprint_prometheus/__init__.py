# coding=utf-8

""" Octoprint-Prometheus
    Scott Baker, http://www.smbaker.com/

    This is an Octoprint plugin that exposes a Prometheus client endpoint, allowing printer statistics to be
    collected by Prometheus and view in Grafana.

    Development notes:
       # Sourcing the oprint environment on the pi for development.
       source ~/oprint/bin/activate

       # Find octoprint logs here
       tail -f /home/pi/.octoprint/logs/octoprint.log

       # Uninstall and cleanup
       pip uninstall octoprint-prometheus
       rm -rf /home/pi/oprint/local/lib/python2.7/site-packages/octoprint_prometheus*

       # Upload to pypi
       rm -rf dist
       python setup.py sdist bdist_wheel
       twine upload dist/*

"""

from __future__ import absolute_import

from threading import Timer
from flask import Response, abort
import httplib

import octoprint.plugin
from prometheus_client import Counter, Enum, Gauge, Info, start_http_server

from .gcodeparser import Gcode_parser


class PrometheusPlugin(octoprint.plugin.StartupPlugin,
                       octoprint.plugin.SettingsPlugin,
                       octoprint.plugin.TemplatePlugin,
                       octoprint.plugin.ProgressPlugin,
                       octoprint.plugin.EventHandlerPlugin,
                       octoprint.plugin.BlueprintPlugin):

    @octoprint.plugin.BlueprintPlugin.route("/metrics", methods=["GET"])
    def metrics_proxy(self):
        self._logger.info("Prometheus Proxy (Exposed: %s)" % bool(self._settings.get(["prometheus_exposed"])))
        if not bool(self._settings.get(["prometheus_exposed"])):
            self._logger.info("Prometheus metrics are not exposed")
            abort(404)

        conn = httplib.HTTPConnection("localhost", int(self._settings.get(["prometheus_port"])))
        conn.request("GET", "/metrics")
        resp = conn.getresponse()
        return Response(response=resp.read(), status=resp.status, content_type=resp.getheader('content-type'))

    DESCRIPTIONS = {"octoprint_temperature_bed_actual": "Actual Temperature in Celsius of Bed",
                    "octoprint_temperature_bed__target": "Target Temperature in Celsius of Bed",
                    "octoprint_temperature_tool0_actual": "Actual Temperature in Celsius of Extruder Hot End",
                    "octoprint_temperature_tool0__target": "Target Temperature in Celsius of Extruder Hot End",
                    "octoprint_movement_x": "Movement of X axis from G0 or G1 gcode",
                    "octoprint_movement_y": "Movement of Y axis from G0 or G1 gcode",
                    "octoprint_movement_z": "Movement of Z axis from G0 or G1 gcode",
                    "octoprint_movement_e": "Movement of Extruder from G0 or G1 gcode",
                    "octoprint_movement_speed": "Speed setting from G0 or G1 gcode",
                    "octoprint_extrusion_print": "Filament extruded this print",
                    "octoprint_extrusion_total": "Filament extruded total",
                    "octoprint_progress": "Progress percentage of print",
                    "octoprint_printing": "1 if printing, 0 otherwise",
                    "octoprint_print": "Filename information about print",
                    "octoprint_print_time": "Time passing of print",
                    "octoprint_print_time_left": "Time left of print"
                    }

    def __init__(self, *args, **kwargs):
        super(PrometheusPlugin, self).__init__(*args, **kwargs)
        self.parser = Gcode_parser()
        self.gauges = {}  # holds gauges, counters, infos, and enums
        self.last_extrusion_counter = 0
        self.completion_timer = None

        self.gauges["octoprint_printer_state"] = Enum("octoprint_printer_state",
                                                      "State of printer",
                                                      states=["init", "printing", "done", "failed", "cancelled", "idle"])
        self.gauges["octoprint_printer_state"].state("init")

        self.init_gauge("octoprint_progress")
        self.init_gauge("octoprint_extrusion_print")
        self.init_gauge("octoprint_printing")
        self.init_gauge("octoprint_zchange")
        self.init_gauge("octoprint_movement_x")
        self.init_gauge("octoprint_movement_y")
        self.init_gauge("octoprint_movement_z")
        self.init_gauge("octoprint_movement_e")
        self.init_gauge("octoprint_movement_speed")
        self.init_gauge("octoprint_temperature_bed_actual")
        self.init_gauge("octoprint_temperature_bed_target")
        self.init_gauge("octoprint_temperature_tool0_actual")
        self.init_gauge("octoprint_temperature_tool0_target")
        self.init_gauge("octoprint_temperature_tool1_actual")
        self.init_gauge("octoprint_temperature_tool1_target")
        self.init_gauge("octoprint_temperature_tool2_actual")
        self.init_gauge("octoprint_temperature_tool2_target")
        self.init_gauge("octoprint_temperature_tool3_actual")
        self.init_gauge("octoprint_temperature_tool3_target")
        self.init_gauge("octoprint_print_fan_speed")
        self.init_gauge("octoprint_print_time")
        self.init_gauge("octoprint_print_time_left")

        self.init_counter("octoprint_extrusion_total")

        self.init_info("octoprint_print")

    def on_after_startup(self):
        self._logger.info("Starting Prometheus! (port: %s)" %
                          self._settings.get(["prometheus_port"]))
        start_http_server(int(self._settings.get(["prometheus_port"])))

    def get_settings_defaults(self):
        return dict(prometheus_port=8000, prometheus_exposed=False)

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

    def init_gauge(self, name):
        self.gauges[name] = Gauge(name, self.DESCRIPTIONS.get(name, name))

    def init_counter(self, name):
        self.gauges[name] = Counter(name, self.DESCRIPTIONS.get(name, name))

    def init_info(self, name):
        self.gauges[name] = Info(name, self.DESCRIPTIONS.get(name, name))

    def get_gauge(self, name):
        return self.gauges[name]

    def on_print_progress(self, storage, path, progress):
        gauge = self.get_gauge("octoprint_progress")
        gauge.set(progress)

    def print_complete_callback(self):
        self.get_gauge("octoprint_printer_state").state("idle")
        self.get_gauge("octoprint_progress").set(0)
        self.get_gauge("octoprint_extrusion_print").set(0)
        # This doesn't actually cause it to reset...
        self.get_gauge("octoprint_print").info({})
        self.get_gauge("octoprint_print_time").set(0)
        self.get_gauge("octoprint_print_time_left").set(0)
        self.completion_timer = None

    def print_complete(self, reason):
        self.get_gauge("octoprint_printer_state").state(reason)
        # TODO: may be redundant with printer_state
        self.get_gauge("octoprint_printing").set(0)

        # In 30 seconds, reset all the progress variables back to 0
        # At a default 10 second interval, this gives us plenty of room for Prometheus to capture the 100%
        # complete gauge.

        # TODO: Is this really a good idea?

        self.completion_timer = Timer(30, self.print_complete_callback)
        self.completion_timer.start()

    def on_event(self, event, payload):
        if event == "ZChange":
            # TODO: This doesn't seem useful...
            gauge = self.get_gauge("octoprint_zchange")
            gauge.set(payload["new"])
        elif event == "PrintStarted":
            # If there's a completion timer running, kill it.
            if self.completion_timer:
                self.completion_timer.cancel()
                self.completion_timer = None

            # reset the extrusion counter
            self.parser.reset()
            self.last_extrusion_counter = 0
            # TODO: may be redundant with printer_state
            self.get_gauge("octoprint_printing").set(1)
            self.get_gauge("octoprint_printer_state").state("printing")
            self.get_gauge("octoprint_print").info({"name": payload.get("name", ""),
                                                    "path": payload.get("path", ""),
                                                    "origin": payload.get("origin", "")})
        elif event == "PrintFailed":
            self.print_complete("failed")
        elif event == "PrintDone":
            self.print_complete("done")
        elif event == "PrintCancelled":
            self.print_complete("cancelled")

        """
                # This was my first attempt at measuring positions and extrusions. 
                # Didn't work the way I expected.
                # Went with gcodephase_hook and counting extrusion gcode instead.
                if (event == "PositionUpdate"):
                    for (k,v) in payload.items():
                        if k in ["x", "y", "z", "e"]:
                            k = "position_" + k
                            gauge = self.get_gauge(k)
                            gauge.set(v)
                """

    def gcodephase_hook(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
        if phase == "sent":
            parse_result = self.parser.process_line(cmd)
            if parse_result == "movement":
                for k in ["x", "y", "z", "e", "speed"]:
                    v = getattr(self.parser, k)
                    if v is not None:
                        gauge = self.get_gauge("octoprint_movement_" + k)
                        gauge.set(v)

                # extrusion_print is modeled as a gauge so we can reset it after every print
                gauge = self.get_gauge("octoprint_extrusion_print")
                gauge.set(self.parser.extrusion_counter)

                if self.parser.extrusion_counter > self.last_extrusion_counter:
                    # extrusion_total is monotonically increasing for the lifetime of the plugin
                    counter = self.get_gauge("octoprint_extrusion_total")
                    counter.inc(self.parser.extrusion_counter -
                                self.last_extrusion_counter)
                    self.last_extrusion_counter = self.parser.extrusion_counter

            elif parse_result == "octoprint_print_fan_speed":
                v = getattr(self.parser, "octoprint_print_fan_speed")
                if v is not None:
                    gauge = self.get_gauge("octoprint_print_fan_speed")
                    gauge.set(v)

            currentData = self._printer.get_current_data()
            printTime = currentData["progress"]["printTime"]
            if printTime is not None:
                self.get_gauge('octoprint_print_time').set(printTime)
            printTimeLeft = currentData["progress"]["printTimeLeft"]
            if printTimeLeft is not None:
                self.get_gauge('octoprint_print_time_left').set(printTimeLeft)

        return None  # no change

    def temperatures_handler(self, comm, parsed_temps):
        for (k, v) in parsed_temps.items():
            mapname = {"B": "octoprint_temperature_bed",
                       "T0": "octoprint_temperature_tool0",
                       "T1": "octoprint_temperature_tool1",
                       "T2": "octoprint_temperature_tool2",
                       "T3": "octoprint_temperature_tool3"}

            # We only support four tools. If someone runs into a printer with more tools, please
            # let me know...
            if k not in mapname:
                continue

            k_actual = mapname.get(k, k) + "_actual"
            gauge = self.get_gauge(k_actual)
            try:
                gauge.set(v[0])
            except TypeError:
                pass  # not an integer or float

            k_target = mapname.get(k, k) + "_target"
            gauge = self.get_gauge(k_target)
            try:
                gauge.set(v[1])
            except TypeError:
                pass  # not an integer or float

        return parsed_temps


def __plugin_load__():
    plugin = PrometheusPlugin()

    global __plugin_implementation__
    __plugin_implementation__ = plugin

    global __plugin_hooks__
    __plugin_hooks__ = {"octoprint.comm.protocol.temperatures.received": plugin.temperatures_handler,
                        "octoprint.comm.protocol.gcode.sent": plugin.gcodephase_hook}
