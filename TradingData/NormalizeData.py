import sys
import datetime
import re

TODAY = datetime.datetime.today().strftime("%Y%m%d")


def run(file_name):
    output_file = file_name + ".%s.csv"%TODAY
    with open(output_file, 'w') as output_file:
        with open(file_name, 'r', encoding='UTF-8') as input_file:
            i = 0
            for line in input_file.readlines():
                line = re.sub('[\t ]+', ',', line)
                if i > 1:
                    words = line.split(',')
                    words[0] = words[0].replace('/', '-')
                    output_file.write("%s\n" % ','.join(words[0:7]))
                elif i == 1:
                    output_file.write("date,open,high,low,close,volume,turnover\n")
                i += 1


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("<usage> python NormalizeData.py <file1> <file2>")
        sys.exit(0)
    for i in sys.argv[1:]:
        run(i)