import struct
import csv
import re
import os
import math

class OGMXE:
    def __init__(self):
        self.mxen_header = b''
        self.mxec_header = b''
        self.somethings_info = b''
        self.somethings = b''
        self.end = b''

Copy = OGMXE()

def read_uint32(file):
    return struct.unpack('<I', file.read(4))[0]

def write_uint32(data, offset, value):
    data[offset:offset+4] = struct.pack('<I', value)

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

def convert_sjis(csv_path):
    try:
        with open(csv_path, 'r', newline= '\n', encoding='utf-8', errors='replace') as csvfile:
            content = csvfile.read()

        with open(csv_path, 'w', newline= '\n', encoding='cp932', errors='replace') as csvfile:
            csvfile.write(content)
    
    except UnicodeEncodeError:
        print("Something went wrong during the conversion to Shift JIS...")
        return
    
def copy_header(mxe_path):
    try:
        with open(mxe_path, "rb") as mxe:
            if mxe.read(4) != b'MXEN':
                print("Wrong file format. Expected MXE file.")
                return

            mxe.seek(0x08)
            mxenheader_Size = read_uint32(mxe)
            
            mxe.seek(0x00)
            Copy.mxen_header = mxe.read(mxenheader_Size)

            mxe.seek(0x08 + mxenheader_Size)
            mxecheader_Size = read_uint32(mxe)
            
            mxe.seek(mxenheader_Size)
            Copy.mxec_header = mxe.read(mxecheader_Size)
    except FileNotFoundError:
        print("MXE file not found.")
        return
    return mxenheader_Size, mxecheader_Size
    
def copy_somethings_info(mxe_path, mxenheader_Size, mxecheader_Size): 
    with open(mxe_path, "rb") as mxe:
        mxe.seek(mxenheader_Size + mxecheader_Size)
        somethings_info_Size = 0x80
        Copy.somethings_info = mxe.read(somethings_info_Size)
        s_offset_somethings_info = mxenheader_Size + mxecheader_Size
    return s_offset_somethings_info, somethings_info_Size

def findtext(mxe_path, s_offset_somethings_info, mxenheader_Size, mxecheader_Size, somethings_info_Size):
    with open(mxe_path, "rb") as mxe:
        mxe.seek(s_offset_somethings_info + 0x44)
        something1_count = read_uint32(mxe)
        
        mxe.seek(mxenheader_Size + mxecheader_Size + 0x0c)
        something2_header_ptr = read_uint32(mxe)

        something1_s_offset = mxenheader_Size + mxecheader_Size + somethings_info_Size

        something1_entry_Size = 0x10
        something1_size = something1_count * something1_entry_Size

        something1_end_offset = something1_s_offset + something1_size
        mxe.seek(something1_end_offset - 0x04); last_entry_data_ptr = read_uint32(mxe)
        mxe.seek(something1_end_offset - 0x08); last_entry_data_size = read_uint32(mxe)
        last_entry_data_s_offset = last_entry_data_ptr + mxenheader_Size

        if something2_header_ptr != 0:                  
            something2_header_ptr = mxenheader_Size + something2_header_ptr
            mxe.seek(something2_header_ptr + 0x04); something2_count = read_uint32(mxe)
            mxe.seek(something2_header_ptr + 0x08); something2_ptr = read_uint32(mxe)
            something2_ptr = something2_ptr + mxenheader_Size

            mxe.seek(something2_header_ptr + 0x0C); something3_count = read_uint32(mxe)
            mxe.seek(something2_header_ptr + 0x10); something3_ptr = read_uint32(mxe)
            something3_ptr = something3_ptr + mxenheader_Size
            something3_entry_Size = 0x04
            something3_data_size = something3_count * something3_entry_Size
            txt_block_s_offset = something3_ptr + something3_data_size
        
        else:
            txt_block_s_offset = last_entry_data_s_offset + last_entry_data_size

    return txt_block_s_offset, something1_s_offset

def skip_padding(mxe_path, txt_block_s_offset, something1_s_offset):
    with open(mxe_path, "rb") as mxe:
        mxe.seek(txt_block_s_offset)
        s_txt_offset = txt_block_s_offset
        while True:
            text_find = mxe.read(1)
            if text_find != b'\x00':
                break
            s_txt_offset += 1
            mxe.seek(s_txt_offset)
    return s_txt_offset

def copy_somethings(mxe_path, something1_s_offset, s_txt_offset):
    with open(mxe_path, "rb") as mxe:
            mxe.seek(something1_s_offset)
            Copy.somethings = mxe.read(s_txt_offset - something1_s_offset)

def get_ogfilesize(mxe_path): 
    with open(mxe_path, "rb") as mxe: 
        mxe.seek(0, 2)
        ogfilesize = mxe.tell()
    return ogfilesize

def findtext_end(mxe_path, txt_block_s_offset):
    with open(mxe_path, "rb") as mxe: 
        mxe.seek(txt_block_s_offset)
        p_offset = txt_block_s_offset
        while True:
            text_terminator = mxe.read(4)
            if text_terminator == b'POF0' or len(text_terminator) < 4:
                break
            p_offset += 1
            mxe.seek(p_offset)
    return p_offset

def copy_end(mxe_path, p_offset, ogfilesize): 
    with open(mxe_path, "rb") as mxe:
            mxe.seek(p_offset)
            Copy.end = mxe.read(ogfilesize - p_offset)

