import asyncio
import logging

ENCODINGS = ['utf-8', 'latin-1', 'Windows-1251', 'ascii', 'koi8-r']


async def check_port_protocol(target_host: str, port: int) -> str:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(target_host, port),
            timeout=1  # Reduced timeout for faster checks
        )
        try:
            protocol_info = await asyncio.wait_for(reader.read(1024), timeout=0.5)
            for encoding in ENCODINGS:
                try:
                    return protocol_info.decode(encoding).strip()[:100]  # Limit response size
                except UnicodeDecodeError:
                    continue
            return "Error decoding with known encodings"
        finally:
            writer.close()
            await writer.wait_closed()
    except asyncio.TimeoutError:
        # return "Connection timed out"
        return "Banner is missing"
    except ConnectionRefusedError:
        return "Connection refused"
    except Exception as e:
        return f"Error: {str(e)[:100]}"  # Limit error message size


def run_check_banner(host: str, port: int):
    result =asyncio.run(check_port_protocol(host, port))
    logging.info(f"Server_Banner: {result}")
    # return result


# if __name__ == "__main__":
#     # run_check_banner('th1.vpnjantit.com', 22)
#     host = 'th1.vpnjantit.com'
#     port = 22
#     logging.info(f"Server_Banner: {run_check_banner(host, port)}")
