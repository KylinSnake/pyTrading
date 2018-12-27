if [[ -z ${ARCHIVE_DIR} ]]; then
	echo "ERROR: no ardir set"
	exit 1
fi

FOLDER="/tmp/download_"`date '+%Y%m%d_%H%M%S'`
mkdir -p $FOLDER
echo "Tmp folders is ${FOLDER}"

TARGET=${ARCHIVE_DIR}/DCE/
cd $FOLDER

wget -U "Opera" "http://www.dce.com.cn/dalianshangpin/xqsj/lssj/index.html"
ERROR=$?
if [[ $ERROR -ne 0 ]];then
	MSG="Failed to download the webpage http://www.dce.com.cn/dalianshangpin/xqsj/lssj/index.html"
else
	for i in `egrep "zip|csv" index.html | grep -v "期权" | sed "s/.*rel=\"\([^\"]*\)\".*/\1/g"`
	do
		FILE_NAME=`echo $i | sed "s/.*cms\///g" | tr -s "\/" "_"`
		if [[ -f ${TARGET}${FILE_NAME} ]]; then
			echo "$FILE_NAME exists."
		else
			wget "http://www.dce.com.cn${i}"
			if [[ $? -ne 0 ]]; then
				ERROR=1
				MSG="Faild to download $i"
				break
			fi
			mkdir -p tmp
			EXT=`echo $FILE_NAME | cut -d"." -f2`
			if [[ "$EXT" == "zip" ]]; then
				unzip *.zip -d tmp/
				if [[ $? -ne 0 ]]; then
					ERROR=1
					MSG="Faild to unzip $i"
					break
				fi
				mv *.zip $TARGET/$FILE_NAME
			else
				mv *.csv $TARGET/$FILE_NAME
			fi
			rm -rf tmp
		fi
	done
fi

cd ../

rm -rf $FOLDER/*
LAST_DAY=""
MD_TARGET=${MD_DIR}/DCE/history/

LAST_FILE="${MD_TARGET}/.last"

if [ -f ${LAST_FILE} ]; then
	LAST_DAY=`cat $LAST_FILE`
else
	LAST_DAY='20100101'
fi

mkdir -p $FOLDER/tmp
cd $FOLDER/tmp/

C=0
for i in `ls --color=none $ARCHIVE_DIR/DCE/*.zip`
do
	C=$((C+1))
	unzip $i -d ./
	mv *.csv ../${C}.csv
done
for i in `ls --color=none $ARCHIVE_DIR/DCE/*.csv`
do
	cp -p $i ../
done

python3 << EOF
from os import listdir
from os.path import isfile, join
import datetime
import sys
from Tools.Mail import *

if $ERROR != 0:
	send_mail("$MSG", 'Process DCE data Failed on %s'%str(datetime.date.today()))
	print("ERROR: $MSG")
	sys.exit(1)

last_day='$LAST_DAY'

output_files=dict()

lots_map = {"C":10,"CS":10,"A":10,"B":10,"M":10,"Y":10,"P":10,"FB":500,"BB":500,"JD":10,"L":5,"V":5,"PP":5,"J":100,"JM":60,"I":100,"EG":10}

def n(a):
	if type(a) == str:
		return float(a.strip().replace(",","")) if a.strip().isdigit() else 0.0
	return float(a)

class Record:
	
	def multiply_with_lot(self, a):
		key = self.code[0:2].upper()
		if key[1].isdigit():
			key = key[1]
		if key in lots_map:
			return a * lots_map[key]
		return a
		
	def __init__(self, array):
		self.date = array[2].strip() if type(array[2]) == str else str(array[2])
		self.code = array[1].strip()
		self.last_close = n(array[3])
		self.last_settle = n(array[4])
		self.open = n(array[5])
		self.high = n(array[6])
		self.low = n(array[7])
		self.close = n(array[8])
		self.settle = n(array[9])
		self.volume = self.multiply_with_lot(n(array[12]))
		self.outstanding = self.multiply_with_lot(n(array[14]))
		self.turnover = n(array[13]) # the number is already multiplied with 10000
	
	def to_csv(self, f):
		f.write('%s,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%s\n'%(self.date, self.open, self.high, self.low, self.close, self.volume, self.turnover, self.outstanding, self.code))

def get_file(id):
	if id not in output_files:
		existing = isfile("${MD_TARGET}/%s_md.csv"%id)
		output_files[id] = open("${MD_TARGET}/%s_md.csv"%id, 'a')
		if not existing:
			output_files[id].write('#date|open|high|low|close|volume|turnover|outstanding|contractName\n')
	return output_files[id]

def process(key, records):
	# we only keep the major contract, as there are more than 10 contract for each product, and expiry date are normally more than 1 year
	rec = max(records,key = lambda x: x.turnover)
	f = get_file(key)
	rec.to_csv(f)

def read_file(path, filename, md_maps: dict):
	date_str = filename[0:8]
	
	def __handle__(array):
		if type(array[0]) == str and not array[0].isdigit():
			return
		record = Record(array)
		if record.date <= last_day:
			return
		key = record.code[0:2].upper()
		if key[1].isdigit():
			key = key[0]
		if key in md_maps:
			value = md_maps[key]
			if record.date not in value:
				value[record.date] = list()
			value[record.date].append(record)
	
	import pandas as pd

	try:
		data_frame = pd.read_excel(join(path, filename))
		arrays = data_frame.values
		for i in range(0, arrays.shape[0]):
			__handle__(arrays[i])
	except Exception as e:
		lines = []
		with open(join(path, filename), 'rb') as f:
			content = f.read()
			lines = ''.join(chr(i) for i in content if i < 128).split('\n')

		for line in lines:
			array = line.replace("\r", "").replace('"','').split(',')
			__handle__(array)

input_dir="$FOLDER"

content = dict()
for i in lots_map.keys():
	content[i] = dict()

files = [f for f in listdir(input_dir) if isfile(join(input_dir, f))]
try:
	for f in sorted(files):
		print ('read file: %s'%f)
		read_file(input_dir, f, content)

	for key in content:
		values = content[key]
		print ('output file: %s'%key)
		for date in sorted(values.keys()):
			process(key, values[date])
			if date > last_day:
				last_day = date

	for f in output_files.values():
		f.close()

	with open("$LAST_FILE",'w') as f:
		f.write(last_day)
	print('Success on the DCE data on %s'%str(datetime.date.today()))
except Exception as e:
	print("Error: %s"%str(e))
	send_mail(str(e), 'Process DCE data Failed on %s'%str(datetime.date.today()))

EOF

rm -rf $FOLDER
