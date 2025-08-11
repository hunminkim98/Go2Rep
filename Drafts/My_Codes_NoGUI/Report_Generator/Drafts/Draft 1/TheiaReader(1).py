import os
import struct
import numpy as np


class Rotation(object):

    def __init__(self, name, nb_frames=1):
        self.name = name
        self.values = np.zeros([nb_frames, 4,4])

    def set_frame(self, frame_num, val):
        self.values[frame_num] = val

    def copy(self):
        r = Rotation(self.name, self.values.shape[0])
        r.trajectory = self.values.copy()
        return r

    def get_frame(self, frame_num):
        if frame_num < self.values.shape[0]:
            return self.values[frame_num, :, :].copy()


class TheiaReader(object):

    def __init__(self, file_name):
        self.header = dict()
        self.parameters_group = dict()
        self.filename = file_name
        self.rotations = dict()
        if os.path.exists(file_name):
            self.__handle = open(self.filename, 'rb')
            try:
                self.__read_header()
                self.__read_parameters()
                self.__read_data()
            except Exception as er:
                print(er)
            finally:
                self.__handle.close()

    def __read_header(self):
        self.__handle.seek(0)
        self.header['parameter_block'], magic = struct.unpack('BB', self.__handle.read(2))
        if magic != 80:
            print('This not a c3d file!')
            return
        self.__handle.seek((self.header['parameter_block'] - 1) * 512 + 3)
        processor = struct.unpack('B', self.__handle.read(1))[0]#should be 84 (INTEL)
        if processor != 84:
            print('Decoder for processor %d not implemented' %processor)
            return
        self.__handle.seek(2)
        self.header['point_count'] = self.__get_uint16()
        self.header['analog_count'] = self.__get_uint16()
        self.header['first_frame'] = self.__get_uint16()
        self.header['last_frame'] = self.__get_uint16()
        self.header['max_gap'] = self.__get_uint16()
        self.header['scale_factor'] = self.__get_float()
        self.header['data_block'] = self.__get_uint16()
        self.header['analog_per_frame'] = self.__get_uint16()
        if self.header['analog_per_frame'] > 0 and self.header['analog_count'] > 0:
            self.header['analog_count'] /= self.header['analog_per_frame']
            self.header['analog_count'] = int(self.header['analog_count'])
        if self.header['analog_per_frame'] == 0:
            self.header['analog_per_frame'] = 1
        self.header['frame_rate'] = self.__get_float()

    def __read_parameters(self):
        self.__handle.seek((self.header['parameter_block'] - 1) * 512)
        self.__handle.read(2)
        block_num = self.__get_uint8()
        self.__handle.read(1)
        nb_byte_read = 4
        while True:
            nb_char_label = self.__get_int8()
            nb_byte_read += abs(nb_char_label) + 1
            if nb_char_label == 0:
                break
            group_id = self.__get_int8()
            nb_byte_read += 1
            name = self.__get_string(abs(nb_char_label))
            lastEntry = False
            offset = self.__get_uint16()
            nb_byte_read += offset
            if offset == 0:
                lastEntry = True
            offset -= 2

            if group_id < 0:
                desc_len = self.__get_uint8()
                offset -= 1
                desc = self.__get_string(desc_len)
                offset -= desc_len
                g = {'name': name.strip(), 'description': desc, 'parameters': dict()}
                # print(name.strip())
                self.parameters_group[abs(group_id)] = g
            else:
                # print('----%s : %d' %(name.strip(), group_id))
                g = self.parameters_group[group_id]
                if name.strip() in g:
                    print('error reading file')
                    return

                data_type = self.__get_int8()
                offset -= 1
                n_dim = self.__get_int8()
                offset -= 1
                dims = []
                for i in range(n_dim):
                    dims.append(self.__get_uint8())
                    offset -= 1
                prod = 1
                inc = 0
                while inc < n_dim:
                    prod *= dims[inc]
                    inc += 1
                data_size = prod * abs(data_type)
                if data_type == -1:
                    if len(dims) >= 2:
                        row = 1
                        inc2 = 1
                        while inc2 < n_dim:
                            row *= dims[inc2]
                            inc2 += 1
                        data = []
                        for i in range(row):
                            data.append(self.__get_string(dims[0]).strip())
                    else:
                        data = self.__get_string(prod)
                elif data_type == 1:
                    data = []
                    for i in range(prod):
                        data.append(self.__get_int8())
                elif data_type == 2:
                    data = []
                    for i in range(prod):
                        data.append(self.__get_uint16())
                elif data_type == 4:
                    data = []
                    for i in range(prod):
                        data.append(self.__get_float())
                offset -= data_size
                g['parameters'][name.strip()] = {'value': data}
                if offset != 0:
                    desc_len = self.__get_uint8()
                    desc = self.__get_string(desc_len)
                    g['parameters'][name.strip()]['description'] = desc
                    offset -= desc_len
                if lastEntry:
                    offset = 0
                    break

    def __read_data(self):
        data_start = self.get_parameter('ROTATION', 'DATA_START')
        self.__handle.seek((512 * (data_start - 1)))
        is_float = self.header['scale_factor'] < 0
        nb_rot = self.get_parameter('ROTATION', 'USED')
        labels = self.get_parameter('ROTATION', 'LABELS')
        if len(labels) != nb_rot:
            labels = labels[:nb_rot]
        nb_frames = self.header['last_frame'] - self.header['first_frame'] + 1
        for i in range(nb_frames):
            for j in range(nb_rot):
                if is_float:
                    p = np.array([[self.__get_float(), self.__get_float(), self.__get_float(), self.__get_float()],
                                  [self.__get_float(), self.__get_float(), self.__get_float(), self.__get_float()],
                                  [self.__get_float(), self.__get_float(), self.__get_float(), self.__get_float()],
                                  [self.__get_float(), self.__get_float(), self.__get_float(), self.__get_float()]]).transpose()
                else:
                    p = np.array([[self.__get_uint16(), self.__get_uint16(), self.__get_uint16(), self.__get_uint16()],
                                  [self.__get_uint16(), self.__get_uint16(), self.__get_uint16(), self.__get_uint16()],
                                  [self.__get_uint16(), self.__get_uint16(), self.__get_uint16(), self.__get_uint16()],
                                  [self.__get_uint16(), self.__get_uint16(), self.__get_uint16(), self.__get_uint16()]])
                if labels[j] not in self.rotations:
                    self.rotations[labels[j]] = Rotation(labels[j], nb_frames)
                self.rotations[labels[j]].set_frame(i, p)
                self.__handle.read(4)

    def __get_int8(self):
        return struct.unpack('b', self.__handle.read(1))[0]

    def __get_uint8(self):
        return struct.unpack('B', self.__handle.read(1))[0]

    def __get_int16(self):
        return struct.unpack('h', self.__handle.read(2))[0]

    def __get_uint16(self):
        return struct.unpack('H', self.__handle.read(2))[0]

    def __get_int32(self):
        return struct.unpack('i', self.__handle.read(4))[0]

    def __get_uint32(self):
        return struct.unpack('I', self.__handle.read(4))[0]

    def __get_float(self):
        return struct.unpack('f', self.__handle.read(4))[0]

    def __get_string(self, numChar):
        return self.__handle.read(numChar).decode('utf-8')

    def get_group(self, group_name):
        g = {}
        for k, v in self.parameters_group.items():
            if v['name'] == group_name:
                g = v
                break
        return g

    def get_parameter(self, group, param, only_value=True):
        g = self.get_group(group)
        if len(g) > 0:
            fields = g['parameters'].keys()
            if param in fields:
                if only_value:
                    if len(g['parameters'][param]['value']) == 1:
                        return g['parameters'][param]['value'][0]
                    else:
                        return g['parameters'][param]['value']
                else:
                    return g['parameters'][param]
            else:
                return {}
        else:
            return {}
