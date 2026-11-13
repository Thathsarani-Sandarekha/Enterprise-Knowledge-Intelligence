"""Run `python -m app.worker` for continuous processing or `--once` for one job."""
import argparse
import logging
from time import sleep
from app.services.ingestion import claim_next_document, process_claimed_document


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true', help='Process at most one queued document and exit')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    print('Document worker active (Ctrl+C to stop)')
    try:
        while True:
            document_id = claim_next_document()
            if document_id:
                process_claimed_document(document_id)
            elif not args.once:
                sleep(2)
            if args.once:
                break
    except KeyboardInterrupt:
        print('Worker stopped')


if __name__ == '__main__':
    main()
