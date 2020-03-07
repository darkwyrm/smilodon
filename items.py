class ClientItem():
	def __init__(self):
		self.id = ''
		self.type = ''
		self.attachments = list()


class Message(ClientItem):
	def __init__(self):
		ClientItem.__init__(self)
		self.type = 'message'
		self.version = 1.0
		self.sender = ''
		self.recipients = list()
		self.ccrecipients = list()
		self.bccrecipients = list()
		self.date = ''
		self.subject = ''
		self.body = ''
		self.thread_id = ''


class Note(ClientItem):
	def __init__(self):
		ClientItem.__init__(self)
		self.type = 'note'
		self.version = 1.0
		self.title = ''
		self.body = ''
		self.notebook = ''
		self.created = ''
		self.updated = ''
		self.tags = list()


