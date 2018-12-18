YEAR=2010
MONTH=04


if [[ -z ${ARCHIVE_DIR} ]]; then
	echo "ERROR: no ardir set"
	exit 1
fi

FOLDER="/tmp/download_"`date '+%Y%m%d_%H%M%S'`
mkdir -p $FOLDER
echo "Tmp folders is ${FOLDER}"

TARGET=${ARCHIVE_DIR}/CFFEX/
cd $FOLDER

LAST=`ls -tr ${TARGET}| grep zip | tail -1 | xargs basename`
if [ ! -z "$LAST" ] ; then
	YEAR=${LAST:0:4}
	MONTH=${LAST:4:2}
fi
CURRENT=`date '+%Y%m'`
LAST=${YEAR}${MONTH}
ERROR=0
MSG=""

while [[ $((CURRENT-LAST)) -ge 0 ]] ;
do
	wget "http://www.cffex.com.cn/sj/historysj/$LAST/zip/${LAST}.zip" 
	if [[ $? -ne 0 ]] ; then
		ERROR = 1
		MSG="Failed to download ${LAST}"
		break
	fi
	unzip ${LAST}.zip
	if [[ $? -ne 0 ]]; then
		ERROR = 1
		MSG="Failed to unzip ${LAST}.zip"
		break
	fi
	mv ${LAST}.zip $TARGET

	MONTH=$((MONTH+1))
	if [[ $MONTH -gt 12 ]]; then
		MONTH=1
		YEAR=$((YEAR+1))
	fi

	if [[ $MONTH -lt 10 ]]; then
		LAST=${YEAR}0${MONTH}
	else
		LAST=${YEAR}${MONTH}
	fi

done
cd ../


LAST_DAY=""
MD_TARGET=${MD_DIR}/CFFEX

rm -rf $FOLDER/*

LAST_FILE="${MD_DIR}/CFFEX/.last"

if [ -f ${LAST_FILE} ]; then
	LAST_DAY=`cat $LAST_FILE`
else
	LAST_DAY='20100101'
fi

ls --color=none $ARCHIVE_DIR/CFFEX/*.zip | xargs -I {} basename {} | awk -v var=${LAST_DAY:0:6} '$1 >= var' | sort | xargs -I {} unzip $ARCHIVE_DIR/CFFEX/{} -d $FOLDER/
ls --color=none $FOLDER/*.csv | xargs -I {} basename {} | awk -v var=${LAST_DAY}_9 '$1 <= var' | xargs -I {} rm $FOLDER/{}

python3 << EOF
from os import listdir
from os.path import isfile, join
import datetime
from Tools.Mail import *

output_files=dict()

def get_file(id):
	if id not in output_files:
		existing = isfile("${MD_DIR}/CFFEX/%s_md.csv"%id)
		output_files[id] = open("${MD_DIR}/CFFEX/%s_md.csv"%id, 'a')
		if not existing:
			output_files[id].write('#date|open|high|low|close|volume|turnover|outstanding|contractName\n')
	return output_files[id]

def process_lines(key, lines, date_str):
	def _t(token):
		s = token.strip()
		return token if len(token) > 0 else '0.0'
	if len(lines) == 3:
		# we only keep the major contract for bond, based on the turnover, as its liquity is too low
		def local_compare(x):
			a = x.split(',')
			return 0.0 if a[5] is None or len(a[5]) == 0 else float(a[5])
		line = max(lines,key = local_compare)
		token = line.split(',')
		f = get_file(key)
		f.write('%s,%s,%s,%s,%s,%s,%s,%s,%s\n'%(date_str, _t(token[1]), _t(token[2]), _t(token[3]), _t(token[7]), _t(token[4]), _t(token[5]), _t(token[6]), _t(token[0])))

	elif len(lines) == 4:
		# On index future, we have C0 => Current month continuous, C1 => Next month continuous; S0 => Following 1st season continuous, S1 => Following 2nd season continuous
		file_names = ['C0','C1', 'S0', 'S1']
		for i in range(0, 4):
			token = lines[i].split(',')
			f = get_file(key+'_'+file_names[i])
			f.write('%s,%s,%s,%s,%s,%s,%s,%s,%s\n'%(date_str, _t(token[1]), _t(token[2]), _t(token[3]), _t(token[7]), _t(token[4]), _t(token[5]), _t(token[6]), _t(token[0])))
		

def handle_file(path, filename):
	date_str = filename[0:8]
	md_maps = {'IF':[], 'IC':[], 'IH':[], 'TS':[], 'TF':[], 'T':[] }
	lines = []
	with open(join(input_dir, filename), 'rb') as f:
		content = f.read()
		lines = ''.join(chr(i) for i in content if i < 128).split('\n')
	line_map = dict()
	for line in lines:
		if line.startswith('IF'):
			md_maps['IF'].append(line.strip())
		elif line.startswith('IC'):
			md_maps['IC'].append(line.strip())
		elif line.startswith('IH'):
			md_maps['IH'].append(line.strip())
		elif line.startswith('TS'):
			md_maps['TS'].append(line.strip())
		elif line.startswith('TF'):
			md_maps['TF'].append(line.strip())
		elif line.startswith('T'):
			md_maps['T'].append(line.strip())
	
	for key in md_maps:
		if len(md_maps[key]) > 0:
			process_lines(key, md_maps[key], date_str)


input_dir="$FOLDER"
last_file=None
files = [f for f in listdir(input_dir) if isfile(join(input_dir, f))]
try:
	for f in sorted(files):
		handle_file(input_dir, f)
		last_file=f[0:8]

	for f in output_files.values():
		f.close()

	if last_file is not None:
		with open("$LAST_FILE",'w') as f:
			f.write(last_file)
	print('Success on the CFFEX data on %s'%str(datetime.date.today()))
except Exception as e:
	send_mail(str(e), 'Process CFFEX data Failed on %s'%str(datetime.date.today()))

EOF

rm -rf $FOLDER
