#!/usr/bin/python
import argparse
import math
from enum import Enum
import re
import os
from typing import List


class Line:
    def __init__(self, xy1: tuple, xy2: tuple):
        self.x1 = xy1[0]
        self.y1 = xy1[1]
        self.x2 = xy2[0]
        self.y2 = xy2[1]
        self._length = None

    def length(self):
        if self._length is None:
            self._length = math.hypot(self.x2 - self.x1, self.y2 - self.y1)
        return self._length

    def __str__(self):
        return f'X1:{self.x1} Y1:{self.y1} X2:{self.x2} Y2:{self.y2}'


class Parameter:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return f"{self.name}{self.value}"

    def clone(self):
        return Parameter(self.name, self.value)


class State:
    def __init__(self, x=None, y=None, z=None, e=None, f=None,
                 extr_temp=None, bed_temp=None, fan=None, move_absolute=True,
                 extrude_absolute=True):
        self.X = x
        self.Y = y
        self.Z = z
        self.E = e
        self.F = f
        self.ExtruderTemperature = extr_temp
        self.BedTemperature = bed_temp
        self.Fan = fan
        self.move_is_absolute = move_absolute
        self.extrude_is_absolute = extrude_absolute

    def clone(self):
        return State(self.X, self.Y, self.Z, self.E, self.F,
                     self.ExtruderTemperature, self.BedTemperature, self.Fan)


