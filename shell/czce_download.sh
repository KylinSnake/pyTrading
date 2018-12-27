YEAR=2010

if [[ -z ${ARCHIVE_DIR} ]]; then
	echo "ERROR: no ardir set"
	exit 1
fi

FOLDER="/tmp/download_"`date '+%Y%m%d_%H%M%S'`
mkdir -p $FOLDER
echo "Tmp folders is ${FOLDER}"

TARGET=${ARCHIVE_DIR}/CZCE/
cd $FOLDER

LAST=`ls -tr ${TARGET}| grep zip | tail -1 | xargs basename`
if [ ! -z "$LAST" ] ; then
	YEAR=${LAST:0:4}
fi
CURRENT=`date '+%Y'`
LAST=${YEAR}
ERROR=0
MSG=""

while [[ $((CURRENT-LAST)) -ge 0 ]] ;
do
	if [[ $LAST -gt 2014 ]]; then
		wget -U "Opera" "http://www.czce.com.cn/cn/DFSStaticFiles/Future/${LAST}/FutureDataHistory.zip"
		ERROR=$?
		mv FutureDataHistory.zip ${LAST}.zip
	else
		wget -U "Opera" "http://www.czce.com.cn/cn/exchange/datahistory${LAST}.zip"
		ERROR=$?
		mv *.zip ${LAST}.zip
	fi
	if [[ $ERROR -ne 0 ]] ; then
		MSG="Failed to download ${LAST}"
		break
	fi
	unzip ${LAST}.zip
	if [[ $? -ne 0 ]]; then
		ERROR=1
		MSG="Failed to unzip ${LAST}.zip"
		break
	fi
	mv ${LAST}.zip $TARGET
	rm *

	LAST=$((LAST+1))
done
cd ../

rm -rf $FOLDER/*
LAST_DAY=""
MD_TARGET=${MD_DIR}/CZCE

LAST_FILE="${MD_TARGET}/.last"

if [ -f ${LAST_FILE} ]; then
	LAST_DAY=`cat $LAST_FILE`
else
	LAST_DAY='20100101'
fi

mkdir -p $FOLDER/tmp
cd $FOLDER/tmp/

YEAR=${LAST_DAY:0:4}
for i in `ls --color=none $ARCHIVE_DIR/CZCE/`
do
	C=${i:0:4}
	if [[ $((C-YEAR)) -gt 0 ]];then
		unzip $ARCHIVE_DIR/CZCE/$i -d ./
		mv *.txt ../${C}.txt
	fi
done

python3 << EOF
from os import listdir
from os.path import isfile, join
import datetime
import sys
from Tools.Mail import *

if $ERROR != 0:
	send_mail("$MSG", 'Process CZCE data Failed on %s'%str(datetime.date.today()))
	print("ERROR: $MSG")
	sys.exit(1)

last_day='$LAST_DAY'

output_files=dict()

def n(a):
	return float(a.strip().replace(",",""))

class Record:
	def _turnover(self, a):
		return a * 10000
	
	def multiply_with_lot(self, a):
		if self.code.startswith('WH'):
			return a * 20
		if self.code.startswith('PM'):
			return a * 50
		if self.code.startswith('CF'):
			return a * 5
		if self.code.startswith('SR'):
			return a * 10
		if self.code.startswith('OI'):
			return a * 10
		if self.code.startswith('RI'):
			return a * 20
		if self.code.startswith('RS'):
			return a * 10
		if self.code.startswith('RM'):
			return a * 10
		if self.code.startswith('JR'):
			return a * 20
		if self.code.startswith('LR'):
			return a * 20
		if self.code.startswith('CY'):
			return a * 5
		if self.code.startswith('AP'):
			return a * 10
		if self.code.startswith('TA'):
			return a * 5
		if self.code.startswith('MA'):
			return a * 10
		if self.code.startswith('FG'):
			return a * 20
		if self.code.startswith('ZC'):
			return a * 100
		if self.code.startswith('SF'):
			return a * 5
		if self.code.startswith('SM'):
			return a * 5
		return a
		
	def __init__(self, array):
		self.date = array[0].strip().replace("-","")
		self.code = array[1].strip()
		self.last_settle = n(array[2])
		self.open = n(array[3])
		self.high = n(array[4])
		self.low = n(array[5])
		self.close = n(array[6])
		self.settle = n(array[7])
		self.volume = self.multiply_with_lot(n(array[10]))
		self.outstanding = self.multiply_with_lot(n(array[11]))
		self.turnover = self._turnover(n(array[13]))
	
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

	lines = []
	with open(join(path, filename), 'rb') as f:
		content = f.read()
		lines = ''.join(chr(i) for i in content if i < 128).split('\n')

	for line in lines:
		array = line.split('|')
		if len(array) > 1 and array[0].strip().replace("-","").isdigit():
			record = Record(array)
			if record.date <= last_day:
				continue
			key = record.code[0:2].upper()
			if key in md_maps:
				value = md_maps[key]
				if record.date not in value:
					value[record.date] = list()
				value[record.date].append(record)


input_dir="$FOLDER"

content = dict()
for i in ["AP","CF","CY","FG","JR","LR","MA","OI","PM","RI","RM","RS","SF","SM","SR","TA","WH","ZC"]:
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
	print('Success on the CZCE data on %s'%str(datetime.date.today()))
except Exception as e:
	print("Error: %s"%str(e))
	send_mail(str(e), 'Process CZCE data Failed on %s'%str(datetime.date.today()))

EOF

rm -rf $FOLDER
