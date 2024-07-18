import os
import random

import namesgenerator


def generate_friendly_name():
    return namesgenerator.get_random_name(sep='-')


def generate_random_data(size_mib):
    return os.urandom(size_mib * 1024 * 1024)


def create_files(n, min_size_mib, max_size_mib, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for _ in range(n):
        file_name = generate_friendly_name() + ".log"
        file_size = random.randint(min_size_mib, max_size_mib)
        file_data = generate_random_data(file_size)

        with open(os.path.join(output_dir, file_name), 'wb') as f:
            f.write(file_data)
        print(f"Created file: {file_name} with size: {file_size} MiB")


if __name__ == "__main__":
    n = 10  # Number of files to generate
    min_size_mib = 1  # Minimum size in MiB
    max_size_mib = 5  # Maximum size in MiB
    output_dir = "logs"  # Directory to save the files

    create_files(n, min_size_mib, max_size_mib, output_dir)