class Gcode:
    def __init__(self, command: str = None, parameters: List[Parameter] = None,
                 move_is_absolute: bool = True, extrude_is_absolute: bool = True,
                 comment: str = None, previous_state: State = None):
        self.command = command
        if parameters is None:
            self.parameters = []
        else:
            self.parameters = parameters
        self.move_is_absolute = move_is_absolute
        self.extrude_is_absolute = extrude_is_absolute
        self.comment = comment
        self.previous_state = previous_state
        self.num_line = None

    def __str__(self):
        string = ""
        if self.command is not None:
            string += self.command
            for st in self.parameters:
                if st.value is None:
                    string += f' {st.name}'
                else:
                    if st.name == "X":
                        string += f' {st.name}{round(st.value, 3)}'
                    elif st.name == "Y":
                        string += f' {st.name}{round(st.value, 3)}'
                    elif st.name == "Z":
                        value = round(st.value, 3)
                        value = format(value, '.3f')
                        value = value.rstrip('0').rstrip('.')
                        string += f' {st.name}{value}'
                    elif st.name == "E":
                        value = round(st.value, 2)
                        value = format(value, '.2f')
                        value = value.rstrip('0').rstrip('.')
                        string += f' {st.name}{value}'
                    else:
                        string += f' {st.name}{st.value}'

        if self.comment is not None and len(self.comment) > 1:
            if string == "":
                string += f"; {self.comment}"
            else:
                string += f" ; {self.comment}"

        return string

    def clone(self):
        if self.previous_state is None:
            prev_state = State()
        else:
            prev_state = self.previous_state.clone()
        gcode = Gcode(self.command,
                      move_is_absolute=self.move_is_absolute, extrude_is_absolute=self.extrude_is_absolute,
                      comment=self.comment, previous_state=prev_state)
        for param in self.parameters:
            gcode.parameters.append(param.clone())

        if self.num_line is not None:
            gcode.num_line = self.num_line
        return gcode

    def state(self):
        if self.previous_state is None:
            _state = State()
            _state.X = 0
            _state.Y = 0
            _state.Z = 0
            _state.E = 0
        else:
            _state = self.previous_state.clone()

        if self.command == "G1":
            for parameter in self.parameters:
                if parameter.name == "X":
                    if _state.move_is_absolute:
                        _state.X = parameter.value
                    else:
                        _state.X += parameter.value
                elif parameter.name == "Y":
                    if _state.move_is_absolute:
                        _state.Y = parameter.value
                    else:
                        _state.Y += parameter.value
                elif parameter.name == "Z":
                    if _state.move_is_absolute:
                        _state.Z = parameter.value
                    else:
                        _state.Z += parameter.value
                elif parameter.name == "E":
                    if _state.extrude_is_absolute:
                        _state.E = parameter.value
                    else:
                        _state.E += parameter.value
                elif parameter.name == "F":
                    _state.F = parameter.value
        elif self.command == "G28":
            restore_all = True
            for parameter in self.parameters:
                if parameter.name == "X":
                    _state.X = 0
                    restore_all = False
                elif parameter.name == "Y":
                    _state.Y = 0
                    restore_all = False
                elif parameter.name == "Z":
                    _state.Z = 0
                    restore_all = False
            if restore_all:
                _state.X = 0
                _state.Y = 0
                _state.Z = 0
                _state.E = 0
                _state.F = None
        elif self.command == "M104" or self.command == "M109":
            for parameter in self.parameters:
                if parameter.name == "S":
                    _state.ExtruderTemperature = parameter.value
        elif self.command == "M140" or self.command == "M190":
            for parameter in self.parameters:
                if parameter.name == "S":
                    _state.BedTemperature = parameter.value
        elif self.command == "M106":
            for parameter in self.parameters:
                if parameter.name == "S":
                    _state.Fan = parameter.value
        elif self.command == "G92":  # Set current position
            for parameter in self.parameters:
                if parameter.name == "X":
                    _state.X = parameter.value
                elif parameter.name == "Y":
                    _state.Y = parameter.value
                elif parameter.name == "Z":
                    _state.Z = parameter.value
                elif parameter.name == "E":
                    _state.E = parameter.value

        _state.move_is_absolute = self.move_is_absolute
        _state.extrude_is_absolute = self.extrude_is_absolute
        return _state

    def is_xy_movement(self):
        if self.command != "G1":
            return False
        found_x = next((gc for gc in self.parameters if gc.name == "X" and gc.value is not None), None)
        found_y = next((gc for gc in self.parameters if gc.name == "Y" and gc.value is not None), None)
        if found_x is not None or found_y is not None:
            return True
        return False

    def is_z_movement(self):
        if self.command != "G1":
            return False
        found_z = next((gc for gc in self.parameters if gc.name == "Z" and gc.value is not None), None)
        if found_z is not None:
            return True
        return False

    def is_any_movement(self):
        if self.is_xy_movement() or self.is_z_movement():
            return True
        return False

    def is_extruder_move(self):
        found_e = next((gc for gc in self.parameters if gc.name == "E" and gc.value is not None), None)
        if found_e is not None and self.command != "G92":
            return True
        return False

    def move_length(self) -> float:
        state = self.state()
        x1 = self.previous_state.X
        y1 = self.previous_state.Y
        x2 = state.X
        y2 = state.Y
        if x1 and x2 and y1 and y2:
            return distance_between_points(x1, y1, x2, y2)
        return None

    def set_param(self, name, value):
        found = next((gc for gc in self.parameters if gc.name == name), None)
        if found is not None:
            found.value = value
        else:
            self.parameters.append(Parameter(name, value))

    def get_param(self, name):
        found = next((gc for gc in self.parameters if gc.name == name), None)
        if found is not None:
            return found.value


def validate_gcode_command_string(string):
    # The pattern matches a letter followed by a positive number or zero
    pattern = re.compile("^[A-Za-z][0-9]+$")
    # The match method returns None if the string does not match the pattern
    return pattern.match(string) is not None


