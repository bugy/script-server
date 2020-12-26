def decode(data, encoding):
    try:
        return data.decode(encoding)
    except UnicodeDecodeError as e:
        if encoding.lower() == 'utf-8':
            return _decode_utf8_with_mixes(data)

        raise e


def _decode_utf8_with_mixes(data):
    new_data = bytearray()
    skip_count = 0
    for index, char in enumerate(data):
        if skip_count > 0:
            skip_count -= 1
            continue

        if char < 127:
            new_data.append(char)
            continue

        next_bytes_count = 0
        valid = None
        if 192 <= char <= 223:
            next_bytes_count = 1
        elif 224 <= char <= 239:
            next_bytes_count = 2
        elif 240 <= char <= 247:
            next_bytes_count = 3

        if next_bytes_count:
            valid = True
            for offset in range(0, next_bytes_count):
                if not (128 <= data[index + offset + 1] <= 192):
                    valid = False
                    break

        if valid:
            selected_bytes = data[index:(index + next_bytes_count + 1)]
            new_data.extend(selected_bytes)
            skip_count = next_bytes_count
            continue

        converted_bytes = data[index:index + 1].decode('iso-8859-1').encode('utf-8')
        new_data.extend(converted_bytes)

    return new_data.decode('utf-8', errors='replace')
