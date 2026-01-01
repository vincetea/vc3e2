import struct
import csv
import os



def read_uint32(file):
    return struct.unpack('<I', file.read(4))[0]


def read_uint8(file):
    return int.from_bytes(file.read(1), 'little')


def decrypt(mxe_path):
    try:
            with open(mxe_path, "r+b") as mxe:
                if mxe.read(4) != b'MXEN':
                    print("Wrong file format. Expected MXE file.")
                    return
                mxe.seek(0x08); old_mxenheader_Size = read_uint32(mxe)
                mxe.seek(0x08 + old_mxenheader_Size); old_mxecheader_Size = read_uint32(mxe)

                if old_mxecheader_Size == 0x20: 
                     mxe.seek(0x14 + old_mxenheader_Size); old_mxecdata_Size = read_uint32(mxe)
                
                mxe.seek(old_mxenheader_Size + 0x0E); flag_byte = mxe.read(1)
                flag_int = int.from_bytes(flag_byte, "little")

                if flag_int != 0x08: 
                    decry_s_offset = old_mxenheader_Size + old_mxecheader_Size
                    decry_end_offset = old_mxenheader_Size + old_mxecheader_Size + old_mxecdata_Size
                    mxe.seek(decry_s_offset)
                    encrypted_bytes = mxe.read(decry_end_offset - decry_s_offset)
                    decrypted_bytes = bytearray()
                    for i, byte in enumerate(encrypted_bytes):
                        if i == 0:
                            decrypted_bytes.append(byte)
                        else:
                            decrypted_bytes.append(byte ^ encrypted_bytes[i - 1])
                    
                    mxe.seek(decry_s_offset)
                    mxe.write(decrypted_bytes)
                    mxe.seek(old_mxenheader_Size + 0x0E)
                    mxe.write(bytes([0x08]))
                    mxe.seek(decry_s_offset)
                    mxe.write(bytes([0x01]))

    except FileNotFoundError:
            print("MXE file not found.")
            return
    

                
"""TODO: There are instances of other tables. Something2 and Something3 must be accounted for. Must search rel text offset in both of these records. Text starts
different location when something2 & 3 are present... Apply changes """
def getheader(mxe_path):   
    with open(mxe_path, "r+b") as mxe:
        mxe.seek(0x08); mxenheader_Size = read_uint32(mxe)
        mxe.seek(0x08 + mxenheader_Size); mxecheader_Size = read_uint32(mxe)
        
        if mxecheader_Size == 0x20: 
             mxe.seek(0x14 + mxenheader_Size); mxecdata_Size = read_uint32(mxe)
        mxe.seek(0x44 + mxenheader_Size + mxecheader_Size); num_tbl_entries = read_uint32(mxe)
    return mxenheader_Size, mxecheader_Size , mxecdata_Size, num_tbl_entries
        
def findtext(mxe_path, mxenheader_Size, mxecheader_Size , mxecdata_Size, num_tbl_entries):
    with open(mxe_path, "r+b") as mxe: 
        mxe.seek(mxenheader_Size + mxecheader_Size + 0x0c); something2_header_ptr = read_uint32(mxe)
        table_s_offset = mxenheader_Size + mxecheader_Size + 128
        table_size = num_tbl_entries * 16 
        table_end_offset = table_s_offset + table_size
        mxe.seek(table_end_offset - 4); last_entry_data_ptr = read_uint32(mxe)
        mxe.seek(table_end_offset - 8); last_entry_data_size = read_uint32(mxe)
    
        last_entry_data_s_offset = last_entry_data_ptr + mxenheader_Size
        end_something1_data = last_entry_data_s_offset + last_entry_data_size
        search_regions = []
        search_regions.append((table_s_offset, end_something1_data))
        if something2_header_ptr != 0:                  
            something2_header_ptr = mxenheader_Size + something2_header_ptr
            mxe.seek(something2_header_ptr + 0x04); something2_count = read_uint32(mxe)
            mxe.seek(something2_header_ptr + 0x08); something2_ptr = read_uint32(mxe)
            something2_ptr = something2_ptr + mxenheader_Size
            end_something2_data = something2_ptr + (something2_count * 64)

            mxe.seek(something2_header_ptr + 0x0C); something3_count = read_uint32(mxe)
            mxe.seek(something2_header_ptr + 0x10); something3_ptr = read_uint32(mxe)
            something3_ptr = something3_ptr + mxenheader_Size 
            something3_data_size = something3_count * 4
            txt_block_s_offset = something3_ptr + something3_data_size
            search_regions.append((something2_ptr, end_something2_data))
        else:
            txt_block_s_offset = last_entry_data_s_offset + last_entry_data_size
            
        mxe.seek(txt_block_s_offset)
        txt_s_offset = txt_block_s_offset
        while True:
            txt_find = mxe.read(1)
            if txt_find != b'\x00':
                break
            txt_s_offset += 1
            mxe.seek(txt_s_offset)
        txt_end = mxenheader_Size + mxecheader_Size + mxecdata_Size - 1
        txt_size = txt_end - txt_s_offset + 1
        return(txt_block_s_offset, txt_size, search_regions)

    

    #TODO: extract text and put 