def parse_gcode_line(gcode_line: str, prev_state: State) -> Gcode:
    gcode = Gcode()
    if prev_state is not None:
        gcode.previous_state = prev_state.clone()

    gcode_line = gcode_line.strip()
    if not gcode_line:
        return gcode
    if gcode_line.startswith(";") or gcode_line.startswith("\n"):  # If contain only comment
        # gcode.comment = gcode_line.replace("\n", "").replace(';', "").strip()
        if gcode_line.endswith("\n"):
            gcode_line = gcode_line[:len(gcode_line) - 1]
        gcode.command = gcode_line.replace("\n", "", )
        return gcode

    parts = gcode_line.split(';', 1)
    if len(parts) > 1:
        gcode.comment = parts[1].replace("\n", "").replace(';', "").strip()

    gcode_parts = parts[0].strip().split()  # Split the line at semicolon to remove comments

    if validate_gcode_command_string(gcode_parts[0]) is False:  # validate command is one letter and one positive number
        gcode.command = parts[0]
        return gcode

    gcode.command = gcode_parts[0]

    for part in gcode_parts[1:]:  # Iterate through the remaining parts and extract key-value pairs
        name = part[0]
        value = part[1:]
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError as e:
                # Just keep everything in name
                name = part
                value = None
        parameter = Parameter(name, value)
        gcode.parameters.append(parameter)

    return gcode


class Mode(Enum):
    REGULAR = 0
    PERIMETER = 1
    EXT_PERIMETER = 2
    OVERHANG_PERIMETER = 3
    BR_INFILL = 4
    SOLID_INFILL = 5
    TOP_SOLID_INFILL = 6


def distance_between_points(x1, y1, x2, y2):
    if x2 is None:
        x2 = x1
    if y2 is None:
        y2 = y1
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def delete_file_if_exists(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"The file {file_path} has been deleted.")
    else:
        print(f"The file {file_path} does not exist.")


def read_gcode_file(path: str) -> List[Gcode]:
    gcodes = []
    print("Read gcode file to memory")
    with open(path, "r") as readfile:
        lines = readfile.readlines()
        last_state = None
        num_line = 1
        for line in lines:
            gcode = parse_gcode_line(line, last_state)
            if gcode.command == "G90":  # enable absolute coordinates
                gcode.move_is_absolute = True
            elif gcode.command == "G91":  # enable relative coordinates
                gcode.move_is_absolute = False
            elif gcode.command == "M82":  # enable absolute distances for extrusion
                gcode.extrude_is_absolute = True
            elif gcode.command == "M83":  # enable relative distances for extrusion
                gcode.extrude_is_absolute = False
            last_state = gcode.state()
            gcode.num_line = num_line
            num_line += 1

            z_value = gcode.get_param("Z")
            if z_value is not None and z_value > gcode.previous_state.Z:
                gcode.comment = "Z lift"

            gcodes.append(gcode)
    readfile.close()
    return gcodes


def calculate_length_of_lines(sliced: List[Gcode]) -> float:
    length = 0
    for gcode in sliced:
        if gcode.is_xy_movement() is False:
            continue
        length_of_move = gcode.move_length()
        if length_of_move is not None:
            length += length_of_move
    return length


def find_closed_loops(gcodes: List[Gcode],
                      max_distance_start_end: float,
                      min_loop_length: float,
                      first_layer_height: float):
    loops = []
    start = None
    end = None
    for gcode_id in range(len(gcodes)):
        gcode = gcodes[gcode_id]
        if gcode.is_xy_movement() is False:
            continue

        if gcode.is_extruder_move():
            if start is None and gcode.state().Z > first_layer_height:
                start = gcode
                end = gcode
            else:
                end = gcode

        if start is not None and gcode.is_extruder_move() is False:
            start_state = start.previous_state
            end_state = end.state()
            distance = distance_between_points(start_state.X, start_state.Y, end_state.X, end_state.Y)
            if distance < max_distance_start_end:
                start_index = gcodes.index(start)
                end_index = gcodes.index(end)
                sliced = gcodes[start_index:end_index + 1]
                loop_length = calculate_length_of_lines(sliced)
                if loop_length > min_loop_length:
                    loops.append((start_index, end_index))
                    print(f"Found a loop number {len(loops)}")
            start = None
            end = None

    return loops


def vector_from_points(p1, p2):
    return [p2[0] - p1[0], p2[1] - p1[1]]


