""" kicks off the cusum watcher process """


from loguru import logger

from watcher.cusum import CUSUM


@logger.catch
def main():

    watcher = CUSUM(
        interval=10,
    )

    watcher.run()


if __name__ == "__main__":
    main()