def gettext(mxe_path, txt_s_offset, txt_size, search_regions, mxenheader_Size):
    with open(mxe_path, "rb") as mxe:
        mxe.seek(txt_s_offset)
        segments = mxe.read(txt_size)

    # --- Extract Shift-JIS strings and gather info ---
    strings = []
    idx = 0
    while idx < len(segments):
        # skip leading nulls (shouldn't be needed, but safe)
        while idx < len(segments) and segments[idx] == 0:
            idx += 1
        if idx >= len(segments):
            break
        start = idx
        # Find the end of the string (next null byte)
        while idx < len(segments) and segments[idx] != 0:
            idx += 1
        end = idx
        part = segments[start:end]
        if part:
            try:
                text = part.decode('cp932')
            except Exception:
                text = part.decode('cp932', errors='replace')
            # Count trailing nulls after the string
            trailing_nulls = 0
            while idx < len(segments) and segments[idx] == 0:
                trailing_nulls += 1
                idx += 1
            strings.append((text, trailing_nulls, txt_s_offset + start))
        # idx is already at the next non-null or end


    region_tables = []
    with open(mxe_path, "rb") as mxe:
        for start, end in search_regions: 
            mxe.seek(start)
            data = mxe.read(end - start)
            region_tables.append((start, data))
            print(f"Region start: {start}, size: {len(data)} bytes")


   

    ## Read the pointer table range
    #with open(mxe_path, "rb") as mxe:
    #    mxe.seek(table_s_offset)
    #    pointer_table = mxe.read(txt_s_offset - table_s_offset)

#TODO: add different region to serach for
    csv_rows = []
    for text, trailing_nulls, abs_offset in strings:
        rel_offset = abs_offset - mxenheader_Size
        #print(rel_offset)
        ptr_bytes = struct.pack('<I', rel_offset)
        locations = []
        for starting_offset, scan_size, in region_tables:  
            search_start = 0
            while True:
                found = scan_size.find(ptr_bytes, search_start)
                if found == -1:
                    break
                abs_location = starting_offset + found
                locations.append(f"0x{abs_location:X}")
                search_start = found + 1
        csv_rows.append([
            "",
            text,
            "",
            text,
            trailing_nulls,
            '|'.join(locations) if locations else '',
            hex(abs_offset)
        ])
    return(csv_rows)

    # Write to CSV
def writecsv(csv_path, csv_rows):
    with open(csv_path, 'w', newline='\n', encoding='utf-8', errors = 'replace') as out:
        writer = csv.writer(out)
        #Disable writing headers if needed below
        #writer.writerow(['work on', 'original', 'translated', 'edited', 'trailing zeros', 'pointers location', 'absolute location'])
        for row in csv_rows:
            writer.writerow(row)
    

def main():
    input_mxe_dir = 'og_mxe'
    output_csv_dir = 'mxe_csv'

    os.makedirs(output_csv_dir, exist_ok=True)

    for filename in os.listdir(input_mxe_dir):
        if filename.lower().endswith('.mxe'):
            base = os.path.splitext(filename)[0]
            mxe_path = os.path.join(input_mxe_dir, filename)
            csv_path = os.path.join(output_csv_dir, base + '.MXE' + '.csv')
            decrypt(mxe_path)
            mxenheader_Size, mxecheader_Size , mxecdata_Size, num_tbl_entries = getheader(mxe_path)
            txt_s_offset, txt_size, search_regions = findtext(mxe_path, mxenheader_Size, mxecheader_Size , mxecdata_Size, num_tbl_entries)
            csv_rows = gettext(mxe_path, txt_s_offset, txt_size, search_regions, mxenheader_Size)
            writecsv(csv_path, csv_rows)


if __name__ == "__main__":
    main()