def get_datapack_size(mxe_path): 
    with open(mxe_path, "rb") as mxe: 
        mxe.seek(0x04)
        mxeNP_size = read_uint32(mxe)
        mxe.seek(0x24)
        mxeCP_size = read_uint32(mxe)
        mxe.seek(0x34)
        mxeCD_size = read_uint32(mxe)
    return mxeNP_size, mxeCP_size, mxeCD_size


def get_edited_text(csv_path, s_txt_offset, txt_block_s_offset):    
    segments = []
    with open(csv_path, newline='', encoding='cp932', errors = 'replace') as csvfile:
        reader = csv.reader(csvfile)
        #Disable reading the first row or nah
        next(reader, None)
        for row in reader:
            if len(row) > 4:
                text = row[4]

                raw_pointers = row[3].split('|')
                pointers = [int(p, 16) for p in raw_pointers]
            
                num_nulls = int(row[2]) - 1
                trailing_bytes = bytes([0x00] * num_nulls)

                segment_data = unescape_hex(text) + b'\x00' + trailing_bytes

                segments.append((segment_data, pointers))
                print(segments)
                total_text_bytes = sum(len(segment) for segment, _ in segments) + (s_txt_offset - txt_block_s_offset)
                print ("ass")
                print(f"{total_text_bytes}\n")
    return segments

def writetofile(output_path, segments, mxenheader_Size): 
    with open(output_path, "wb") as out:
        out.write(Copy.mxen_header)
        out.write(Copy.mxec_header)
        out.write(Copy.somethings_info)
        out.write(Copy.somethings)
        
        newtext_offsets = {}
        for segment, pointer_list in segments:
            current_offset = out.tell()
            out.write(segment)
            rel_offset = current_offset - (mxenheader_Size)
            for ptr in pointer_list:
                newtext_offsets[ptr] = rel_offset

        print(newtext_offsets)
        text_end_offset = out.tell() - 1
        
        num_null = (16 - ((text_end_offset + 1) % 16)) % 16 # Aligns by 16 bytes
        null_bytes = bytes([0] * num_null)
        extra_bytes = bytes([0] * 16) # Add 16 bytes for minor additions to text
       
        out.write(null_bytes)
        out.write(extra_bytes)
        out.write(Copy.end)
    return newtext_offsets
    
def update_sizes_ptrs(output_path, ogfilesize, newtext_offsets, mxeNP_size, mxeCP_size, mxeCD_size):
    with open(output_path, "r+b") as out:
        for ptr_offset, rel_offset in newtext_offsets.items():
            out.seek(ptr_offset)
            out.write(struct.pack('<I', rel_offset))
        out.seek(0,2)
        newfilesize = out.tell()
        diffsize = newfilesize - ogfilesize

        #Round up to 16
        new_mexNP_size = int((math.ceil((mxeNP_size + diffsize)) / 16) * 16)
        new_mexCP_size = int((math.ceil((mxeCP_size + diffsize)) / 16) * 16)
        new_mexCD_size = int((math.ceil((mxeCD_size + diffsize)) / 16) * 16)
        
        out.seek(0x04)
        out.write(new_mexNP_size.to_bytes(4, 'little'))

        out.seek(0x24)
        out.write(new_mexCP_size.to_bytes(4, 'little'))

        out.seek(0x34)
        out.write(new_mexCD_size.to_bytes(4, 'little'))

    print(hex(mxeNP_size))
    print("Files created. Sizes & pointers updated!")

def convertutf8(csv_path): 
    with open(csv_path, 'r', newline = '\n', encoding = 'cp932', errors = 'replace') as csvfile: 
        stuff = csvfile.read()
    with open(csv_path, 'w', newline = '\n', encoding='utf-8', errors='replace') as csvfile:
        csvfile.write(stuff)

def main():
    input_mxe_dir = 'og_mxe'
    input_csv_dir = 'edited_mxe_csv'
    output_dir = 'edited_mxe'

    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_mxe_dir):
        if filename.lower().endswith('.mxe'):
            base = os.path.splitext(filename)[0]
            mxe_path = os.path.join(input_mxe_dir, filename)
            csv_path = os.path.join(input_csv_dir, base + '.csv')
            output_path = os.path.join(output_dir, filename)

            if os.path.exists(csv_path):
               mxenheader_Size, mxecheader_Size = copy_header(mxe_path)
               s_offset_somethings_info, somethings_info_Size = copy_somethings_info(mxe_path, mxenheader_Size, mxecheader_Size)
               txt_block_s_offset, something1_s_offset = findtext(mxe_path, s_offset_somethings_info, mxenheader_Size, mxecheader_Size, somethings_info_Size)
               s_txt_offset = skip_padding(mxe_path, txt_block_s_offset, something1_s_offset)
               copy_somethings(mxe_path, something1_s_offset, s_txt_offset)
               ogfilesize = get_ogfilesize(mxe_path)
               p_offset = findtext_end(mxe_path, txt_block_s_offset)
               copy_end(mxe_path, p_offset, ogfilesize)
               mxeNP_size, mxeCP_size, mxeCD_size = get_datapack_size(mxe_path)
               segments = get_edited_text(csv_path, s_txt_offset, txt_block_s_offset)
               newtext_offsets = writetofile(output_path, segments, mxenheader_Size)
               update_sizes_ptrs(output_path, ogfilesize, newtext_offsets, mxeNP_size, mxeCP_size, mxeCD_size)
               convertutf8(csv_path)

            else:
                print(f"CSV not found for: {filename}")

if __name__ == "__main__":
    main()
