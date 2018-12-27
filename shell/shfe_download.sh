YEAR=2008

if [[ -z ${ARCHIVE_DIR} ]]; then
	echo "ERROR: no ardir set"
	exit 1
fi

FOLDER="/tmp/download_"`date '+%Y%m%d_%H%M%S'`
mkdir -p $FOLDER
echo "Tmp folders is ${FOLDER}"

TARGET=${ARCHIVE_DIR}/SHFE/
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
	wget "http://www.shfe.com.cn/historyData/MarketData_Year_${LAST}.zip" 
	if [[ $? -ne 0 ]] ; then
		ERROR=1
		MSG="Failed to download ${LAST}"
		break
	fi
	mkdir tmp
	unzip MarketData_Year_${LAST}.zip -d tmp/
	if [[ $? -ne 0 ]]; then
		ERROR=1
		MSG="Failed to unzip ${LAST}.zip"
		break
	fi
	rm -rf tmp
	mv MarketData_Year_${LAST}.zip $TARGET/${LAST}.zip

	LAST=$((LAST + 1))

done
cd ../


LAST_DAY=""
MD_TARGET=${MD_DIR}/SHFE/history

rm -rf $FOLDER/*


LAST_FILE="${MD_TARGET}/.last"

if [ -f ${LAST_FILE} ]; then
	LAST_DAY=`cat $LAST_FILE`
else
	LAST_DAY='20080101'
fi

YEAR=${LAST_DAY:0:4}
mkdir -p $FOLDER/xls

for i in `ls --color=none $ARCHIVE_DIR/SHFE/`
do
	Y=${i:0:4}
	if [[ $((Y-YEAR)) -ge 0 ]]; then
		unzip $ARCHIVE_DIR/SHFE/$i -d $FOLDER/xls/
		mv $FOLDER/xls/*.xls $FOLDER/${Y}.xls
	fi
done

rm -rf $FOLDER/xls

python3 << EOF
from os import listdir
from os.path import isfile, join
import pandas as pd
import numpy as np
import datetime
import sys
from Tools.Mail import *

if $ERROR != 0:
	send_mail("$MSG", 'Process SHFE history data Failed on %s'%str(datetime.date.today()))
	print("ERROR: $MSG")
	sys.exit(1)

last_day='$LAST_DAY'

def n(a):
	return 0 if np.isnan(a) else a

class Record:
	def _turnover(self, a):
		return a * 10000
	
	def multiply_with_lot(self, a):
		if self.code.startswith('au'):
			return a * 1000
		if self.code.startswith('ag'):
			return a * 15
		if self.code.startswith('cu'):
			return a * 5
		if self.code.startswith('al'):
			return a * 5
		if self.code.startswith('zn'):
			return a * 5
		if self.code.startswith('ru'):
			return a * 10 if self.code >= 'ru1208' else a * 5
		if self.code.startswith('fu'):
			return a * 50 if self.code >= 'fu1202' else a * 10
		if self.code.startswith('bu'):
			return a * 10
		if self.code.startswith('rb'):
			return a * 10
		if self.code.startswith('wr'):
			return a * 10
		if self.code.startswith('hc'):
			return a * 10
		if self.code.startswith('pb'):
			return a * 5 if self.date >= '20130902' else a * 25
		code = self.code[0:2].upper()
		lots_map = {'AU':1000, 'AG':15, 'CU':5, 'AL':5, 'ZN':5, 'RU':10, 'FU':50, 'BU':10, 'RB':10, 'WR':10, 'HC':10, 'PB':5, 'SP':10, 'NI':1, 'SN':1, 'SC':1000}
		if code in lots_map:
			return lots_map[code]
		raise Exception('No lots found')
		
	def __init__(self, contract_code, array):
		self.code = contract_code
		self.date = array[1].strip()
		self.last_close = n(array[2])
		self.last_settle = n(array[3])
		self.open = n(array[4])
		self.high = n(array[5])
		self.low = n(array[6])
		self.close = n(array[7])
		self.settle = n(array[8])
		self.volume = self.multiply_with_lot(n(array[11]))
		self.turnover = self._turnover(n(array[12]))
		self.outstanding = self.multiply_with_lot(n(array[13]))
	
	def to_csv(self, f):
		f.write('%s,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%s\n'%(self.date, self.open, self.high, self.low, self.close, self.volume, self.turnover, self.outstanding, self.code))

output_files=dict()

def get_file(id):
	if id not in output_files:
		existing = isfile("${MD_TARGET}/%s_md.csv"%id)
		output_files[id] = open("${MD_TARGET}/%s_md.csv"%id, 'a')
		if not existing:
			output_files[id].write('#date|open|high|low|close|volume|turnover|outstanding|contractNo\n')
	return output_files[id]

def process(key, records):
	# we only keep the major contract, as there are more than 10 contract for each product, and expiry date are normally more than 1 year
	rec = max(records,key = lambda x: x.turnover)
	f = get_file(key)
	rec.to_csv(f)


def read_file(path, filename, ret: dict):
	content=pd.read_excel(join(path, filename)).values[2:-4]
	cur_contract = None
	for i in range(0, content.shape[0]):
		date = content[i][1]
		if type(date) == float and type(content[i][0]) == float:
			break
		if type(content[i][1]) != str or not content[i][1].isdigit() or len(content[i][1].strip()) != 8:
			continue
		if type(content[i][0]) == str:
			cur_contract = content[i][0].strip()
		if len(cur_contract) > 6: #ignore option
			continue
		r = Record(cur_contract, content[i])
		if r.date <= last_day:
			continue
		key = r.code[0:2].upper()
		if key not in ret:
			ret[key]=dict()
		value = ret[key]
		if r.date not in value:
			value[r.date] = list()
		value[r.date].append(r)

input_dir="$FOLDER"
files = [f for f in listdir(input_dir) if isfile(join(input_dir, f))]

try:
	content = dict()
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
	print('Success on the SHFE history data on %s'%str(datetime.date.today()))
except Exception as e:
	print("ERROR: %s"%str(e))
	send_mail(str(e), 'Process SHFE history data Failed on %s'%str(datetime.date.today()))

EOF

rm -rf $FOLDER