def vector_add(v1, v2):
    return [v1[0] + v2[0], v1[1] + v2[1]]


def vector_mul(v, s):
    return [v[0] * s, v[1] * s]


def vector_mag(v):
    return (v[0] ** 2 + v[1] ** 2) ** 0.5


def vector_norm(v):
    m = vector_mag(v)
    return [v[0] / m, v[1] / m]


def cut_gcode(gcode: Gcode, distance):
    start = [gcode.previous_state.X, gcode.previous_state.Y]  # Define the start and end points as lists
    end = [gcode.state().X, gcode.state().Y]
    direction = vector_from_points(start, end)  # Calculate the direction vector of the line
    direction = vector_norm(direction)  # Normalize the direction vector to unit length
    point = vector_add(start, vector_mul(direction,
                                         distance))  # Calculate the point on the line at the given distance from the start

    if gcode.extrude_is_absolute:
        raise Exception("extrude mast to be relative")

    length = gcode.move_length()
    ratio = distance / length

    extruded_length = gcode.get_param("E")
    extruded_position_1 = extruded_length * ratio
    extruded_position_2 = extruded_length - extruded_position_1

    gcode1 = gcode.clone()
    gcode1.set_param(name="X", value=point[0])
    gcode1.set_param(name="Y", value=point[1])
    gcode1.set_param(name="E", value=extruded_position_1)

    gcode2 = gcode.clone()
    gcode2.set_param(name="E", value=extruded_position_2)
    gcode2.previous_state = gcode1.state()

    return gcode1, gcode2


def make_slope_step_brothers_gcodes(slope_step_gcodes: List[Gcode],
                                    layer_height,
                                    current_layer_level,
                                    slope_height):
    start = []
    finish = []

    finish_nozzle_height = current_layer_level + layer_height
    slope_nozzle_height = current_layer_level + slope_height
    layer_ratio = slope_height / layer_height

    for gcode in slope_step_gcodes:
        if gcode.is_xy_movement() is False:
            start.append(gcode)
            continue

        filament_length_original = gcode.get_param("E")
        gcode_start = gcode.clone()
        gcode_start.set_param("Z", slope_nozzle_height)
        filament_start_length = filament_length_original * layer_ratio
        gcode_start.set_param("E", filament_start_length)
        line_lenght1 = gcode_start.move_length()
        extrude_rate1 = filament_start_length / line_lenght1
        gcode_start.comment = f"Slope increase. Length={round(line_lenght1, 3)} R={round(extrude_rate1, 3)}"
        start.append(gcode_start)

        gcode_finish = gcode.clone()
        gcode_finish.set_param("Z", finish_nozzle_height)

        filament_finish_length = filament_length_original - filament_start_length
        gcode_finish.set_param("E", filament_finish_length)
        line_lenght2 = gcode_finish.move_length()
        extrude_rate2 = filament_finish_length / line_lenght2
        gcode_finish.comment = f"Slope decrease. Length={round(line_lenght2, 3)} R={round(extrude_rate2, 3)}"
        finish.append(gcode_finish)

    return start, finish


def reverse_movement_sequence(gcodes: List[Gcode]):
    new_gcode_list = []

    for gcode in reversed(gcodes):
        gc = gcode.clone()
        gc.comment = "Return to the original point for the next move"

        speed = next((par for par in gc.parameters if par.name == "F"), None)
        if speed is not None:
            gc.parameters.remove(speed)

        extrude = next((par for par in gc.parameters if par.name == "E"), None)
        if extrude is not None:
            gc.parameters.remove(extrude)

        new_gcode_list.append(gc)

    new_gcode_list.remove(new_gcode_list[0])  # because we are already here
    return new_gcode_list


