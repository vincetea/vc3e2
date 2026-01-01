import struct
import csv
import re
import os
import math

class OGMTP:
     def __init__(self): 
          self.mtp_header = b''
          self.info_header = b''
          self.unknown6 = b'' 
          self.pointer_segment = b''
          self.data_segment = b'' 
          self.end = b''
          
def unescape_hex(text):
    parts = re.split(r'(\\x[0-9A-Fa-f]{2})', text)
    result = bytearray()
    for part in parts:
        if part.startswith('\\x') and len(part) == 4:
            result.append(int(part[2:], 16))
        else:
            try:
                result.extend(part.encode('cp932'))
            except:
                result.extend(part.encode('cp932', errors= 'replace'))
    return bytes(result)


def read_uint32(file):
    return struct.unpack('<I', file.read(4))[0]

def read_uint8(file):
    return int.from_bytes(file.read(1), 'little')

def write_uint32(data, offset, value):
    data[offset:offset+4] = struct.pack('<I', value)

def process_file(mtp_path, csv_path, output_path):
    Copy = OGMTP()
    try:
        with open(csv_path, 'r', newline = '\n', encoding = 'utf-8', errors = 'replace') as csvfile: 
            content = csvfile.read()

        with open(csv_path, 'w', newline = '\n', encoding='cp932', errors='replace') as csvfile:
            csvfile.write(content)

        with open(mtp_path, "rb") as mtp:
            if mtp.read(4) != b'MTPA': 
                print("Wrong file format. Expected MTP file")
                return 
            
            mtp.seek(0x08); header_size = read_uint32(mtp)

            info_header_size = 16
            
            mtp.seek(0x00 + header_size); Copy.info_header = mtp.read(info_header_size)

            mtp.seek(0x00); Copy.mtp_header = mtp.read(header_size)
            mtp.seek(header_size); Copy.info_header = mtp.read(16)
            
            mtp.seek(header_size + 0x04); pointer_count = read_uint32(mtp)
            mtp.seek(header_size + 0x0C); data_count = read_uint32(mtp)
            mtp.seek(header_size + 0x08); data_size = read_uint32(mtp)
            unknown6_s_offset = info_header_size + header_size

            pointer_segment_s_offset = unknown6_s_offset + (16)

            #if data_size == 2:
            #    data_segment_s_offset = pointer_segment_s_offset + ((pointer_count - 2) * 4)
            #else: 
            #    data_segment_s_offset = pointer_segment_s_offset + (pointer_count * 4)

            #mtp.seek(header_size + 0x10); Copy.unknown6 = mtp.read(16)

            #if data_size == 2:
            #    mtp.seek(header_size + 0x20); Copy.pointer_segment = mtp.read((pointer_count - 2) * 4)
            #else: 
            #    mtp.seek(header_size + 0x20); Copy.pointer_segment = mtp.read(pointer_count * 4)

            mtp.seek(header_size + 0x10); Copy.unknown6 = mtp.read(16)

            if data_size == 2:
                data_segment_s_offset = pointer_segment_s_offset + ((pointer_count - 2) * 4)
                mtp.seek(header_size + 0x20); Copy.pointer_segment = mtp.read((pointer_count - 2) * 4)
                mtp.seek(data_segment_s_offset); Copy.data_segment = mtp.read(data_count * 8)
                txt_block_s_offset = data_segment_s_offset + (data_count * 8)
            else:
                data_segment_s_offset = pointer_segment_s_offset + (pointer_count * 4)
                mtp.seek(header_size + 0x20); Copy.pointer_segment = mtp.read(pointer_count * 4)
                mtp.seek(data_segment_s_offset); Copy.data_segment = mtp.read(data_count * 16)
                txt_block_s_offset = data_segment_s_offset + (data_count * 16)
            
            mtp.seek (0x00); test = read_uint8(mtp)

            mtp.seek(0,2)
            ogfilesize = mtp.tell()
            
            mtp.seek(txt_block_s_offset)
            enrs_s_offset = txt_block_s_offset
            
            while True:
                text_terminator = mtp.read(4)
                if text_terminator == b'ENRS' or len(text_terminator) < 4:
                    break
                enrs_s_offset += 1
                mtp.seek(enrs_s_offset)
            
            mtp.seek(enrs_s_offset)
            Copy.end = mtp.read(ogfilesize - enrs_s_offset)

            if header_size == 16:
                mtp.seek(0x04)
                mtp_pak_size = read_uint32(mtp)
            else: 
                mtp.seek(0x04)
                mtp_pak_size = read_uint32(mtp)
                mtp.seek(0x14)
                mtp_data_size = read_uint32(mtp)

    
    except FileNotFoundError:
        print("MTP file not found.")
        return 
        
    segments = []
    text_offsets = []
    with open(csv_path, newline='\n', encoding='cp932',  errors = 'replace') as csvfile:
        reader = csv.reader(csvfile)
        #Disable reading the first row or nah
        next(reader, None)
        for row in reader:
            if len(row) > 4:
                edited_text = row[2]
                segments_s_offsets = row[3] 
                text_positions_list_s_offset = row[4]
                text_pointers = [int(text_positions_list_s_offset,16)]
                segment_data = unescape_hex(edited_text) 
                segments.append((segment_data, text_pointers))
                text_offsets.append((segments_s_offsets))
                
    text_start_offset = int(text_offsets[0],16)

    
    print (text_offsets)
    print(text_start_offset) 
    #print(hex(test))
    #print(hex(data_size))
    #print(hex((header_size + 0x0D)))
    #print(hex(header_size))
    #print(hex(pointer_segment_s_offset))
    #print(hex(data_segment_s_offset))

    updated_list = []
    for segment_data, text_positions_list_s_offset, in segments:
        new_text_length = len(segment_data)
        lit_new_text_length = struct.pack('<I', new_text_length)
        updated_list.append ((segment_data, lit_new_text_length, text_positions_list_s_offset))

    with open(output_path, "wb") as out:
        out.write(Copy.mtp_header)
        out.write(Copy.info_header)
        out.write(Copy.unknown6)
        out.write(Copy.pointer_segment)
        out.write(Copy.data_segment)
        
        updated_positions = {}
        for segment_data, lit_new_text_length, text_positions_list_s_offset in updated_list:
            if b'!x00' in segment_data:
                out.write(bytes([1] * 4))
                new_position = out.tell() - text_start_offset
                for ptr in text_positions_list_s_offset: 
                    updated_positions[ptr] = new_position 
                out.write(bytes([1] * 4))
            else:
                plus_new_text_length = bytes(((b + 1) % 256) for b in lit_new_text_length )
                out.write(plus_new_text_length)
                new_position = out.tell() - text_start_offset
                #print(new_position)
                #if b'>Oh?' in segment_data:
                #    print("TEST")
                plus_segment_data = bytes(((b + 1) % 256) for b in segment_data )
                out.write(plus_segment_data)
                out.write(bytes([1]))
                text_end_offset = out.tell() - 1
                #print(text_end_offset)
                num_null = (4 - ((text_end_offset + 1) % 4)) % 4
                null_bytes = bytes([1] * num_null)
                out.write(null_bytes)
                for ptr in text_positions_list_s_offset: 
                    updated_positions[ptr] = new_position 
            
        print(updated_positions)

        out.write(Copy.end)
        #out.write(bytes([20]))

    with open(output_path, "r+b") as out:
        for ptr_offset, rel_offset in updated_positions.items():
            out.seek(ptr_offset)
            print(f"rel_offset: {rel_offset}")
            out.write(struct.pack('<I', rel_offset))
        out.seek(0, 2)
        newfilesize = out.tell() 
        diffsize = newfilesize - ogfilesize 
        print(diffsize)
        #Round the number up to the nearest multiple of 16
        new_mtp_pak_size = int((math.ceil((mtp_pak_size + diffsize)) / 16) * 16)
        out.seek(0x04)
        out.write(new_mtp_pak_size.to_bytes(4, 'little'))

        new_mtp_data_size = int((math.ceil((mtp_data_size + diffsize)) / 16) * 16)
        out.seek(0x14)
        out.write(new_mtp_data_size.to_bytes(4, 'little'))


    #TODO: Update text_positions and packet_size and header size

    with open(csv_path, 'r', newline = '\n', encoding = 'cp932', errors = 'replace') as csvfile: 
        stuff = csvfile.read()
    with open(csv_path, 'w', newline = '\n', encoding='utf-8', errors='replace') as csvfile:
        csvfile.write(stuff)



def main():
    input_mtp_dir = 'og_mtp'
    input_csv_dir = 'edited_mtp_csv'
    output_dir = 'edited_mtp'


    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_mtp_dir):
        if filename.lower().endswith('.mtp'):
            base = os.path.splitext(filename)[0]
            mtp_path = os.path.join(input_mtp_dir, filename)
            csv_path = os.path.join(input_csv_dir, base + '.csv')
            output_path = os.path.join(output_dir, filename)
            process_file(mtp_path, csv_path, output_path)

if __name__ == "__main__":
    main()