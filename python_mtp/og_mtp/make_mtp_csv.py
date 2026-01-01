import struct
import csv
import os

def write_uint32(data, offset, value):
    data[offset:offset+4] = struct.pack('<I', value)

def read_uint32(file):
    return struct.unpack('<I', file.read(4))[0]

def read_uint8(file):
    return int.from_bytes(file.read(1), 'little')

def process_file(mtp_path, csv_path):
    try:
        with open(mtp_path, "rb") as mtp:
            if mtp.read(4) != b'MTPA': 
                print("Wrong file format. Expected MTP file")
                return 
            
            mtp.seek(0x08); header_size = read_uint32(mtp)
            
            info_header_size = 16
            
            mtp.seek(header_size + 0x04); pointer_count = read_uint32(mtp)
            mtp.seek(header_size + 0x0C); data_count = read_uint32(mtp)
            mtp.seek(header_size + 0x08); data_size = read_uint32(mtp)
            unknown6_s_offset = info_header_size + header_size

            pointer_segment_s_offset = unknown6_s_offset + (16)
            
            if data_size == 2:
                data_segment_s_offset = pointer_segment_s_offset + ((pointer_count - 2) * 4)
                txt_block_s_offset = data_segment_s_offset + (data_count * 8)
            else:
                data_segment_s_offset = pointer_segment_s_offset + (pointer_count * 4)
                txt_block_s_offset = data_segment_s_offset + (data_count * 16)

            
            mtp.seek (0x00); test = read_uint8(mtp)

        
            mtp.seek(txt_block_s_offset)
            enrs_s_offset = txt_block_s_offset
            
            while True:
                text_terminator = mtp.read(4)
                if text_terminator == b'ENRS' or len(text_terminator) < 4:
                    break
                enrs_s_offset += 1
                mtp.seek(enrs_s_offset)
            
            txt_size = enrs_s_offset - txt_block_s_offset

            print(hex(test))
            print(hex(unknown6_s_offset))
            print(hex(pointer_segment_s_offset))
            print(hex(data_segment_s_offset))
            print(hex(txt_block_s_offset))
            print(hex(enrs_s_offset))
            print(f"Text size is: {hex(txt_size)}")     

    except FileNotFoundError:
        print("MTP file not found.")
        return 
    


    with open(mtp_path, "rb") as mtp:
        mtp.seek(txt_block_s_offset)
        segments = mtp.read(txt_size)

    
    text_pos_list = []
  
    
    if data_size == 2:
        epic = txt_block_s_offset - 8
        i = data_segment_s_offset + 4
    else:
        epic = txt_block_s_offset - 16
        i = data_segment_s_offset + 8
    
    text_pos_list.append(hex(i))

    
    with open(mtp_path, "rb") as mtp:
        while i <= epic:
            if data_size == 2: 
                i += 8
                mtp.seek(i)
                text_pos_list.append((hex(i)))
                
            else:
                i += 16
                mtp.seek(i)
                text_pos_list.append((hex(i)))
                
    print (text_pos_list)
    print(f"Length of segment is {len(segments)}")

    #TODO:change the code below to get text properly. No skipping 01s

    strings = []
    idx = 0

    current_offset = txt_block_s_offset
    
    if (current_offset % 16) in (0x00, 0x04, 0x08, 0x0C): 
        is_text = False
        is_padding = False
    else: 
        is_text = False 
        is_padding = True

    
    while idx < len(segments):
        # Skip text length 4 bytes
        while not is_text and not is_padding and idx < len(segments):
            idx += 4
            current_offset += 4
            is_text = True

        while not is_text and is_padding and idx < len(segments):
            idx += 1
            current_offset += 1
            if current_offset % 16 in (0x00, 0x04, 0x08, 0x0C): 
                is_padding = False

        if idx >= len(segments):
            break

        start = idx

        
        if is_text and idx < len(segments):
            if segments[idx] != 0x01:
                while idx < len(segments) and segments[idx] != 0x01:
                    idx += 1
                    current_offset += 1

                if idx >= len(segments):
                    break  

                if segments[idx] == 0x01:
                    is_padding = True
                    is_text = False

            elif segments[idx] == 0x01:
                idx += 4
                current_offset += 4
                is_padding = False
                is_text = False

        if idx < len(segments) and segments[idx] == 0x00 and is_text:
            break

        end = idx
        part = segments[start:end]

        if part:
            modified = bytes((b - 1) for b in part)
            try:
                text = modified.decode('cp932')
            except Exception:
                text = modified.decode('cp932', errors='replace')
            strings.append((text, "", text, hex(txt_block_s_offset + start)))

    #print(part)
    #print(strings)


    
 
    #print(txt_starting_offset)

    #for text, _, abs_offset in text_only:
    #    rel_offset = abs_offset - txt_starting_offset
    #    updated_offset.append((text, text, hex(rel_offset)))


    #print(updated_offset)


    merged = []
    for i in range(len(strings)):
        if i < len(text_pos_list):
            merged.append(strings[i] + (text_pos_list[i],))

    
    print(merged)

    #print(len(text_pos_list))

    #print(len(strings))

    #with open(csv_path, 'w', newline='', encoding='utf-8') as out:
    #    writer = csv.writer(out)
    #    for t in merged:
    #         writer.writerow(t)

    
    with open(csv_path, 'w', newline='\n', encoding='utf-8') as out:
        writer = csv.writer(out)
        #Disable writing headers if needed below
        #writer.writerow(['jp', 'eng', 'final', 'text location', 'pointers location'])
        for t in merged:
            cleaned_row = []
            for v in t:
                cleaned_row.append(str(v).replace('\x00', '!x00'))
            writer.writerow(cleaned_row)
        

def main():
    input_mtp_dir = 'og_mtp'
    output_csv_dir = 'mtp_csv'

    os.makedirs(output_csv_dir, exist_ok=True)

    for filename in os.listdir(input_mtp_dir):
        if filename.lower().endswith('.mtp'):
            base = os.path.splitext(filename)[0]
            mtp_path = os.path.join(input_mtp_dir, filename)
            csv_path = os.path.join(output_csv_dir, base + '.MTP' + '.csv')
            process_file(mtp_path, csv_path)






if __name__ == "__main__":
    main()