def modify_loop_with_slope(loop_gcodes: List[Gcode], slope_steps: int, layer_height: float) -> \
        List[Gcode]:
    """
    generate gcode with slopes
    :param loop_gcodes:
    :param layer_height:
    :param slope_steps:
    :return:
    """

    remaining_gcodes = list(loop_gcodes)
    first_move_Z = next((gc for gc in loop_gcodes if gc.is_extruder_move() and gc.is_xy_movement()))
    current_nozzle_finish_height = first_move_Z.state().Z
    current_layer_level = current_nozzle_finish_height - layer_height
    slope_length = calculate_length_of_lines(loop_gcodes)
    slope_length_per_step = slope_length / slope_steps
    slope_height_per_step = layer_height / slope_steps

    slope_increase = []
    slope_decrease = []

    move_to_position_gcode = Gcode(command="G1")
    move_to_position_gcode.parameters.append(Parameter("Z", current_layer_level + slope_height_per_step))
    move_to_position_gcode.comment = "Move nozzle in start slope position"
    slope_increase.append(move_to_position_gcode)

    for step in range(1, slope_steps + 1):
        slope_length_per_step_left = slope_length_per_step
        slope_height = slope_height_per_step * step
        slope_increase_step_gcodes = []
        while round(slope_length_per_step_left, 6) > 0:
            if len(remaining_gcodes) ==0:
                break
            if remaining_gcodes[0].is_xy_movement() is False:  # any change of speed and acceleration
                slope_increase.append(remaining_gcodes[0])
                remaining_gcodes.remove(remaining_gcodes[0])
                continue
            minimal_line_to_draw = 0.1

            while round(slope_length_per_step_left, 6) > 0:
                if remaining_gcodes[0].move_length() - slope_length_per_step_left > minimal_line_to_draw:
                    gcode1, gcode2 = cut_gcode(remaining_gcodes[0], slope_length_per_step_left)
                    slope_increase_step_gcodes.append(gcode1)
                    slope_length_per_step_left -= gcode1.move_length()
                    remaining_gcodes[0] = gcode2
                else:
                    slope_length_per_step_left -= remaining_gcodes[0].move_length()
                    slope_increase_step_gcodes.append(remaining_gcodes[0])
                    remaining_gcodes.remove(remaining_gcodes[0])
                    break

        (slope_increase_step_gcodes,
         slope_decrease_step_gcodes) = make_slope_step_brothers_gcodes(
            slope_step_gcodes=slope_increase_step_gcodes,
            layer_height=layer_height,
            current_layer_level=current_layer_level,
            slope_height=slope_height)
        slope_increase.extend(slope_increase_step_gcodes)
        if step != slope_steps:  # don't write last decrease step sequence because its with zero extrusion
            slope_decrease.extend(slope_decrease_step_gcodes)



    for_return = []
    for_return.extend(slope_increase)
    for_return.extend(remaining_gcodes)
    for_return.extend(slope_decrease)

    #for_return.extend(reverse_movement_sequence(slope_decrease))

    # lift = Gcode(command="G1", comment="Z lift")
    # lift.set_param("Z", current_nozzle_finish_height + 0.1)
    # for_return.append(lift)

    # retract = Gcode("G1",comment="little retract before slope")
    # retract.set_param("E", -0.05)
    # for_return.insert(0, retract)

    return for_return


def convert_to_relative_extrude(gcodes: List[Gcode]):
    gcodes_new = []
    print("Convert gcode to relative extrude moves")

    first_move = next((gc for gc in gcodes if gc.command == "G1"), None)
    first_move_id = gcodes.index(first_move)
    enable_relative_extrude = Gcode(command="M83", comment="enable relative extrude mode")
    gcodes.insert(first_move_id, enable_relative_extrude)
    for gcode in gcodes:
        if gcode.command == "M82":  # pass enable absolute mode command
            continue

        gcode_new = gcode.clone()
        gcode_new.extrude_is_absolute = False

        if len(gcodes_new) > 1:
            gcode_new.previous_state = gcodes_new[-1].state()

        if gcode.is_extruder_move():
            relative_extrude_length = gcode.get_param("E") - gcode.previous_state.E
            gcode_new.set_param("E", relative_extrude_length)
            gcodes_new.append(gcode_new)
        else:
            gcodes_new.append(gcode_new)

    return gcodes_new


