import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
# For guessing MIME type based on file name extension
import mimetypes

from email import encoders
from email.message import Message
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import os

sender='kylinsnake@gmail.com'
receiver = '250446897@qq.com'
server_name = 'smtp.gmail.com'
port = 465

f=open(os.environ['HOME']+'/.passwd')
passwd = f.readlines()[0].strip()
f.close()

def send_mail(content = "", subject = "", is_html = False, attachments = list(), resources = dict()):
	msg_root = MIMEMultipart('mixed')
	msg_root['From']=formataddr(["ruyunli", sender])
	msg_root['To'] = formataddr(['250446897', receiver])
	msg_root['Subject'] = subject

	is_set = False

	def pack_attachment(full_name):
		if not os.path.isfile(full_name):
			return None
		ctype, encoding = mimetypes.guess_type(full_name)
		if ctype is None or encoding is not None:
			ctype = 'application/octet-stream'
		maintype, subtype = ctype.split('/', 1)

		fp = None

		try:
			if maintype == 'text':
				fp = open(full_name)
				return MIMEText(fp.read(), _subtype=subtype, _charset='utf=8')

			if maintype == 'image':
				fp = open(full_name, 'rb')
				return MIMEImage(fp.read(), _subtype=subtype)

			if maintype == 'audio':
				fp = open(full_name, 'rb')
				return MIMEAudio(fp.read(), _subtype=subtype)

			fp = open(full_name, 'rb')
			msg = MIMEBase(maintype, subtype)
			msg.set_payload(fp.read())
			# Encode the payload using Base64
			encoders.encode_base64(msg)
			return msg
		finally:
			if fp is not None:
				fp.close()

	for full_path in attachments:
		attachment = pack_attachment(full_path)
		(path, filename) = os.path.split(full_path)
		attachment.add_header('Content-Disposition', 'attachment', filename=filename)
		msg_root.attach(attachment)
		is_set = True	
	
	msg_related = msg_root
	if len(content) > 0 or len(resources.keys()) > 0:
		if len(attachments) > 0:
			msg_related = MIMEMultipart('related')
			msg_root.attach(msg_related)
		for key in resources:
			attachment = pack_attachment(resources[key])
			attachment.add_header('Content-ID', '<%s>'%key)
			msg_related.attach(attachment)
			is_set = True
	
		if len(content) > 0:
			msg_text = msg_related
			if len(resources.keys()) > 0:
				msg_text = MIMEMultipart('alternative')
				msg_related.attach(msg_text)
			if is_html:
				msg_text.attach(MIMEText(content, 'html', 'utf-8'))
			else:
				msg_text.attach(MIMEText(content, 'plain', 'utf-8'))
			is_set = True
	
	if is_set:
		__send__(msg_root)

def __send__(msg):
	try:
		data = msg.as_string()
		print('Ready to send mail, length = %d'%len(data))
		server=smtplib.SMTP_SSL(server_name, port, timeout=60)
		server.login(sender, passwd)
		server.sendmail(sender, [receiver], data)
		server.quit()
	except Exception as a:
		print("error happen: %s, %s"%(str(a), type(a)))
		return False
	print("Success")
	return True


if __name__ == '__main__':
	mail_msg = """
	<p>Python Mail Test...</p>
	<p><a href="http://www.bing.com">Linkage</a></p>
	<p>Pictures is following:</p>
	<p><img src="cid:image1"></p>
	"""
	#send_mail(mail_msg,'My Test', attachments=['/tmp/1.xz'], is_html = True, resources = {'image1':'/tmp/test.jpg'})
