import argparse
from uhd_fft_remote import UhdFftRemote

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_ROOM_ID = "test"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='UHD FFT Remote Client')
    parser.add_argument("-b", "--base-url", type=str, default=DEFAULT_BASE_URL,
                        help="Server Base URL")
    parser.add_argument("-r", "--room-id", type=str, default=DEFAULT_ROOM_ID,
                        help="Room ID")
    args = parser.parse_args()

    app = None
    try:
        app = UhdFftRemote(args.base_url,
                           args.room_id)
        app.measurement_worker()
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        if app:
            app.running = False