def include_speed_in_command(gcodes: List[Gcode]):
    gcodes_new = []
    gcode_speed_change = None
    print("Include speed command in to move command")
    for gcode in gcodes:
        index = gcodes.index(gcode)
        if index % 100 == 0:
            print(f"{index} of {len(gcodes)}")
        gcodes_new.append(gcode)
        if gcode.command == "G1":
            if gcode.get_param("F") is not None and gcode.is_any_movement() is False:
                if gcode_speed_change is not None:
                    gcodes_new.remove(gcode_speed_change)
                gcode_speed_change = gcode
                continue

            if gcode_speed_change is not None and gcode.is_any_movement() and gcode.get_param("F") is None:
                gcode.set_param("F", gcode_speed_change.get_param("F"))
                gcodes_new.remove(gcode_speed_change)
                gcode_speed_change = None

    return gcodes_new


def main():
    parser = argparse.ArgumentParser(description='Seam hide post-process')
    parser.add_argument('path', help='the path to the file')
    parser.add_argument('--first_layer', dest='first_layer', default=0.3, type=float)
    parser.add_argument('--other_layers', dest='other_layers', default=0.3, type=float)
    parser.add_argument('--slope_min_length', dest='slope_min_length', default=5, type=float)
    parser.add_argument('--slope_steps', dest='slope_steps', default=10, type=int)
    parser.add_argument('--save_to_file', dest='save_to_file', default=None, type=bool)

    args = parser.parse_args()

    first_layer_height = args.first_layer
    layer_height = args.other_layers
    slope_min_length = args.slope_min_length
    slope_steps = args.slope_steps
    save_to_file = args.save_to_file

    file_path = args.path

    # prusa_env_output_name = str(os.getenv('SLIC3R_PP_OUTPUT_NAME'))
    gcodes = read_gcode_file(file_path)
    # gcodes = include_speed_in_command(gcodes)
    gcodes = convert_to_relative_extrude(gcodes)

    closed_loop_ids = find_closed_loops(gcodes, 0.4, slope_min_length,
                                        first_layer_height=first_layer_height)  # start end indexes
    closed_loops_with_data = []
    for cl_id in closed_loop_ids:
        print(f"Add a slope to perimeter {closed_loop_ids.index(cl_id)}")
        modified_loop = modify_loop_with_slope(gcodes[cl_id[0]: cl_id[1] + 1], slope_steps,
                                               layer_height=layer_height)
        closed_loops_with_data.append((cl_id, modified_loop))

    gcode_for_save = []
    last_id = -1
    print(f"Compiling the gcode file")
    for original_gcode_id in range(len(gcodes)):
        if original_gcode_id <= last_id:
            continue
        if len(closed_loops_with_data) > 0:
            closed_loop = closed_loops_with_data[0]
            closed_loop_id_range = closed_loop[0]
            closed_loop_id_data = closed_loop[1]
            closed_loop_start_id = closed_loop_id_range[0]
            closed_loop_end_id = closed_loop_id_range[1]
            if original_gcode_id != closed_loop_start_id:
                gcode_for_save.append(gcodes[original_gcode_id])
            else:
                gcode_for_save.extend(closed_loop_id_data)
                last_id = closed_loop_end_id
                closed_loops_with_data.remove(closed_loops_with_data[0])
        else:
            gcode_for_save.append(gcodes[original_gcode_id])

    destFilePath = file_path
    if save_to_file is not None:
        save_to_file
        destFilePath = re.sub(r'\.gcode$', '', file_path) + '_post_processed.gcode'

    delete_file_if_exists(destFilePath)
    with open(destFilePath, "w") as writefile:
        for gcode in gcode_for_save:
            writefile.write(str(gcode) + "\n")
    writefile.close()


if __name__ == '__main__':
    main()
